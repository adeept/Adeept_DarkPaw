from time import sleep, sleep_ms
import math, ustruct
from machine import I2C,Pin
from mpython import *


# Registers/etc:
PCA9685_ADDRESS    = 0x40
MODE1              = 0x00
MODE2              = 0x01
SUBADR1            = 0x02
SUBADR2            = 0x03
SUBADR3            = 0x04
PRESCALE           = 0xFE
LED0_ON_L          = 0x06
LED0_ON_H          = 0x07
LED0_OFF_L         = 0x08
LED0_OFF_H         = 0x09
ALL_LED_ON_L       = 0xFA
ALL_LED_ON_H       = 0xFB
ALL_LED_OFF_L      = 0xFC
ALL_LED_OFF_H      = 0xFD

S1 = 0x1
S2 = 0x2
S3 = 0x3
S4 = 0x4
S5 = 0x5
S6 = 0x6
S7 = 0x7
S8 = 0x8

M1A = 0x1
M1B = 0x2
M2A = 0x3
M2B = 0x4

# Bits:
RESTART            = 0x80
SLEEP              = 0x10
ALLCALL            = 0x01
INVRT              = 0x10
OUTDRV             = 0x04
RESET              = 0x00

STP_CHA_L = 2047
STP_CHA_H = 4095

STP_CHB_L = 1
STP_CHB_H = 2047

STP_CHC_L = 1023
STP_CHC_H = 3071

STP_CHD_L = 3071
STP_CHD_H = 1023

