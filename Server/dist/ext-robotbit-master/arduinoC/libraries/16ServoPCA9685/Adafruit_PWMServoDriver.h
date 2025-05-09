/*************************************************** 
  This is a library for our Adafruit 16-channel PWM & Servo driver

  Pick one up today in the adafruit shop!
  ------> http://www.adafruit.com/products/815

  These displays use I2C to communicate, 2 pins are required to  
  interface. For Arduino UNOs, thats SCL -> Analog 5, SDA -> Analog 4

  Adafruit invests time and resources providing this open source code, 
  please support Adafruit and open-source hardware by purchasing 
  products from Adafruit!

  Written by Limor Fried/Ladyada for Adafruit Industries.  
  BSD license, all text above must be included in any redistribution
 ****************************************************/

#ifndef _ADAFRUIT_PWMServoDriver_H
#define _ADAFRUIT_PWMServoDriver_H

#if ARDUINO >= 100
#    include "Arduino.h"
#else
#    include "WProgram.h"
#endif

#define PCA9685_ADDRESS 0x40
#define MODE1 0x00
#define MODE2 0x01

#define SUBADR1 0x2
#define SUBADR2 0x3
#define SUBADR3 0x4

#define PCA9685_MODE1 0x0
#define PRESCALE 0xFE

#define LED0_ON_L 0x6
#define LED0_ON_H 0x7
#define LED0_OFF_L 0x8
#define LED0_OFF_H 0x9

#define ALL_LED_ON_L 0xFA
#define ALL_LED_ON_H 0xFB
#define ALL_LED_OFF_L 0xFC
#define ALL_LED_OFF_H 0xFD

#define S1 0x1
#define S2 0x2
#define S3 0x3
#define S4 0x4
#define S5 0x5
#define S6 0x6
#define S7 0x7
#define S8 0x8

#define M1A 0x1
#define M1B 0x2
#define M2A 0x3
#define M2B 0x4


#define RESTART 0x80
#define SLEEP 0x10
#define ALLCALL 0x01
#define INVRT 0x10
#define OUTDRV 0x04
#define RESET 0x00

#define STP_CHA_L 2047
#define STP_CHA_H 4095

#define STP_CHB_L 1
#define STP_CHB_H 2047

#define STP_CHC_L 1023
#define STP_CHC_H 3071

#define STP_CHD_L 3071
#define STP_CHD_H 1023



class Adafruit_PWMServoDriver {
    public:
        Adafruit_PWMServoDriver(uint8_t addr = 0x40);
        void begin(void);
        void reset(void);
        void setPWMFreq(float freq);
        void setPWM(uint8_t num, uint16_t on, uint16_t off);
        void setPin(uint8_t num, uint16_t val, bool invert=false);
        void Servo(uint8_t n,uint8_t angle);
        void geekServo9g(uint8_t n,uint8_t angle);
        void geekServo2kg(uint8_t n,uint8_t angle);
        void setServoPulse(uint8_t n, double pulse);
        void motor(uint8_t index,uint8_t speed,uint8_t delay=0);
        void setMotorPWM(uint8_t num, uint16_t on, uint16_t off);
        void setStepper(uint8_t index, uint8_t dir)；
        void stopMotor(uint8_t index)；
        void motorStopAll()；
        void stepperDegree(uint8_t index,uint8_t degree)；
        void RoSonar(uint8_t port)；
        void stepperDual(uint8_t degree1, uint8_t degree2)；
    private:
        uint8_t _i2caddr;

        uint8_t read8(uint8_t addr);
        void write8(uint8_t addr, uint8_t d);
};

#endif
