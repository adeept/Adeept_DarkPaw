#!/usr/bin/env/python
# File name   : server.py
# Production  : RaspTankPro
# Website     : www.adeept.com
# Author      : William
# Date        : 2020/03/17

import time
import threading
import move
import Adafruit_PCA9685
import os
import info

import robotLight
import switch
import socket

import SpiderG
SpiderG.move_init()

#websocket
import asyncio
import websockets

import json
import app

OLED_connection = 0
curpath = os.path.realpath(__file__)
thisPath = "/" + os.path.dirname(curpath)

direction_command = 'no'
turn_command = 'no'

FLB_init_pwm = SpiderG.FLB_init_pwm
FLM_init_pwm = SpiderG.FLM_init_pwm
FLE_init_pwm = SpiderG.FLE_init_pwm

FRB_init_pwm = SpiderG.FRB_init_pwm
FRM_init_pwm = SpiderG.FRM_init_pwm
FRE_init_pwm = SpiderG.FRE_init_pwm

HLB_init_pwm = SpiderG.HLB_init_pwm
HLM_init_pwm = SpiderG.HLM_init_pwm
HLE_init_pwm = SpiderG.HLE_init_pwm

HRB_init_pwm = SpiderG.HRB_init_pwm
HRM_init_pwm = SpiderG.HRM_init_pwm
HRE_init_pwm = SpiderG.HRE_init_pwm


def servoPosInit():
    SpiderG.move_init()


def replace_num(initial,new_num):   #Call this function to replace data in '.txt' file
    global r
    newline=""
    str_num=str(new_num)
    with open(thisPath+"/SpiderG.py","r") as f:
        for line in f.readlines():
            if(line.find(initial) == 0):
                line = initial+"%s" %(str_num+"\n")
            newline += line
    with open(thisPath+"/SpiderG.py","w") as f:
        f.writelines(newline)


def ap_thread():
    os.system("sudo create_ap wlan0 eth0 Groovy 12345678")


def functionSelect(command_input, response):
    global functionMode
    
    if 'findColor' == command_input:
        flask_app.modeselect('findColor')

    elif 'motionGet' == command_input:
        flask_app.modeselect('watchDog')

    elif 'stopCV' == command_input:
        flask_app.modeselect('none')
        switch.switch(1,0)
        switch.switch(2,0)
        switch.switch(3,0)
        time.sleep(0.1)
        switch.switch(1,0)
        switch.switch(2,0)
        switch.switch(3,0)

    elif 'police' == command_input:
        RL.police()

    elif 'policeOff' == command_input:
        RL.pause()


def switchCtrl(command_input, response):
    if 'Switch_1_on' in command_input:
        switch.switch(1,1)

    elif 'Switch_1_off' in command_input:
        switch.switch(1,0)

    elif 'Switch_2_on' in command_input:
        switch.switch(2,1)

    elif 'Switch_2_off' in command_input:
        switch.switch(2,0)

    elif 'Switch_3_on' in command_input:
        switch.switch(3,1)

    elif 'Switch_3_off' in command_input:
        switch.switch(3,0) 


def robotCtrl(command_input, response):
    global direction_command, turn_command
    if 'forward' == command_input:
        command_input = 'forward'
        SpiderG.walk('forward')
    
    elif 'backward' == command_input:
        command_input = 'backward'
        SpiderG.walk('backward')

    elif 'DS' in command_input:
        command_input = 'no'
        if turn_command == 'no':
            SpiderG.move_init()
            SpiderG.servoStop()
        elif turn_command == 'left':
            SpiderG.walk('turnleft')
        elif turn_command == 'right':
            SpiderG.walk('turnright')


    elif 'left' == command_input:
        turn_command = 'left'
        SpiderG.walk('turnleft')

    elif 'right' == command_input:
        turn_command = 'right'
        SpiderG.walk('turnright')

    elif 'TS' in command_input:
        turn_command = 'no'
        if direction_command == 'no':
            SpiderG.move_init()
            SpiderG.servoStop()
        else:
            SpiderG.walk(direction_command)


    elif 'steadyCamera' == command_input:     
        SpiderG.move_init()               #Steady
        SpiderG.steadyModeOn()

    elif 'steadyCameraOff' == command_input:                    #Steady
        SpiderG.steadyModeOff()


    elif 'lookleft' == command_input:
        SpiderG.walk('Lean-L')

    elif 'lookright' == command_input:
        SpiderG.walk('Lean-R')

    elif 'up' == command_input:
        SpiderG.status_GenOut(0, -150, 0)
        SpiderG.direct_M_move()

    elif 'down' == command_input:
        SpiderG.status_GenOut(0, 150, 0)
        SpiderG.direct_M_move()

    elif 'stop' == command_input:
        pass

    elif 'home' == command_input:
        SpiderG.move_init()

    elif 'wsB' in command_input:
        try:
            set_B=command_input.split()
            speed_set = int(set_B[1])
        except:
            pass

    elif 'grab' == command_input:
        SpiderG.status_GenOut(-200, 0, 0)
        SpiderG.direct_M_move()

    elif 'loose' == command_input:
        SpiderG.status_GenOut(200, 0, 0)
        SpiderG.direct_M_move()


    elif 'home' in command_input:#3
        SpiderG.status_GenOut(0, 0, 0)
        SpiderG.direct_M_move()

    else:
        pass

    print(command_input)



