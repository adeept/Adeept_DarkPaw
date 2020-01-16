#!/usr/bin/env/python3
# File name   : server.py
# Description : for FPV video and OpenCV functions
# Website     : www.gewbot.com
# Author      : William(Based on Adrian Rosebrock's OpenCV code on pyimagesearch.com)
# Date        : 2019/08/28

import time
import threading
import cv2
import zmq
import base64
import picamera
from picamera.array import PiRGBArray
import argparse
import imutils
from collections import deque
import psutil
import os
import SpiderG
import PID
import LED
import datetime
from rpi_ws281x import *
import switch
import numpy as np #1

pid = PID.PID()
pid.SetKp(0.5)
pid.SetKd(0)
pid.SetKi(0)
Y_lock = 0
X_lock = 0
tor    = 17
FindColorMode = 0
WatchDogMode  = 0
UltraData = 3
LED  = LED.LED()

#2
CVrun = 1
FindLineMode = 0
linePos_1 = 440
linePos_2 = 380
lineColorSet = 255
frameRender = 0
findLineError = 20

SpiderG.move_init()#2

#2
camera = picamera.PiCamera() 
camera.resolution = (640, 480)
camera.framerate = 20
rawCapture = PiRGBArray(camera, size=(640, 480))

temp = 0
def findLineCtrl(posInput, setCenter):#2
    global temp
    temp+=1
    if posInput and temp >= 20:
        if posInput > (setCenter + findLineError):
            temp = 0
            SpiderG.walk('turnright')#2
            time.sleep(0.2)
            pass
        elif posInput < (setCenter - findLineError):
            temp = 0
            SpiderG.walk('turnleft')#2
            time.sleep(0.2)
            pass
        else:
            if CVrun:
                # move.move(80, 'forward', 'no', 0.5)
                SpiderG.walk('forward')#2
            #forward
            pass
    else:
        # if CVrun:
        #   try:
        #       move.motorStop()
        #   except Exception as e:
        #       print(e)
        #   move.move(80, 'backward', 'no', 0.5)
        pass

