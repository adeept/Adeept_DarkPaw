enum RGB {
    //% block="1"
    0,
    //% block="2"
    1
    //% block="3"
    2,
    //% block="4"
    3
}

enum MOTOR {
    //% block="M1A"
    1,
    //% block="M1B"
    2,
    //% block="M2A"
    3,
    //% block="M2B"
    4
}

enum SERVO {
    //% block="S1"
    8,
    //% block="S2"
    9,
    //% block="S3"
    10,
    //% block="S4"
    11,
    //% block="S5"
    12,
    //% block="S6"
    13,
    //% block="S7"
    14,
    //% block="S8"
    15
}

enum RGB {
    //% block="0"
    0,
    //% block="1"
    1,
    //% block="2"
    2,
    //% block="3"
    3
}

enum PIN{
    //% block="P0"
    0,
    //% block="P1"
    1,
    //% block="P2"
    2,
    //% block="P8"
    8,
    //% block="P12"
    12,
    //% block="P13"
    13,
    //% block="P14"
    14,
    //% block="P15"
    15
}

 
enum DIRECTION{
    //% block="正转"
    HIGH,
    //% block="反转"
    LOW
}

    //% color="#004198" iconWidth=50 iconHeight=40
    namespace Robot{
    //% block="扩展板初始化" blockType="command" 
    export function RobotBitInit(parameter: any, block: any) {
    Generator.addInclude("DFRobot_NeoPixel","#include <DFRobot_NeoPixel.h>");
    Generator.addInclude("Adafruit_PWMServoDriver","#include <Adafruit_PWMServoDriver.h>");
    Generator.addObject(`neoPixel_16`, `DFRobot_NeoPixel`, `neoPixel_16;`);
    Generator.addCode(`neoPixel_16.begin(16, 4);`);
    Generator.addObject(`pwm1 = Adafruit_PWMServoDriver(0x40)`, `Adafruit_PWMServoDriver`, `pwm1 = Adafruit_PWMServoDriver(0x40);`);
    Generator.addCode(`pwm1.begin();`);
    Generator.addCode(`pwm1.setPWMFreq(50);`);
    }


    //% block="电机[MOTOR]速度[SPEED]" blockType="command" 
    //% MOTOR.shadow="dropdown" MOTOR.options="MOTOR"
    //% SPEED.shadow="range" SPEED.params.min=-255 SPEED.params.max=255 SPEED.defl=100
    export function MotorRun(parameter: any, block: any) {
        let motor = parameter.MOTOR.code;  
        let speed = parameter.SPEED.code;
        let num = (motor - 1) * 2;
        let on = 0;
        let off = speed;
        Generator.addCode(`pwm1.Motor(${num},0,${off});`);        
        
    }


    //% block="电机[MOTOR]速度[SPEED]延迟[DELAY]" blockType="command" 
    //% MOTOR.shadow="dropdown" MOTOR.options="MOTOR"
    //% SPEED.shadow="range" SPEED.params.min=-255 SPEED.params.max=255 SPEED.defl=100
    //% DELAY.shadow="number" DELAY.defl="2000"
    export function MotorRunDelay(parameter: any, block: any) {
        let motor = parameter.MOTOR.code;  
        let speed = parameter.SPEED.code;
        let delay = parameter.DELAY.code;
        Generator.addCode(``);
    }


    //% block="停止[MOTOR]电机" blockType="command" 
    //% MOTOR.shadow="dropdown" MOTOR.options="MOTOR" MOTOR.defl="MOTOR.1"
    export function MotoStop(parameter: any, block: any) {
        let motor = parameter.MOTOR.code; 
        Generator.addCode(``);
    }



    //% block="步进电机转动 M1[M1ANGEL] M2[M2ANGEL]" blockType="command" 
    //% M1ANGEL.shadow="range" M1ANGEL.params.min=0 M1ANGEL.params.max=360 M1ANGEL.defl=180
    //% M2ANGEL.shadow="range" M2ANGEL.params.min=0 M1ANGEL.params.max=360 M2ANGEL.defl=180
    export function StepperDual(parameter: any, block: any) {
        let m1angel = M1ANGEL.params.edge;  
        let m2angel = M2ANGEL.params.edge;
        Generator.addCode(``);
    }


    //% block="停止所有电机" blockType="command" 
    export function MotoStopAll(parameter: any, block: any) {
        Generator.addCode(``);
    }
	

	
    //% block="---"
    export function noteSep1() {

    }
    
    
    //% block="舵机[SERVO]角度[ANGEL]" blockType="command" 
    //% SERVO.shadow="dropdown" SERVO.options="SERVO"
    //% ANGEL.shadow="range" ANGEL.params.min=0 ANGEL.params.max=180 ANGEL.defl=90
    export function Stepper(parameter: any, block: any) {
        let servo = parameter.SERVO.code;  
        let angel = parameter.ANGEL.code;
        Generator.addCode(`pwm1.Servo(${servo},${angel});`);
    }


    //% block="Geek 9g舵机[SERVO]角度[ANGEL]" blockType="command"
    //% SERVO.shadow="dropdown" SERVO.options="SERVO"
    //% ANGEL.shadow="range" ANGEL.params.min=-45 ANGEL.params.max=225 ANGEL.defl=180
    export function ServoGeek(parameter: any, block: any) {
        let servo = parameter.SERVO.code;
        let angel = parameter.ANGEL.code;  
        Generator.addCode(`pwm1.geekServo9g(${servo},${angel});`);
    }

    
    //% block="Geek 2Kg舵机[SERVO]角度[ANGEL]" blockType="command"
    //% SERVO.shadow="dropdown" SERVO.options="SERVO"
    //% ANGEL.shadow="range" ANGEL.params.min=0 ANGEL.params.max=360 ANGEL.defl=180
    export function Servo2Kg(parameter: any, block: any) {
        let servo = parameter.SERVO.code;
        let angel = parameter.ANGEL.code;           
        enerator.addCode(`pwm1.geekServo2kg(${servo},${angel});`);
    }


    //% block="360度舵机设置引脚[PIN]以[SPEED]%速度[DIRECTION]" blockType="command"
    //% PIN.shadow="dropdownRound" PIN.options="PIN"    
    //% SPEED.shadow="range" SPEED.params.min=0 SPEED.params.max=100 SPEED.defl=50 
    //% DIRECTION.shadow="dropdown" DIRECTION.options="DIRECTION" 
    export function ServoPCA9685speed(parameter: any, block: any) {        
        let pin = parameter.PIN.code;         
        let speed = parameter.SPEED.code;
        let direction = parameter.DIRECTION.code;
 
        Generator.addCode(`${pin},${speed};`);
      
            
  }

    //% block="---"
    export function noteSep2() {

    }
 

 
    //% block="红[RED]绿[GREEN]蓝[BLUE]" blockType="reporter"
    //% RED.shadow="range" RED.params.min=0 RED.params.max=255 RED.defl=255
    //% GREEN.shadow="range" GREEN.params.min=0 GREEN.params.max=255 GREEN.defl=0
    //% BLUE.shadow="range" BLUE.params.min=0 BLUE.params.max=255 BLUE.defl=0
    export function SetRgb(parameter: any, block: any) {
        let red = parameter.RED.code;
        let green = parameter.GREEN.code;
        let blue = parameter.BLUE.code;
        if red > 9{
                let r = red.toString(16);
         }else{
                 let r = "0" + red.toString(16);
        }
        if green > 9{
                 let g = green.toString(16);
        }else{
                let g = "0" + green.toString(16);
        }
        if blue > 9{
                let b = blue.toString(16);
        }else{
                 let b = "0" + blue.toString(16);
        }
        let color = "0x" + r + g + b
        Generator.addCode(`(${color})`);
    }
	
	
    //% block="彩灯RGB[RGB]亮颜色[COLOR]" blockType="command"
    //% RGB.shadow="dropdown" RGB.options="RGB"
    //% COLOR.shadow="colorSlider"
    export function NeopixelColorSlider(parameter: any, block: any) {
        let rgb = parameter.RGB.code;
        let color = parameter.COLOR.code;
        Generator.addCode(`neoPixel_16.setRangeColor(${rgb},${rgb},${color});`);

    }


//% block="彩灯RGB[RGB]亮颜色[COLOR]" blockType="command"
    //% RGB.shadow="dropdown" RGB.options="RGB"
    //% COLOR.shadow="colorPalette" COLOR.defl="COLOR.1" 
    export function NeopixelColorPalette(parameter: any, block: any) {
        let rgb = parameter.RGB.code;
        let color = parameter.COLOR.code;
        Generator.addCode(`neoPixel_16.setRangeColor(${rgb},${rgb},${color});`);
    }


    //% block="彩灯RGB[RGB]红[RED]绿[GREEN]蓝[BLUE]" blockType="command"
    //% RGB.shadow="dropdown" RGB.options="RGB"
    //% RED.shadow="range" RED.params.min=0 RED.params.max=255 RED.defl=255
    //% GREEN.shadow="range" GREEN.params.min=0 GREEN.params.max=255 GREEN.defl=0
    //% BLUE.shadow="range" BLUE.params.min=0 BLUE.params.max=255 BLUE.defl=0
    export function NeopixelRgb(parameter: any, block: any) {
        let rgb = parameter.RGB.code;
        let red = parameter.RED.code;
        let green = parameter.GREEN.code;
        let blue = parameter.BLUE.code;
        if red > 9{
                let r = red.toString(16);
        }else{
                let r = "0" + red.toString(16);
        }
        if green > 9{
                let g = green.toString(16);
        }else{
                let g = "0" + green.toString(16);
        }
        if blue > 9{
                let b = blue.toString(16);
        }else{
                let b = "0" + blue.toString(16);
        }
        let color = "0x" + r + g + b
        Generator.addCode(`neoPixel_16.setRangeColor(0,3,${color});`);
    }

    //% block="RGB彩灯全亮 颜色[COLOR]" blockType="command"
    //% COLOR.shadow="colorSlider" 
    export function NeopixelColorSliderAll(parameter: any, block: any) {
        let color = parameter.COLOR.code;
        Generator.addCode(`neoPixel_16.setRangeColor(0,3,${color});`);
    }


    //% block="RGB彩灯全亮 颜色[COLOR]" blockType="command"
    //% COLOR.shadow="colorPalette" 
    export function NeopixelColorPaletteAll(parameter: any, block: any) {
        let color = parameter.COLOR.code;
        Generator.addCode(`neoPixel_16.setRangeColor(0,3,${color});`);
    }


    //% block="RGB彩灯全亮红[RED]绿[GREEN]蓝[BLUE]" blockType="command"
    //% RED.shadow="range" RED.params.min=0 RED.params.max=255 RED.defl=255
    //% GREEN.shadow="range" GREEN.params.min=0 GREEN.params.max=255 GREEN.defl=0
    //% BLUE.shadow="range" BLUE.params.min=0 BLUE.params.max=255 BLUE.defl=0
    export function NeopixelRgbAll(parameter: any, block: any) {
        let red = parameter.RED.code;
        let green = parameter.GREEN.code;
        let blue = parameter.BLUE.code;
        if red > 9{
                let r = red.toString(16);
        }else{
                let r = "0" + red.toString(16);
        }
        if green > 9{
                let g = green.toString(16);
        }else{
                let g = "0" + green.toString(16);
        }
        if blue > 9{
                let b = blue.toString(16);
        }else{
                let b = "0" + blue.toString(16);
        }
        let color = "0x" + r + g + b
        Generator.addCode(`neoPixel_16.setRangeColor(0,3,${color});`);
    }


    //% block="RGB彩灯关闭" blockType="command"
    export function NeopixelClear(parameter: any, block: any) {
        Generator.addCode(`neoPixel_16.clear();`);
    }

    
}
    