#!/usr/bin/env/python
# File name   : server.py
# Description : main programe for DarkPaw
# Website     : www.adeept.com
# E-mail      : support@adeept.com
# Author      : William
# Date        : 2018/08/22

import socket
import time
import threading
import move
import Adafruit_PCA9685
from rpi_ws281x import *
import argparse
import os
import psutil
import switch
import LED

'''
Initiation number of steps, don't have to change it.
'''
step_set = 1

'''
The range of the legs wiggling, you can decrease it to make the robot slower while the frequency unchanged.
DO NOT increase or it may cause mechanical collisions.
'''
speed_set = 150

'''
Initiation commands
'''
direction_command = 'no'
turn_command = 'no'

pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(50)
LED = LED.LED()

SmoothMode = 0
steadyMode = 0

def breath_led():
    LED.breath(255)


def ap_thread():
    os.system("sudo create_ap wlan0 eth0 AdeeptCar 12345678")


def get_cpu_tempfunc():
    """ Return CPU temperature """
    result = 0
    mypath = "/sys/class/thermal/thermal_zone0/temp"
    with open(mypath, 'r') as mytmpfile:
        for line in mytmpfile:
            result = line

    result = float(result)/1000
    result = round(result, 1)
    return str(result)


def get_gpu_tempfunc():
    """ Return GPU temperature as a character string"""
    res = os.popen('/opt/vc/bin/vcgencmd measure_temp').readline()
    return res.replace("temp=", "")


def get_cpu_use():
    """ Return CPU usage using psutil"""
    cpu_cent = psutil.cpu_percent()
    return str(cpu_cent)


def get_ram_info():
    """ Return RAM usage using psutil """
    ram_cent = psutil.virtual_memory()[2]
    return str(ram_cent)


def get_swap_info():
    """ Return swap memory  usage using psutil """
    swap_cent = psutil.swap_memory()[3]
    return str(swap_cent)


def info_get():
    global cpu_t,cpu_u,gpu_t,ram_info
    while 1:
        cpu_t = get_cpu_tempfunc()
        cpu_u = get_cpu_use()
        ram_info = get_ram_info()
        time.sleep(3)


def move_thread():
    global step_set
    stand_stu = 1
    while 1:
        if not steadyMode:
            if direction_command == 'forward' and turn_command == 'no':
                stand_stu = 0
                move.dove_move_tripod(step_set, 150, 'forward')
                step_set += 1
                if step_set == 9:
                    step_set = 1
                continue

            elif direction_command == 'backward' and turn_command == 'no':
                stand_stu = 0
                move.dove_move_tripod(step_set, 150, 'backward')
                step_set += 1
                if step_set == 9:
                    step_set = 1
                continue

            else:
                pass

            if turn_command != 'no':
                stand_stu = 0
                move.dove_move_diagonal(step_set, 150, turn_command)
                step_set += 1
                if step_set == 9:
                    step_set = 1
                continue
            else:
                pass

            if turn_command == 'no' and direction_command == 'stand':
                if stand_stu == 0:
                    move.robot_stand(150)
                    step_set = 1
                    stand_stu = 1
                else:
                    time.sleep(0.01)
                    pass

            pass
        else:
            pass
            move.robot_X(150, 100)
            move.steady()
            #print('steady')
            #time.sleep(0.2)


def info_send_client():
    SERVER_IP = addr[0]
    SERVER_PORT = 2256   #Define port serial 
    SERVER_ADDR = (SERVER_IP, SERVER_PORT)
    Info_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Set connection value for socket
    Info_Socket.connect(SERVER_ADDR)
    print(SERVER_ADDR)
    while 1:
        try:
            Info_Socket.send((get_cpu_tempfunc()+' '+get_cpu_use()+' '+get_ram_info()).encode())
            time.sleep(1)
        except:
            pass


