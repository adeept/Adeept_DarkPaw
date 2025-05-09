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

#include "Adafruit_PWMServoDriver.h"
#include <Wire.h>



// Set to true to print some debug messages, or false to disable them.
#define ENABLE_DEBUG_OUTPUT true

Adafruit_PWMServoDriver::Adafruit_PWMServoDriver(uint8_t addr) {
    _i2caddr = addr;
}

void Adafruit_PWMServoDriver::begin(void) {
 WIRE.begin();
 reset();
}


void Adafruit_PWMServoDriver::reset(void) {
 write8(PCA9685_MODE1, 0x0);
}

void Adafruit_PWMServoDriver::setServoPulse(uint8_t n, double pulse) {
    double pulselength;
    
    pulselength = 1000000;     // 1,000,000 us per second
    pulselength /= 50;             // 50 Hz
    Serial.print(pulselength); Serial.println(" us per period"); 
    pulselength /= 4096;         // 12 bits of resolution
    Serial.print(pulselength); Serial.println(" us per bit"); 
    pulse *= 1000;
    pulse /= pulselength;
    Serial.println(pulse);
    setPWM(n, 0, pulse);
}

void Adafruit_PWMServoDriver::Servo(uint8_t n,uint8_t angle){
    // 50hz: 25,000 us
    // 500~2500 us->0~180
    // v_us = 100/9*degree + 500
    double pulse;
    pulse=0.5+angle/90.0;
    setServoPulse(n,pulse);
}

void Adafruit_PWMServoDriver::geekServo9g(uint8_t n,uint8_t angle){
    // 50hz: 25,000 us
    // 600~2600us->-45~225
    // v_us = 20/3*degree + 900
    // v_us = 200/27*degree + 1000/3 + 600    
    double pulse;
    pulse=0.6+angle/27.0*5.0+1.0/3.0;
    setServoPulse(n,pulse);
}

void Adafruit_PWMServoDriver::geekServo2kg(uint8_t n,uint8_t angle){
    // 50hz: 25,000 us
    // 500~2650us->0~360
    // v_us = degree * 50 / 9 +500
    // v_us = 215/36*degree + 500
    double pulse;
    pulse=0.5+angle*43.0/7200.0;
    setServoPulse(n,pulse);
}



void Adafruit_PWMServoDriver::setPWMFreq(float freq) {
    //Serial.print("Attempting to set freq ");
    //Serial.println(freq);
    freq *= 0.9;    // Correct for overshoot in the frequency setting (see issue #11).
    float prescaleval = 25000000;
    prescaleval /= 4096;
    prescaleval /= freq;
    prescaleval -= 1;
    if (ENABLE_DEBUG_OUTPUT) {
        Serial.print("Estimated pre-scale: "); Serial.println(prescaleval);
    }
    uint8_t prescale = floor(prescaleval + 0.5);
    if (ENABLE_DEBUG_OUTPUT) {
        Serial.print("Final pre-scale: "); Serial.println(prescale);
    }
    
    uint8_t oldmode = read8(PCA9685_MODE1);
    uint8_t newmode = (oldmode&0x7F) | 0x10; // sleep
    write8(PCA9685_MODE1, newmode); // go to sleep
    write8(PCA9685_PRESCALE, prescale); // set the prescaler
    write8(PCA9685_MODE1, oldmode);
    delay(5);
    write8(PCA9685_MODE1, oldmode | 0xa1);    //    This sets the MODE1 register to turn on auto increment.
                                                                                    // This is why the beginTransmission below was not working.
    //    Serial.print("Mode now 0x"); Serial.println(read8(PCA9685_MODE1), HEX);
}

void Adafruit_PWMServoDriver::setMotorPWM(uint8_t num, uint16_t on, uint16_t off) {
    //Serial.print("Setting PWM "); Serial.print(num); Serial.print(": "); Serial.print(on); Serial.print("->"); Serial.println(off);

    Wire.beginTransmission(_i2caddr); 
    Wire.write(LED0_ON_L+4*channel);  
    Wire.write(on & 0xFF);  
    Wire.endTransmission();

    Wire.beginTransmission(_i2caddr); 
    Wire.write(LED0_ON_H+4*channel);  
    Wire.write(off >> 8);  
    Wire.endTransmission();

    Wire.beginTransmission(_i2caddr); 
    Wire.write(LED0_OFF_L+4*channel);  
    Wire.write(on & 0xFF);  
    Wire.endTransmission();

    Wire.beginTransmission(_i2caddr); 
    Wire.write(LED0_OFF_H+4*channel);  
    Wire.write(off >> 8);  
    Wire.endTransmission();
}


void Adafruit_PWMServoDriver::motor(uint8_t index,uint8_t speed,uint8_t delay=0){
        if (index>4 or index<=0){
            return;
        }
        speed = 4095/255 *speed;
        pp = (index-1)*2;
        pn = (index-1)*2+1;
        if (speed >= 0){
            set_Motorpwm(pp, 0, int(speed));
            set_Motorpwm(pn, 0, 0);
        }else{
            set_Motorpwm(pp, 0, 0);
            set_Motorpwm(pn, 0, int(-speed));
        }
        if (delay){
            delay(delay);
            set_Motorpwm(pp, 0, 0);
            set_Motorpwm(pn, 0, 0);
        }

}


