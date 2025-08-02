#! /usr/bin/python
# File name   : move.py
# Description : Controlling all servos
# Website	 : www.adeept.com
# E-mail	  : support@adeept.com
# Author	  : William
# Date		: 2019/04/08
import time
import Adafruit_PCA9685
import logging

import Kalman_filter
import PID

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(50)

# Using lists instead of exec for safer and cleaner code
pwm_init = [300] * 16
pwm_max = [450] * 16
pwm_min = [150] * 16

'''
Leg_I   --- forward --- Leg_III
               |
           robotbody
               |
Leg_II  -- backward --- Leg_IV 
'''
Set_Direction = 1
reach_wiggle = 100
max_wiggle = 150

'''
the bigger pixel is, the slower the robot run.
'''
pixel = 4

'''
Set PID
'''
P = 3
I = 0.1
D = 0

'''
>>> instantiation <<<
'''
X_fix_output = 0
Y_fix_output = 0
X_steady = 0
Y_steady = 0
X_pid = PID.PID()
X_pid.SetKp(P)
X_pid.SetKd(I)
X_pid.SetKi(D)
Y_pid = PID.PID()
Y_pid.SetKp(P)
Y_pid.SetKd(I)
Y_pid.SetKi(D)

sensor = None
try:
	from mpu6050 import mpu6050
	sensor = mpu6050(0x68)
	logging.info("MPU6050 sensor initialized.")
except (ImportError, FileNotFoundError) as e:
	logging.warning(f"Could not import or initialize mpu6050. Steady mode will be unavailable. Error: {e}")
	pass

kalman_filter_X =  Kalman_filter.Kalman_filter(0.001,0.1)
kalman_filter_Y =  Kalman_filter.Kalman_filter(0.001,0.1)


'''
if the robot roll over when turning, decrease this value below.
'''
turn_steady = 4/5  # 2/3 4/5 5/6 ...


def mpu6050Test():
	if not sensor:
		logging.error("MPU6050 sensor not available.")
		return
	while 1:
		accelerometer_data = sensor.get_accel_data()
		logging.info('X=%f,Y=%f,Z=%f'%(accelerometer_data['x'],accelerometer_data['y'],accelerometer_data['x']))
		time.sleep(0.3)


