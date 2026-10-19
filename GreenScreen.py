import pyrealsense2 as rs
import numpy as np
import cv2
import os
os.environ["DISPLAY"] = ':0.0'

pipeline = rs.pipeline()
config = rs.config()

config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

pipeline.start(config)

align = rs.align(rs.stream.color)

try:
    while True:
        frames = pipeline.wait_for_frames()
        frames = align.process(frames)

        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        # Convert raw depth values to meters
        depth_scale = pipeline.get_active_profile() \
            .get_device() \
            .first_depth_sensor() \
            .get_depth_scale()

        depth_meters = depth_image * depth_scale

        # Make everything farther than 4 meters black
        color_image[depth_meters > 4.0] = 0

        cv2.imshow("Less Than 4 Meters", color_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()