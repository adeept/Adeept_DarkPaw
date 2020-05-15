#!/usr/bin/env/python
# File name   : server.py
# Production  : DarkPaw
# Website     : www.adeept.com
# Author      : William
# Date        : 2019/07/24

import socket
import time
import threading
import SpiderG
SpiderG.move_init()
import os
import FPV
import info
import LED
import switch

functionMode = 0

def info_send_client():
    SERVER_IP = addr[0]
    SERVER_PORT = 2256   #Define port serial 
    SERVER_ADDR = (SERVER_IP, SERVER_PORT)
    Info_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Set connection value for socket
    Info_Socket.connect(SERVER_ADDR)
    print(SERVER_ADDR)
    while 1:
        try:
            Info_Socket.send((info.get_cpu_tempfunc()+' '+info.get_cpu_use()+' '+info.get_ram_info()+' '+str(SpiderG.get_direction())).encode())
            time.sleep(1)
        except:
            time.sleep(10)
            pass


def FPV_thread():
    global fpv
    fpv=FPV.FPV()
    fpv.capture_thread(addr[0])


def  ap_thread():
    os.system("sudo create_ap wlan0 eth0 Groovy 12345678")


def run():
    global speed_set, functionMode, direction_command, turn_command

    speed_set = 100
    direction_command = 'no'
    turn_command = 'no'

    info_threading=threading.Thread(target=info_send_client)    #Define a thread for FPV and OpenCV
    info_threading.setDaemon(True)                             #'True' means it is a front thread,it would close when the mainloop() closes
    info_threading.start()                                     #Thread starts

    while True: 
        data = ''
        data = str(tcpCliSock.recv(BUFSIZ).decode())
        if not data:
            continue

        elif 'forward' == data:
            print('1')
            SpiderG.walk('forward')
        
        elif 'backward' == data:
            SpiderG.walk('backward')

        elif 'DS' in data:
            if turn_command == 'no':
                SpiderG.servoStop()

        elif 'left' == data:
            SpiderG.walk('turnleft')

        elif 'right' == data:
            SpiderG.walk('turnright')

        elif 'TS' in data:
            if direction_command == 'no':
                SpiderG.servoStop()


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


        elif 'steady' in data:                    #Steady
            functionMode = 1
            SpiderG.steadyModeOn()
            tcpCliSock.send(('steady').encode())

        elif 'FindColor' in data:                    #Color Find
            functionMode = 2
            fpv.FindColor(1)
            tcpCliSock.send(('FindColor').encode())

        elif 'WatchDog' in data:                    #Watch Dog
            functionMode = 3
            fpv.WatchDog(1)
            tcpCliSock.send(('WatchDog').encode())

        elif 'function_4_on' in data:                    #T/D
            functionMode = 4
            SpiderG.gait_set = 0
            tcpCliSock.send(('function_4_on').encode())

        elif 'function_5_on' in data:                    #None (Action 1)
            functionMode = 5
            tcpCliSock.send(('function_5_on').encode())
            SpiderG.action_1()
            functionMode = 0
            tcpCliSock.send(('function_5_off').encode())

        elif 'function_6_on' in data:                    #None (Action 2)
            functionMode = 6
            tcpCliSock.send(('function_6_on').encode())
            SpiderG.action_2()
            functionMode = 0
            tcpCliSock.send(('function_6_off').encode())

        if 'funEnd' in data:
            SpiderG.steadyModeOff()
            fpv.FindColor(0)
            fpv.WatchDog(0)
            functionMode = 0
            switch.switch(1,0)
            switch.switch(2,0)
            switch.switch(3,0)
            tcpCliSock.send(('FunEnd').encode())
            print('STOP ALL FUNCTIONS')

        elif 'function_1_off' in data:
            functionMode = 0
            SpiderG.steadyModeOff()
            tcpCliSock.send(('function_1_off').encode())

        elif 'function_2_off' in data:
            functionMode = 0
            fpv.FindColor(0)
            switch.switch(1,0)
            switch.switch(2,0)
            switch.switch(3,0)
            tcpCliSock.send(('function_2_off').encode())

        elif 'function_3_off' in data:
            functionMode = 0
            fpv.WatchDog(0)
            tcpCliSock.send(('function_3_off').encode())

        elif 'function_4_off' in data:
            functionMode = 0
            SpiderG.gait_set = 1
            tcpCliSock.send(('function_4_off').encode())

        elif 'function_5_off' in data:
            functionMode = 0
            tcpCliSock.send(('function_5_off').encode())

        elif 'function_6_off' in data:
            functionMode = 0
            tcpCliSock.send(('function_6_off').encode())


        elif 'lookleft' == data:
            servo_command = 'lookleft'
            SpiderG.headLeft()

        elif 'lookright' == data:
            servo_command = 'lookright'
            SpiderG.headRight()

        elif 'up' == data:
            servo_command = 'up'
            SpiderG.headUp()

        elif 'down' == data:
            servo_command = 'down'
            SpiderG.headDown()

        elif 'stop' == data:
            if not functionMode:
                SpiderG.headStop()
            servo_command = 'no'
            pass

        elif 'home' == data:
            SpiderG.move_init()

        elif 'wsB' in data:
            try:
                set_B=data.split()
                speed_set = int(set_B[1])
            except:
                pass

        elif 'StandUp' == data:
            SpiderG.walk('StandUp')

        elif 'StayLow' == data:
            SpiderG.walk('StayLow')

        elif 'Lean-R' == data:
            SpiderG.walk('Lean-R')

        elif 'Lean-L' == data:
            SpiderG.walk('Lean-L')

        elif 'CVFL' in data:#2 start
            if not FPV.FindLineMode:
                FPV.FindLineMode = 1
                tcpCliSock.send(('CVFL_on').encode())
            else:
                # move.motorStop()
                # FPV.cvFindLineOff()
                FPV.FindLineMode = 0
                tcpCliSock.send(('CVFL_off').encode())
                SpiderG.servoStop()

        elif 'Render' in data:
            if FPV.frameRender:
                FPV.frameRender = 0
            else:
                FPV.frameRender = 1

        elif 'WBswitch' in data:
            if FPV.lineColorSet == 255:
                FPV.lineColorSet = 0
            else:
                FPV.lineColorSet = 255

        elif 'lip1' in data:
            try:
                set_lip1=data.split()
                lip1_set = int(set_lip1[1])
                FPV.linePos_1 = lip1_set
            except:
                pass

        elif 'lip2' in data:
            try:
                set_lip2=data.split()
                lip2_set = int(set_lip2[1])
                FPV.linePos_2 = lip2_set
            except:
                pass

        elif 'err' in data:#2 end
            try:
                set_err=data.split()
                err_set = int(set_err[1])
                FPV.findLineError = err_set
            except:
                pass

        elif 'setEC' in data:#Z
            ECset = data.split()
            try:
                fpv.setExpCom(int(ECset[1]))
            except Exception as e:
                print(e)

        elif 'defEC' in data:#Z
            fpv.defaultExpCom()

        elif 'headup' in data:#3
            SpiderG.status_GenOut(0, -150, 0)
            SpiderG.direct_M_move()

        elif 'headdown' in data:#3
            SpiderG.status_GenOut(0, 150, 0)
            SpiderG.direct_M_move()

        elif 'low' in data:#3
            SpiderG.status_GenOut(200, 0, 0)
            SpiderG.direct_M_move()

        elif 'high' in data:#3
            SpiderG.status_GenOut(-200, 0, 0)
            SpiderG.direct_M_move()

        elif 'home' in data:#3
            SpiderG.status_GenOut(0, 0, 0)
            SpiderG.direct_M_move()

        else:
            pass

        print(data)


