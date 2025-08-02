#!/usr/bin/python3
# File name   : LED.py
# Description : WS_2812
# Website     : based on the code from https://github.com/rpi-ws281x/rpi-ws281x-python/blob/master/examples/strandtest.py
# E-mail      : support@adeept.com
# Author      : original code by Tony DiCola (tony@tonydicola.com)
# Date        : 2018/10/12
import time
from rpi_ws281x import *
import argparse
import threading

class LED:
    def __init__(self):
        # LED strip configuration:
        self.LED_COUNT      = 16      # Number of LED pixels.
        self.LED_PIN        = 12      # GPIO pin connected to the pixels (18 uses PWM!).
        self.LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
        self.LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
        self.LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
        self.LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
        self.LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

        # Internal state
        self.breath_enabled = True
        self.color = 'yellow'
        self.frequency = 50
        self.delay = 0.1
        self.state_lock = threading.Lock()

        parser = argparse.ArgumentParser()
        parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
        args = parser.parse_args()

        # Create NeoPixel object with appropriate configuration.
        self.strip = Adafruit_NeoPixel(self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT, self.LED_BRIGHTNESS, self.LED_CHANNEL)
        # Intialize the library (must be called once before other functions).
        self.strip.begin()

    def colorWipe(self, color, wait_ms=0):
        """Wipe color across display a pixel at a time."""
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, color)
        self.strip.show()
        if wait_ms > 0:
            time.sleep(wait_ms/1000.0)

    def breath_status_set(self, status):
        with self.state_lock:
            self.breath_enabled = bool(status)

    def breath_color_set(self, invar):
        with self.state_lock:
            self.color = invar

    def breath_frequency_set(self, frequency_input):
        with self.state_lock:
            self.frequency = frequency_input

    def breath(self, brightness):
        color_map = {
            'red': (1, 0, 0),
            'green': (0, 1, 0),
            'blue': (0, 0, 1),
            'yellow': (1, 1, 0),
        }

        while True:
            with self.state_lock:
                enabled = self.breath_enabled
                color_name = self.color
                freq = self.frequency

            if not enabled:
                time.sleep(0.2)
                continue

            r_base, g_base, b_base = color_map.get(color_name, (0, 1, 1)) # Default to a cyan-ish blue

            # Fade In
            for i in range(0, brightness, freq):
                with self.state_lock:
                    if not self.breath_enabled: break
                if i > 255: i = 255 # cap brightness
                self.colorWipe(Color(r_base*i, g_base*i, b_base*i))
                time.sleep(self.delay)

            # Fade Out
            for i in range(0, brightness, freq):
                with self.state_lock:
                    if not self.breath_enabled: break
                level = brightness - 1 - i
                if level < 0: level = 0 # cap brightness
                self.colorWipe(Color(r_base*level, g_base*level, b_base*level))
                time.sleep(self.delay)