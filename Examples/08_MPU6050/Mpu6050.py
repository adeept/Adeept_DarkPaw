#!/usr/bin/env/python
# File name   : Mpu6050.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/24

from mpu6050 import mpu6050
import time

sensor = mpu6050(0x68)
def mpu6050test():
  x = 0
  y = 0
  z = 0
  for i in range(0,10):
    accelerometer_data = sensor.get_accel_data()
    x = x + accelerometer_data['x']
    y = y + accelerometer_data['y']
    z = z + accelerometer_data['z']
  print('X=%.3f, Y=%.3f, Z=%.3f'%(x/10.0,y/10.0,z/10.0))
  time.sleep(0.3)

if __name__ == "__main__":
  try:
    while True:
      mpu6050test()
  except:
    pass
  
  
