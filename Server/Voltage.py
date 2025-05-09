#!/usr/bin/env/python
# File name   : Voltage.py
# Website     : www.adeept.com
# Author      : Adeept
# Date        : 2025/04/25
import time
import threading
import statistics
from collections import deque
from gpiozero import TonalBuzzer
import Switch as switch
import smbus


OLED_connection = 1

try:
    import OLED
    screen = OLED.OLED_ctrl()
    screen.start()
    screen.screen_show(6, 'Voltage')
except:
    OLED_connection = 0
    pass

# Initialize buzzer
buzzer = TonalBuzzer(18)
SINGLE_NOTE = [("C4", 1)]


average_voltage = 0.0


WarningThreshold = 6
# read the ADC value of channel 0
ADCVref = 4.93
channel = 0
R15 = 3000
R17 = 1000
DivisionRatio = R17 / (R15 + R17)
    

class ADS7830(object):
    def __init__(self):
        self.cmd = 0x84
        self.bus=smbus.SMBus(1)
        self.address = 0x48 # 0x48 is the default i2c address for ADS7830 Module.   
        
    def analogRead(self, chn): # ADS7830 has 8 ADC input pins, chn:0,1,2,3,4,5,6,7
        value = self.bus.read_byte_data(self.address, self.cmd|(((chn<<2 | chn>>1)&0x07)<<4))
        return value



class BatteryLevelMonitor(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.voltage_data = deque(maxlen=10)
        self.adc = ADS7830()
        super(BatteryLevelMonitor, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.clear()

    def run(self):
        global average_voltage
        while True:
            ADCValue = self.adc.analogRead(channel)    # read the ADC value of channel 0
            A0Voltage = ADCValue / 255.0 * ADCVref  # calculate the voltage value
            actual_battery_voltage = A0Voltage / DivisionRatio
            self.voltage_data.append(actual_battery_voltage)
            #print ('ADC Value : %d, Voltage : %.2f, actual_battery_voltage %.2f'%(ADCValue,A0Voltage,actual_battery_voltage))
            if len(self.voltage_data) == self.voltage_data.maxlen:
                median = statistics.median(self.voltage_data)
                filtered_data = [v for v in self.voltage_data if abs(v - median) < 1]

                if filtered_data:
                    average_voltage = sum(filtered_data) / len(filtered_data)
                    if OLED_connection:
                        display_text = f'Voltage {average_voltage:.2f} V'
                        screen.screen_show(6, display_text)
                    if average_voltage < WarningThreshold:
                        print("Warning! The battery level is too low. Please charge in time!")
                        self.trigger_alarm()
                else:
                    print("No valid data after filtering.")
                self.voltage_data.clear()

            time.sleep(0.1)

    def play_note(self):
        for note, duration in SINGLE_NOTE:
            buzzer.play(note)
            time.sleep(float(duration))
        buzzer.stop()

    def trigger_alarm(self):
        self.play_note()
        switch.switch(1, 1)
        switch.switch(2, 1)
        switch.switch(3, 1)
        time.sleep(0.5)
        self.play_note()
        switch.switch(1, 0)
        switch.switch(2, 0)
        switch.switch(3, 0)


if __name__ == "__main__":
    monitor = BatteryLevelMonitor()
    monitor.start()
    switch.switchSetup()
    switch.set_all_switch_off()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program terminated by user.")