def run():
    global direction_command, turn_command, SmoothMode, steadyMode
    moving_threading=threading.Thread(target=move_thread)    #Define a thread for FPV and OpenCV
    moving_threading.setDaemon(True)                             #'True' means it is a front thread,it would close when the mainloop() closes
    moving_threading.start()                                     #Thread starts

    info_threading=threading.Thread(target=info_send_client)    #Define a thread for FPV and OpenCV
    info_threading.setDaemon(True)                             #'True' means it is a front thread,it would close when the mainloop() closes
    info_threading.start()                                     #Thread starts

    ws_R = 0
    ws_G = 0
    ws_B = 0

    Y_pitch = 300
    Y_pitch_MAX = 600
    Y_pitch_MIN = 100

    while True: 
        data = ''
        data = str(tcpCliSock.recv(BUFSIZ).decode())
        if not data:
            continue
        elif 'forward' == data:
            direction_command = 'forward'
        elif 'backward' == data:
            direction_command = 'backward'
        elif 'DS' in data:
            direction_command = 'stand'

        elif 'left' == data:
            turn_command = 'left'
        elif 'right' == data:
            turn_command = 'right'
        elif 'leftside' == data:
            turn_command = 'left'
        elif 'rightside'== data:
            turn_command = 'right'
        elif 'TS' in data:
            turn_command = 'no'

        elif 'headup' == data:
            move.ctrl_pitch_roll(150, -100, 0)
        elif 'headdown' == data:
            move.ctrl_pitch_roll(150, 100, 0)
        elif 'headhome' == data:
            move.ctrl_pitch_roll(150, 0, 0)

        elif 'low' == data:
            move.robot_stand(-150)
        elif 'hight' == data:
            move.robot_stand(150)
        elif 'wsR' in data:
            try:
                set_R=data.split()
                ws_R = int(set_R[1])
                LED.colorWipe(Color(ws_R,ws_G,ws_B))
            except:
                pass
        elif 'wsG' in data:
            try:
                set_G=data.split()
                ws_G = int(set_G[1])
                LED.colorWipe(Color(ws_R,ws_G,ws_B))
            except:
                pass
        elif 'wsB' in data:
            try:
                set_B=data.split()
                ws_B = int(set_B[1])
                LED.colorWipe(Color(ws_R,ws_G,ws_B))
            except:
                pass

        elif 'FindColor' in data:
            LED.breath_status_set(1)
            fpv.FindColor(1)
            tcpCliSock.send(('FindColor').encode())

        elif 'WatchDog' in data:
            LED.breath_status_set(1)
            fpv.WatchDog(1)
            tcpCliSock.send(('WatchDog').encode())

        elif 'steady' in data:
            LED.breath_status_set(1)
            LED.breath_color_set('blue')
            steadyMode = 1
            tcpCliSock.send(('steady').encode())

        elif 'funEnd' in data:
            LED.breath_status_set(0)
            fpv.FindColor(0)
            fpv.WatchDog(0)
            steadyMode = 0
            tcpCliSock.send(('FunEnd').encode())


        elif 'Smooth_on' in data:
            SmoothMode = 1
            tcpCliSock.send(('Smooth_on').encode())

        elif 'Smooth_off' in data:
            SmoothMode = 0
            tcpCliSock.send(('Smooth_off').encode())


        elif 'Switch_1_on' in data:
            switch.switch(1,1)
            tcpCliSock.send(('Switch_1_on').encode())

        elif 'Switch_1_off' in data:
            switch.switch(1,0)
            tcpCliSock.send(('Switch_1_off').encode())

        elif 'Switch_2_on' in data:
            switch.switch(2,1)
            tcpCliSock.send(('Switch_2_on').encode())

        elif 'Switch_2_off' in data:
            switch.switch(2,0)
            tcpCliSock.send(('Switch_2_off').encode())

        elif 'Switch_3_on' in data:
            switch.switch(3,1)
            tcpCliSock.send(('Switch_3_on').encode())

        elif 'Switch_3_off' in data:
            switch.switch(3,0)
            tcpCliSock.send(('Switch_3_off').encode())

        else:
            pass
        #print(data)


def destory():
    move.clean_all()


if __name__ == '__main__':
    switch.switchSetup()
    switch.set_all_switch_off()
    move.init_servos()

    HOST = ''
    PORT = 10223                              #Define port serial 
    BUFSIZ = 1024                             #Define buffer size
    ADDR = (HOST, PORT)

    try:
        led_threading=threading.Thread(target=breath_led)         #Define a thread for LED breathing
        led_threading.setDaemon(True)                             #'True' means it is a front thread,it would close when the mainloop() closes
        led_threading.start()                                     #Thread starts
        LED.breath_color_set('blue')
    except:
        print('Use "sudo pip3 install rpi_ws281x" to install WS_281x package')
        pass

    while  1:
        try:
            s =socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            s.connect(("1.1.1.1",80))
            ipaddr_check=s.getsockname()[0]
            s.close()
            print(ipaddr_check)
        except:
            ap_threading=threading.Thread(target=ap_thread)   #Define a thread for data receiving
            ap_threading.setDaemon(True)                          #'True' means it is a front thread,it would close when the mainloop() closes
            ap_threading.start()                                  #Thread starts

            LED.colorWipe(Color(0,16,50))
            time.sleep(1)
            LED.colorWipe(Color(0,16,100))
            time.sleep(1)
            LED.colorWipe(Color(0,16,150))
            time.sleep(1)
            LED.colorWipe(Color(0,16,200))
            time.sleep(1)
            LED.colorWipe(Color(0,16,255))
            time.sleep(1)
            LED.colorWipe(Color(35,255,35))

        try:
            tcpSerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcpSerSock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            tcpSerSock.bind(ADDR)
            tcpSerSock.listen(5)                      #Start server,waiting for client
            print('waiting for connection...')
            tcpCliSock, addr = tcpSerSock.accept()
            print('...connected from :', addr)
            move.robot_stand(150)

            break
        except:
            LED.colorWipe(Color(0,0,0))
            pass

    try:
        LED.breath_status_set(0)
        LED.colorWipe(Color(64,128,255))
    except:
        pass

    try:
        run()
    except:
        LED.colorWipe(Color(0,0,0))
        destory()
        move.clean_all()
        switch.switch(1,0)
        switch.switch(2,0)
        switch.switch(3,0)
