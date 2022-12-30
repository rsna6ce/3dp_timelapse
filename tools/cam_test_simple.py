#!/usr/bin/env python3
import sys
import cv2

cam_name = '/dev/video0'
cam_width = 640#1280
cam_height = 360#720
cam_fps = 30

args = sys.argv
if len(args) > 1:
    cam_name = args[1]
cap = cv2.VideoCapture(cam_name)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,cam_height)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FPS, cam_fps)

print('press esc to exit.')
while True:
    ret, frame = cap.read()
    height, width, channels = frame.shape[:3]
    cv2.imshow('camera' , frame)
    key_esc = 27
    key =cv2.waitKey(10)
    if key == key_esc:
        break
cap.release()
cv2.destroyAllWindows()