//% color="#AA278D"
namespace RobotBit{
    //% block="RobotBit Init" blockType="command"
    export function robotbitInit(parameter: any, block: any){
        Generator.addImport("from mpython import *"); 
        Generator.addImport("from RobotBit import *"); 
        Generator.addImport("from machine import I2C,Pin"); 
        Generator.addImport("import neopixel"); 
        //Generator.addImport("from  pca9685 import *"); 
        //Generator.addImport("from  motor import *"); 
        //Generator.addImport("from servo import Servos"); 
        //Generator.addImport("from stepper  import *"); 
        Generator.addCode(`robot = RobotBit(i2c)`); 
        Generator.addCode(`np = neopixel.NeoPixel(Pin(Pin.P16), n=4, bpp=3, timing=1);`); 
    }


    //% block="Motor[motor]Speed[speed]" blockType="command" 
    //% motor.shadow="dropdown" motor.options="motor"
    //% speed.shadow="range" speed.params.min=-255 speed.params.max=255 speed.defl=100
    export function motorRun(parameter: any, block: any) {
        let motor = parameter.motor.code;  
        let speed = parameter.speed.code;
        Generator.addCode(`robot.motor(${motor},${speed});`);        
        
    }


    //% block="Stop[motor]Motor" blockType="command" 
    //% motor.shadow="dropdown" motor.options="motor"
    export function motoStop(parameter: any, block: any) {
        let motor = parameter.motor.code; 
        Generator.addCode(`robot.stopmotor(${motor});`);
    }


    //% block="Stop All Motor" blockType="command" 
    export function motoStopAll(parameter: any, block: any) {
        Generator.addCode(`robot.motorStopAll();`);
    }


    //% block="---"
    export function noteSep1() {

    }
    
    
    //% block="9g Servo[servo]Degree[angel]°" blockType="command" 
    //% angel.shadow="range" angel.params.min=0 angel.params.max=180 angel.defl=90
    //% servo.shadow="dropdown" servo.options="servo"
    export function servo(parameter: any, block: any) {
        let servo = parameter.servo.code;  
        let angel = parameter.angel.code;
        Generator.addCode(`robot.servo(${servo},${angel});`);
    }


    //% block="Geek 9g Servo[servo]Degree[angel]°" blockType="command"
    //% angel.shadow="range" angel.params.min=-45 angel.params.max=225 angel.defl=90
    //% servo.shadow="dropdown" servo.options="servo"
    export function servoGeek(parameter: any, block: any) {
        let servo = parameter.servo.code;
        let angel = parameter.angel.code;  
        Generator.addCode(`robot.geekServo9g(${servo},${angel});`);
    }

    
    //% block="Geek 2KgServo[servo]Degree[angel]°" blockType="command"
    //% angel.shadow="range" angel.params.min=0 angel.params.max=360 angel.defl=180
    //% servo.shadow="dropdown" servo.options="servo"
    export function servo2Kg(parameter: any, block: any) {
        let servo = parameter.servo.code;
        let angel = parameter.angel.code;           
        Generator.addCode(`robot.geekservo2kg(${servo},${angel});`);
    }



    //% block="---"
    export function noteSep2() {

    }
    
    
    //% block="28BYJ-48 Stepper Motor[stepper] Degree[angel]" blockType="command" 
    //% angel.shadow="number" angel.defl="360"
    //% stepper.shadow="dropdown" stepper.options="stepper"
    export function stepperDegree(parameter: any, block: any) {
        let stepper = parameter.stepper.code;  
        let angel = parameter.angel.code;
        Generator.addCode(`robot.stepperDegree(${stepper},${angel});`);
    }
    
    
    //% block="Double 28BYJ-48 Stepper Motor M1 Degree[m1angel] M2 Degree[m2angel]" blockType="command" 
    //% m1angel.shadow="number" m1angel.defl="360"
    //% m2angel.shadow="number" m2angel.defl="-360"
    export function stepperDual(parameter: any, block: any) {
        let m1angel = parameter.m1angel.code;  
        let m2angel = parameter.m2angel.code;
        Generator.addCode(`robot.stepperDual(${m1angel},${m2angel});`);
    }
 
 

    //% block="---"
    export function noteSep3() {

    }	


    //% block="Red[RED]Green[GREEN]Yellow[YELLOW]" blockType="reporter"
    //% RED.shadow="range" RED.params.min=0 RED.params.max=255 RED.defl=255
    //% GREEN.shadow="range" GREEN.params.min=0 GREEN.params.max=255 GREEN.defl=0
    //% YELLOW.shadow="range" YELLOW.params.min=0 YELLOW.params.max=255 YELLOW.defl=0
    export function GetRgb(parameter: any, block: any) {
        let red = parameter.RED.code;
        let green = parameter.GREEN.code;
        let yellow = parameter.YELLOW.code;
        Generator.addCode(`(${red}, ${green}, ${yellow});`);
    }

    
    //% block="RGB LED[RGB]Color[COLOR]" blockType="command"
    //% RGB.shadow="dropdown" RGB.options="RGB"
    //% COLOR.shadow="colorSlider" COLOR.defl="#f00"
    export function NeopixelColorSlider(parameter: any, block: any) {
        let rgb = parameter.RGB.code;
        let color = parameter.COLOR.code;
        var r = 0;
        var g = 0;
        var b = 0;
        try {
            if ( color.length == 8 ) {
                r = parseInt(color.substring(2, 4), 16);
                g = parseInt(color.substring(4, 6), 16);
                b = parseInt(color.substring(6, 8), 16);
            }
        } catch(e) {
            return '';
        }
        Generator.addCode(`np[${rgb}]= (${r},${g},${b});`);
        Generator.addCode(`np.write();`);
    }


