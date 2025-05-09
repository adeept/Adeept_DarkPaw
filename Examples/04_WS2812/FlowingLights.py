#!/usr/bin/env python3
# File name   : FlowingLights.py.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/23
import time
import sys
import subprocess
from gpiozero import PWMOutputDevice as PWM
import threading
import spidev
import numpy
from numpy import sin, cos, pi

# List of basic colors
base_colors = [
    (0, 255, 255),  
    (255, 0, 0),    
    (0, 255, 0),    
    (0, 0, 255),    
    (255, 255, 0),  
    (255, 0, 255),  
    (0, 128, 255),   
    (192, 192, 192),
    (192, 192, 0),  
    (128, 128, 128),
    (128, 0, 0),    
    (128, 128, 0),  
    (0, 128, 0),    
    (0, 128, 128)   
]

# Function to generate a list of color sequences
def generate_color_sequences():
    color_sequences = []
    for i in range(len(base_colors)):
        new_sequence = base_colors[i:] + base_colors[:i]
        color_sequences.append(new_sequence)
    return color_sequences

# Check the Raspberry Pi model
def check_rpi_model():
    _, result = run_command("cat /proc/device-tree/model |awk '{print $3}'")
    result = result.strip()
    if result == '3':
        return 3
    elif result == '4':
        return 4
    elif result == '5':
        return 5
    else:
        return None

# Run a command and return the result
def run_command(cmd=""):
    try:
        p = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result = p.stdout.read().decode('utf-8')
        status = p.poll()
        return status, result
    except Exception as e:
        print(f"Error occurred while running the command: {e}")
        return None, None

# Mapping function
def map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

