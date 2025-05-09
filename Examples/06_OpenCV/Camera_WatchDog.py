#!/usr/bin/env/python3
# File name   : Camera_WatchDog.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/24
import time
import cv2
import imutils
import numpy as np
from picamera2 import Picamera2
import libcamera
from base_camera import BaseCamera
import datetime
from flask import Flask, render_template, Response

hflip = 0
vflip = 0
ImgIsNone = 0
app = Flask(__name__)


class Camera(BaseCamera):
    def __init__(self):
        super().__init__()
        self.avg = None
        self.drawing = 0
        self.motionCounter = 0
        self.lastMovtionCaptured = datetime.datetime.now()

    def watchDog(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.avg is None:
            print("[INFO] starting background model...")
            self.avg = gray.copy().astype("float")
            return frame

        cv2.accumulateWeighted(gray, self.avg, 0.5)
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg))

        thresh = cv2.threshold(frameDelta, 5, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        for c in cnts:
            if cv2.contourArea(c) < 5000:
                continue
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            self.drawing = 1
            self.motionCounter += 1
            self.lastMovtionCaptured = datetime.datetime.now()

        if (datetime.datetime.now() - self.lastMovtionCaptured).seconds >= 0.5:
            self.drawing = 0

        return frame

    @staticmethod
    def frames():
        picam2 = Picamera2()
        preview_config = picam2.preview_configuration
        preview_config.size = (640, 480)
        preview_config.format = 'RGB888'
        preview_config.transform = libcamera.Transform(hflip=hflip, vflip=vflip)
        preview_config.colour_space = libcamera.ColorSpace.Sycc()
        preview_config.buffer_count = 4
        preview_config.queue = True

        if not picam2.is_open:
            raise RuntimeError('Could not start camera.')

        try:
            picam2.start()
            time.sleep(2)
            camera_ins = Camera()

            while True:
                img = picam2.capture_array()

                if img is None:
                    if ImgIsNone == 0:
                        print("--------------------")
                        print("\033[31merror: Unable to read camera data.\033[0m")
                        print("Press the keyboard keys \033[34m'Ctrl + C'\033[0m multiple times to exit the current program.")
                        print("--------Ctrl+C quit-----------")
                        ImgIsNone = 1
                    continue

                processed_frame = camera_ins.watchDog(img)
                _, encoded_frame = cv2.imencode('.jpg', processed_frame)
                yield encoded_frame.tobytes()

        except Exception as e:
            print(f"\033[38;5;1mError:\033[0m\n{e}")
            print("\nPlease check whether the camera is connected well,  "
                  "and disable the \"legacy camera driver\" on raspi-config")
        finally:
            picam2.stop()


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    while True:
        frame = camera.get_frame()
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
    