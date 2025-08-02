#!/usr/bin/env/python3
# File name   : FPV.py
# Description : for FPV video and OpenCV functions
# Website     : www.adeept.com
# E-mail      : support@adeept.com
# Author      : William(Based on Adrian Rosebrock's OpenCV code on pyimagesearch.com)
# Date        : 2018/08/22
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
import datetime
from rpi_ws281x import Color
import move
import logging

class FPV: 
    def __init__(self, led_instance=None):
        self.led = led_instance
        self.frame_num = 0
        self.fps = 0

        # OpenCV settings
        self.colorUpper = (44, 255, 255)
        self.colorLower = (24, 100, 100)

        # State variables
        self.y_lock = 0
        self.x_lock = 0
        self.tor = 17 # Tolerance for color tracking
        self.find_color_mode = False
        self.watch_dog_mode = False
        self.state_lock = threading.Lock()

    def FindColor(self, enabled):
        with self.state_lock:
            self.find_color_mode = bool(enabled)
            logging.info(f"FindColor mode set to: {self.find_color_mode}")
        if not self.find_color_mode:
            move.look_home()

    def WatchDog(self, enabled):
        with self.state_lock:
            self.watch_dog_mode = bool(enabled)
            logging.info(f"WatchDog mode set to: {self.watch_dog_mode}")

    def capture_thread(self, IPinver):
        ap = argparse.ArgumentParser()
        ap.add_argument("-b", "--buffer", type=int, default=64, help="max buffer size")
        args = vars(ap.parse_args())
        pts = deque(maxlen=args["buffer"])

        font = cv2.FONT_HERSHEY_SIMPLEX

        with picamera.PiCamera() as camera:
            camera.resolution = (640, 480)
            camera.framerate = 20
            rawCapture = PiRGBArray(camera, size=(640, 480))

            context = zmq.Context()
            footage_socket = context.socket(zmq.PUB)
            try:
                footage_socket.connect(f'tcp://{IPinver}:5555')
            except zmq.ZMQError as e:
                logging.error(f"Could not connect ZMQ socket: {e}")
                return

            avg = None
            lastMovtionCaptured = datetime.datetime.now()

            for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
                frame_image = frame.array
                cv2.line(frame_image,(300,240),(340,240),(128,255,128),1)
                cv2.line(frame_image,(320,220),(320,260),(128,255,128),1)
                timestamp = datetime.datetime.now()

                with self.state_lock:
                    find_color = self.find_color_mode
                    watch_dog = self.watch_dog_mode

                if find_color:
                    self._process_find_color(frame_image, pts, args, font)
                
                if watch_dog:
                    avg, lastMovtionCaptured = self._process_watch_dog(frame_image, avg, lastMovtionCaptured, timestamp)

                encoded, buffer = cv2.imencode('.jpg', frame_image)
                jpg_as_text = base64.b64encode(buffer)
                try:
                    footage_socket.send(jpg_as_text)
                except zmq.ZMQError as e:
                    logging.error(f"ZMQ error on send: {e}. Closing FPV thread.")
                    break

                rawCapture.truncate(0)

    def _process_find_color(self, frame_image, pts, args, font):
        hsv = cv2.cvtColor(frame_image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.colorLower, self.colorUpper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

        if len(cnts) > 0:
            cv2.putText(frame_image, 'Target Detected', (40,60), font, 0.5, (255,255,255), 1, cv2.LINE_AA)
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)

            if radius > 10:
                cv2.rectangle(frame_image, (int(x-radius), int(y+radius)), (int(x+radius), int(y-radius)), (255,255,255), 1)

            # Dead-zone tracking logic
            self.y_lock = 1 if (240 - self.tor) < y < (240 + self.tor) else 0
            self.x_lock = 1 if (320 - self.tor) < x < (320 + self.tor) else 0

            if self.x_lock and self.y_lock:
                if self.led: self.led.breath_color_set('red')
        else:
            cv2.putText(frame_image, 'Target Detecting', (40,60), font, 0.5, (255,255,255), 1, cv2.LINE_AA)
            if self.led: self.led.breath_color_set('yellow')

    def _process_watch_dog(self, frame_image, avg, lastMovtionCaptured, timestamp):
        gray = cv2.cvtColor(frame_image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if avg is None:
            logging.info("Starting background model for WatchDog...")
            avg = gray.copy().astype("float")
            return avg, lastMovtionCaptured

        cv2.accumulateWeighted(gray, avg, 0.5)
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

        thresh = cv2.threshold(frameDelta, 5, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        motion_detected = False
        for c in cnts:
            if cv2.contourArea(c) < 5000:
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame_image, (x, y), (x + w, y + h), (128, 255, 0), 1)
            motion_detected = True

        if motion_detected:
            if self.led: self.led.breath_color_set('red')
            lastMovtionCaptured = timestamp
        elif (timestamp - lastMovtionCaptured).seconds >= 0.5:
            if self.led: self.led.breath_color_set('blue')

        return avg, lastMovtionCaptured

if __name__ == '__main__':
    # This is for testing FPV.py directly
    # You would need to mock the LED class or run it without LED support
    logging.basicConfig(level=logging.INFO)
    fpv_test = FPV()
    try:
        # Replace with a valid IP for testing
        fpv_test.capture_thread('127.0.0.1')
    except KeyboardInterrupt:
        logging.info("FPV test stopped by user.")
