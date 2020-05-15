#!/usr/bin/python3
# Description : move.py
# Website	 : gewbot.com
# Author	  : original code by William
# Date		: 2019/09/20
import socket
import time
import threading
try:
	import Adafruit_PCA9685
	pwm = Adafruit_PCA9685.PCA9685()
	pwm.set_pwm_freq(50)
except:
	import os
	os.system("sudo pip3 install adafruit-pca9685")
	import Adafruit_PCA9685
	pwm = Adafruit_PCA9685.PCA9685()
	pwm.set_pwm_freq(50)

MPU_connection = 1
try:
	from mpu6050 import mpu6050
	import PID
	import Kalman_filter
	sensor = mpu6050(0x68)
	print('mpu6050 connected\nmpu6050 is connected and related functions are available.')
	mpu_tor = 0
	X_steady = 0
	Y_steady = 0
	P = 0.3
	I = 0.1
	D = 0
	X_pid = PID.PID()
	X_pid.SetKp(P)
	X_pid.SetKd(I)
	X_pid.SetKi(D)
	Y_pid = PID.PID()
	Y_pid.SetKp(P)
	Y_pid.SetKd(I)
	Y_pid.SetKi(D)
	kalman_filter_X =  Kalman_filter.Kalman_filter(0.001,0.1)
	kalman_filter_Y =  Kalman_filter.Kalman_filter(0.001,0.1)
	steadyMode = 0
except:
	MPU_connection = 0
	steadyMode = 0
	print('mpu6050 disconnected\nmpu6050 is not connected and the related functions are unavailable.')

FLB_port = 0
FLM_port = 1
FLE_port = 2

FRB_port = 6
FRM_port = 7
FRE_port = 8

HLB_port = 3
HLM_port = 4
HLE_port = 5

HRB_port = 9
HRM_port = 10
HRE_port = 11

P_port = 12
T_port = 13

FLB_init_pwm = 313
FLM_init_pwm = 305
FLE_init_pwm = 313

FRB_init_pwm = 325
FRM_init_pwm = 281
FRE_init_pwm = 301

HLB_init_pwm = 312
HLM_init_pwm = 287
HLE_init_pwm = 260

HRB_init_pwm = 305
HRM_init_pwm = 195
HRE_init_pwm = 340

P_init_pwm   = 300
T_init_pwm   = 300

def move_init():
	pwm.set_pwm(FLB_port, 0, FLB_init_pwm)
	pwm.set_pwm(FLM_port, 0, FLM_init_pwm)
	pwm.set_pwm(FLE_port, 0, FLE_init_pwm)

	pwm.set_pwm(FRB_port, 0, FRB_init_pwm)
	pwm.set_pwm(FRM_port, 0, FRM_init_pwm)
	pwm.set_pwm(FRE_port, 0, FRE_init_pwm)

	pwm.set_pwm(HLB_port, 0, HLB_init_pwm)
	pwm.set_pwm(HLM_port, 0, HLM_init_pwm)
	pwm.set_pwm(HLE_port, 0, HLE_init_pwm)

	pwm.set_pwm(HRB_port, 0, HRB_init_pwm)
	pwm.set_pwm(HRM_port, 0, HRM_init_pwm)
	pwm.set_pwm(HRE_port, 0, HRE_init_pwm)

	pwm.set_pwm(P_port, 0, P_init_pwm)
	pwm.set_pwm(T_port, 0, T_init_pwm)

	pwm.set_pwm(14 , 0, 300)
	pwm.set_pwm(15 , 0, 300)
	try:
		old_dict['FLB'] = FLB_init_pwm
		old_dict['FLM'] = FLM_init_pwm
		old_dict['FLE'] = FLE_init_pwm

		old_dict['FRB'] = FRB_init_pwm
		old_dict['FRM'] = FRM_init_pwm
		old_dict['FRE'] = FRE_init_pwm

		old_dict['HLB'] = HLB_init_pwm
		old_dict['HLM'] = HLM_init_pwm
		old_dict['HLE'] = HLE_init_pwm

		old_dict['HRB'] = HRB_init_pwm
		old_dict['HRM'] = HRM_init_pwm
		old_dict['HRE'] = HRE_init_pwm

		old_dict['P'] = P_init_pwm
		old_dict['T'] = T_init_pwm
	except:
		pass

