#!/usr/bin/env/python
# File name   : appserver.py
# Production  : RaspClaws
# Website     : www.adeept.com
# Author      : William
# Date        : 2019/11/21

import socket
import threading
import time
import os
from rpi_ws281x import *
import LED
# import move
import SpiderG
SpiderG.move_init()

LED = LED.LED()
LED.colorWipe(0,64,255)

step_set = 1
speed_set = 500
DPI = 17

new_frame = 0
direction_command = 'no'
turn_command = 'no'
servo_command = 'no'

SmoothMode = 0
steadyMode = 0

class Servo_ctrl(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(Servo_ctrl, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.set()
        # self.__running = threading.Event()
        # self.__running.set()

    def pause(self):
        self.__flag.clear()

    def resume(self):
        self.__flag.set()

    def stop(self):
        self.__flag.set()
        # self.__running.clear()


def app_ctrl():
    global servo_move
    app_HOST = ''
    app_PORT = 10123
    app_BUFSIZ = 1024
    app_ADDR = (app_HOST, app_PORT)

    servo_move = Servo_ctrl()
    servo_move.start()
    servo_move.pause()

    def  ap_thread():
        os.system("sudo create_ap wlan0 eth0 Adeept_Robot 12345678")


    def appCommand(data_input):
        global direction_command, turn_command, servo_command
        if data_input == 'forwardStart\n':
            SpiderG.walk('forward')

        elif data_input == 'backwardStart\n':
            SpiderG.walk('backward')

        elif data_input == 'leftStart\n':
            SpiderG.walk('turnleft')

        elif data_input == 'rightStart\n':
            SpiderG.walk('turnright')

        elif 'forwardStop' in data_input:
            SpiderG.move_init()
            SpiderG.servoStop()

        elif 'backwardStop' in data_input:
            SpiderG.move_init()
            SpiderG.servoStop()

        elif 'leftStop' in data_input:
            SpiderG.move_init()
            SpiderG.servoStop()

        elif 'rightStop' in data_input:
            SpiderG.move_init()
            SpiderG.servoStop()


        if data_input == 'lookLeftStart\n':
            SpiderG.status_GenOut(0, 150, 0)
            SpiderG.direct_M_move()

        elif data_input == 'lookRightStart\n': 
            SpiderG.status_GenOut(0, -150, 0)
            SpiderG.direct_M_move()

        elif data_input == 'downStart\n':
            SpiderG.walk('Lean-R')

        elif data_input == 'upStart\n':
            SpiderG.walk('Lean-L')

        elif 'lookLeftStop' in data_input:
            pass
        elif 'lookRightStop' in data_input:
            pass
        elif 'downStop' in data_input:
            pass
        elif 'upStop' in data_input:
            pass


        if data_input == 'aStart\n':
            if SmoothMode:
                SmoothMode = 0
            else:
                SmoothMode = 1

        elif data_input == 'bStart\n':
            if steadyMode:
                steadyMode = 0
            else:
                steadyMode = 1

        elif data_input == 'cStart\n':
            LED.colorWipe(255,64,0)

        elif data_input == 'dStart\n':
            LED.colorWipe(64,255,0)

        elif 'aStop' in data_input:
            pass
        elif 'bStop' in data_input:
            pass
        elif 'cStop' in data_input:
            pass
        elif 'dStop' in data_input:
            pass

        print(data_input)

    def appconnect():
        global AppCliSock, AppAddr
        try:
            s =socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            s.connect(("1.1.1.1",80))
            ipaddr_check=s.getsockname()[0]
            s.close()
            print(ipaddr_check)

            AppSerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            AppSerSock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            AppSerSock.bind(app_ADDR)
            AppSerSock.listen(5)
            print('waiting for App connection...')
            AppCliSock, AppAddr = AppSerSock.accept()
            print('...App connected from :', AppAddr)
        except:
            ap_threading=threading.Thread(target=ap_thread)       #Define a thread for AP Mode
            ap_threading.setDaemon(True)                          #'True' means it is a front thread,it would close when the mainloop() closes
            ap_threading.start()                                  #Thread starts

            LED.colorWipe(0,16,50)
            time.sleep(1)
            LED.colorWipe(0,16,100)
            time.sleep(1)
            LED.colorWipe(0,16,150)
            time.sleep(1)
            LED.colorWipe(0,16,200)
            time.sleep(1)
            LED.colorWipe(0,16,255)
            time.sleep(1)
            LED.colorWipe(35,255,35)

            AppSerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            AppSerSock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            AppSerSock.bind(app_ADDR)
            AppSerSock.listen(5)
            print('waiting for App connection...')
            AppCliSock, AppAddr = AppSerSock.accept()
            print('...App connected from :', AppAddr)

    appconnect()
    # setup()
    app_threading=threading.Thread(target=appconnect)         #Define a thread for app connection
    app_threading.setDaemon(True)                             #'True' means it is a front thread,it would close when the mainloop() closes
    app_threading.start()                                     #Thread starts

    while 1:
        data = ''
        data = str(AppCliSock.recv(app_BUFSIZ).decode())
        if not data:
            continue
        appCommand(data)
        pass

if __name__ == '__main__':
    app_ctrl()