def leg_move_diagonal(name, pos, wiggle):
	if name == 'I':
		if pos == 1:
			if Set_Direction:
				pwm.set_pwm(0, 0, pwm_init[0])
				pwm.set_pwm(1, 0, pwm_init[1]-wiggle)
				pwm.set_pwm(2, 0, pwm_init[2]-max_wiggle)
			else:
				pwm.set_pwm(0, 0, pwm_init[0])
				pwm.set_pwm(1, 0, pwm_init[1]+wiggle)
				pwm.set_pwm(2, 0, pwm_init[2]+max_wiggle)
		elif pos == 2:
			if Set_Direction:
				pwm.set_pwm(0, 0, pwm_init[0]+wiggle)
				pwm.set_pwm(1, 0, pwm_init[1]+wiggle)
				pwm.set_pwm(2, 0, pwm_init[2]-reach_wiggle)
			else:
				pwm.set_pwm(0, 0, pwm_init[0]-wiggle)
				pwm.set_pwm(1, 0, pwm_init[1]-wiggle)
				pwm.set_pwm(2, 0, pwm_init[2]+reach_wiggle)
		elif pos == 3:
			if Set_Direction:
				pwm.set_pwm(0, 0, pwm_init[0])
				pwm.set_pwm(1, 0, pwm_init[1]+int(wiggle/2))
				pwm.set_pwm(2, 0, pwm_init[2]-int(reach_wiggle/2))
			else:
				pwm.set_pwm(0, 0, pwm_init[0])
				pwm.set_pwm(1, 0, pwm_init[1]-int(wiggle/2))
				pwm.set_pwm(2, 0, pwm_init[2]+int(reach_wiggle/2))
		elif pos == 4:
			if Set_Direction:
				pwm.set_pwm(0, 0, pwm_init[0]-wiggle)
				pwm.set_pwm(1, 0, pwm_init[1]+int(wiggle/4))
				pwm.set_pwm(2, 0, pwm_init[2])
			else:
				pwm.set_pwm(0, 0, pwm_init[0]+wiggle)
				pwm.set_pwm(1, 0, pwm_init[1]-int(wiggle/4))
				pwm.set_pwm(2, 0, pwm_init[2])

	elif name == 'II':
		if pos == 1:
			if Set_Direction:
				pwm.set_pwm(3, 0, pwm_init[3])
				pwm.set_pwm(4, 0, pwm_init[4]+wiggle)
				pwm.set_pwm(5, 0, pwm_init[5]+max_wiggle)
			else:
				pwm.set_pwm(3, 0, pwm_init[3])
				pwm.set_pwm(4, 0, pwm_init[4]+wiggle)
				pwm.set_pwm(5, 0, pwm_init[5]-max_wiggle)
		elif pos == 2:
			if Set_Direction:
				pwm.set_pwm(3, 0, pwm_init[3]-wiggle)
				pwm.set_pwm(4, 0, pwm_init[4]-int(wiggle/4))
				pwm.set_pwm(5, 0, pwm_init[5])
			else:
				pwm.set_pwm(3, 0, pwm_init[3]+wiggle)
				pwm.set_pwm(4, 0, pwm_init[4]+int(wiggle/4))
				pwm.set_pwm(5, 0, pwm_init[5])
		elif pos == 3:
			if Set_Direction:
				pwm.set_pwm(3, 0, pwm_init[3])
				pwm.set_pwm(4, 0, pwm_init[4]-int(wiggle/2))
				pwm.set_pwm(5, 0, pwm_init[5]+int(reach_wiggle/2))
			else:
				pwm.set_pwm(3, 0, pwm_init[3])
				pwm.set_pwm(4, 0, pwm_init[4]+int(wiggle/2))
				pwm.set_pwm(5, 0, pwm_init[5]-int(reach_wiggle/2))
		elif pos == 4:
			if Set_Direction:
				pwm.set_pwm(3, 0, pwm_init[3]+wiggle)
				pwm.set_pwm(4, 0, pwm_init[4]-wiggle)
				pwm.set_pwm(5, 0, pwm_init[5]+reach_wiggle)
			else:
				pwm.set_pwm(3, 0, pwm_init[3]-wiggle)
				pwm.set_pwm(4, 0, pwm_init[4]+wiggle)
				pwm.set_pwm(5, 0, pwm_init[5]-reach_wiggle)

	elif name == 'III':
		if pos == 1:
			if Set_Direction:
				pwm.set_pwm(6, 0, pwm_init[6])
				pwm.set_pwm(7, 0, pwm_init[7]+wiggle)
				pwm.set_pwm(8, 0, pwm_init[8]+max_wiggle)
			else:
				pwm.set_pwm(6, 0, pwm_init[6])
				pwm.set_pwm(7, 0, pwm_init[7]-wiggle)
				pwm.set_pwm(8, 0, pwm_init[8]-reach_wiggle)
		elif pos == 2:
			if Set_Direction:
				pwm.set_pwm(6, 0, pwm_init[6]-wiggle)
				pwm.set_pwm(7, 0, pwm_init[7]-wiggle)
				pwm.set_pwm(8, 0, pwm_init[8]+reach_wiggle)
			else:
				pwm.set_pwm(6, 0, pwm_init[6]+wiggle)
				pwm.set_pwm(7, 0, pwm_init[7]+wiggle)
				pwm.set_pwm(8, 0, pwm_init[8]-reach_wiggle)
		elif pos == 3:
			if Set_Direction:
				pwm.set_pwm(6, 0, pwm_init[6])
				pwm.set_pwm(7, 0, pwm_init[7]-int(wiggle/2))
				pwm.set_pwm(8, 0, pwm_init[8]+int(reach_wiggle/2))
			else:
				pwm.set_pwm(6, 0, pwm_init[6])
				pwm.set_pwm(7, 0, pwm_init[7]+int(wiggle/2))
				pwm.set_pwm(8, 0, pwm_init[8]-int(reach_wiggle/2))
		elif pos == 4:
			if Set_Direction:
				pwm.set_pwm(6, 0, pwm_init[6]+wiggle)
				pwm.set_pwm(7, 0, pwm_init[7]-int(wiggle/4))
				pwm.set_pwm(8, 0, pwm_init[8])
			else:
				pwm.set_pwm(6, 0, pwm_init[6]-wiggle)
				pwm.set_pwm(7, 0, pwm_init[7]+int(wiggle/4))
				pwm.set_pwm(8, 0, pwm_init[8])

	elif name == 'IV':
		if pos == 1:
			if Set_Direction:
				pwm.set_pwm(9, 0, pwm_init[9])
				pwm.set_pwm(10, 0, pwm_init[10]-wiggle)
				pwm.set_pwm(11, 0, pwm_init[11]-max_wiggle)
			else:
				pwm.set_pwm(9, 0, pwm_init[9])
				pwm.set_pwm(10, 0, pwm_init[10]+wiggle)
				pwm.set_pwm(11, 0, pwm_init[11]+max_wiggle)
		elif pos == 2:
			if Set_Direction:
				pwm.set_pwm(9, 0, pwm_init[9]+wiggle)
				pwm.set_pwm(10, 0, pwm_init[10]+int(wiggle/4))
				pwm.set_pwm(11, 0, pwm_init[11])
			else:
				pwm.set_pwm(9, 0, pwm_init[9]-wiggle)
				pwm.set_pwm(10, 0, pwm_init[10]-int(wiggle/4))
				pwm.set_pwm(11, 0, pwm_init[11])
		elif pos == 3:
			if Set_Direction:
				pwm.set_pwm(9, 0, pwm_init[9])
				pwm.set_pwm(10, 0, pwm_init[10]+int(wiggle/2))
				pwm.set_pwm(11, 0, pwm_init[11]-int(reach_wiggle/2))
			else:
				pwm.set_pwm(9, 0, pwm_init[9])
				pwm.set_pwm(10, 0, pwm_init[10]-int(wiggle/2))
				pwm.set_pwm(11, 0, pwm_init[11]+int(reach_wiggle/2))
		elif pos == 4:
			if Set_Direction:
				pwm.set_pwm(9, 0, pwm_init[9]-wiggle)
				pwm.set_pwm(10, 0, pwm_init[10]+wiggle)
				pwm.set_pwm(11, 0, pwm_init[11]-reach_wiggle)
			else:
				pwm.set_pwm(9, 0, pwm_init[9]+wiggle)
				pwm.set_pwm(10, 0, pwm_init[10]-wiggle)
				pwm.set_pwm(11, 0, pwm_init[11]+reach_wiggle)

	else:
		logging.warning("The names of the legs is 'I II III IV'")
		pass


