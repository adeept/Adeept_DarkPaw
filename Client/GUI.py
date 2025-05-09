#!/usr/bin/env/python
# File name   : GUI.py
# Website     : www.adeept.com
# Author      : Adeept
# Date		: 2025/04/26
import cv2
import zmq
import base64
import numpy as np
from socket import *
import sys
import time
import threading as thread
import tkinter as tk
import subprocess

ip_stu=1		#Shows connection status
c_f_stu = 0
c_b_stu = 0
c_l_stu = 0
c_r_stu = 0
c_ls_stu= 0
c_rs_stu= 0
funcMode= 0
tcpClicSock = ''
root = ''
stat = 0

Switch_3 = 0
Switch_2 = 0
Switch_1 = 0
SmoothMode = 0

########>>>>>VIDEO<<<<<########
def RGB_to_Hex(r, g, b):
	return ('#'+str(hex(r))[-2:]+str(hex(g))[-2:]+str(hex(b))[-2:]).replace('x','0').upper()

def run_open():
    script_path = 'Footage-GUI.py'
    result = subprocess.run(['python', script_path], capture_output=True, text=True)
    print('stdout:', result.stdout)
    print('stderr:', result.stderr)



def video_thread():
	global footage_socket, font, frame_num, fps
	context = zmq.Context()
	footage_socket = context.socket(zmq.PAIR)
	footage_socket.bind('tcp://*:5555')
	cv2.namedWindow('Stream',flags=cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
	font = cv2.FONT_HERSHEY_SIMPLEX
	frame_num = 0
	fps = 0

def get_FPS():
	global frame_num, fps
	while 1:
		try:
			time.sleep(1)
			fps = frame_num
			frame_num = 0
		except:
			time.sleep(1)

def opencv_r():
	global frame_num
	while True:
		try:
			frame = footage_socket.recv_string()
			img = base64.b64decode(frame)
			npimg = np.frombuffer(img, dtype=np.uint8)
			source = cv2.imdecode(npimg, 1)
			cv2.putText(source,('PC FPS: %s'%fps),(40,20), font, 0.5,(255,255,255),1,cv2.LINE_AA)
			try:
				cv2.putText(source,('CPU Temperature: %s'%CPU_TEP),(370,350), font, 0.5,(128,255,128),1,cv2.LINE_AA)
				cv2.putText(source,('CPU Usage: %s'%CPU_USE),(370,380), font, 0.5,(128,255,128),1,cv2.LINE_AA)
				cv2.putText(source,('RAM Usage: %s'%RAM_USE),(370,410), font, 0.5,(128,255,128),1,cv2.LINE_AA)
			except:
				pass
			cv2.imshow("Stream", source)
			frame_num += 1
			cv2.waitKey(1)

		except:
			time.sleep(0.5)
			break
########>>>>>VIDEO<<<<<########


def replace_num(initial,new_num):   #Call this function to replace data in '.txt' file
	newline=""
	str_num=str(new_num)
	with open("ip.txt","r") as f:
		for line in f.readlines():
			if(line.find(initial) == 0):
				line = initial+"%s" %(str_num)
			newline += line
	with open("ip.txt","w") as f:
		f.writelines(newline)	#Call this function to replace data in '.txt' file


def num_import(initial):			#Call this function to import data from '.txt' file
	with open("ip.txt") as f:
		for line in f.readlines():
			if(line.find(initial) == 0):
				r=line
	begin=len(list(initial))
	snum=r[begin:]
	n=snum
	return n	


def call_forward(event):		 #When this function is called,client commands the car to move forward
	global c_f_stu
	if c_f_stu == 0:
		tcpClicSock.send(('forward').encode())
		c_f_stu=1


def call_back(event):			#When this function is called,client commands the car to move backward
	global c_b_stu 
	if c_b_stu == 0:
		tcpClicSock.send(('backward').encode())
		c_b_stu=1


def call_FB_stop(event):			#When this function is called,client commands the car to stop moving
	global c_f_stu,c_b_stu,c_l_stu,c_r_stu,c_ls_stu,c_rs_stu
	c_f_stu=0
	c_b_stu=0
	tcpClicSock.send(('DS').encode())


def call_Turn_stop(event):			#When this function is called,client commands the car to stop moving
	global c_f_stu,c_b_stu,c_l_stu,c_r_stu,c_ls_stu,c_rs_stu
	c_l_stu=0
	c_r_stu=0
	c_ls_stu=0
	c_rs_stu=0
	tcpClicSock.send(('TS').encode())


def call_Left(event):			#When this function is called,client commands the car to turn left
	global c_l_stu
	if c_l_stu == 0:
		tcpClicSock.send(('left').encode())
		c_l_stu=1


def call_Right(event):		   #When this function is called,client commands the car to turn right
	global c_r_stu
	if c_r_stu == 0:
		tcpClicSock.send(('right').encode())
		c_r_stu=1


def call_StandUp(event):
	global c_ls_stu
	if c_ls_stu == 0:
		tcpClicSock.send(('StandUp').encode())
		c_ls_stu=1


def call_StayLow(event):
	global c_rs_stu
	if c_rs_stu == 0:
		tcpClicSock.send(('StayLow').encode())
		c_rs_stu=1


def call_up(event):
	tcpClicSock.send(('up').encode())


def call_down(event):
	tcpClicSock.send(('down').encode())


def call_Lean_L(event):
	tcpClicSock.send(('Lean-L').encode())


def call_Lean_R(event):
	tcpClicSock.send(('Lean-R').encode())


def call_home(event):
	tcpClicSock.send(('home').encode())


def call_steady(event):
	global funcMode
	if funcMode == 0:
		tcpClicSock.send(('steadyCamera').encode())
		funcMode = 1
	else:
		tcpClicSock.send(('steadyCameraOff').encode())
		funcMode = 0


def call_FindColor(event):
	global funcMode
	if funcMode == 0:
		tcpClicSock.send(('findColor').encode())
		funcMode = 1
	else:
		tcpClicSock.send(('stopCV').encode())
		funcMode = 0
def call_Police(event):
	global funcMode
	if funcMode == 0:
		tcpClicSock.send(('police').encode())
		funcMode = 1
	else:
		tcpClicSock.send(('policeOff').encode())
		funcMode = 0

def call_WatchDog(event):
	global funcMode
	if funcMode == 0:
		tcpClicSock.send(('motionGet').encode())
		funcMode = 1
	else:
		tcpClicSock.send(('stopCV').encode())
		funcMode = 0

def call_Switch_1(event):
	if Switch_1 == 0:
		tcpClicSock.send(('Switch_1_on').encode())
	else:
		tcpClicSock.send(('Switch_1_off').encode())


def call_Switch_2(event):
	if Switch_2 == 0:
		tcpClicSock.send(('Switch_2_on').encode())
	else:
		tcpClicSock.send(('Switch_2_off').encode())


def call_Switch_3(event):
	if Switch_3 == 0:
		tcpClicSock.send(('Switch_3_on').encode())
	else:
		tcpClicSock.send(('Switch_3_off').encode())


def all_btn_red():
	Btn_Steady.config(bg='#FF6D00', fg='#000000')
	Btn_FindColor.config(bg='#FF6D00', fg='#000000')
	Btn_WatchDog.config(bg='#FF6D00', fg='#000000')
	Btn_Police.config(bg='#FF6D00', fg='#000000')


def all_btn_normal():
	Btn_Steady.config(bg=color_btn, fg=color_text)
	Btn_FindColor.config(bg=color_btn, fg=color_text)
	Btn_WatchDog.config(bg=color_btn, fg=color_text)
	Btn_Police.config(bg=color_btn, fg=color_text)


def connection_thread():
	global funcMode, Switch_3, Switch_2, Switch_1, SmoothMode
	while 1:
		car_info = (tcpClicSock.recv(BUFSIZ)).decode()
		if not car_info:
			continue

		elif 'findColor' in car_info:
			funcMode = 1
			Btn_FindColor.config(bg='#FF6D00', fg='#000000')

		elif 'steadyCamera' == car_info:
			funcMode = 1
			Btn_Steady.config(bg='#FF6D00', fg='#000000')

		elif 'steadyCameraOff' == car_info:
			funcMode = 0
			Btn_Steady.config(bg=color_btn, fg=color_text)

		elif 'motionGet' in car_info:
			funcMode = 1
			Btn_WatchDog.config(bg='#FF6D00', fg='#000000')

		elif 'police' == car_info:
			funcMode = 1
			Btn_Police.config(bg='#FF6D00', fg='#000000')

		elif 'policeOff' == car_info:
			funcMode = 0
			Btn_Police.config(bg=color_btn, fg=color_text)

		elif 'Switch_3_on' in car_info:
			Switch_3 = 1
			Btn_Switch_3.config(bg='#4CAF50')

		elif 'Switch_2_on' in car_info:
			Switch_2 = 1
			Btn_Switch_2.config(bg='#4CAF50')

		elif 'Switch_1_on' in car_info:
			Switch_1 = 1
			Btn_Switch_1.config(bg='#4CAF50')

		elif 'Switch_3_off' in car_info:
			Switch_3 = 0
			Btn_Switch_3.config(bg=color_btn)

		elif 'Switch_2_off' in car_info:
			Switch_2 = 0
			Btn_Switch_2.config(bg=color_btn)

		elif 'Switch_1_off' in car_info:
			Switch_1 = 0
			Btn_Switch_1.config(bg=color_btn)

		elif 'stopCV' in car_info:
			funcMode = 0
			Btn_FindColor.config(bg=color_btn, fg=color_text)
			Btn_WatchDog.config(bg=color_btn, fg=color_text)

		print(car_info)


def Info_receive():
	global CPU_TEP,CPU_USE,RAM_USE
	HOST = ''
	INFO_PORT = 2256							#Define port serial 
	ADDR = (HOST, INFO_PORT)
	InfoSock = socket(AF_INET, SOCK_STREAM)
	InfoSock.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
	InfoSock.bind(ADDR)
	InfoSock.listen(5)					  #Start server,waiting for client
	InfoSock, addr = InfoSock.accept()
	print('Info connected')
	while 1:
		try:
			info_data = ''
			info_data = str(InfoSock.recv(BUFSIZ).decode())
			info_get = info_data.split()
			CPU_TEP,CPU_USE,RAM_USE= info_get
			CPU_TEP_lab.config(text='CPU Temp: %s℃'%CPU_TEP)
			CPU_USE_lab.config(text='CPU Usage: %s'%CPU_USE)
			RAM_lab.config(text='RAM Usage: %s'%RAM_USE)
		except:
			pass


def socket_connect():	 #Call this function to connect with the server
	global ADDR,tcpClicSock,BUFSIZ,ip_stu,ipaddr
	ip_adr=E1.get()	   #Get the IP address from Entry

	if ip_adr == '':	  #If no input IP address in Entry,import a default IP
		ip_adr=num_import('IP:')
		l_ip_4.config(text='Connecting')
		l_ip_4.config(bg='#FF8F00')
		l_ip_5.config(text='Default:%s'%ip_adr)
		pass
	
	SERVER_IP = ip_adr
	SERVER_PORT = 10223   #Define port serial 
	BUFSIZ = 1024		 #Define buffer size
	ADDR = (SERVER_IP, SERVER_PORT)
	tcpClicSock = socket(AF_INET, SOCK_STREAM) #Set connection value for socket

	for i in range (1,6): #Try 5 times if disconnected
		if ip_stu == 1:
			print("Connecting to server @ %s:%d..." %(SERVER_IP, SERVER_PORT))
			print("Connecting")
			tcpClicSock.connect(ADDR)		#Connection with the server
		
			print("Connected")
		
			l_ip_5.config(text='IP:%s'%ip_adr)
			l_ip_4.config(text='Connected')
			l_ip_4.config(bg='#558B2F')

			replace_num('IP:',ip_adr)
			E1.config(state='disabled')	  #Disable the Entry
			Btn14.config(state='disabled')   #Disable the Entry
			
			ip_stu=0						 #'0' means connected

			connection_threading=thread.Thread(target=connection_thread)		 #Define a thread for FPV and OpenCV
			connection_threading.daemon = True						 #'True' means it is a front thread,it would close when the mainloop() closes
			connection_threading.start()									 #Thread starts

			info_threading=thread.Thread(target=Info_receive)		 #Define a thread for FPV and OpenCV
			info_threading.daemon = True									 #'True' means it is a front thread,it would close when the mainloop() closes
			info_threading.start()									 #Thread starts

			video_threading=thread.Thread(target=run_open)		 #Define a thread for FPV and OpenCV
			video_threading.daemon = True
			video_threading.start()									 #Thread starts

			break
		else:
			print("Cannot connecting to server,try it latter!")
			l_ip_4.config(text='Try %d/5 time(s)'%i)
			l_ip_4.config(bg='#EF6C00')
			print('Try %d/5 time(s)'%i)
			ip_stu=1
			time.sleep(1)
			continue

	if ip_stu == 1:
		l_ip_4.config(text='Disconnected')
		l_ip_4.config(bg='#F44336')


def connect_click():	   #Call this function to connect with the server
	if ip_stu == 1:
		sc=thread.Thread(target=socket_connect) #Define a thread for connection
		sc.daemon = True
		sc.start()							  #Thread starts


def loop():					  #GUI
	global tcpClicSock,root,E1,connect,l_ip_4,l_ip_5,color_btn,color_text,Btn14,CPU_TEP_lab,CPU_USE_lab,RAM_lab,canvas_ultra,color_text,var_R,var_B,var_G,Btn_Steady,Btn_FindColor,Btn_WatchDog,Btn_Police,Btn_Switch_1,Btn_Switch_2,Btn_Switch_3,Btn_Smooth   #The value of tcpClicSock changes in the function loop(),would also changes in global so the other functions could use it.
	while True:
		color_bg='#000000'		#Set background color
		color_text='#E1F5FE'	  #Set text color
		color_btn='#0277BD'	   #Set button color
		color_line='#01579B'	  #Set line color
		color_can='#212121'	   #Set canvas color
		color_oval='#2196F3'	  #Set oval color
		target_color='#FF6D00'

		root = tk.Tk()			#Define a window named root
		root.title('Adeept DarkPaw')	  #Main window title
		root.geometry('565x510')  #Main window size, middle of the English letter x.
		root.config(bg=color_bg)  #Set the background color of root window

		try:
			logo =tk.PhotoImage(file = 'logo.png')		 #Define the picture of logo,but only supports '.png' and '.gif'
			l_logo=tk.Label(root,image = logo,bg=color_bg) #Set a label to show the logo picture
			l_logo.place(x=30,y=13)						#Place the Label in a right position
		except:
			pass

		CPU_TEP_lab=tk.Label(root,width=18,text='CPU Temp:',fg=color_text,bg='#212121')
		CPU_TEP_lab.place(x=400,y=15)						 #Define a Label and put it in position

		CPU_USE_lab=tk.Label(root,width=18,text='CPU Usage:',fg=color_text,bg='#212121')
		CPU_USE_lab.place(x=400,y=45)						 #Define a Label and put it in position

		RAM_lab=tk.Label(root,width=18,text='RAM Usage:',fg=color_text,bg='#212121')
		RAM_lab.place(x=400,y=75)						 #Define a Label and put it in position

		l_ip_4=tk.Label(root,width=18,text='Disconnected',fg=color_text,bg='#F44336')
		l_ip_4.place(x=400,y=110)						 #Define a Label and put it in position

		l_ip_5=tk.Label(root,width=18,text='Use default IP',fg=color_text,bg=color_btn)
		l_ip_5.place(x=400,y=145)						 #Define a Label and put it in position

		E1 = tk.Entry(root,show=None,width=16,bg="#37474F",fg='#eceff1')
		E1.place(x=180,y=40)							 #Define a Entry and put it in position

		l_ip_3=tk.Label(root,width=10,text='IP Address:',fg=color_text,bg='#000000')
		l_ip_3.place(x=175,y=15)						 #Define a Label and put it in position

		Btn_Switch_1 = tk.Button(root, width=8, text='Port 1',fg=color_text,bg=color_btn,relief='ridge')
		Btn_Switch_2 = tk.Button(root, width=8, text='Port 2',fg=color_text,bg=color_btn,relief='ridge')
		Btn_Switch_3 = tk.Button(root, width=8, text='Port 3',fg=color_text,bg=color_btn,relief='ridge')

		Btn_Switch_1.place(x=30,y=265)
		Btn_Switch_2.place(x=100,y=265)
		Btn_Switch_3.place(x=170,y=265)

		Btn_Switch_1.bind('<ButtonPress-1>', call_Switch_1)
		Btn_Switch_2.bind('<ButtonPress-1>', call_Switch_2)
		Btn_Switch_3.bind('<ButtonPress-1>', call_Switch_3)

		Btn0 = tk.Button(root, width=8, text='Forward',fg=color_text,bg=color_btn,relief='ridge')
		Btn1 = tk.Button(root, width=8, text='Backward',fg=color_text,bg=color_btn,relief='ridge')
		Btn2 = tk.Button(root, width=8, text='Left',fg=color_text,bg=color_btn,relief='ridge')
		Btn3 = tk.Button(root, width=8, text='Right',fg=color_text,bg=color_btn,relief='ridge')

		Btn_LeftSide = tk.Button(root, width=8, text='STAND UP',fg=color_text,bg=color_btn,relief='ridge')
		Btn_LeftSide.place(x=30,y=195)
		Btn_LeftSide.bind('<ButtonPress-1>', call_StandUp)
		Btn_LeftSide.bind('<ButtonRelease-1>', call_Turn_stop)

		Btn_RightSide = tk.Button(root, width=8, text='STAY LOW',fg=color_text,bg=color_btn,relief='ridge')
		Btn_RightSide.place(x=170,y=195)
		Btn_RightSide.bind('<ButtonPress-1>', call_StayLow)
		Btn_RightSide.bind('<ButtonRelease-1>', call_Turn_stop)

		Btn0.place(x=400,y=195)
		Btn1.place(x=400,y=265)
		Btn2.place(x=330,y=230)
		Btn3.place(x=470,y=230)

		Btn0.bind('<ButtonPress-1>', call_forward)
		Btn1.bind('<ButtonPress-1>', call_back)
		Btn2.bind('<ButtonPress-1>', call_Left)
		Btn3.bind('<ButtonPress-1>', call_Right)

		Btn0.bind('<ButtonRelease-1>', call_FB_stop)
		Btn1.bind('<ButtonRelease-1>', call_FB_stop)
		Btn2.bind('<ButtonRelease-1>', call_Turn_stop)
		Btn3.bind('<ButtonRelease-1>', call_Turn_stop)

		root.bind('<KeyPress-w>', call_forward) 
		root.bind('<KeyPress-a>', call_Left)
		root.bind('<KeyPress-d>', call_Right)
		root.bind('<KeyPress-s>', call_back)

		root.bind('<KeyPress-u>', call_StandUp)
		root.bind('<KeyPress-o>', call_StayLow)
		root.bind('<KeyRelease-u>', call_Turn_stop)
		root.bind('<KeyRelease-o>', call_Turn_stop)

		root.bind('<KeyRelease-w>', call_FB_stop)
		root.bind('<KeyRelease-a>', call_Turn_stop)
		root.bind('<KeyRelease-d>', call_Turn_stop)
		root.bind('<KeyRelease-s>', call_FB_stop)

		Btn_up = tk.Button(root, width=8, text='UP',fg=color_text,bg=color_btn,relief='ridge')
		Btn_down = tk.Button(root, width=8, text='DOWN',fg=color_text,bg=color_btn,relief='ridge')
		Btn_left = tk.Button(root, width=8, text='LEAN-L',fg=color_text,bg=color_btn,relief='ridge')
		Btn_right = tk.Button(root, width=8, text='LEAN-R',fg=color_text,bg=color_btn,relief='ridge')
		Btn_home = tk.Button(root, width=8, text='Home',fg=color_text,bg=color_btn,relief='ridge')
		Btn_up.place(x=100,y=195)
		Btn_down.place(x=100,y=230)
		Btn_left.place(x=30,y=230)
		Btn_right.place(x=170,y=230)
		Btn_home.place(x=400,y=230)
		root.bind('<KeyPress-i>', call_up) 
		root.bind('<KeyPress-k>', call_down)
		root.bind('<KeyPress-j>', call_Lean_L)
		root.bind('<KeyPress-l>', call_Lean_R)
		root.bind('<KeyPress-h>', call_home)
		Btn_up.bind('<ButtonPress-1>', call_up)
		Btn_down.bind('<ButtonPress-1>', call_down)
		Btn_left.bind('<ButtonPress-1>', call_Lean_L)
		Btn_right.bind('<ButtonPress-1>', call_Lean_R)
		Btn_home.bind('<ButtonPress-1>', call_home)

		Btn14= tk.Button(root, width=8,height=2, text='Connect',fg=color_text,bg=color_btn,command=connect_click,relief='ridge')
		Btn14.place(x=315,y=15)						  #Define a Button and put it in position

		root.bind('<Return>', connect)
		global canvas_show
		def R_send(event):
			canvas_show.config(bg = RGB_to_Hex(int(var_R.get()), int(var_G.get()), int(var_B.get())))
			time.sleep(0.03)


		def G_send(event):
			canvas_show.config(bg = RGB_to_Hex(int(var_R.get()), int(var_G.get()), int(var_B.get())))
			time.sleep(0.03)

		def B_send(event):
			canvas_show.config(bg = RGB_to_Hex(int(var_R.get()), int(var_G.get()), int(var_B.get())))
			time.sleep(0.03)  

		def call_SET(event):
			r = int(var_R.get())
			g = int(var_G.get())
			b = int(var_B.get())

			data_str = f"{r}, {g}, {b}"
			message = f"{{'title': 'findColorSet', 'data': [{data_str}]}}"
			tcpClicSock.send(message.encode())
		var_R = tk.StringVar()
		var_R.set(80)

		Scale_R = tk.Scale(root,label=None,
		from_=0,to=255,orient=tk.HORIZONTAL,length=238,
		showvalue=1,tickinterval=None,resolution=1,variable=var_R,troughcolor='#F44336',command=R_send,fg=color_text,bg=color_bg,highlightthickness=0)
		Scale_R.place(x=30,y=330)							#Define a Scale and put it in position

		var_G = tk.StringVar()
		var_G.set(80)

		Scale_G = tk.Scale(root,label=None,
		from_=0,to=255,orient=tk.HORIZONTAL,length=238,
		showvalue=1,tickinterval=None,resolution=1,variable=var_G,troughcolor='#00E676',command=G_send,fg=color_text,bg=color_bg,highlightthickness=0)
		Scale_G.place(x=30,y=360)							#Define a Scale and put it in position

		var_B = tk.StringVar()
		var_B.set(80)

		Scale_B = tk.Scale(root,label=None,
		from_=0,to=255,orient=tk.HORIZONTAL,length=238,
		showvalue=1,tickinterval=None,resolution=1,variable=var_B,troughcolor='#448AFF',command=B_send,fg=color_text,bg=color_bg,highlightthickness=0)
		Scale_B.place(x=30,y=390)							#Define a Scale and put it in position
		canvas_cover=tk.Canvas(root,bg=color_bg,height=30,width=510,highlightthickness=0)
		canvas_cover.place(x=30,y=330+90)
		canvas_show=tk.Canvas(root,bg=RGB_to_Hex(int(var_R.get()), int(var_G.get()), int(var_B.get())),height=35,width=170,highlightthickness=0)
		canvas_show.place(x=238+30+21,y=330+15)


		Btn_WB = tk.Button(root, width=23, text='Color Set',fg=color_text,bg='#212121',relief='ridge')
		Btn_WB.place(x=30+238+21,y=330+60)
		Btn_WB.bind('<ButtonPress-1>', call_SET)
  

		canvas_cover=tk.Canvas(root,bg=color_bg,height=30,width=510,highlightthickness=0)
		canvas_cover.place(x=30,y=420)

		Btn_Steady = tk.Button(root, width=10, text='Steady',fg=color_text,bg=color_btn,relief='ridge')
		Btn_Steady.place(x=30,y=445)
		root.bind('<KeyPress-z>', call_steady)
		Btn_Steady.bind('<ButtonPress-1>', call_steady)

		Btn_FindColor = tk.Button(root, width=10, text='FindColor',fg=color_text,bg=color_btn,relief='ridge')
		Btn_FindColor.place(x=115,y=445)
		root.bind('<KeyPress-z>', call_FindColor)
		Btn_FindColor.bind('<ButtonPress-1>', call_FindColor)

		Btn_WatchDog = tk.Button(root, width=10, text='WatchDog',fg=color_text,bg=color_btn,relief='ridge')
		Btn_WatchDog.place(x=200,y=445)
		root.bind('<KeyPress-z>', call_WatchDog)
		Btn_WatchDog.bind('<ButtonPress-1>', call_WatchDog)

		Btn_Police = tk.Button(root, width=10, text='Police',fg=color_text,bg=color_btn,relief='ridge')
		Btn_Police.place(x=285,y=445)
		root.bind('<KeyPress-z>', call_Police)
		Btn_Police.bind('<ButtonPress-1>', call_Police)

		global stat
		if stat==0:			  # Ensure the mainloop runs only once
			root.mainloop()  # Run the mainloop()
			stat=1		   # Change the value to '1' so the mainloop() would not run again.


if __name__ == '__main__':
	try:
		loop()				   # Load GUI
	except:
		tcpClicSock.close()		  # Close socket or it may not connect with the server again
		footage_socket.close()
		cv2.destroyAllWindows()
		pass