void Adafruit_PWMServoDriver::setStepper(uint8_t index, uint8_t dir){
    if (index == 1){
        if (dir){
            set_Motorpwm(0, STP_CHA_L, STP_CHA_H);
            set_Motorpwm(2, STP_CHB_L, STP_CHB_H);
            set_Motorpwm(1, STP_CHC_L, STP_CHC_H);
            set_Motorpwm(3, STP_CHD_L, STP_CHD_H);
        }else{
            set_Motorpwm(3, STP_CHA_L, STP_CHA_H);
            set_Motorpwm(1, STP_CHB_L, STP_CHB_H);
            set_Motorpwm(2, STP_CHC_L, STP_CHC_H);
            set_Motorpwm(0, STP_CHD_L, STP_CHD_H);
		}
    }else if(index==2){
        if (dir){
            set_Motorpwm(4, STP_CHA_L, STP_CHA_H);
            set_Motorpwm(6, STP_CHB_L, STP_CHB_H);
            set_Motorpwm(5, STP_CHC_L, STP_CHC_H);
            set_Motorpwm(7, STP_CHD_L, STP_CHD_H);
        }else{
            set_Motorpwm(7, STP_CHA_L, STP_CHA_H);
            set_Motorpwm(5, STP_CHB_L, STP_CHB_H);
            set_Motorpwm(6, STP_CHC_L, STP_CHC_H);
            set_Motorpwm(4, STP_CHD_L, STP_CHD_H);
		}
    }
}


void Adafruit_PWMServoDriver::stopMotor(uint8_t index){
    set_Motorpwm((index - 1) * 2, 0, 0);
    set_Motorpwm((index - 1) * 2 + 1, 0, 0);

}



void Adafruit_PWMServoDriver::motorStopAll(){
    for (idx in range(1,5)){
        stopMotor(idx);
	}
}


void Adafruit_PWMServoDriver::stepperDegree(uint8_t index,uint8_t degree){
    setStepper(index, degree > 0);
    degree = abs(degree);
    delay(int(10240 * degree / 360));
    motorStopAll();
}


void Adafruit_PWMServoDriver::RoSonar(uint8_t port){
    p = RoPort[port];
    p.write_digital(0);
    sleep_us(2);
    p.write_digital(1);
    sleep_us(10);
    p.write_digital(0);
    p.read_digital();
    duration = p.pulsein(2000000);
    if (duration<0){
      return -1;
    }
	return (duration/2);   //29.1
}



void Adafruit_PWMServoDriver::stepperDual(uint8_t degree1, uint8_t degree2){
    setStepper(1, degree1 > 0);
    setStepper(2, degree2 > 0);
    degree1 = abs(degree1);
    degree2 = abs(degree2);
    delay(int(10240 * min(degree1, degree2) / 360));
    if(degree1 > degree2){
        stopMotor(3);
        stopMotor(4);
        delay(int(10240 * (degree1 - degree2) / 360))
    }else{
        stopMotor(1);
        stopMotor(2);
        delay(int(10240 * (degree2 - degree1) / 360))
    }
	motorStopAll();
}


// Sets pin without having to deal with on/off tick placement and properly handles
// a zero value as completely off.    Optional invert parameter supports inverting
// the pulse for sinking to ground.    Val should be a value from 0 to 4095 inclusive.
void Adafruit_PWMServoDriver::setPin(uint8_t num, uint16_t val, bool invert)
{
    // Clamp value between 0 and 4095 inclusive.
    val = min(val, 4095);
    if (invert) {
        if (val == 0) {
            // Special value for signal fully on.
            setPWM(num, 4096, 0);
        }
        else if (val == 4095) {
            // Special value for signal fully off.
            setPWM(num, 0, 4096);
        }
        else {
            setPWM(num, 0, 4095-val);
        }
    }
    else {
        if (val == 4095) {
            // Special value for signal fully on.
            setPWM(num, 4096, 0);
        }
        else if (val == 0) {
            // Special value for signal fully off.
            setPWM(num, 0, 4096);
        }
        else {
            setPWM(num, 0, val);
        }
    }
}

uint8_t Adafruit_PWMServoDriver::read8(uint8_t addr) {
    WIRE.beginTransmission(_i2caddr);
    WIRE.write(addr);
    WIRE.endTransmission();

    WIRE.requestFrom((uint8_t)_i2caddr, (uint8_t)1);
    return WIRE.read();
}



void Adafruit_PWMServoDriver::write8(uint8_t addr, uint8_t d) {
    WIRE.beginTransmission(_i2caddr);
    WIRE.write(addr);
    WIRE.write(d);
    WIRE.endTransmission();
}
