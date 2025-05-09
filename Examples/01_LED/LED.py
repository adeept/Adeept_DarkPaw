#!/usr/bin/env/python3
# File name   : LED.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/23

import time
from gpiozero import LED

def switchSetup():
    global led1,led2,led3
    led1 = LED(9)
    led2 = LED(25)
    led3 = LED(11)

def switch(port, status):
    if port == 1:
        if status == 1:
            led1.on()
        elif status == 0:
            led1.off()
    elif port == 2:
        if status == 1:
            led2.on()
        elif status == 0:
            led2.off()
    elif port == 3:
        if status == 1:
            led3.on()
        elif status == 0:
            led3.off()
    else:
        print('Wrong Command: Example--switch(3, 1)->to switch on port3')

def set_all_switch_off():
    switch(1,0)
    switch(2,0)
    switch(3,0)


if __name__ == "__main__":
    switchSetup()
    while True:
        switch(1,1)
        print("LED1 on")
        time.sleep(1)
        switch(2,1)
        print("LED2 on")
        time.sleep(1)
        switch(3,1)
        print("LED3 on")
        time.sleep(1)
        set_all_switch_off()
        print("All LED off")
        time.sleep(1)
