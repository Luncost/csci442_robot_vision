import pyrealsense2 as rs
import numpy as np
import cv2 as cv
import os
import robot_controller as controller

os.environ["DISPLAY"] = ':0.0'


pipeline = rs.pipeline()
config = rs.config()
robot = controller.RobotController(simulation_mode = False)

maxValue = 255
maxValueH = 360//2
lowH = 0
lowS = 0
lowV = 0
highH = maxValueH
highS = maxValue
highV = maxValue
realSenseCameraName = "Video"
resetButtonName = "Reset"
HSVFrame = None
INIT = (0, 0, 0, maxValueH, maxValue, maxValue)
resetEnables = 0

def resetHSV(enabled):
    if (enabled == 1):
        global lowH, lowS, lowV, highH, highS, highV, sampled
        lowH, lowS, lowV, highH, highS, highV = INIT
        sampled = False          # the next click starts a fresh sample

        if k == ord('r'):
            resetHSV()


# End Reset

cv.namedWindow(realSenseCameraName)

# Define mouse input event
hsvRange = 10
panStep = 0.01   # fraction of head pan range moved per frame
tiltStep = 0.01  # Head tilt per frame movement
sampled = False  # global

def getHSVValue(event, x, y, flags, param):
    global lowH, lowS, lowV, highH, highS, highV, sampled
    if event != cv.EVENT_LBUTTONDOWN or HSVFrame is None:
        return
    h, s, v = (int(c) for c in HSVFrame[y, x])   # cast from np.uint8
    if not sampled:
        lowH, lowS, lowV = h-hsvRange, s-hsvRange, v-hsvRange
        highH, highS, highV = h+hsvRange, s+hsvRange, v+hsvRange
        sampled = True
    else:
        #lowH, highH = max(0, min(lowH, h-hsvRange)), min(maxValueH, (highH, h+hsvRange))
        lowH, highH = min(lowH, h), max(highH, h)
        lowS, highS = min(lowS, s), max(highS, s)
        lowV, highV = min(lowV, v), max(highV, v)
        # same for S and V
    print(f"Current -> H({lowH} -> {highH}), S({lowS} -> {highS}), V({lowV} -> {highV})")

cv.setMouseCallback(realSenseCameraName, getHSVValue)

try:
    pipeline.start()
    while True:
            frames = pipeline.wait_for_frames()
            
            color_frame = frames.get_color_frame()
            
            if not color_frame:
                continue

            image = np.asanyarray(color_frame.get_data())
            
            frameH, frameW = image.shape[:2]
            cx, cy = frameW // 2, frameH // 2
            half = 50

            rectangleTL = (cx - half, cy - half)
            rectangleBR = (cx + half, cy + half)



            HSVFrame = cv.cvtColor(image, cv.COLOR_BGR2HSV)
            
            thresholdFrame = cv.inRange(HSVFrame, (lowH, lowS, lowV), (highH, highS, highV))

            contours, _ = cv.findContours(thresholdFrame, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
           #cv.drawContours(image, contours, -1, (0, 255, 0), 2)
            minArea = 500
            big = [c for c in contours if cv.contourArea(c) >= minArea]   # same filter as your loop's `continue`

            inTarget = False
            objX = None                               # stays None if nothing is detected this frame
            if big:                                   # empty list = nothing detected this frame
                c = max(big, key=cv.contourArea)      # the one object you track
                x, y, w, h = cv.boundingRect(c)
                cv.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

                M = cv.moments(c)
                if M["m00"] != 0:
                    objX, objY = int(M["m10"] / M["m00"]), int (M["m01"] / M["m00"])
                    cv.circle(image, (objX, objY), 5, (0, 0, 255), -1)
                    inTarget = (rectangleTL[0] <= objX <= rectangleBR[0] and
                                    rectangleTL[1] <= objY <= rectangleBR[1])

            rectangleColor = (0, 255, 0) if inTarget else (0, 0, 255)
            cv.rectangle(image, rectangleTL, rectangleBR, rectangleColor, 2)
            

            if objX is not None:
                # Pan only when the object is left/right of the target box
                if objX < rectangleTL[0]:
                    robot.set_head_pan(robot.get_head_pan() + panStep)

                elif objX > rectangleBR[0]:
                    robot.set_head_pan(robot.get_head_pan() - panStep)


                if objY < rectangleTL[1]:
                    robot.set_head_tilt(robot.get_head_tilt() + tiltStep) 
  
                elif objY > rectangleBR[1]:
                    robot.set_head_tilt(robot.get_head_tilt() - tiltStep)           

            cv.imshow(realSenseCameraName, image)
            
            k = cv.waitKey(30)
            if k == ord('q') or k == 27:
                break


finally:
    #pipeline.stop()
    cv.destroyAllWindows()
