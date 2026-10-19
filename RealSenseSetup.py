import pyrealsense2 as rs
import numpy as np
import cv2


# --------------------------------------------------
# REALSENSE SETUP
# --------------------------------------------------

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


# --------------------------------------------------
# MOUSE INFORMATION
# --------------------------------------------------

mouse_x = None
mouse_y = None


def mouse_callback(event, x, y, flags, param):
    global mouse_x, mouse_y

    if event == cv2.EVENT_LBUTTONDOWN:
        mouse_x = x
        mouse_y = y


cv2.namedWindow("RealSense RGB")
cv2.setMouseCallback(
    "RealSense RGB",
    mouse_callback
)


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


        # --------------------------------------------------
        # CENTER PIXEL
        # --------------------------------------------------

        height, width = color_image.shape[:2]

        center_x = width // 2
        center_y = height // 2


        # get_distance returns METERS
        center_distance = depth_frame.get_distance(
            center_x,
            center_y
        )


        # Draw center crosshair
        cv2.drawMarker(
            color_image,
            (center_x, center_y),
            (0, 255, 255),
            markerType=cv2.MARKER_CROSS,
            markerSize=30,
            thickness=2
        )


        cv2.putText(
            color_image,
            f"Center: {center_distance:.2f} m",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            2
        )


        # --------------------------------------------------
        # MOUSE CLICK DISTANCE
        # --------------------------------------------------

        if mouse_x is not None:

            mouse_distance = depth_frame.get_distance(
                mouse_x,
                mouse_y
            )

            cv2.circle(
                color_image,
                (mouse_x, mouse_y),
                6,
                (0, 255, 0),
                -1
            )

            cv2.putText(
                color_image,
                f"{mouse_distance:.2f} m",
                (mouse_x + 10, mouse_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )


        cv2.imshow(
            "RealSense RGB",
            color_image
        )


        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break


finally:

    pipeline.stop()
    cv2.destroyAllWindows()