class RobotBit(object):
    """PCA9685 PWM LED/servo controller."""
    def __init__(self, i2c, address=PCA9685_ADDRESS):
        """Initialize the PCA9685."""
        # self.i2c = I2C(0, scl=Pin(15), sda=Pin(21), freq=100000)
        # self.i2c = I2C(0, scl=Pin(19), sda=Pin(20), freq=100000)
        self.address = address
        self.i2c = i2c
        self.i2c.writeto(self.address, bytearray([MODE1, RESET])) # reset not sure if needed but other libraries do it
        self.i2c.writeto(self.address, bytearray([MODE1, RESET]))
        self.i2c.writeto(self.address, bytearray([MODE2, OUTDRV]))
        self.i2c.writeto(self.address, bytearray([MODE1, ALLCALL]))
        sleep(0.005)  # wait for oscillator
        mode1 = self.i2c.readfrom_mem(self.address, MODE1, 1)[0]
        mode1 = mode1 & ~SLEEP  # wake up (reset sleep)
        self.i2c.writeto(self.address, bytearray([MODE1, mode1]))
        sleep(0.005)  # wait for oscillator
        self.set_pwm_freq(50)
        
    
    def set_pwm_freq(self, freq_hz):
        """Set the PWM frequency to the provided value in hertz."""
        prescaleval = 25000000.0    # 25MHz
        prescaleval /= 4096.0       # 12-bit
        prescaleval /= float(freq_hz)
        prescaleval -= 1.0
        prescale = int(math.floor(prescaleval + 0.5))
        oldmode = self.i2c.readfrom_mem(self.address, MODE1, 1)[0]
        newmode = (oldmode & 0x7F) | 0x10    # sleep
        self.i2c.writeto(self.address, bytearray([MODE1, newmode]))
        self.i2c.writeto(self.address, bytearray([PRESCALE, prescale]))
        self.i2c.writeto(self.address, bytearray([MODE1, oldmode]))
        sleep(0.005)
        self.i2c.writeto(self.address, bytearray([MODE1, oldmode | 0x80]))

    def set_pwm(self, channel, on, off):
        """Sets a single PWM channel."""
        if on is None or off is None:
            data = self.i2c.mem_read(4, self.address, LED0_ON_L+4*channel)
            return ustruct.unpack('<HH', data)
        self.i2c.writeto(self.address, bytearray([LED0_ON_L+4*channel, on & 0xFF]))
        self.i2c.writeto(self.address, bytearray([LED0_ON_H+4*channel, on >> 8]))
        self.i2c.writeto(self.address, bytearray([LED0_OFF_L+4*channel, off & 0xFF]))
        self.i2c.writeto(self.address, bytearray([LED0_OFF_H+4*channel, off >> 8]))



    def pulse_width(self, index, v):
        value = int(v/20000*4095)
        self.set_pwm(index+7, 0, value)   

    def servo(self, index, degree): 
        # 50hz: 25,000 us
        # 500~2500 us->0~180
        v_us = 100/9*degree + 500
        value = int(v_us*4096/20000)
        self.set_pwm(index+7, 0, value)

    def geekServo9g(self, index, degree):
        # 50hz: 25,000 us
        # 600~2600us->-45~225
        # v_us = 20/3*degree + 900
        v_us = 200/27*degree + 1000/3 + 500  # calibrated
        value = int(v_us*4096/20000)
        self.set_pwm(index+7, 0, value)
        
    def geekServo2kg(self, index, degree):
        # 50hz: 25,000 us
        # 500~2650us->0~360
        # v_us = degree * 50 / 9 +500
        v_us = 200/36*degree + 500  # calibrated
        value = int(v_us*4096/20000)
        self.set_pwm(index+7, 0, value)

    def motor(self, index, speed):
        if index>4 or index<=0:
            return
        speed = 4095/255 *speed
        pp = (index-1)*2
        pn = (index-1)*2+1
        if speed >= 0:
            self.set_pwm(pp, 0, int(speed))
            self.set_pwm(pn, 0, 0)
        else:
            self.set_pwm(pp, 0, 0)
            self.set_pwm(pn, 0, int(-speed))

    def setStepper(self, index, dir):
        if (index == 1):
            if (dir):
                self.set_pwm(0, STP_CHA_L, STP_CHA_H)
                self.set_pwm(2, STP_CHB_L, STP_CHB_H)
                self.set_pwm(1, STP_CHC_L, STP_CHC_H)
                self.set_pwm(3, STP_CHD_L, STP_CHD_H)
            else:
                self.set_pwm(3, STP_CHA_L, STP_CHA_H)
                self.set_pwm(1, STP_CHB_L, STP_CHB_H)
                self.set_pwm(2, STP_CHC_L, STP_CHC_H)
                self.set_pwm(0, STP_CHD_L, STP_CHD_H)
        elif (index==2):
            if (dir):
                self.set_pwm(4, STP_CHA_L, STP_CHA_H)
                self.set_pwm(6, STP_CHB_L, STP_CHB_H)
                self.set_pwm(5, STP_CHC_L, STP_CHC_H)
                self.set_pwm(7, STP_CHD_L, STP_CHD_H)
            else:
                self.set_pwm(7, STP_CHA_L, STP_CHA_H)
                self.set_pwm(5, STP_CHB_L, STP_CHB_H)
                self.set_pwm(6, STP_CHC_L, STP_CHC_H)
                self.set_pwm(4, STP_CHD_L, STP_CHD_H)

    def stopMotor(self,index):
        self.set_pwm((index - 1) * 2, 0, 0)
        self.set_pwm((index - 1) * 2 + 1, 0, 0)

    def motorStopAll(self):
        for idx in range(1,5):
            self.stopMotor(idx)

    def stepperDegree(self,index,degree):
        self.setStepper(index, degree > 0)
        degree = abs(degree)
        sleep_ms(int(10240 * degree / 360))
        self.motorStopAll()

    def stepperDual(self,degree1, degree2):
        self.setStepper(1, degree1 > 0)
        self.setStepper(2, degree2 > 0)
        degree1 = abs(degree1)
        degree2 = abs(degree2)
        sleep_ms(int(10240 * min(degree1, degree2) / 360))
        if (degree1 > degree2):
            self.stopMotor(3)
            self.stopMotor(4)
            sleep_ms(int(10240 * (degree1 - degree2) / 360))
        else:
            self.stopMotor(1)
            self.stopMotor(2)
            sleep_ms(int(10240 * (degree2 - degree1) / 360))
        self.motorStopAll()
        
    def RoSonar(self, port):
        p = MPythonPin(port,PinMode.OUT)
        p.write_digital(0)
        sleep_us(2)
        p.write_digital(1)
        sleep_us(10)
        p.write_digital(0)
        p = MPythonPin(0,PinMode.IN)
        p.read_digital()
        duration = p.pulsein(2000000)
        if duration<0:
          return -1
        return (duration//2)//29.1
    
    
    def ultrasonic(self, trig, echo):
        trig_p = MPythonPin(trig,PinMode.OUT)
        trig_p.write_digital(0)
        sleep_us(2)
        trig_p.write_digital(1)
        sleep_us(10)
        trig_p.write_digital(0)
        echo_p = MPythonPin(echo,PinMode.IN)
        echo_p.read_digital()
        duration = echo_p.pulsein(2000000)
        if duration<0:
          return -1
        return (duration//2)//29.1