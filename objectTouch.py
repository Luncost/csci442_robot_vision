from ultralytics import YOLO
import pyrealsense2 as rs
import numpy as np
import cv2 as cv
import os
import robot_controller as controller

import time

os.environ["DISPLAY"] = ':0.0'

# Pick which object to track before anything starts
OBJECTS = {0: "red ball", 1: "masking tape", 2: "screwdriver"}
while True:
    choice = input("Track which object? 0 = ball, 1 = tape, 2 = screwdriver: ").strip()
    if choice.isdigit() and int(choice) in OBJECTS:
        TARGET_CLASS = int(choice)
        break
    print("Invalid choice, enter 0, 1, or 2.")
print(f"Tracking: {OBJECTS[TARGET_CLASS]}")

pipeline = rs.pipeline()
config = rs.config()

config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

profile = pipeline.start(config)
depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()

align = rs.align(rs.stream.color)

robot = controller.RobotController(simulation_mode=False)
tiltStep = 0.01  # Head tilt per frame movement
wheelTurnStep = 0.01
wheelForward = 0.01
STOP_DIST = 0.35; #Meters



model = YOLO("best_ncnn_model")

# Fixed target box (x1, y1, x2, y2), centered in the 640x480 frame (This is the target)
BOX_W, BOX_H = 150, 150
TARGET = (320 - BOX_W // 2, 240 - BOX_H // 2, 320 + BOX_W // 2, 240 + BOX_H // 2)

def overlaps(a, b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]

robot.set_head_tilt(robot.get_head_tilt() - 0.1)

try:
    while True:
        frames = pipeline.wait_for_frames()
        frames = align.process(frames)

        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())
        
        depth_image = np.asanyarray(depth_frame.get_data())
        depth_meters = depth_image * depth_scale

        
        # color_image[depth_meters > 0.5] = 0

        results = model.track(color_image, persist=True, conf=0.5, imgsz=320, classes=[TARGET_CLASS])
        annotated = results[0].plot()   # BGR numpy array with boxes drawn

        boxes = results[0].boxes.xyxy.cpu().numpy()
        touching = any(overlaps(b, TARGET) for b in boxes)

        color = (0, 255, 0) if touching else (0, 0, 255)
        cv.rectangle(annotated, TARGET[:2], TARGET[2:], color, 3)



        # Tilt toward the most object's center until it's inside the box and if the object
        if (len(boxes)):
            x1, y1, x2, y2 = boxes[results[0].boxes.conf.cpu().numpy().argmax()]
            objY = (y1 + y2) / 2
            objX = (x1 + x2) / 2

            # Median depth of a small patch at the object's center, ignoring 0 (no reading)
            cx, cy = int(objX), int(objY)
            patch = depth_meters[max(cy - 50, 0):cy + 50, max(cx - 50, 0):cx + 50]
            valid = patch[patch > 0]
            dist = np.median(valid) if valid.size else None

            if dist is not None and dist <= STOP_DIST:
                robot.drive(0, 0)
                robot._set_servo('right_elbow', 10000)
                time.sleep(5)
                robot._set_servo('right_shoulder1', 10000)
                time.sleep(5)
                #TODO: Make a for loop that puts a delay between setting the right shoulder 2
                #       movement for n times using _get_normalized and _set_normalized
                robot._set_servo('right_shoulder2', 7500)
                time.sleep(5)
                break;
                
            else:
                # Head tilt to meet the target y position
                if objY < TARGET[1]:
                    robot.set_head_tilt(robot.get_head_tilt() + tiltStep)
                elif objY > TARGET[3]:
                    robot.set_head_tilt(robot.get_head_tilt() - tiltStep)
            
                # Rotate wheels to meet the target x position
                if objX < TARGET[0]:
                    robot.drive(wheelTurnStep, -wheelTurnStep)
                elif objX > TARGET[2]:
                    robot.drive(-wheelTurnStep, wheelTurnStep)
                else:
                    robot.drive(wheelForward, wheelForward)

        # Stop robot motion if no object is detected
        else:
            robot.drive(0, 0)


        cv.imshow("track", annotated)


        if cv.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
    robot.close()
    cv.destroyAllWindows()
