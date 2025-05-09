#!/usr/bin/env/python3
# File name   : BatteryLevelMonitoring.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/24
import time
import board
import busio
from adafruit_bus_device.i2c_device import I2CDevice

i2c = busio.I2C(board.SCL, board.SDA)
# ADS7830 adress 0x48
device = I2CDevice(i2c, 0x48)

# Define constants
Vref = 8.4
WarningThreshold = 6.0
R15 = 3000
R17 = 1000
DivisionRatio = R17 / (R15 + R17)

#Define the ADC channel and command.
cmd = 0x84
channel = 0
control_byte = cmd | (((channel << 2 | channel >> 1) & 0x07) << 4)

if __name__ == "__main__":
    buffer = [1]
    while True:
        device.write_then_readinto(bytes([control_byte]), buffer)
        adcValue = buffer[0]
        A0Voltage = (adcValue / 255) * 5
        ActualBatteryVoltage = A0Voltage / DivisionRatio

        BatteryPercentage = (ActualBatteryVoltage - WarningThreshold) / (Vref - WarningThreshold) * 100

        print(f"Current battery level: {BatteryPercentage:.2f} %")

        # Battery level warning judgment
        if BatteryPercentage < 20:
            print("Warning! The battery level is too low. Please charge in time!")
        time.sleep(0.5)