class Adeept_SPI_LedPixel(threading.Thread):
    def __init__(self, count=8, bright=255, sequence='GRB', bus=0, device=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_led_type(sequence)
        self.set_led_count(count)
        self.set_led_brightness(bright)
        self.led_begin(bus, device)
        self.lightMode = 'none'
        self.colorBreathR = 0
        self.colorBreathG = 0
        self.colorBreathB = 0
        self.breathSteps = 10
        # self.spi_gpio_info()
        self.set_all_led_color(0, 0, 0)
        self.__flag = threading.Event()
        self.__flag.clear()

    def led_begin(self, bus=0, device=0):
        self.bus = bus
        self.device = device
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(self.bus, self.device)
            self.spi.mode = 0
            self.led_init_state = 1
        except OSError:
            print("Please check the configuration in /boot/firmware/config.txt.")
            if self.bus == 0:
                print("You can turn on the 'SPI' in 'Interface Options' by using 'sudo raspi-config'.")
                print("Or make sure that 'dtparam=spi=on' is not commented, then reboot the Raspberry Pi. Otherwise spi0 will not be available.")
            else:
                print(f"Please add 'dtoverlay=spi{self.bus}-2cs' at the bottom of the /boot/firmware/config.txt, then reboot the Raspberry Pi. Otherwise spi{self.bus} will not be available.")
            self.led_init_state = 0

    def check_spi_state(self):
        return self.led_init_state

    def spi_gpio_info(self):
        bus_info = {
            0: "SPI0-MOSI: GPIO10(WS2812-PIN)  SPI0-MISO: GPIO9  SPI0-SCLK: GPIO11  SPI0-CE0: GPIO8  SPI0-CE1: GPIO7",
            1: "SPI1-MOSI: GPIO20(WS2812-PIN)   SPI1-MISO: GPIO19  SPI1-SCLK: GPIO21  SPI1-CE0: GPIO18  SPI1-CE1: GPIO17  SPI0-CE1: GPIO16",
            2: "SPI2-MOSI: GPIO41(WS2812-PIN)   SPI2-MISO: GPIO40  SPI2-SCLK: GPIO42  SPI2-CE0: GPIO43  SPI2-CE1: GPIO44  SPI2-CE1: GPIO45",
            3: "SPI3-MOSI: GPIO2(WS2812-PIN)  SPI3-MISO: GPIO1  SPI3-SCLK: GPIO3  SPI3-CE0: GPIO0  SPI3-CE1: GPIO24",
            4: "SPI4-MOSI: GPIO6(WS2812-PIN)  SPI4-MISO: GPIO5  SPI4-SCLK: GPIO7  SPI4-CE0: GPIO4  SPI4-CE1: GPIO25",
            5: "SPI5-MOSI: GPIO14(WS2812-PIN)  SPI5-MISO: GPIO13  SPI5-SCLK: GPIO15  SPI5-CE0: GPIO12  SPI5-CE1: GPIO26",
            6: "SPI6-MOSI: GPIO20(WS2812-PIN)  SPI6-MISO: GPIO19  SPI6-SCLK: GPIO21  SPI6-CE0: GPIO18  SPI6-CE1: GPIO27"
        }
        print(bus_info.get(self.bus, f"Unknown bus number: {self.bus}"))

    def led_close(self):
        try:
            self.set_all_led_rgb([0, 0, 0])
            self.spi.close()
        except Exception as e:
            print(f"Error occurred while closing the LED: {e}")

    def set_led_count(self, count):
        self.led_count = count
        self.led_color = [0, 0, 0] * self.led_count
        self.led_original_color = [0, 0, 0] * self.led_count

    def set_led_type(self, rgb_type):
        try:
            led_type = ['RGB', 'RBG', 'GRB', 'GBR', 'BRG', 'BGR']
            led_type_offset = [0x06, 0x09, 0x12, 0x21, 0x18, 0x24]
            index = led_type.index(rgb_type)
            self.led_red_offset = (led_type_offset[index] >> 4) & 0x03
            self.led_green_offset = (led_type_offset[index] >> 2) & 0x03
            self.led_blue_offset = (led_type_offset[index] >> 0) & 0x03
            return index
        except ValueError:
            self.led_red_offset = 1
            self.led_green_offset = 0
            self.led_blue_offset = 2
            return -1

    def set_led_brightness(self, brightness):
        self.led_brightness = brightness
        for i in range(self.led_count):
            self.set_led_rgb_data(i, self.led_original_color)

    def set_ledpixel(self, index, r, g, b):
        p = [0, 0, 0]
        p[self.led_red_offset] = round(r * self.led_brightness / 255)
        p[self.led_green_offset] = round(g * self.led_brightness / 255)
        p[self.led_blue_offset] = round(b * self.led_brightness / 255)
        self.led_original_color[index * 3 + self.led_red_offset] = r
        self.led_original_color[index * 3 + self.led_green_offset] = g
        self.led_original_color[index * 3 + self.led_blue_offset] = b
        for i in range(3):
            self.led_color[index * 3 + i] = p[i]

    def setSomeColor_data(self, index, r, g, b):
        self.set_ledpixel(index, r, g, b)

    def set_led_rgb_data(self, index, color):
        self.set_ledpixel(index, color[0], color[1], color[2])

    def setSomeColor(self, index, r, g, b):
        self.set_ledpixel(index, r, g, b)
        self.show()

    def set_led_rgb(self, index, color):
        self.set_led_rgb_data(index, color)
        self.show()

    def set_all_led_color_data(self, r, g, b):
        for i in range(self.led_count):
            self.setSomeColor_data(i, r, g, b)

    def set_all_led_rgb_data(self, color):
        for i in range(self.led_count):
            self.set_led_rgb_data(i, color)

    def set_all_led_color(self, r, g, b):
        for i in range(self.led_count):
            self.setSomeColor_data(i, r, g, b)
        self.show()

    def set_all_led_rgb(self, color):
        for i in range(self.led_count):
            self.set_led_rgb_data(i, color)
        self.show()

    def write_ws2812_numpy8(self):
        d = numpy.array(self.led_color).ravel()
        tx = numpy.zeros(len(d) * 8, dtype=numpy.uint8)
        for ibit in range(8):
            tx[7 - ibit::8] = ((d >> ibit) & 1) * 0x78 + 0x80
        if self.led_init_state != 0:
            if self.bus == 0:
                self.spi.xfer(tx.tolist(), int(8 / 1.25e-6))
            else:
                self.spi.xfer(tx.tolist(), int(8 / 1.0e-6))

    def write_ws2812_numpy4(self):
        d = numpy.array(self.led_color).ravel()
        tx = numpy.zeros(len(d) * 4, dtype=numpy.uint8)
        for ibit in range(4):
            tx[3 - ibit::4] = ((d >> (2 * ibit + 1)) & 1) * 0x60 + ((d >> (2 * ibit + 0)) & 1) * 0x06 + 0x88
        if self.led_init_state != 0:
            if self.bus == 0:
                self.spi.xfer(tx.tolist(), int(4 / 1.25e-6))
            else:
                self.spi.xfer(tx.tolist(), int(4 / 1.0e-6))

    def show(self, mode=1):
        if mode == 1:
            write_ws2812 = self.write_ws2812_numpy8
        else:
            write_ws2812 = self.write_ws2812_numpy4
        write_ws2812()

    def wheel(self, pos):
        if pos < 85:
            return [(255 - pos * 3), (pos * 3), 0]
        elif pos < 170:
            pos = pos - 85
            return [0, (255 - pos * 3), (pos * 3)]
        else:
            pos = pos - 170
            return [(pos * 3), 0, (255 - pos * 3)]

    def hsv2rgb(self, h, s, v):
        h = h % 360
        rgb_max = round(v * 2.55)
        rgb_min = round(rgb_max * (100 - s) / 100)
        i = round(h / 60)
        diff = round(h % 60)
        rgb_adj = round((rgb_max - rgb_min) * diff / 60)
        if i == 0:
            r = rgb_max
            g = rgb_min + rgb_adj
            b = rgb_min
        elif i == 1:
            r = rgb_max - rgb_adj
            g = rgb_max
            b = rgb_min
        elif i == 2:
            r = rgb_min
            g = rgb_max
            b = rgb_min + rgb_adj
        elif i == 3:
            r = rgb_min
            g = rgb_max - rgb_adj
            b = rgb_max
        elif i == 4:
            r = rgb_min + rgb_adj
            g = rgb_min
            b = rgb_max
        else:
            r = rgb_max
            g = rgb_min
            b = rgb_max - rgb_adj
        return [r, g, b]

    def police(self):
        self.lightMode = 'police'
        self.resume()

    def breath(self, R_input, G_input, B_input):
        self.lightMode = 'breath'
        self.colorBreathR = R_input
        self.colorBreathG = G_input
        self.colorBreathB = B_input
        self.resume()

    def resume(self):
        self.__flag.set()

    def pause(self):
        self.lightMode = 'none'
        self.set_all_led_color_data(0, 0, 0)
        self.__flag.clear()

    def breathProcessing(self):
        while self.lightMode == 'breath':
            for i in range(0, self.breathSteps):
                if self.lightMode != 'breath':
                    break
                self.set_all_led_color(self.colorBreathR * i / self.breathSteps,
                                       self.colorBreathG * i / self.breathSteps,
                                       self.colorBreathB * i / self.breathSteps)
                time.sleep(0.03)
            for i in range(0, self.breathSteps):
                if self.lightMode != 'breath':
                    break
                self.set_all_led_color(self.colorBreathR - (self.colorBreathR * i / self.breathSteps),
                                       self.colorBreathG - (self.colorBreathG * i / self.breathSteps),
                                       self.colorBreathB - (self.colorBreathB * i / self.breathSteps))
                time.sleep(0.03)

    def policeProcessing(self):
        while self.lightMode == 'police':
            for i in range(0, 3):
                self.set_all_led_color_data(0, 0, 255)
                self.show()
                time.sleep(0.05)
                self.set_all_led_color_data(0, 0, 0)
                self.show()
                time.sleep(0.05)
            if self.lightMode != 'police':
                break
            time.sleep(0.1)
            for i in range(0, 3):
                self.set_all_led_color_data(255, 0, 0)
                self.show()
                time.sleep(0.05)
                self.set_all_led_color_data(0, 0, 0)
                self.show()
                time.sleep(0.05)
            time.sleep(0.1)

    def setDifferentColors(self, colors):
        max_led = min(len(colors), self.led_count)
        for i in range(max_led):
            r, g, b = colors[i]
            self.setSomeColor_data(i, r, g, b)
        self.show()

    def lightChange(self):
        if self.lightMode == 'none':
            self.pause()
        elif self.lightMode == 'police':
            self.policeProcessing()
        elif self.lightMode == 'breath':
            self.breathProcessing()

    def run(self):
        while True:
            self.__flag.wait()
            self.lightChange()

if __name__ == '__main__':
    # Configuration parameters
    LED_COUNT = 14
    BRIGHTNESS = 50
    ANIMATION_DELAY = 0.3

    #Generate a color sequence list
    color_sequences = generate_color_sequences()

    # Initialize LED controller
    RL = Adeept_SPI_LedPixel(count=LED_COUNT, bright=BRIGHTNESS)
    RL.start()

    try:
        while True:
            for sequence in color_sequences:
                RL.setDifferentColors(sequence)
                time.sleep(ANIMATION_DELAY)
    except KeyboardInterrupt:
        # Safe shutdown process
        RL.pause()
        RL.led_close()
        print("\he lighting animation has safely stopped")
        sys.exit(0)
    except Exception as e:
        print(f"Unknown error occurred: {e}")
        RL.pause()
        RL.led_close()
        sys.exit(1)