def configPWM(command_input, response):
    global  FLB_init_pwm, FLM_init_pwm, FLE_init_pwm, HLB_init_pwm, HLM_init_pwm, HLE_init_pwm, FRB_init_pwm, FRM_init_pwm, FRE_init_pwm, HRB_init_pwm, HRM_init_pwm, HRE_init_pwm

    if 'SiLeft' in command_input:
        numServo = int(command_input[7:])
        if numServo == 0:
            FLB_init_pwm -= 1
            SpiderG.FLB_init_pwm = FLB_init_pwm
        elif numServo == 1:
            FLM_init_pwm -= 1
            SpiderG.FLM_init_pwm = FLM_init_pwm
        elif numServo == 2:
            FLE_init_pwm -= 1
            SpiderG.FLE_init_pwm = FLE_init_pwm

        elif numServo == 3:
            HLB_init_pwm -= 1
            SpiderG.HLB_init_pwm = HLB_init_pwm
        elif numServo == 4:
            HLM_init_pwm -= 1
            SpiderG.HLM_init_pwm = HLM_init_pwm
        elif numServo == 5:
            HLE_init_pwm -= 1
            SpiderG.HLE_init_pwm = HLE_init_pwm

        elif numServo == 6:
            FRB_init_pwm -= 1
            SpiderG.FRB_init_pwm = FRB_init_pwm
        elif numServo == 7:
            FRM_init_pwm -= 1
            SpiderG.FRM_init_pwm = FRM_init_pwm
        elif numServo == 8:
            FRE_init_pwm -= 1
            SpiderG.FRE_init_pwm = FRE_init_pwm

        elif numServo == 9:
            HRB_init_pwm -= 1
            SpiderG.HRB_init_pwm = HRB_init_pwm
        elif numServo == 10:
            HRM_init_pwm -= 1
            SpiderG.HRM_init_pwm = HRM_init_pwm
        elif numServo == 11:
            HRE_init_pwm -= 1
            SpiderG.HRE_init_pwm = HRE_init_pwm

        SpiderG.move_init()


    if 'SiRight' in command_input:
        numServo = int(command_input[8:])
        if numServo == 0:
            FLB_init_pwm += 1
            SpiderG.FLB_init_pwm = FLB_init_pwm
        elif numServo == 1:
            FLM_init_pwm += 1
            SpiderG.FLM_init_pwm = FLM_init_pwm
        elif numServo == 2:
            FLE_init_pwm += 1
            SpiderG.FLE_init_pwm = FLE_init_pwm

        elif numServo == 3:
            HLB_init_pwm += 1
            SpiderG.HLB_init_pwm = HLB_init_pwm
        elif numServo == 4:
            HLM_init_pwm += 1
            SpiderG.HLM_init_pwm = HLM_init_pwm
        elif numServo == 5:
            HLE_init_pwm += 1
            SpiderG.HLE_init_pwm = HLE_init_pwm

        elif numServo == 6:
            FRB_init_pwm += 1
            SpiderG.FRB_init_pwm = FRB_init_pwm
        elif numServo == 7:
            FRM_init_pwm += 1
            SpiderG.FRM_init_pwm = FRM_init_pwm
        elif numServo == 8:
            FRE_init_pwm += 1
            SpiderG.FRE_init_pwm = FRE_init_pwm

        elif numServo == 9:
            HRB_init_pwm += 1
            SpiderG.HRB_init_pwm = HRB_init_pwm
        elif numServo == 10:
            HRM_init_pwm += 1
            SpiderG.HRM_init_pwm = HRM_init_pwm
        elif numServo == 11:
            HRE_init_pwm += 1
            SpiderG.HRE_init_pwm = HRE_init_pwm

        SpiderG.move_init()


    if 'PWMMS' in command_input:
        numServo = int(command_input[6:])
        if numServo == 0:
            replace_num('FLB_init_pwm = ', FLB_init_pwm)
        elif numServo == 1:
            replace_num('FLM_init_pwm = ', FLM_init_pwm)
        elif numServo == 2:
            replace_num('FLE_init_pwm = ', FLE_init_pwm)

        elif numServo == 3:
            replace_num('HLB_init_pwm = ', HLB_init_pwm)
        elif numServo == 4:
            replace_num('HLM_init_pwm = ', HLM_init_pwm)
        elif numServo == 5:
            replace_num('HLE_init_pwm = ', HLE_init_pwm)

        elif numServo == 6:
            replace_num('FRB_init_pwm = ', FRB_init_pwm)
        elif numServo == 7:
            replace_num('FRM_init_pwm = ', FRM_init_pwm)
        elif numServo == 8:
            replace_num('FRE_init_pwm = ', FRE_init_pwm)

        elif numServo == 9:
            replace_num('HRB_init_pwm = ', HRB_init_pwm)
        elif numServo == 10:
            replace_num('HRM_init_pwm = ', HRM_init_pwm)
        elif numServo == 11:
            replace_num('HRE_init_pwm = ', HRE_init_pwm)

        SpiderG.move_init()

    if 'PWMINIT' == command_input:
        SpiderG.move_init()

    elif 'PWMD' == command_input:
        FLB_init_pwm = 300
        FLM_init_pwm = 300
        FLE_init_pwm = 300

        HLB_init_pwm = 300
        HLM_init_pwm = 300
        HLE_init_pwm = 300

        FRB_init_pwm = 300
        FRM_init_pwm = 300
        FRE_init_pwm = 300

        HRB_init_pwm = 300
        HRM_init_pwm = 300
        HRE_init_pwm = 300

        SpiderG.FLB_init_pwm = FLB_init_pwm
        SpiderG.FLM_init_pwm = FLM_init_pwm
        SpiderG.FLE_init_pwm = FLE_init_pwm

        SpiderG.HLB_init_pwm = HLB_init_pwm
        SpiderG.HLM_init_pwm = HLM_init_pwm
        SpiderG.HLE_init_pwm = HLE_init_pwm

        SpiderG.FRB_init_pwm = FRB_init_pwm
        SpiderG.FRM_init_pwm = FRM_init_pwm
        SpiderG.FRE_init_pwm = FRE_init_pwm

        SpiderG.HRB_init_pwm = HRB_init_pwm
        SpiderG.HRM_init_pwm = HRM_init_pwm
        SpiderG.HRE_init_pwm = HRE_init_pwm

        replace_num('FLB_init_pwm = ', FLB_init_pwm)
        replace_num('FLM_init_pwm = ', FLM_init_pwm)
        replace_num('FLE_init_pwm = ', FLE_init_pwm)

        replace_num('HLB_init_pwm = ', HLB_init_pwm)
        replace_num('HLM_init_pwm = ', HLM_init_pwm)
        replace_num('HLE_init_pwm = ', HLE_init_pwm)

        replace_num('FRB_init_pwm = ', FRB_init_pwm)
        replace_num('FRM_init_pwm = ', FRM_init_pwm)
        replace_num('FRE_init_pwm = ', FRE_init_pwm)

        replace_num('HRB_init_pwm = ', HRB_init_pwm)
        replace_num('HRM_init_pwm = ', HRM_init_pwm)
        replace_num('HRE_init_pwm = ', HRE_init_pwm)