FLB_direction = 1
FLM_direction = -1
FLE_direction = -1

FRB_direction = -1
FRM_direction = 1
FRE_direction = 1

HLB_direction = -1
HLM_direction = 1
HLE_direction = 1

HRB_direction = 1
HRM_direction = -1
HRE_direction = -1

P_direction = 1
T_direction = 1

wiggle_h = 120
wiggle_v = 200
wiggle_middle = 30

deley_time  = 0.02
total_count = 3

old_command = ''
old_dict = {'FLB': FLB_init_pwm, 'FLM': FLM_init_pwm, 'FLE': FLE_init_pwm,
			'FRB': FRB_init_pwm, 'FRM': FRM_init_pwm, 'FRE': FRE_init_pwm,
			'HLB': HLB_init_pwm, 'HLM': HLM_init_pwm, 'HLE': HLE_init_pwm,
			'HRB': HRB_init_pwm, 'HRM': HRM_init_pwm, 'HRE': HRE_init_pwm,
			'P': P_init_pwm, 'T': T_init_pwm}

now_command =''
now_dict = {'FLB': FLB_init_pwm, 'FLM': FLM_init_pwm, 'FLE': FLE_init_pwm,
			'FRB': FRB_init_pwm, 'FRM': FRM_init_pwm, 'FRE': FRE_init_pwm,
			'HLB': HLB_init_pwm, 'HLM': HLM_init_pwm, 'HLE': HLE_init_pwm,
			'HRB': HRB_init_pwm, 'HRM': HRM_init_pwm, 'HRE': HRE_init_pwm,
			'P': P_init_pwm, 'T': T_init_pwm}

goal_command = ''
goal_dict = {'FLB': FLB_init_pwm, 'FLM': FLM_init_pwm, 'FLE': FLE_init_pwm,
			'FRB': FRB_init_pwm, 'FRM': FRM_init_pwm, 'FRE': FRE_init_pwm,
			'HLB': HLB_init_pwm, 'HLM': HLM_init_pwm, 'HLE': HLE_init_pwm,
			'HRB': HRB_init_pwm, 'HRM': HRM_init_pwm, 'HRE': HRE_init_pwm,
			'P': P_init_pwm, 'T': T_init_pwm}

max_dict = {'FLB': 500, 'FLM': 500, 'FLE': 500,
			'FRB': 500, 'FRM': 500, 'FRE': 500,
			'HLB': 500, 'HLM': 500, 'HLE': 500,
			'HRB': 500, 'HRM': 500, 'HRE': 500,
			'P': 500, 'T': 500}

min_dict = {'FLB': 100, 'FLM': 100, 'FLE': 100,
			'FRB': 100, 'FRM': 100, 'FRE': 100,
			'HLB': 100, 'HLM': 100, 'HLE': 100,
			'HRB': 100, 'HRM': 100, 'HRE': 100,
			'P': 100, 'T': 200}


FL_height = 0
FR_height = 0
HL_height = 0
HR_height = 0

PT_speed = 7
P_command = 'stop'
T_command = 'stop'
PT_deley = 0.07

global_position = 0

