#!/usr/bin/env/python
# File name   : initPosServos.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/22
import time
import Adafruit_PCA9685

pwm = Adafruit_PCA9685.PCA9685(address=0x5F, busnum=1)
pwm.set_pwm_freq(50)

while 1:
	pwm.set_all_pwm(0, 300)
	time.sleep(1)