def update_code():
    # Update local to be consistent with remote
    projectPath = thisPath[:-7]
    with open(f'{projectPath}/config.json', 'r') as f1:
        config = json.load(f1)
        if not config['production']:
            print('Update code')
            # Force overwriting local code
            if os.system(f'cd {projectPath} && sudo git fetch --all && sudo git reset --hard origin/master && sudo git pull') == 0:
                print('Update successfully')
                print('Restarting...')
                os.system('sudo reboot')

def wifi_check():
    try:
        s =socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        s.connect(("1.1.1.1",80))
        ipaddr_check=s.getsockname()[0]
        s.close()
        print(ipaddr_check)
        update_code()
        if OLED_connection:
            screen.screen_show(2, 'IP:'+ipaddr_check)
            screen.screen_show(3, 'AP MODE OFF')
    except:
        RL.pause()
        RL.setColor(0,255,64)
        ap_threading=threading.Thread(target=ap_thread)   #Define a thread for data receiving
        ap_threading.setDaemon(True)                          #'True' means it is a front thread,it would close when the mainloop() closes
        ap_threading.start()                                  #Thread starts
        if OLED_connection:
            screen.screen_show(2, 'AP Starting 10%')
        RL.setColor(0,16,50)
        time.sleep(1)
        if OLED_connection:
            screen.screen_show(2, 'AP Starting 30%')
        RL.setColor(0,16,100)
        time.sleep(1)
        if OLED_connection:
            screen.screen_show(2, 'AP Starting 50%')
        RL.setColor(0,16,150)
        time.sleep(1)
        if OLED_connection:
            screen.screen_show(2, 'AP Starting 70%')
        RL.setColor(0,16,200)
        time.sleep(1)
        if OLED_connection:
            screen.screen_show(2, 'AP Starting 90%')
        RL.setColor(0,16,255)
        time.sleep(1)
        if OLED_connection:
            screen.screen_show(2, 'AP Starting 100%')
        RL.setColor(35,255,35)
        if OLED_connection:
            screen.screen_show(2, 'IP:192.168.12.1')
            screen.screen_show(3, 'AP MODE ON')