gait_set = 1
def position_ctrl(change_input):
	global global_position
	if change_input == 'Tforward':
		global_position += 1
		if global_position == 9:
			global_position = 1
	elif change_input == 'Tbackward':
		global_position -= 1
		if global_position <= 0:
			global_position = 8

	elif change_input == 'Dforward':
		if global_position <= 1:
			global_position = 2
		elif global_position > 1 and global_position < 5:
			global_position = 5
		elif global_position > 4 and global_position < 8:
			global_position = 8
		elif global_position == 8:
			global_position = 1
	elif change_input == 'Dbackward':
		if global_position <= 1:
			global_position = 8
		elif global_position > 1 and global_position < 5:
			global_position = 1
		elif global_position > 4 and global_position < 8:
			global_position = 2
		elif global_position == 8:
			global_position = 5


def ctrl_range(raw, max_genout, min_genout):
	if raw > max_genout:
		raw_output = max_genout
	elif raw < min_genout:
		raw_output = min_genout
	else:
		raw_output = raw
	return int(raw_output)


def get_direction():
	return (goal_dict['P'] - P_init_pwm)


def lookleft(speed):
	input_pos = goal_dict['P']
	input_pos += speed*P_direction
	goal_dict['P'] = ctrl_range(input_pos, max_dict['P'], min_dict['P'])
	pwm.set_pwm(P_port, 0, goal_dict['P'])


def lookright(speed):
	input_pos = goal_dict['P']
	input_pos -= speed*P_direction
	goal_dict['P'] = ctrl_range(input_pos, max_dict['P'], min_dict['P'])
	pwm.set_pwm(P_port, 0, goal_dict['P'])


def up(speed):
	input_pos = goal_dict['T']
	input_pos += speed*T_direction
	goal_dict['T'] = ctrl_range(input_pos, max_dict['T'], min_dict['T'])
	pwm.set_pwm(T_port, 0, goal_dict['T'])


def down(speed):
	input_pos = goal_dict['T']
	input_pos -= speed*T_direction
	goal_dict['T'] = ctrl_range(input_pos, max_dict['T'], min_dict['T'])
	pwm.set_pwm(T_port, 0, goal_dict['T'])


def update_old():
	old_dict['FLB'] = now_dict['FLB']
	old_dict['FLM'] = now_dict['FLM']
	old_dict['FLE'] = now_dict['FLE']

	old_dict['FRB'] = now_dict['FRB']
	old_dict['FRM'] = now_dict['FRM']
	old_dict['FRE'] = now_dict['FRE']

	old_dict['HLB'] = now_dict['HLB']
	old_dict['HLM'] = now_dict['HLM']
	old_dict['HLE'] = now_dict['HLE']

	old_dict['HRB'] = now_dict['HRB']
	old_dict['HRM'] = now_dict['HRM']
	old_dict['HRE'] = now_dict['HRE']

	old_dict['P'] = now_dict['P']
	old_dict['T'] = now_dict['T']


def move_smooth_base(servo_name, goal_pwm, old_pwm, now_pos, total_range):
	pwm_input = int(old_pwm+(goal_pwm-old_pwm)*now_pos/total_range)
	pwm.set_pwm(servo_name, 0, pwm_input)
	return pwm_input


def direct_M_move():
	pwm.set_pwm(FLM_port, 0, goal_dict['FLM'])
	pwm.set_pwm(FRM_port, 0, goal_dict['FRM'])
	pwm.set_pwm(HLM_port, 0, goal_dict['HLM'])
	pwm.set_pwm(HRM_port, 0, goal_dict['HRM'])
	old_dict['FLM'] = goal_dict['FLM']
	old_dict['FRM'] = goal_dict['FRM']
	old_dict['HLM'] = goal_dict['HLM']
	old_dict['HRM'] = goal_dict['HRM']


