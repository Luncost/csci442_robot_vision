from ultralytics import YOLO
import pyrealsense2 as rs
import numpy as np
import cv2 as cv
import os
os.environ["DISPLAY"] = ':0.0'

pipeline = rs.pipeline()
config = rs.config()

config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

pipeline.start(config)

align = rs.align(rs.stream.color)

model = YOLO("best_ncnn_model")

try:
    while True:
        frames = pipeline.wait_for_frames()
        frames = align.process(frames)

        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())

        results = model.track(color_image, persist=True, conf=0.5, imgsz=320)
        annotated = results[0].plot()   # BGR numpy array with boxes drawn
        cv.imshow("track", annotated)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
    cv.destroyAllWindows()
