#!/usr/bin/env/python3
# File name   : camera_pi2.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/23
import io
import time
from picamera2 import Picamera2, Preview
from base_camera import BaseCamera

class Camera(BaseCamera):
    @staticmethod
    def frames():
        with Picamera2() as camera:
            camera.start()

            # let camera warm up
            time.sleep(2) 

            stream = io.BytesIO()
            try:
                while True:
                    camera.capture_file(stream, format='jpeg')
                    stream.seek(0)
                    yield stream.read()

                    # reset stream for next frame
                    stream.seek(0)
                    stream.truncate()
            finally:
                camera.stop()