def move_smooth_goal():
	global now_command

	if gait_set == 0 or now_command == 'turnleft' or now_command == 'turnright':
		count_input = total_count*3
	elif gait_set == 1:
		count_input = total_count

	for i in range(0, count_input):
		if goal_command != now_command:
			update_old()
			now_command = goal_command
			return 1
		now_dict['FLB'] = move_smooth_base(FLB_port, goal_dict['FLB'], old_dict['FLB'], i, count_input)
		now_dict['FLM'] = move_smooth_base(FLM_port, goal_dict['FLM'], old_dict['FLM'], i, count_input)
		now_dict['FLE'] = move_smooth_base(FLE_port, goal_dict['FLE'], old_dict['FLE'], i, count_input)

		now_dict['FRB'] = move_smooth_base(FRB_port, goal_dict['FRB'], old_dict['FRB'], i, count_input)
		now_dict['FRM'] = move_smooth_base(FRM_port, goal_dict['FRM'], old_dict['FRM'], i, count_input)
		now_dict['FRE'] = move_smooth_base(FRE_port, goal_dict['FRE'], old_dict['FRE'], i, count_input)

		now_dict['HLB'] = move_smooth_base(HLB_port, goal_dict['HLB'], old_dict['HLB'], i, count_input)
		now_dict['HLM'] = move_smooth_base(HLM_port, goal_dict['HLM'], old_dict['HLM'], i, count_input)
		now_dict['HLE'] = move_smooth_base(HLE_port, goal_dict['HLE'], old_dict['HLE'], i, count_input)

		now_dict['HRB'] = move_smooth_base(HRB_port, goal_dict['HRB'], old_dict['HRB'], i, count_input)
		now_dict['HRM'] = move_smooth_base(HRM_port, goal_dict['HRM'], old_dict['HRM'], i, count_input)
		now_dict['HRE'] = move_smooth_base(HRE_port, goal_dict['HRE'], old_dict['HRE'], i, count_input)

		#now_dict['P'] = move_smooth_base(P_port, goal_dict['P'], old_dict['P'], i, count_input)
		#now_dict['T'] = move_smooth_base(T_port, goal_dict['T'], old_dict['T'], i, count_input)
		time.sleep(deley_time)

	pwm.set_pwm(FLM_port, 0, goal_dict['FLM'])
	pwm.set_pwm(FRM_port, 0, goal_dict['FRM'])
	pwm.set_pwm(HLM_port, 0, goal_dict['HLM'])
	pwm.set_pwm(HRM_port, 0, goal_dict['HRM'])
	old_dict['FLB'] = goal_dict['FLB']
	old_dict['FLM'] = goal_dict['FLM']
	old_dict['FLE'] = goal_dict['FLE']

	old_dict['FRB'] = goal_dict['FRB']
	old_dict['FRM'] = goal_dict['FRM']
	old_dict['FRE'] = goal_dict['FRE']

	old_dict['HLB'] = goal_dict['HLB']
	old_dict['HLM'] = goal_dict['HLM']
	old_dict['HLE'] = goal_dict['HLE']

	old_dict['HRB'] = goal_dict['HRB']
	old_dict['HRM'] = goal_dict['HRM']
	old_dict['HRE'] = goal_dict['HRE']

	old_dict['P'] = goal_dict['P']
	old_dict['T'] = goal_dict['T']
	return 0