def wifi_check():
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



if __name__ == '__main__':
    switch.switchSetup()
    switch.set_all_switch_off()

    HOST = ''
    PORT = 10223                              #Define port serial 
    BUFSIZ = 1024                             #Define buffer size
    ADDR = (HOST, PORT)

    try:
        LED  = LED.LED()
        LED.colorWipe(255,16,0)
    except:
        print('Use "sudo pip3 install rpi_ws281x" to install WS_281x package\n使用"sudo pip3 install rpi_ws281x"命令来安装rpi_ws281x')
        pass

    while  1:
        wifi_check()
        try:
            tcpSerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcpSerSock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            tcpSerSock.bind(ADDR)
            tcpSerSock.listen(5)                      #Start server,waiting for client
            print('waiting for connection...')
            tcpCliSock, addr = tcpSerSock.accept()
            print('...connected from :', addr)

            fpv=FPV.FPV()
            fps_threading=threading.Thread(target=FPV_thread)         #Define a thread for FPV and OpenCV
            fps_threading.setDaemon(True)                             #'True' means it is a front thread,it would close when the mainloop() closes
            fps_threading.start()                                     #Thread starts
            break
        except:
            LED.colorWipe(0,0,0)

        try:
            LED.colorWipe(0,80,255)
        except:
            pass
    run()
    try:
        run()
    except:
        LED.colorWipe(0,0,0)
