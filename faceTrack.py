import pyrealsense2 as rs
import numpy as np
import cv2
import robot_controller as controller
import time
import os

# --------------------------------------------------
# FACE CASCADE SETUP
# --------------------------------------------------

CASCADE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data/haarcascades/haarcascade_frontalface_default.xml"
)

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
assert not face_cascade.empty(), f"Failed to load cascade: {CASCADE_PATH}"

EYE_CASCADE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data/haarcascades/haarcascade_eye.xml"
)

eye_cascade = cv2.CascadeClassifier(EYE_CASCADE_PATH)
assert not eye_cascade.empty(), f"Failed to load cascade: {EYE_CASCADE_PATH}"



# --------------------------------------------------
# REALSENSE SETUP
# --------------------------------------------------

os.environ["DISPLAY"] = ':0.0'
pipeline = rs.pipeline()
config = rs.config()

config.enable_stream(
    rs.stream.depth,
    640,
    480,
    rs.format.z16,
    30
)

config.enable_stream(
    rs.stream.color,
    640,
    480,
    rs.format.bgr8,
    30
)

profile = pipeline.start(config)

depth_scale = pipeline.get_active_profile().get_device().first_depth_sensor().get_depth_scale()

# Color intrinsics (depth is aligned to color): fy = focal length in px, ppy = optical center row
color_intrinsics = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()

# Align depth pixels with RGB pixels
align = rs.align(rs.stream.color)

# Robot setup: start head at a known tilt
robot = controller.RobotController(simulation_mode=False)
robot._set_servo('head_tilt', 5500)
time.sleep(0.5)
tilt_steps = 0

# Face centering tuning
CENTER_TOLERANCE = 30   # px from frame center counted as "centered"
TILT_GAIN = 0.0002      # tilt units per px of error
MAX_TILT_STEP = 0.02    # largest tilt change per frame
TILT_DIRECTION = 1      # flip to -1 if the head moves away from the face

# Fullscreen display window
cv2.namedWindow("RealSense RGB", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("RealSense RGB", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------


try:

    while True:

        frames = pipeline.wait_for_frames()

        # Align depth to RGB
        aligned_frames = align.process(frames)

        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue


        # Convert RGB frame to numpy/OpenCV image
        color_image = np.asanyarray(
            color_frame.get_data()
        )

        # Get the depth image for height estimation
        depth_image = np.asanyarray(
                depth_frame.get_data()
        )


        # Get the depth as meters

        depth_meters = depth_image * depth_scale

        # Detect faces (Haar cascades work on grayscale)
        gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=5,
            minSize=(40, 40)
        )

        # Draw a box around each detected face
        for (x, y, w, h) in faces:
            cv2.rectangle(
                color_image,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

        if len(faces) > 0:
            # Center on the largest face vertically
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

            # Find eyes in the top half of box (eliminates mouth and noze false positives)
            face_top = gray[y:y + h // 2, x:x + w]
            eyes = eye_cascade.detectMultiScale(
                face_top,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(w // 10, w // 10)
            )

            if len(eyes) > 0:
                # Keep the two largest hits and average their centers (frame coords)
                eyes = sorted(eyes, key=lambda e: e[2] * e[3], reverse=True)[:2]
                eye_y = int(np.mean([y + ey + eh / 2 for (ex, ey, ew, eh) in eyes]))
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(color_image, (x + ex, y + ey),
                                  (x + ex + ew, y + ey + eh), (255, 0, 0), 2)
            else:
                # Fallback: eyes sit ~40% down a frontal face box
                eye_y = int(y + 0.4 * h)

            cv2.line(color_image, (x, eye_y), (x + w, eye_y), (0, 0, 255), 1)
            eye_to_top = eye_y - y   # px from eye line to top of face box
            face_center_y = y + h / 2
            frame_center_y = color_image.shape[0] / 2
            error = frame_center_y - face_center_y   # + = face below center

            if abs(error) > CENTER_TOLERANCE:
                # Step size proportional to error, capped at MAX_TILT_STEP
                step = max(-MAX_TILT_STEP, min(MAX_TILT_STEP, error * TILT_GAIN))
                new_tilt = robot.get_head_tilt() + TILT_DIRECTION * step
                robot.set_head_tilt(max(0.0, min(1.0, new_tilt)))


        #---Height calculations
            #head_target = eye_y - (eye_y - y) + 10 
            head_target = y 
            
            cx = x + w // 2   # horizontal center of the face box

            # Median depth over a 5x5 patch, ignoring pixels with no depth 
            patch = depth_meters[max(head_target - 2, 0):head_target + 3,
                                 max(cx - 2, 0):cx + 3]
            valid = patch[patch > 0]

            if valid.size > 0:
                distance = np.median(valid)

                angle = (0.0241 * robot._get_raw('head_tilt')) - 133.64
                # Add the vertical angle from the optical center to the target pixel (above center = +)
                angle += np.degrees(np.arctan((color_intrinsics.ppy - head_target) / color_intrinsics.fy))
                height = distance * np.sin(np.deg2rad(angle)) + 1.016 #1.016 is the height of the camera

                print(f"target height: {height * 3.28084:.2f}, ({height:.2f} Meters)")
            else:
                print("no valid depth at target, skipping frame")

        else:
            # No face: sweep, resetting to start after 600 steps
            if tilt_steps >= 600:
                robot._set_servo('head_tilt', 5500)
                time.sleep(0.5)
                tilt_steps = 0

            robot.set_head_tilt(robot.get_head_tilt() + 0.001)
            tilt_steps += 1


        cv2.imshow("RealSense RGB", color_image)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break


finally:

    pipeline.stop()
    cv2.destroyAllWindows()
    robot.close()