def cvFindLine():#2
    global frame_findline, camera#3
    # camera.exposure_mode = 'off'
    frame_findline = cv2.cvtColor(frame_image, cv2.COLOR_BGR2GRAY)
    retval, frame_findline =  cv2.threshold(frame_findline, 0, 255, cv2.THRESH_OTSU)# 对图片进行二值化处理
    frame_findline = cv2.erode(frame_findline, None, iterations=6)# 侵蚀
    colorPos_1 = frame_findline[linePos_1]
    colorPos_2 = frame_findline[linePos_2]

    try:
        lineColorCount_Pos1 = np.sum(colorPos_1 == lineColorSet)
        lineColorCount_Pos2 = np.sum(colorPos_2 == lineColorSet)

        lineIndex_Pos1 = np.where(colorPos_1 == lineColorSet)
        lineIndex_Pos2 = np.where(colorPos_2 == lineColorSet)

        if lineColorCount_Pos1 == 0:
            lineColorCount_Pos1 = 1
        if lineColorCount_Pos2 == 0:
            lineColorCount_Pos2 = 1

        left_Pos1 = lineIndex_Pos1[0][lineColorCount_Pos1-1]
        right_Pos1 = lineIndex_Pos1[0][0]
        center_Pos1 = int((left_Pos1+right_Pos1)/2)

        left_Pos2 = lineIndex_Pos2[0][lineColorCount_Pos2-1]
        right_Pos2 = lineIndex_Pos2[0][0]
        center_Pos2 = int((left_Pos2+right_Pos2)/2)

        center = int((center_Pos1+center_Pos2)/2)
    except Exception as e:#3
        print(e)
        center = None

    findLineCtrl(center, 320)
    # print(center)
    try:
        if lineColorSet == 255:
            cv2.putText(frame_image,('Following White Line'),(30,50), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(128,255,128),1,cv2.LINE_AA)
            cv2.putText(frame_findline,('Following White Line'),(30,50), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(128,255,128),1,cv2.LINE_AA)
        else:
            cv2.putText(frame_image,('Following Black Line'),(30,50), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(128,255,128),1,cv2.LINE_AA)
            cv2.putText(frame_findline,('Following Black Line'),(30,50), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(128,255,128),1,cv2.LINE_AA)

        if frameRender:
            cv2.line(frame_image,(left_Pos1,(linePos_1+30)),(left_Pos1,(linePos_1-30)),(255,128,64),1)
            cv2.line(frame_image,(right_Pos1,(linePos_1+30)),(right_Pos1,(linePos_1-30)),(64,128,255),)
            cv2.line(frame_image,(0,linePos_1),(640,linePos_1),(255,255,64),1)

            cv2.line(frame_image,(left_Pos2,(linePos_2+30)),(left_Pos2,(linePos_2-30)),(255,128,64),1)
            cv2.line(frame_image,(right_Pos2,(linePos_2+30)),(right_Pos2,(linePos_2-30)),(64,128,255),1)
            cv2.line(frame_image,(0,linePos_2),(640,linePos_2),(255,255,64),1)

            cv2.line(frame_image,((center-20),int((linePos_1+linePos_2)/2)),((center+20),int((linePos_1+linePos_2)/2)),(0,0,0),1)
            cv2.line(frame_image,((center),int((linePos_1+linePos_2)/2+20)),((center),int((linePos_1+linePos_2)/2-20)),(0,0,0),1)
        else:
            cv2.line(frame_findline,(left_Pos1,(linePos_1+30)),(left_Pos1,(linePos_1-30)),(255,128,64),1)
            cv2.line(frame_findline,(right_Pos1,(linePos_1+30)),(right_Pos1,(linePos_1-30)),(64,128,255),1)
            cv2.line(frame_findline,(0,linePos_1),(640,linePos_1),(255,255,64),1)

            cv2.line(frame_findline,(left_Pos2,(linePos_2+30)),(left_Pos2,(linePos_2-30)),(255,128,64),1)
            cv2.line(frame_findline,(right_Pos2,(linePos_2+30)),(right_Pos2,(linePos_2-30)),(64,128,255),1)
            cv2.line(frame_findline,(0,linePos_2),(640,linePos_2),(255,255,64),1)

            cv2.line(frame_findline,((center-20),int((linePos_1+linePos_2)/2)),((center+20),int((linePos_1+linePos_2)/2)),(0,0,0),1)
            cv2.line(frame_findline,((center),int((linePos_1+linePos_2)/2+20)),((center),int((linePos_1+linePos_2)/2-20)),(0,0,0),1)
    except Exception as e:
        print(e)
        pass