def goal_GenOut(position_input, left_direction, right_direction):
	def leg_FL(pos, direction_input):
		if pos == 1:
			goal_dict['FLB'] = int(FLB_init_pwm + (wiggle_middle)*FLB_direction)
			goal_dict['FLM'] = int(FLM_init_pwm + (wiggle_v - FL_height)*FLM_direction)
			goal_dict['FLE'] = int(FLE_init_pwm + (wiggle_v + 0)*FLE_direction)
		elif pos == 2:
			goal_dict['FLB'] = int(FLB_init_pwm + (wiggle_middle + wiggle_h*direction_input)*FLB_direction)
			goal_dict['FLM'] = int(FLM_init_pwm - FL_height*FLM_direction)
			goal_dict['FLE'] = int(FLE_init_pwm)
		else:
			goal_dict['FLB'] = int(FLB_init_pwm + (wiggle_middle + (wiggle_h*(6-(pos-2))/3 - wiggle_h)*direction_input)*FLB_direction)
			goal_dict['FLM'] = int(FLM_init_pwm - FL_height*FLM_direction)
			goal_dict['FLE'] = int(FLE_init_pwm)
		#print('FL: %d'%pos)
	
	def leg_FR(pos, direction_input):
		if pos == 1:
			goal_dict['FRB'] = int(FRB_init_pwm + (wiggle_middle)*FRB_direction)
			goal_dict['FRM'] = int(FRM_init_pwm + (wiggle_v - FR_height)*FRM_direction)
			goal_dict['FRE'] = int(FRE_init_pwm + (wiggle_v + 0)*FRE_direction)
		elif pos == 2:
			goal_dict['FRB'] = int(FRB_init_pwm + (wiggle_middle + wiggle_h*direction_input)*FRB_direction)
			goal_dict['FRM'] = int(FRM_init_pwm - FR_height*FRM_direction)
			goal_dict['FRE'] = int(FRE_init_pwm)
		else:
			goal_dict['FRB'] = int(FRB_init_pwm + (wiggle_middle + (wiggle_h*(6-(pos-2))/3 - wiggle_h)*direction_input)*FRB_direction)
			goal_dict['FRM'] = int(FRM_init_pwm - FR_height*FRM_direction)
			goal_dict['FRE'] = int(FRE_init_pwm)
		#print('FR: %d'%pos)

	def leg_HL(pos, direction_input):
		if pos == 1:
			goal_dict['HLB'] = int(HLB_init_pwm + (-wiggle_middle)*HLB_direction)
			goal_dict['HLM'] = int(HLM_init_pwm + (wiggle_v - HL_height)*HLM_direction)
			goal_dict['HLE'] = int(HLE_init_pwm + (wiggle_v + 0)*HLE_direction)
		elif pos == 2:
			goal_dict['HLB'] = int(HLB_init_pwm + (-wiggle_middle + wiggle_h*direction_input)*HLB_direction)
			goal_dict['HLM'] = int(HLM_init_pwm - HL_height*HLM_direction)
			goal_dict['HLE'] = int(HLE_init_pwm)
		else:
			goal_dict['HLB'] = int(HLB_init_pwm + (-wiggle_middle + (wiggle_h*(6-(pos-2))/3 - wiggle_h)*direction_input)*HLB_direction)
			goal_dict['HLM'] = int(HLM_init_pwm - HL_height*HLM_direction)
			goal_dict['HLE'] = int(HLE_init_pwm)
		#print('HL: %d'%pos)

	def leg_HR(pos, direction_input):
		if pos == 1:
			goal_dict['HRB'] = int(HRB_init_pwm + (-wiggle_middle)*HRB_direction)
			goal_dict['HRM'] = int(HRM_init_pwm + (wiggle_v - HR_height)*HRM_direction)
			goal_dict['HRE'] = int(HRE_init_pwm + (wiggle_v + 0)*HRE_direction)
		elif pos == 2:
			goal_dict['HRB'] = int(HRB_init_pwm + (-wiggle_middle + wiggle_h*direction_input)*HRB_direction)
			goal_dict['HRM'] = int(HRM_init_pwm - HR_height*HRM_direction)
			goal_dict['HRE'] = int(HRE_init_pwm)
		else:
			goal_dict['HRB'] = int(HRB_init_pwm + (-wiggle_middle + (wiggle_h*(6-(pos-2))/3 - wiggle_h)*direction_input)*HRB_direction)
			goal_dict['HRM'] = int(HRM_init_pwm - HR_height*HRM_direction)
			goal_dict['HRE'] = int(HRE_init_pwm)
		#print('HR: %d'%pos)
	#print(position_input)
	if gait_set == 0 or now_command == 'turnleft' or now_command == 'turnright':
		if position_input == 1:
			leg_FL(1, left_direction)
			leg_FR(5, right_direction)

			leg_HL(5, left_direction)
			leg_HR(1, right_direction)
			pass
		elif position_input == 2:
			leg_FL(2, left_direction)
			leg_FR(8, right_direction)

			leg_HL(8, left_direction)
			leg_HR(2, right_direction)
			pass
		elif position_input == 5:
			leg_FL(5, left_direction)
			leg_FR(1, right_direction)

			leg_HL(1, left_direction)
			leg_HR(5, right_direction)
			pass
		elif position_input == 8:
			leg_FL(8, left_direction)
			leg_FR(2, right_direction)

			leg_HL(2, left_direction)
			leg_HR(8, right_direction)
			pass
	elif gait_set == 1:
		if position_input == 1:
			leg_FL(1, left_direction)
			leg_FR(5, right_direction)

			leg_HL(3, left_direction)
			leg_HR(7, right_direction)
			pass
		elif position_input == 2:
			leg_FL(2, left_direction)
			leg_FR(6, right_direction)

			leg_HL(4, left_direction)
			leg_HR(8, right_direction)
			pass
		elif position_input == 3:
			leg_FL(3, left_direction)
			leg_FR(7, right_direction)

			leg_HL(5, left_direction)
			leg_HR(1, right_direction)
			pass
		elif position_input == 4:
			leg_FL(4, left_direction)
			leg_FR(8, right_direction)

			leg_HL(6, left_direction)
			leg_HR(2, right_direction)
			pass
		elif position_input == 5:
			leg_FL(5, left_direction)
			leg_FR(1, right_direction)

			leg_HL(7, left_direction)
			leg_HR(3, right_direction)
			pass
		elif position_input == 6:
			leg_FL(6, left_direction)
			leg_FR(2, right_direction)

			leg_HL(8, left_direction)
			leg_HR(4, right_direction)
			pass
		elif position_input == 7:
			leg_FL(7, left_direction)
			leg_FR(3, right_direction)

			leg_HL(1, left_direction)
			leg_HR(5, right_direction)
			pass
		elif position_input == 8:
			leg_FL(8, left_direction)
			leg_FR(4, right_direction)

			leg_HL(2, left_direction)
			leg_HR(6, right_direction)
			pass