def move_diagonal(step):
	if step == 1:
		leg_move_diagonal('I', 1, 150)
		leg_move_diagonal('IV', 1, 150)

		leg_move_diagonal('II', 3, 150)
		leg_move_diagonal('III', 3, 150)
	elif step == 2:
		leg_move_diagonal('I', 2, 150)
		leg_move_diagonal('IV', 2, 150)

		leg_move_diagonal('II', 4, 150)
		leg_move_diagonal('III', 4, 150)
	elif step == 3:
		leg_move_diagonal('I', 3, 150)
		leg_move_diagonal('IV', 3, 150)

		leg_move_diagonal('II', 1, 150)
		leg_move_diagonal('III', 1, 150)
	elif step == 4:
		leg_move_diagonal('I', 4, 150)
		leg_move_diagonal('IV', 4, 150)

		leg_move_diagonal('II', 2, 150)
		leg_move_diagonal('III', 2, 150)


def leg_tripod(name, pos, spot, wiggle):
	increase = spot/pixel 
	if wiggle > 0:
		direction = 1
	else:
		direction = 0
		wiggle=-wiggle

	if name == 'I':
		if pos == 1:
			if direction:
				pwm.set_pwm(0, 0, int(pwm_init[0]-wiggle+increase*wiggle))
				pwm.set_pwm(1, 0, int(pwm_init[1]+wiggle/4-(increase*wiggle*5/4)))
				pwm.set_pwm(2, 0, int(pwm_init[2]-increase*max_wiggle))
			else:
				pwm.set_pwm(0, 0, int(pwm_init[0]+wiggle-increase*wiggle))
				pwm.set_pwm(1, 0, int(pwm_init[1]+wiggle-2*increase*wiggle))
				pwm.set_pwm(2, 0, int(pwm_init[2]-reach_wiggle-increase*(max_wiggle-reach_wiggle)))
		elif pos == 2:
			if direction:
				pwm.set_pwm(0, 0, int(pwm_init[0]+increase*wiggle))
				pwm.set_pwm(1, 0, int(pwm_init[1]-wiggle+increase*wiggle*2))
				pwm.set_pwm(2, 0, int(pwm_init[2]-max_wiggle+increase*(max_wiggle-reach_wiggle)))
			else:
				pwm.set_pwm(0, 0, int(pwm_init[0]-increase*wiggle))
				pwm.set_pwm(1, 0, int(pwm_init[1]-wiggle+5*increase*wiggle/4))
				pwm.set_pwm(2, 0, int(pwm_init[2]-max_wiggle+increase*max_wiggle))
		# ... (and so on for all positions, just replacing pwmX with pwm_init[X])
		elif pos == 3:
			if direction:
				pwm.set_pwm(0, 0, int(pwm_init[0]+wiggle-increase*wiggle/3))
				pwm.set_pwm(1, 0, int(pwm_init[1]+wiggle-increase*wiggle/6))
				pwm.set_pwm(2, 0, int(pwm_init[2]-reach_wiggle+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(0, 0, int(pwm_init[0]-wiggle+increase*wiggle/3))
				pwm.set_pwm(1, 0, int(pwm_init[1]+wiggle/4+increase*wiggle/12))
				pwm.set_pwm(2, 0, int(pwm_init[2]-increase*reach_wiggle/6))
		elif pos == 4:
			if direction:
				pwm.set_pwm(0, 0, int(pwm_init[0]+2*wiggle/3-increase*wiggle/3))
				pwm.set_pwm(1, 0, int(pwm_init[1]+5*wiggle/6-increase*wiggle/6))
				pwm.set_pwm(2, 0, int(pwm_init[2]-5*reach_wiggle/6+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(0, 0, int(pwm_init[0]-2*wiggle/3+increase*wiggle/3))
				pwm.set_pwm(1, 0, int(pwm_init[1]+wiggle/3+increase*wiggle/12))
				pwm.set_pwm(2, 0, int(pwm_init[2]-reach_wiggle/6-increase*reach_wiggle/6))
		elif pos == 5:
			if direction:
				pwm.set_pwm(0, 0, int(pwm_init[0]+wiggle/3-increase*wiggle/3))
				pwm.set_pwm(1, 0, int(pwm_init[1]+4*wiggle/6-increase*wiggle/6))
				pwm.set_pwm(2, 0, int(pwm_init[2]-2*reach_wiggle/3+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(0, 0, int(pwm_init[0]-wiggle/3+increase*wiggle/3))
				pwm.set_pwm(1, 0, int(pwm_init[1]+5*wiggle/12+increase*wiggle/12))
				pwm.set_pwm(2, 0, int(pwm_init[2]-reach_wiggle/3-increase*reach_wiggle/6))
		elif pos == 6:
			if direction:
				pwm.set_pwm(0, 0, int(pwm_init[0]-increase*wiggle/3))
				pwm.set_pwm(1, 0, int(pwm_init[1]+wiggle/2-wiggle/12))
				pwm.set_pwm(2, 0, int(pwm_init[2]-reach_wiggle/2+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(0, 0, int(pwm_init[0]+increase*wiggle/3))
				pwm.set_pwm(1, 0, int(pwm_init[1]+wiggle/2+increase*wiggle/6))
				pwm.set_pwm(2, 0, int(pwm_init[2]-reach_wiggle/2-increase*reach_wiggle/6))
		elif pos == 7:
			if direction:
				pwm.set_pwm(0, 0, int(pwm_init[0]-wiggle/3-increase*wiggle/3))
				pwm.set_pwm(1, 0, int(pwm_init[1]+5*wiggle/12-increase*wiggle/12))
				pwm.set_pwm(2, 0, int(pwm_init[2]-2*reach_wiggle/6+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(0, 0, int(pwm_init[0]+wiggle/3+increase*wiggle/3))
				pwm.set_pwm(1, 0, int(pwm_init[1]+2*wiggle/3+increase*wiggle/6))
				pwm.set_pwm(2, 0, int(pwm_init[2]-2*reach_wiggle/3-increase*reach_wiggle/6))
		elif pos == 8:
			if direction:
				pwm.set_pwm(0, 0, int(pwm_init[0]-2*wiggle/3-increase*wiggle/3))
				pwm.set_pwm(1, 0, int(pwm_init[1]+4*wiggle/12-wiggle/12))
				pwm.set_pwm(2, 0, int(pwm_init[2]-reach_wiggle/6+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(0, 0, int(pwm_init[0]+2*wiggle/3+increase*wiggle/3))
				pwm.set_pwm(1, 0, int(pwm_init[1]+5*wiggle/6+increase*wiggle/6))
				pwm.set_pwm(2, 0, int(pwm_init[2]-5*reach_wiggle/6-increase*reach_wiggle/6))

	elif name == 'II':
		if pos == 1:
			if direction:
				pwm.set_pwm(3, 0, int(pwm_init[3]+wiggle-increase*wiggle))
				pwm.set_pwm(4, 0, int(pwm_init[4]-wiggle+increase*wiggle*2))
				pwm.set_pwm(5, 0, int(pwm_init[5]+reach_wiggle+increase*(max_wiggle-reach_wiggle)))
			else:
				pwm.set_pwm(3, 0, int(pwm_init[3]-wiggle+increase*wiggle))
				pwm.set_pwm(4, 0, int(pwm_init[4]-wiggle/4+5*increase*wiggle/4))
				pwm.set_pwm(5, 0, int(pwm_init[5]+increase*max_wiggle))
		elif pos == 2:
			if direction:
				pwm.set_pwm(3, 0, int(pwm_init[3]-increase*wiggle))
				pwm.set_pwm(4, 0, int(pwm_init[4]+wiggle-5*increase*wiggle/4))
				pwm.set_pwm(5, 0, int(pwm_init[5]+max_wiggle-increase*max_wiggle))
			else:
				pwm.set_pwm(3, 0, int(pwm_init[3]+increase*wiggle))
				pwm.set_pwm(4, 0, int(pwm_init[4]+wiggle-2*increase*wiggle))
				pwm.set_pwm(5, 0, int(pwm_init[5]+max_wiggle-increase*(max_wiggle-reach_wiggle)))
		elif pos == 3:
			if direction:
				pwm.set_pwm(3, 0, int(pwm_init[3]-wiggle+increase*wiggle/3))
				pwm.set_pwm(4, 0, int(pwm_init[4]-wiggle/4-increase*wiggle/12))
				pwm.set_pwm(5, 0, int(pwm_init[5]+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(3, 0, int(pwm_init[3]+wiggle-increase*wiggle/3))
				pwm.set_pwm(4, 0, int(pwm_init[4]-wiggle+increase*wiggle/6))
				pwm.set_pwm(5, 0, int(pwm_init[5]+reach_wiggle-increase*reach_wiggle/6))
		elif pos == 4:
			if direction:
				pwm.set_pwm(3, 0, int(pwm_init[3]-2*wiggle/3+increase*wiggle/3))
				pwm.set_pwm(4, 0, int(pwm_init[4]-4*wiggle/12-increase*wiggle/12))
				pwm.set_pwm(5, 0, int(pwm_init[5]+reach_wiggle/6+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(3, 0, int(pwm_init[3]+2*wiggle/3-increase*wiggle/3))
				pwm.set_pwm(4, 0, int(pwm_init[4]-5*wiggle/6+increase*wiggle/6))
				pwm.set_pwm(5, 0, int(pwm_init[5]+5*reach_wiggle/6-increase*reach_wiggle/6))
		elif pos == 5:
			if direction:
				pwm.set_pwm(3, 0, int(pwm_init[3]-wiggle/3+increase*wiggle/3))
				pwm.set_pwm(4, 0, int(pwm_init[4]-5*wiggle/12-increase*wiggle/12))
				pwm.set_pwm(5, 0, int(pwm_init[5]+reach_wiggle/3+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(3, 0, int(pwm_init[3]+wiggle/3-increase*wiggle/3))
				pwm.set_pwm(4, 0, int(pwm_init[4]-2*wiggle/3+increase*wiggle/6))
				pwm.set_pwm(5, 0, int(pwm_init[5]+2*reach_wiggle/3-increase*reach_wiggle/6))
		elif pos == 6:
			if direction:
				pwm.set_pwm(3, 0, int(pwm_init[3]+increase*wiggle/3))
				pwm.set_pwm(4, 0, int(pwm_init[4]-wiggle/2-increase*wiggle/6))
				pwm.set_pwm(5, 0, int(pwm_init[5]+reach_wiggle/2+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(3, 0, int(pwm_init[3]-increase*wiggle/3))
				pwm.set_pwm(4, 0, int(pwm_init[4]-wiggle/2+increase*wiggle/12))
				pwm.set_pwm(5, 0, int(pwm_init[5]+reach_wiggle/2-increase*reach_wiggle/6))
		elif pos == 7:
			if direction:
				pwm.set_pwm(3, 0, int(pwm_init[3]+wiggle/3+increase*wiggle/3))
				pwm.set_pwm(4, 0, int(pwm_init[4]-4*wiggle/6-increase*wiggle/6))
				pwm.set_pwm(5, 0, int(pwm_init[5]+2*reach_wiggle/3+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(3, 0, int(pwm_init[3]-wiggle/3-increase*wiggle/3))
				pwm.set_pwm(4, 0, int(pwm_init[4]-5*wiggle/12+increase*wiggle/12))
				pwm.set_pwm(5, 0, int(pwm_init[5]+reach_wiggle/3-increase*reach_wiggle/6))
		elif pos == 8:
			if direction:
				pwm.set_pwm(3, 0, int(pwm_init[3]+2*wiggle/3+increase*wiggle/3))
				pwm.set_pwm(4, 0, int(pwm_init[4]-5*wiggle/6-increase*wiggle/6))
				pwm.set_pwm(5, 0, int(pwm_init[5]+5*reach_wiggle/6+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(3, 0, int(pwm_init[3]-2*wiggle/3-increase*wiggle/3))
				pwm.set_pwm(4, 0, int(pwm_init[4]-wiggle/3+increase*wiggle/12))
				pwm.set_pwm(5, 0, int(pwm_init[5]+reach_wiggle/6-increase*reach_wiggle/6))

	elif name == 'III':
		if pos == 1:
			if direction:
				pwm.set_pwm(6, 0, int(pwm_init[6]+wiggle-increase*wiggle))
				pwm.set_pwm(7, 0, int(pwm_init[7]-wiggle/4+5*increase*wiggle/4))
				pwm.set_pwm(8, 0, int(pwm_init[8]+increase*max_wiggle))
			else:
				pwm.set_pwm(6, 0, int(pwm_init[6]-wiggle+increase*wiggle))
				pwm.set_pwm(7, 0, int(pwm_init[7]-wiggle+2*increase*wiggle))
				pwm.set_pwm(8, 0, int(pwm_init[8]+reach_wiggle+increase*(max_wiggle-reach_wiggle)))
		elif pos == 2:
			if direction:
				pwm.set_pwm(6, 0, int(pwm_init[6]-increase*wiggle))
				pwm.set_pwm(7, 0, int(pwm_init[7]+wiggle-2*increase*wiggle))
				pwm.set_pwm(8, 0, int(pwm_init[8]+max_wiggle-increase*(max_wiggle-reach_wiggle)))
			else:
				pwm.set_pwm(6, 0, int(pwm_init[6]+increase*wiggle))
				pwm.set_pwm(7, 0, int(pwm_init[7]+wiggle-5*increase*wiggle/4))
				pwm.set_pwm(8, 0, int(pwm_init[8]+max_wiggle-increase*max_wiggle))
		elif pos == 3:
			if direction:
				pwm.set_pwm(6, 0, int(pwm_init[6]-wiggle+increase*wiggle/3))
				pwm.set_pwm(7, 0, int(pwm_init[7]-wiggle+increase*wiggle/6))
				pwm.set_pwm(8, 0, int(pwm_init[8]+reach_wiggle-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(6, 0, int(pwm_init[6]+wiggle-increase*wiggle/3))
				pwm.set_pwm(7, 0, int(pwm_init[7]-wiggle/4-increase*wiggle/12))
				pwm.set_pwm(8, 0, int(pwm_init[8]+increase*reach_wiggle/6))
		elif pos == 4:
			if direction:
				pwm.set_pwm(6, 0, int(pwm_init[6]-2*wiggle/3+increase*wiggle/3))
				pwm.set_pwm(7, 0, int(pwm_init[7]-5*wiggle/6+increase*wiggle/6))
				pwm.set_pwm(8, 0, int(pwm_init[8]+5*reach_wiggle/6-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(6, 0, int(pwm_init[6]+2*wiggle/3-increase*wiggle/3))
				pwm.set_pwm(7, 0, int(pwm_init[7]-wiggle/4-increase*wiggle/12))
				pwm.set_pwm(8, 0, int(pwm_init[8]+reach_wiggle/6+increase*reach_wiggle/6))
		elif pos == 5:
			if direction:
				pwm.set_pwm(6, 0, int(pwm_init[6]-wiggle/3+increase*wiggle/3))
				pwm.set_pwm(7, 0, int(pwm_init[7]-2*wiggle/3+increase*wiggle/6))
				pwm.set_pwm(8, 0, int(pwm_init[8]+2*reach_wiggle/3-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(6, 0, int(pwm_init[6]+wiggle/3-increase*wiggle/3))
				pwm.set_pwm(7, 0, int(pwm_init[7]-5*wiggle/12-increase*wiggle/12))
				pwm.set_pwm(8, 0, int(pwm_init[8]+reach_wiggle/3+increase*reach_wiggle/6))
		elif pos == 6:
			if direction:
				pwm.set_pwm(6, 0, int(pwm_init[6]+increase*wiggle/3))
				pwm.set_pwm(7, 0, int(pwm_init[7]-wiggle/2+increase*wiggle/12))
				pwm.set_pwm(8, 0, int(pwm_init[8]+reach_wiggle/2-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(6, 0, int(pwm_init[6]-increase*wiggle/3))
				pwm.set_pwm(7, 0, int(pwm_init[7]-wiggle/2-increase*wiggle/6))
				pwm.set_pwm(8, 0, int(pwm_init[8]+reach_wiggle/2+increase*reach_wiggle/6))
		elif pos == 7:
			if direction:
				pwm.set_pwm(6, 0, int(pwm_init[6]+wiggle/3+increase*wiggle/3))
				pwm.set_pwm(7, 0, int(pwm_init[7]-5*wiggle/12+increase*wiggle/12))
				pwm.set_pwm(8, 0, int(pwm_init[8]+reach_wiggle/3-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(6, 0, int(pwm_init[6]-wiggle/3-increase*wiggle/3))
				pwm.set_pwm(7, 0, int(pwm_init[7]-2*wiggle/3-increase*wiggle/6))
				pwm.set_pwm(8, 0, int(pwm_init[8]+2*reach_wiggle/3+increase*reach_wiggle/6))
		elif pos == 8:
			if direction:
				pwm.set_pwm(6, 0, int(pwm_init[6]+2*wiggle/3+increase*wiggle/3))
				pwm.set_pwm(7, 0, int(pwm_init[7]-4*wiggle/12+increase*wiggle/12))
				pwm.set_pwm(8, 0, int(pwm_init[8]+reach_wiggle/6-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(6, 0, int(pwm_init[6]-2*wiggle/3-increase*wiggle/3))
				pwm.set_pwm(7, 0, int(pwm_init[7]-5*wiggle/6-increase*wiggle/6))
				pwm.set_pwm(8, 0, int(pwm_init[8]+5*reach_wiggle/6+increase*reach_wiggle/6))

	elif name == 'IV':
		if pos == 1:
			if direction:
				pwm.set_pwm(9, 0, int(pwm_init[9]-wiggle+increase*wiggle))
				pwm.set_pwm(10, 0, int(pwm_init[10]+wiggle-2*increase*wiggle))
				pwm.set_pwm(11, 0, int(pwm_init[11]-reach_wiggle-increase*(max_wiggle-reach_wiggle)))
			else:
				pwm.set_pwm(9, 0, int(pwm_init[9]+wiggle-increase*wiggle))
				pwm.set_pwm(10, 0, int(pwm_init[10]+wiggle/4-5*increase*wiggle/4))
				pwm.set_pwm(11, 0, int(pwm_init[11]-increase*max_wiggle))
		elif pos == 2:
			if direction:
				pwm.set_pwm(9, 0, int(pwm_init[9]+increase*wiggle))
				pwm.set_pwm(10, 0, int(pwm_init[10]-wiggle+5*increase*wiggle/4))
				pwm.set_pwm(11, 0, int(pwm_init[11]-max_wiggle+increase*max_wiggle))
			else:
				pwm.set_pwm(9, 0, int(pwm_init[9]-increase*wiggle))
				pwm.set_pwm(10, 0, int(pwm_init[10]-wiggle+2*wiggle*increase))
				pwm.set_pwm(11, 0, int(pwm_init[11]-max_wiggle+increase*(max_wiggle-reach_wiggle)))
		elif pos == 3:
			if direction:
				pwm.set_pwm(9, 0, int(pwm_init[9]+wiggle-increase*wiggle/3))
				pwm.set_pwm(10, 0, int(pwm_init[10]+wiggle/4+increase*wiggle/12))
				pwm.set_pwm(11, 0, int(pwm_init[11]-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(9, 0, int(pwm_init[9]-wiggle+increase*wiggle/3))
				pwm.set_pwm(10, 0, int(pwm_init[10]+wiggle-increase*wiggle/6))
				pwm.set_pwm(11, 0, int(pwm_init[11]-reach_wiggle+increase*reach_wiggle/6))
		elif pos == 4:
			if direction:
				pwm.set_pwm(9, 0, int(pwm_init[9]+2*wiggle/3-increase*wiggle/3))
				pwm.set_pwm(10, 0, int(pwm_init[10]+wiggle/3+increase*wiggle/12))
				pwm.set_pwm(11, 0, int(pwm_init[11]-reach_wiggle/6-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(9, 0, int(pwm_init[9]-2*wiggle/3+increase*wiggle/3))
				pwm.set_pwm(10, 0, int(pwm_init[10]+5*wiggle/6-increase*wiggle/6))
				pwm.set_pwm(11, 0, int(pwm_init[11]-5*reach_wiggle/6+increase*reach_wiggle/6))
		elif pos == 5:
			if direction:
				pwm.set_pwm(9, 0, int(pwm_init[9]+wiggle/3-increase*wiggle/3))
				pwm.set_pwm(10, 0, int(pwm_init[10]+5*wiggle/12+increase*wiggle/12))
				pwm.set_pwm(11, 0, int(pwm_init[11]-reach_wiggle/3-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(9, 0, int(pwm_init[9]-wiggle/3+increase*wiggle/3))
				pwm.set_pwm(10, 0, int(pwm_init[10]+2*wiggle/3-increase*wiggle/6))
				pwm.set_pwm(11, 0, int(pwm_init[11]-2*reach_wiggle/3+increase*reach_wiggle/6))
		elif pos == 6:
			if direction:
				pwm.set_pwm(9, 0, int(pwm_init[9]-increase*wiggle/3))
				pwm.set_pwm(10, 0, int(pwm_init[10]+wiggle/2+increase*wiggle/6))
				pwm.set_pwm(11, 0, int(pwm_init[11]-reach_wiggle/2-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(9, 0, int(pwm_init[9]+increase*wiggle/3))
				pwm.set_pwm(10, 0, int(pwm_init[10]+wiggle/2-increase*wiggle/12))
				pwm.set_pwm(11, 0, int(pwm_init[11]-reach_wiggle/2+increase*reach_wiggle/6))
		elif pos == 7:
			if direction:
				pwm.set_pwm(9, 0, int(pwm_init[9]-wiggle/3-increase*wiggle/3))
				pwm.set_pwm(10, 0, int(pwm_init[10]+4*wiggle/6+increase*wiggle/6))
				pwm.set_pwm(11, 0, int(pwm_init[11]-2*reach_wiggle/3-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(9, 0, int(pwm_init[9]+wiggle/3+increase*wiggle/3))
				pwm.set_pwm(10, 0, int(pwm_init[10]+5*wiggle/12-increase*wiggle/12))
				pwm.set_pwm(11, 0, int(pwm_init[11]-reach_wiggle/3+increase*reach_wiggle/6))
		elif pos == 8:
			if direction:
				pwm.set_pwm(9, 0, int(pwm_init[9]-2*wiggle/3-increase*wiggle/3))
				pwm.set_pwm(10, 0, int(pwm_init[10]+5*wiggle/6+increase*wiggle/6))
				pwm.set_pwm(11, 0, int(pwm_init[11]-5*reach_wiggle/6-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(9, 0, int(pwm_init[9]+2*wiggle/3+increase*wiggle/3))
				pwm.set_pwm(10, 0, int(pwm_init[10]+wiggle/3-increase*wiggle/12))
				pwm.set_pwm(11, 0, int(pwm_init[11]-reach_wiggle/6+increase*reach_wiggle/6))


def dove_move_tripod(step, speed, command):
	step_I  = step
	step_II = step+2
	step_III= step+4
	step_IV = step+6
	if step_II > 8: step_II -= 8
	if step_III> 8: step_III-= 8
	if step_IV > 8: step_IV -= 8

	if command == 'forward':
		for i in range(1,(pixel+1)):
			leg_tripod('I', step_I, i, speed)
			leg_tripod('II', step_II, i, speed)
			leg_tripod('III', step_III, i, speed)
			leg_tripod('IV', step_IV, i, speed)
	elif command == 'backward':
		for i in range(1,(pixel+1)):
			leg_tripod('I', step_I, i, -speed)
			leg_tripod('II', step_II, i, -speed)
			leg_tripod('III', step_III, i, -speed)
			leg_tripod('IV', step_IV, i, -speed)
	elif command == 'left':
		for i in range(1,(pixel+1)):
			leg_tripod('I', step_I, i, -int(speed*turn_steady))
			leg_tripod('II', step_II, i, -int(speed*turn_steady))
			leg_tripod('III', step_III, i, speed)
			leg_tripod('IV', step_IV, i, speed)
	elif command == 'right':
		for i in range(1,(pixel+1)):
			leg_tripod('I', step_I, i, speed)
			leg_tripod('II', step_II, i, speed)
			leg_tripod('III', step_III, i, -int(speed*turn_steady))
			leg_tripod('IV', step_IV, i, -int(speed*turn_steady))


def dove_move_diagonal(step, speed, command):
	step_I  = step
	step_II = step+4
	step_III= step+4
	step_IV = step
	if step_II > 8: step_II -= 8
	if step_III> 8: step_III-= 8
	if step_IV > 8: step_IV -= 8

	if command == 'forward':
		for i in range(1,(pixel+1)):
			leg_tripod('I', step_I, i, speed)
			leg_tripod('II', step_II, i, speed)
			leg_tripod('III', step_III, i, speed)
			leg_tripod('IV', step_IV, i, speed)
	elif command == 'backward':
		for i in range(1,(pixel+1)):
			leg_tripod('I', step_I, i, -speed)
			leg_tripod('II', step_II, i, -speed)
			leg_tripod('III', step_III, i, -speed)
			leg_tripod('IV', step_IV, i, -speed)
	elif command == 'left':
		for i in range(1,(pixel+1)):
			leg_tripod('I', step_I, i, -speed)
			leg_tripod('II', step_II, i, -speed)
			leg_tripod('III', step_III, i, speed)
			leg_tripod('IV', step_IV, i, speed)
	elif command == 'right':
		for i in range(1,(pixel+1)):
			leg_tripod('I', step_I, i, speed)
			leg_tripod('II', step_II, i, speed)
			leg_tripod('III', step_III, i, -speed)
			leg_tripod('IV', step_IV, i, -speed)


def robot_X(wiggle, amp):
	'''
	when amp is 0, robot <body>
	when amp is 100, robot >body<
	'''
	pwm.set_pwm(0, 0, int(pwm_init[0]-wiggle+2*wiggle*amp/100))
	pwm.set_pwm(3, 0, int(pwm_init[3]-wiggle+2*wiggle*amp/100))
	pwm.set_pwm(6, 0, int(pwm_init[6]+wiggle-2*wiggle*amp/100))
	pwm.set_pwm(9, 0, int(pwm_init[9]+wiggle-2*wiggle*amp/100))


def robot_hight(wiggle, amp):
	'''
	when amp is 0, robot <heighest>.
	when amp is 100, robot <lowest>.
	'''
	pwm.set_pwm(1, 0, int(pwm_init[1]+wiggle-2*wiggle*amp/100))
	pwm.set_pwm(4, 0, int(pwm_init[4]-wiggle+2*wiggle*amp/100))
	pwm.set_pwm(7, 0, int(pwm_init[7]-wiggle+2*wiggle*amp/100))
	pwm.set_pwm(10, 0, int(pwm_init[10]+wiggle-2*wiggle*amp/100))


def look_home():
	robot_stand(150)


def robot_stand(wiggle_input):
	robot_X(wiggle_input, 50)
	robot_hight(wiggle_input, 0)
	pwm.set_pwm(2, 0, pwm_init[2])
	pwm.set_pwm(5, 0, pwm_init[5])
	pwm.set_pwm(8, 0, pwm_init[8])
	pwm.set_pwm(11, 0, pwm_init[11])


def ctrl_range(raw, max_genout, min_genout):
	return int(max(min(raw, max_genout), min_genout))


def ctrl_pitch_roll(wiggle, pitch, roll):
	'''
	look up <- pitch -> look down.
	lean right <- roll -> lean left.
	default values are 0.
	range(-100, 100)
	'''
	pitch_delta = wiggle * pitch / 100
	roll_delta = wiggle * roll / 100

	pwm.set_pwm(1, 0, ctrl_range((pwm_init[1] - pitch_delta - roll_delta), pwm_max[1], pwm_min[1]))
	pwm.set_pwm(4, 0, ctrl_range((pwm_init[4] - pitch_delta + roll_delta), pwm_max[4], pwm_min[4]))
	pwm.set_pwm(7, 0, ctrl_range((pwm_init[7] + pitch_delta - roll_delta), pwm_max[7], pwm_min[7]))
	pwm.set_pwm(10, 0, ctrl_range((pwm_init[10] + pitch_delta + roll_delta), pwm_max[10], pwm_min[10]))


def ctrl_yaw(wiggle, yaw):
	'''
	look left <- yaw -> look right
	default value is 0
	'''
	# This function seems to be a placeholder, the pwm values are set to their initial state.
	# I will leave it as is, but it doesn't appear to do anything.
	pwm.set_pwm(2, 0, pwm_init[2])
	pwm.set_pwm(5, 0, pwm_init[5])
	pwm.set_pwm(8, 0, pwm_init[8])
	pwm.set_pwm(11, 0, pwm_init[11])


def steady():
	global X_fix_output, Y_fix_output
	if not sensor:
		# logging.warning("Steady mode attempted but MPU6050 sensor is not available.")
		return

	accelerometer_data = sensor.get_accel_data()
	X = accelerometer_data['x']
	X = kalman_filter_X.kalman(X)
	Y = accelerometer_data['y']
	Y = kalman_filter_Y.kalman(Y)

	X_fix_output -= X_pid.GenOut(X - X_steady)
	Y_fix_output += Y_pid.GenOut(Y - Y_steady)
	X_fix_output = ctrl_range(X_fix_output, 100, -100)
	Y_fix_output = ctrl_range(Y_fix_output, 100, -100)

	ctrl_pitch_roll(150, -X_fix_output, Y_fix_output)


def release():
	pwm.set_all_pwm(0,0)


def clean_all():
	pwm.set_all_pwm(0, 0)


def init_servos():
	pwm.set_all_pwm(0, 300)


if __name__ == '__main__':	
	try:
		# Example usage / test code
		logging.info("Starting move.py test sequence.")
		init_servos()
		time.sleep(1)
		
		# Test steady mode if sensor is available
		if sensor:
			logging.info("Testing steady mode...")
			for _ in range(100):
				steady()
				time.sleep(0.02)
		
		# Test walking
		logging.info("Testing forward walk...")
		for step in range(1, 9):
			dove_move_tripod(step, 150, 'forward')

		logging.info("Test sequence finished.")

	except KeyboardInterrupt:
		logging.info("Test interrupted by user.")
	finally:
		clean_all()
