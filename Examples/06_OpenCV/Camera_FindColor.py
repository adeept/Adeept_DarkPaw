#!/usr/bin/env/python3
# File name   : Camera_FindColor.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/24
from flask import Flask, render_template, Response
import cv2
import numpy as np
import threading
import libcamera
from picamera2 import Picamera2
from base_camera import BaseCamera

hflip = 0
vflip = 0
ImgIsNone = 0
app = Flask(__name__)

colorUpper = np.array([44, 255, 255])
colorLower = np.array([24, 100, 100])


def map(input, in_min, in_max, out_min, out_max):
    return (input - in_min) / (in_max - in_min) * (out_max - out_min) + out_min


class Camera(BaseCamera):
    modeSelect = 'findColor'

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


        CVThreading = 0
        CVMode = 'none'
        imgCV = None
        findColorDetection = 0
        radius = 0
        box_x = None
        box_y = None
        drawing = 0
        __flag = threading.Event()
        __flag.clear()

        def mode(invar, imgInput):
            nonlocal CVMode, imgCV
            CVMode = invar
            imgCV = imgInput
            __flag.set()
        def elementDraw(imgInput):
            nonlocal findColorDetection, drawing, radius, box_x, box_y
            if CVMode == 'findColor':
                if findColorDetection:
                    drawing = 1
                else:
                    drawing = 0

                if radius > 10 and drawing:
                    cv2.rectangle(imgInput, (int(box_x - radius), int(box_y + radius)),
                                  (int(box_x + radius), int(box_y - radius)), (0, 255, 0), 2)
                    cv2.putText(imgInput, "Yellow Object", (int(box_x - radius), int(box_y  - radius - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            return imgInput

        def findColor(frame_image):
            nonlocal findColorDetection, radius, box_x, box_y
            if frame_image is None or frame_image.size == 0:
                print("Error: Input image is empty in findColor function")
                return
            hsv = cv2.cvtColor(frame_image, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, colorLower, colorUpper)
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)
            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)[-2]
            center = None
            if len(cnts) > 0:
                findColorDetection = 1
                c = max(cnts, key=cv2.contourArea)
                ((box_x, box_y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
            else:
                findColorDetection = 0
            __flag.clear()

        def run():
            nonlocal CVThreading, CVMode, imgCV
            while 1:
                __flag.wait()
                if CVMode == 'findColor':
                    if imgCV is not None:
                        CVThreading = 1
                        findColor(imgCV)
                        CVThreading = 0
                    else:
                        pass

        thread = threading.Thread(target=run)
        thread.start()

        mode(Camera.modeSelect, None)

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

            if Camera.modeSelect == 'none':
                __flag.clear()
            elif Camera.modeSelect == 'findColor':
                if not CVThreading:
                    mode(Camera.modeSelect, img)
                try:
                    img = elementDraw(img)
                except:
                    pass

            if cv2.imencode('.jpg', img)[0]:
                yield cv2.imencode('.jpg', img)[1].tobytes()


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