def status_GenOut(height_input, pitch_input, roll_input):
	FL_input = wiggle_v*pitch_input + wiggle_v*roll_input
	FR_input = wiggle_v*pitch_input - wiggle_v*roll_input

	HL_input = - wiggle_v*pitch_input + wiggle_v*roll_input
	HR_input = - wiggle_v*pitch_input - wiggle_v*roll_input
	def leg_FL_status():
		goal_dict['FLB'] = FLB_init_pwm
		goal_dict['FLM'] = ctrl_range(int(FLM_init_pwm + (height_input + FL_input)*FLM_direction), max_dict['FLM'], min_dict['FLM'])
		goal_dict['FLE'] = FLE_init_pwm
	
	def leg_FR_status():
		goal_dict['FRB'] = FRB_init_pwm
		goal_dict['FRM'] = ctrl_range(int(FRM_init_pwm + (height_input + FR_input)*FRM_direction), max_dict['FRM'], min_dict['FRM'])
		goal_dict['FRE'] = FRE_init_pwm

	def leg_HL_status():
		goal_dict['HLB'] = HLB_init_pwm
		goal_dict['HLM'] = ctrl_range(int(HLM_init_pwm + (height_input + HL_input)*HLM_direction), max_dict['FRM'], min_dict['FRM'])
		goal_dict['HLE'] = HLE_init_pwm

	def leg_HR_status():
		goal_dict['HRB'] = HRB_init_pwm
		goal_dict['HRM'] = ctrl_range(int(HRM_init_pwm + (height_input + HR_input)*HRM_direction), max_dict['FRM'], min_dict['FRM'])
		goal_dict['HRE'] = HRE_init_pwm

	leg_FL_status()
	leg_FR_status()
	leg_HL_status()
	leg_HR_status()
	print(goal_dict['FLM'])


