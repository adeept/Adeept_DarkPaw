#!/usr/bin/env/python3
# File name   : Camera_Gesture.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/24
from flask import Flask, render_template, Response
import time
import cv2
import numpy as np
import libcamera
from base_camera import BaseCamera
from picamera2 import Picamera2
hflip = 0
vflip = 0
ImgIsNone = 0
app = Flask(__name__)

class Camera(BaseCamera):
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
        except Exception as e:
            print(f"\033[38;5;1mError:\033[0m\n{e}")
            print("\nPlease check whether the camera is connected well,  "
                  "and disable the \"legacy camera driver\" on raspi-config")

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

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

            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lower_skin = np.array([0, 20, 70], dtype=np.uint8)
            upper_skin = np.array([20, 255, 255], dtype=np.uint8)
            mask = cv2.inRange(hsv, lower_skin, upper_skin)
            mask = cv2.erode(mask, kernel, iterations=2)
            mask = cv2.dilate(mask, kernel, iterations=2)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                max_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(max_contour) > 500:
                    hull = cv2.convexHull(max_contour, returnPoints=False)
                    defects = cv2.convexityDefects(max_contour, hull)
                    if defects is not None:
                        num_defects = 0
                        for i in range(defects.shape[0]):
                            s, e, f, d = defects[i, 0]
                            start = tuple(max_contour[s][0])
                            end = tuple(max_contour[e][0])
                            far = tuple(max_contour[f][0])
                            a = np.sqrt((end[0] - start[0]) ** 2+(end[1] - start[1]) ** 2)
                            b = np.sqrt((far[0] - start[0]) ** 2+(far[1] - start[1]) ** 2)
                            c = np.sqrt((end[0] - far[0]) ** 2+(end[1] - far[1]) ** 2)
                            angle = np.arccos((b ** 2 + c ** 2 - a ** 2)/(2 * b * c)) * 57.2958
                            if angle <= 90:
                                num_defects += 1
                                cv2.circle(img, far, 5, [0, 0, 255], -1)
                        if num_defects < 3:
                            cv2.putText(img, "Fist", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        elif num_defects >= 3:
                            cv2.putText(img, "Open Hand", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            _, encoded_frame = cv2.imencode('.jpg', img)
            yield encoded_frame.tobytes()

@app.route('/')
def index():
    return render_template('index.html')

def gen(camera):
    yield b'--frame\r\n'
    while True:
        frame = camera.get_frame()
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'

@app.route('/video_feed')
def video_feed():
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
    