async def check_permit(websocket):
    while True:
        recv_str = await websocket.recv()
        cred_dict = recv_str.split(":")
        if cred_dict[0] == "admin" and cred_dict[1] == "123456":
            response_str = "congratulation, you have connect with server\r\nnow, you can do something else"
            await websocket.send(response_str)
            return True
        else:
            response_str = "sorry, the username or password is wrong, please submit again"
            await websocket.send(response_str)

async def recv_msg(websocket):
    global speed_set, modeSelect
    # move.setup()
    direction_command = 'no'
    turn_command = 'no'

    while True: 
        response = {
            'status' : 'ok',
            'title' : '',
            'data' : None
        }

        data = ''
        data = await websocket.recv()
        try:
            data = json.loads(data)
        except Exception as e:
            print('not A JSON')

        if not data:
            continue

        if isinstance(data,str):
            robotCtrl(data, response)

            switchCtrl(data, response)

            functionSelect(data, response)

            configPWM(data, response)

            if 'get_info' == data:
                response['title'] = 'get_info'
                response['data'] = [info.get_cpu_tempfunc(), info.get_cpu_use(), info.get_ram_info()]

            if 'wsB' in data:
                try:
                    set_B=data.split()
                    speed_set = int(set_B[1])
                except:
                    pass

            elif 'AR' == data:
                modeSelect = 'AR'
                screen.screen_show(4, 'ARM MODE ON')
                try:
                    fpv.changeMode('ARM MODE ON')
                except:
                    pass

            elif 'PT' == data:
                modeSelect = 'PT'
                screen.screen_show(4, 'PT MODE ON')
                try:
                    fpv.changeMode('PT MODE ON')
                except:
                    pass

            #CVFL
            elif 'CVFL' == data:
                flask_app.modeselect('findlineCV')

            elif 'CVFLColorSet' in data:
                color = int(data.split()[1])
                flask_app.camera.colorSet(color)

            elif 'CVFLL1' in data:
                pos = int(data.split()[1])
                flask_app.camera.linePosSet_1(pos)

            elif 'CVFLL2' in data:
                pos = int(data.split()[1])
                flask_app.camera.linePosSet_2(pos)

            elif 'CVFLSP' in data:
                err = int(data.split()[1])
                flask_app.camera.errorSet(err)

            elif 'defEC' in data:#Z
                fpv.defaultExpCom()

        elif(isinstance(data,dict)):
            if data['title'] == "findColorSet":
                color = data['data']
                flask_app.colorFindSet(color[0],color[1],color[2])

        print(data)
        response = json.dumps(response)
        await websocket.send(response)

async def main_logic(websocket, path):
    await check_permit(websocket)
    await recv_msg(websocket)

if __name__ == '__main__':
    switch.switchSetup()
    switch.set_all_switch_off()

    HOST = ''
    PORT = 10223                              #Define port serial 
    BUFSIZ = 1024                             #Define buffer size
    ADDR = (HOST, PORT)

    global flask_app
    flask_app = app.webapp()
    flask_app.startthread()

    try:
        RL=robotLight.RobotLight()
        RL.start()
        RL.breath(70,70,255)
    except:
        print('Use "sudo pip3 install rpi_ws281x" to install WS_281x package\n使用"sudo pip3 install rpi_ws281x"命令来安装rpi_ws281x')
        pass

    while  1:
        wifi_check()
        try:                  #Start server,waiting for client
            start_server = websockets.serve(main_logic, '0.0.0.0', 8888)
            asyncio.get_event_loop().run_until_complete(start_server)
            print('waiting for connection...')
            # print('...connected from :', addr)
            break
        except Exception as e:
            print(e)
            RL.setColor(0,0,0)

        try:
            RL.breath(70,70,255)
        except:
            pass
    try:
        RL.pause()
        RL.setColor(0,255,64)
        asyncio.get_event_loop().run_forever()
    except Exception as e:
        print(e)
        RL.setColor(0,0,0)
        # move.destroy()