def command_GenOut():
	global now_command
	now_command = goal_command
	if now_command == 'forward':
		goal_GenOut(global_position, 1, 1)
		if gait_set == 1:
			position_ctrl('Tforward')
		elif gait_set  == 0:
			position_ctrl('Dforward')
	elif now_command == 'backward':
		goal_GenOut(global_position, 1, 1)
		if gait_set == 1:
			position_ctrl('Tbackward')
		elif gait_set  == 0:
			position_ctrl('Dbackward')
	elif now_command == 'turnleft':
		goal_GenOut(global_position, -1, 1)
		position_ctrl('Dforward')
	elif now_command == 'turnright':
		goal_GenOut(global_position, 1, -1)
		position_ctrl('Dforward')
	elif now_command == 'stop':
		pass
	
	elif now_command == 'StandUp':
		status_GenOut(-500, 0, 0)
	elif now_command == 'StayLow':
		status_GenOut(500, 0, 0)
	elif now_command == 'Lean-L':
		status_GenOut(0, 0, 10)
	elif now_command == 'Lean-R':
		status_GenOut(0, 0, -10)
	elif now_command == 'Lean-F':
		status_GenOut(0, 10, 0)
	elif now_command == 'Lean-H':
		status_GenOut(0, -10, 0)


def steady():
	global sensor
	if steadyMode:
		if MPU_connection:
			try:
				accelerometer_data = sensor.get_accel_data()
				X = accelerometer_data['x']
				X = kalman_filter_X.kalman(X)
				Y = accelerometer_data['y']
				Y = kalman_filter_Y.kalman(Y)

				#X_error = X_pid.GenOut(X_steady-X)
				#Y_error = Y_pid.GenOut(Y_steady-Y)

				X_error = X-X_steady
				Y_error = Y-Y_steady

				if abs(X_error)>mpu_tor or abs(Y_error)>mpu_tor:
					status_GenOut(0, X_error*P, Y_error*P)
					direct_M_move()
				# print('X:%f'%X_error)
				# print('Y:%f'%Y_error)
			except:
				time.sleep(0.1)
				sensor = mpu6050(0x68)
				pass


def action_1():
	for i in range(-50,50):
		status_GenOut(0, i*0.01, 0)
		direct_M_move()
		time.sleep(0.01)
	for i in range(-50,50):
		status_GenOut(0, -i*0.01, 0)
		direct_M_move()
		time.sleep(0.01)
	for i in range(-50,50):
		status_GenOut(0, i*0.01, 0)
		direct_M_move()
		time.sleep(0.01)
	for i in range(-50,50):
		status_GenOut(0, -i*0.01, 0)
		direct_M_move()
		time.sleep(0.01)
	move_init()


def action_2():
	for i in range(-50,50):
		status_GenOut(0, 0, i*0.01)
		direct_M_move()
		time.sleep(0.01)
	for i in range(-50,50):
		status_GenOut(0, 0, -i*0.01)
		direct_M_move()
		time.sleep(0.01)
	for i in range(-50,50):
		status_GenOut(0, 0, i*0.01)
		direct_M_move()
		time.sleep(0.01)
	for i in range(-50,50):
		status_GenOut(0, 0, -i*0.01)
		direct_M_move()
		time.sleep(0.01)
	move_init()


def walk(direction):
	global goal_command
	goal_command = direction
	Servo.resume()


def servoStop():
	global goal_command
	goal_command = 'stop'
	Servo.pause()


def headUp():
	global T_command
	T_command = 'headUp'
	Head.resume()


def headDown():
	global T_command
	T_command = 'headDown'
	Head.resume()


def headLeft():
	global P_command
	P_command = 'headLeft'
	Head.resume()


def headRight():
	global P_command
	P_command = 'headRight'
	Head.resume()


def headStop():
	global P_command, T_command
	P_command = 'Stop'
	T_command = 'Stop'
	Head.pause()


