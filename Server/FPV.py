#!/usr/bin/env/python3
# File name   : FPV.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/26

import time
import threading
import cv2
import zmq
import base64
import picamera2
import libcamera

from picamera2 import Picamera2, Preview
import io
import argparse
import imutils
from collections import deque
import psutil
import PID
import datetime
import Switch as switch
import numpy as np 

pid = PID.PID()
pid.SetKp(0.5)
pid.SetKd(0)
pid.SetKi(0)
FindColorMode = 0
WatchDogMode  = 0

colorUpper = np.array([44, 255, 255])
colorLower = np.array([24, 100, 100])
hflip = 0  # Video flip horizontally: 0 or 1
vflip = 0  # Video vertical flip: 0/1
picam2 = Picamera2()
preview_config = picam2.preview_configuration
preview_config.size = (640, 480)
preview_config.format = 'RGB888'  # 'XRGB8888', 'XBGR8888', 'RGB888', 'BGR888', 'YUV420'
preview_config.transform = libcamera.Transform(hflip=hflip, vflip=vflip)
preview_config.colour_space = libcamera.ColorSpace.Sycc()
preview_config.buffer_count = 4
preview_config.queue = True

if not picam2.is_open:
    raise RuntimeError('Could not start camera.')
try:
    picam2.start()
except Exception as e:
    print(f"\033[38;5;1mError:\033[0m\n{e}")
    print("\nPlease check whether the camera is connected well, and disable the \"legacy camera driver\" on raspi-config")



class FPV: 
    def __init__(self):
        self.frame_num = 0
        self.fps = 0

    def SetIP(self,invar):
        self.IP = invar

    def colorFindSet(self, invarH, invarS, invarV):
        global colorUpper, colorLower
        HUE_1 = invarH + 100
        HUE_2 = invarH - 100
        if HUE_1 > 255:
            HUE_1 = 255
        if HUE_2 < 0:
            HUE_2 = 0
    
        SAT_1 = invarS + 100
        SAT_2 = invarS - 100
        if SAT_1 > 255:
            SAT_1 = 255
        if SAT_2 < 0:
            SAT_2 = 0

        VAL_1 = invarV + 100
        VAL_2 = invarV - 100
        if VAL_1 > 255:
            VAL_1 = 255
        if VAL_2 < 0:
            VAL_2 = 0

        colorUpper = np.array([HUE_1, SAT_1, VAL_1])
        colorLower = np.array([HUE_2, SAT_2, VAL_2])
        print(colorUpper)
        print(colorLower)
    def FindColor(self,invar):
        global FindColorMode
        FindColorMode = invar


    def WatchDog(self,invar):
        global WatchDogMode
        WatchDogMode = invar



    def capture_thread(self,IPinver):
        global frame_image,picam2,colorUpper, colorLower#Z
        ap = argparse.ArgumentParser()            #OpenCV initialization
        ap.add_argument("-b", "--buffer", type=int, default=64,
            help="max buffer size")
        args = vars(ap.parse_args())

        font = cv2.FONT_HERSHEY_SIMPLEX

        context = zmq.Context()
        footage_socket = context.socket(zmq.PAIR)
        print(IPinver)
        footage_socket.connect('tcp://%s:5555'%IPinver)

        avg = None
        motionCounter = 0

        while True:
            frame_image = picam2.capture_array()
            cv2.line(frame_image,(300,240),(340,240),(128,255,128),1)
            cv2.line(frame_image,(320,220),(320,260),(128,255,128),1)

            if FindColorMode:
                ####>>>OpenCV Start<<<####
                hsv = cv2.cvtColor(frame_image, cv2.COLOR_BGR2RGB)
                mask = cv2.inRange(hsv, colorLower, colorUpper)#1
                mask = cv2.erode(mask, None, iterations=2)
                mask = cv2.dilate(mask, None, iterations=2)
                cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE)[-2]
                center = None
                if len(cnts) > 0:
                    cv2.putText(frame_image,'Target Detected',(40,60), font, 0.5,(255,255,255),1,cv2.LINE_AA)
                    c = max(cnts, key=cv2.contourArea)
                    ((x, y), radius) = cv2.minEnclosingCircle(c)
                    M = cv2.moments(c)
                    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                    X = int(x)
                    Y = int(y)
                    if radius > 10:
                        cv2.rectangle(frame_image,(int(x-radius),int(y+radius)),(int(x+radius),int(y-radius)),(255,255,255),1)
                else:
                    cv2.putText(frame_image,'Target Detecting',(40,60), font, 0.5,(255,255,255),1,cv2.LINE_AA)
            if WatchDogMode:
                gray = cv2.cvtColor(frame_image, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)

                if avg is None:
                    print("[INFO] starting background model...")
                    avg = gray.copy().astype("float")
                    continue

                cv2.accumulateWeighted(gray, avg, 0.5)
                frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

                thresh = cv2.threshold(frameDelta, 5, 255,
                    cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)
                cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE)
                cnts = imutils.grab_contours(cnts)
                for c in cnts:
                    # if the contour is too small, ignore it
                    if cv2.contourArea(c) < 5000:
                        continue
             
                    # compute the bounding box for the contour, draw it on the frame,
                    # and update the text
                    (x, y, w, h) = cv2.boundingRect(c)
                    cv2.rectangle(frame_image, (x, y), (x + w, y + h), (128, 255, 0), 1)
                    text = "Occupied"
                    motionCounter += 1
            encoded, buffer = cv2.imencode('.jpg', frame_image)
            jpg_as_text = base64.b64encode(buffer)
            footage_socket.send(jpg_as_text)


if __name__ == '__main__':
    fpv=FPV()
    while 1:
        fpv.capture_thread('192.168.3.199')
        pass

