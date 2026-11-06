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

pipeline.start(config)


# Align depth pixels with RGB pixels
align = rs.align(rs.stream.color)

# Robot setup: start head at a known tilt
robot = controller.RobotController(simulation_mode=False)
robot._set_servo('head_tilt', 5500)
time.sleep(0.5)
tilt_steps = 0

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

        # Detect faces (Haar cascades work on grayscale)
        gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
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

        cv2.imshow(
            "RealSense RGB",
            color_image
        )

        if tilt_steps >= 600:
            robot._set_servo('head_tilt', 5500)
            time.sleep(0.5)
            tilt_steps = 0;
            
        
        # Gradually tilt head, one step per frame
        if tilt_steps < 600:
            robot.set_head_tilt(robot.get_head_tilt() + 0.001)
            tilt_steps += 1
        

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break


finally:

    pipeline.stop()
    cv2.destroyAllWindows()
    robot.close()