def steadyModeOn():
	global steadyMode
	if MPU_connection:
		steadyMode = 1
		Servo.resume()


def steadyModeOff():
	global steadyMode
	steadyMode = 0
	Servo.pause()


class Servo_ctrl(threading.Thread):
	def __init__(self, *args, **kwargs):
		super(Servo_ctrl, self).__init__(*args, **kwargs)
		self.__flag = threading.Event()
		self.__flag.set()
		self.__running = threading.Event()
		self.__running.set()

	def run(self):
		global goal_pos, servo_command, init_get, if_continue, walk_step
		while self.__running.isSet():
			self.__flag.wait()
			if not steadyMode:
				command_GenOut()
				while move_smooth_goal():
					if goal_command == 'stop':
						break
					else:
						continue
				if goal_command == 'StandUp' or goal_command == 'StayLow' or goal_command == 'Lean-L' or goal_command == 'Lean-R':
					servoStop()
			else:
				steady()
				time.sleep(0.03)		
			print('loop')

	def pause(self):
		self.__flag.clear()

	def resume(self):
		self.__flag.set()

	def stop(self):
		self.__flag.set()
		self.__running.clear()


class Head_ctrl(threading.Thread):
	def __init__(self, *args, **kwargs):
		super(Head_ctrl, self).__init__(*args, **kwargs)
		self.__flag = threading.Event()
		self.__flag.set()
		self.__running = threading.Event()
		self.__running.set()

	def run(self):
		global T_command, P_command
		while self.__running.isSet():
			self.__flag.wait()
			if T_command == 'headUp':
				up(PT_speed)
			elif T_command == 'headDown':
				down(PT_speed)
			
			if P_command == 'headRight':
				lookright(PT_speed)
			elif P_command == 'headLeft':
				lookleft(PT_speed)

			if max_dict['P'] == goal_dict['P'] or min_dict['P'] == goal_dict['P']:
				P_command = 'stop'

			if max_dict['T'] == goal_dict['T'] or min_dict['T'] == goal_dict['T']:
				T_command = 'stop'

			if T_command == 'stop' and P_command == 'stop':
				self.pause()

			time.sleep(PT_deley)
			print('loop')



	def pause(self):
		self.__flag.clear()

	def resume(self):
		self.__flag.set()

	def stop(self):
		self.__flag.set()
		self.__running.clear()


Servo = Servo_ctrl()
Servo.start()
Servo.pause()

Head = Head_ctrl()
Head.start()
Head.pause()

if __name__ == '__main__':
	action_1()
	#steadyMode = 1
	#while 1:
	#	steady()
	#	time.sleep(0.03)
	#	pass
	'''
	time.sleep(3)
	walk('StandUp')
	time.sleep(1)
	walk('StayLow')
	time.sleep(2)
	walk('StandUp')
	time.sleep(2)
	walk('Lean-L')
	time.sleep(2)
	walk('Lean-R')
	time.sleep(2)
	walk('Lean-F')
	time.sleep(2)
	walk('Lean-H')
	'''
	'''
	move_init()
	time.sleep(1)

	headLeft()
	time.sleep(1)
	headRight()
	time.sleep(10)
	headStop()
	'''

	'''
	walk('forward')
	time.sleep(10)
	walk('backward')
	time.sleep(5)

	walk('turnleft')
	time.sleep(5)

	walk('turnright')
	time.sleep(10)

	walk('turnleft')
	time.sleep(5)

	gait_set = 0
	walk('forward')
	time.sleep(10)
	'''
	'''
	walk('backward')
	time.sleep(10)
	'''
	#servoStop()
	#print('start walking')

	
	'''
	#move_smooth_goal()
	goal_dict['FLB'] = 500
	move_smooth_goal()
	goal_dict['FLB'] = 100
	move_smooth_goal()
	goal_dict['FLB'] = 300
	move_smooth_goal()
	'''
	pass