class FPV: 
    def __init__(self):
        self.frame_num = 0
        self.fps = 0

        self.colorUpper = (44, 255, 255)
        self.colorLower = (24, 100, 100)


    def SetIP(self,invar):
        self.IP = invar


    def FindColor(self,invar):
        global FindColorMode
        FindColorMode = invar
        # if not FindColorMode: #2
        #     SpiderG.move_init()


    def WatchDog(self,invar):
        global WatchDogMode
        WatchDogMode = invar

    def setExpCom(self,invar):#Z
        if invar > 25:
            invar = 25
        elif invar < -25:
            invar = -25
        else:
            camera.exposure_compensation = invar


    def defaultExpCom(self):#Z
        camera.exposure_compensation = 0


    def UltraData(self,invar):
        global UltraData
        UltraData = invar


    def capture_thread(self,IPinver):
        global frame_image,camera#Z
        ap = argparse.ArgumentParser()            #OpenCV initialization
        ap.add_argument("-b", "--buffer", type=int, default=64,
            help="max buffer size")
        args = vars(ap.parse_args())
        pts = deque(maxlen=args["buffer"])

        font = cv2.FONT_HERSHEY_SIMPLEX

        context = zmq.Context()
        footage_socket = context.socket(zmq.PUB)
        print(IPinver)
        footage_socket.connect('tcp://%s:5555'%IPinver)

        avg = None
        motionCounter = 0
        #time.sleep(4)
        lastMovtionCaptured = datetime.datetime.now()

        for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            frame_image = frame.array
            cv2.line(frame_image,(300,240),(340,240),(128,255,128),1)
            cv2.line(frame_image,(320,220),(320,260),(128,255,128),1)
            timestamp = datetime.datetime.now()

            if FindLineMode:#2
                cvFindLine()
                camera.exposure_mode = 'off'
            else:
                camera.exposure_mode = 'auto'

            if FindColorMode:
                print(FindColorMode)
                ####>>>OpenCV Start<<<####
                hsv = cv2.cvtColor(frame_image, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, self.colorLower, self.colorUpper)
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

                    if Y < (240-tor):
                        error = (240-Y)/5
                        outv = int(round((pid.GenOut(error)),0))
                        SpiderG.up(outv)
                        Y_lock = 0
                    elif Y > (240+tor):
                        error = (Y-240)/5
                        outv = int(round((pid.GenOut(error)),0))
                        SpiderG.down(outv)
                        Y_lock = 0
                    else:
                        Y_lock = 1

                    
                    if X < (320-tor*3):
                        error = (320-X)/5
                        outv = int(round((pid.GenOut(error)),0))
                        SpiderG.lookleft(outv)
                        #move.move(70, 'no', 'left', 0.6)
                        X_lock = 0
                    elif X > (330+tor*3):
                        error = (X-240)/5
                        outv = int(round((pid.GenOut(error)),0))
                        SpiderG.lookright(outv)
                        #move.move(70, 'no', 'right', 0.6)
                        X_lock = 0
                    else:
                        #move.motorStop()
                        X_lock = 1

                    if X_lock == 1 and Y_lock == 1:
                        switch.switch(1,1)
                        switch.switch(2,1)
                        switch.switch(3,1)
                    else:
                        switch.switch(1,0)
                        switch.switch(2,0)
                        switch.switch(3,0)

                        # if UltraData > 0.5:
                        #     move.move(70, 'forward', 'no', 0.6)
                        # elif UltraData < 0.4:
                        #     move.move(70, 'backward', 'no', 0.6)
                        #     print(UltraData)
                        # else:
                        #     move.motorStop()
                    

                else:
                    cv2.putText(frame_image,'Target Detecting',(40,60), font, 0.5,(255,255,255),1,cv2.LINE_AA)

                ####>>>OpenCV Ends<<<####
                

            if WatchDogMode:
                gray = cv2.cvtColor(frame_image, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)

                if avg is None:
                    print("[INFO] starting background model...")
                    avg = gray.copy().astype("float")
                    rawCapture.truncate(0)
                    continue

                cv2.accumulateWeighted(gray, avg, 0.5)
                frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

                # threshold the delta image, dilate the thresholded image to fill
                # in holes, then find contours on thresholded image
                thresh = cv2.threshold(frameDelta, 5, 255,
                    cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)
                cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE)
                cnts = imutils.grab_contours(cnts)
                # print('x')
                # loop over the contours
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
                    #print(motionCounter)
                    #print(text)
                    LED.colorWipe(255,16,0)
                    lastMovtionCaptured = timestamp
                    switch.switch(1,1)
                    switch.switch(2,1)
                    switch.switch(3,1)

                if (timestamp - lastMovtionCaptured).seconds >= 0.5:
                    LED.colorWipe(255,255,0)
                    switch.switch(1,0)
                    switch.switch(2,0)
                    switch.switch(3,0)


            if FindLineMode and not frameRender:#2
                encoded, buffer = cv2.imencode('.jpg', frame_findline)
            else:
                encoded, buffer = cv2.imencode('.jpg', frame_image)
            jpg_as_text = base64.b64encode(buffer)
            footage_socket.send(jpg_as_text)

            rawCapture.truncate(0)


if __name__ == '__main__':
    fpv=FPV()
    while 1:
        fpv.capture_thread('192.168.0.110')
        pass