    //% block="RGB Led[RGB]Color[COLOR]" blockType="command"
    //% RGB.shadow="dropdown" RGB.options="RGB"
    //% COLOR.shadow="colorPalette"
    export function NeopixelColorPalette(parameter: any, block: any) {
        let rgb = parameter.RGB.code;
        let color = parameter.COLOR.code;	
        var r = 0;
        var g = 0;
        var b = 0;
        try {
            if ( color.length == 8 ) {
                r = parseInt(color.substring(2, 4), 16);
                g = parseInt(color.substring(4, 6), 16);
                b = parseInt(color.substring(6, 8), 16);
            }
        } catch(e) {
            return '';
        }
        Generator.addCode(`np[${rgb}]= (${r},${g},${b});`);
        Generator.addCode(`np.write();`);
    }


    //% block="RGB Led[RGB]Red[RED]Green[GREEN]Yellow[YELLOW]" blockType="command"
    //% RGB.shadow="dropdown" RGB.options="RGB"
    //% RED.shadow="range" RED.params.min=0 RED.params.max=255 RED.defl=255
    //% GREEN.shadow="range" GREEN.params.min=0 GREEN.params.max=255 GREEN.defl=0
    //% YELLOW.shadow="range" YELLOW.params.min=0 YELLOW.params.max=255 YELLOW.defl=0
    export function NeopixelRgb(parameter: any, block: any) {
        let rgb = parameter.RGB.code;
        let red = parameter.RED.code;
        let green = parameter.GREEN.code;
        let yellow = parameter.YELLOW.code;
        Generator.addCode(`np[${rgb}]= (${red}, ${green}, ${yellow});`);
        Generator.addCode(`np.write();`);
    }


    //% block="Trun Off [RGB]RGB Led" blockType="command"
    //% RGB.shadow="dropdown" RGB.options="RGB"
    export function NeopixelOff(parameter: any, block: any) {
        let rgb = parameter.RGB.code;
        Generator.addCode(`np[${rgb}]= ( (0, 0, 0) );`);
        Generator.addCode(`np.write();`);
    } 
 

    //% block="---"
    export function noteSep4() {

    }	
	
	
	
    //% block="All RGB Led Color[COLOR]" blockType="command"
    //% COLOR.shadow="colorSlider"  COLOR.defl="#f00" 
    export function NeopixelColorSliderAll(parameter: any, block: any) {
        let color = parameter.COLOR.code;
        var r = 0;
        var g = 0;
        var b = 0;
        try {
            if ( color.length == 8 ) {
                r = parseInt(color.substring(2, 4), 16);
                g = parseInt(color.substring(4, 6), 16);
                b = parseInt(color.substring(6, 8), 16);
            }
        } catch(e) {
            return '';
        }
        Generator.addCode(`np.fill((${r},${g},${b}));`);
        Generator.addCode(`np.write();`);
    }


    //% block="All RGB Led Color[COLOR]" blockType="command"
    //% COLOR.shadow="colorPalette"
    export function NeopixelColorPaletteAll(parameter: any, block: any) {
        let color = parameter.COLOR.code;
        var r = 0;
        var g = 0;
        var b = 0;
        try {
            if ( color.length == 8 ) {
                r = parseInt(color.substring(2, 4), 16);
                g = parseInt(color.substring(4, 6), 16);
                b = parseInt(color.substring(6, 8), 16);
            }
        } catch(e) {
            return '';
        }
        Generator.addCode(`np.fill((${r},${g},${b}));`);
        Generator.addCode(`np.write();`);
    }


    //% block="All RGB Led Red[RED] Green[GREEN] Yellow[YELLOW]" blockType="command"
    //% RED.shadow="range" RED.params.min=0 RED.params.max=255 RED.defl=255
    //% GREEN.shadow="range" GREEN.params.min=0 GREEN.params.max=255 GREEN.defl=0
    //% YELLOW.shadow="range" YELLOW.params.min=0 YELLOW.params.max=255 YELLOW.defl=0
    export function NeopixelRgbAll(parameter: any, block: any) {
        let red = parameter.RED.code;
        let green = parameter.GREEN.code;
        let yellow = parameter.YELLOW.code;
        Generator.addCode(`np.fill((${red}, ${green}, ${yellow}));`);
        Generator.addCode(`np.write();`);
    }


    //% block="RGB Led Off" blockType="command"
    export function NeopixelClear(parameter: any, block: any) {
        Generator.addCode(`np.fill( (0, 0, 0) );`);
        Generator.addCode(`np.write();`);
    }
}
    