#! /usr/bin/python
# File name   : move.py
# Description : Controlling all servos
# Website	 : www.adeept.com
# E-mail	  : support@adeept.com
# Author	  : William
# Date		: 2019/04/08
import time
import Adafruit_PCA9685

import Kalman_filter
import PID


pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(50)

for i in range(0,16):
	exec('pwm%d=300'%i)
	exec('pwm%d_max=450'%i)
	exec('pwm%d_min=150'%i)

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

try:
	from mpu6050 import mpu6050
	sensor = mpu6050(0x68)
except:
	pass

kalman_filter_X =  Kalman_filter.Kalman_filter(0.001,0.1)
kalman_filter_Y =  Kalman_filter.Kalman_filter(0.001,0.1)


'''
if the robot roll over when turning, decrease this value below.
'''
turn_steady = 4/5  # 2/3 4/5 5/6 ...


def mpu6050Test():
	while 1:
		accelerometer_data = sensor.get_accel_data()
		print('X=%f,Y=%f,Z=%f'%(accelerometer_data['x'],accelerometer_data['y'],accelerometer_data['x']))
		time.sleep(0.3)


def leg_move_diagonal(name, pos, wiggle):
	if name == 'I':
		if pos == 1:
			'''
			   <1>
			 2--3--4
			'''
			if Set_Direction:
				pwm.set_pwm(0, 0, pwm0) #<back&forth>
				pwm.set_pwm(1, 0, pwm1-wiggle) #<up>&down
				pwm.set_pwm(2, 0, pwm2-max_wiggle) #<out>&in
			else:
				pwm.set_pwm(0, 0, pwm0) #<back&forth>
				pwm.set_pwm(1, 0, pwm1+wiggle) #<up>&down
				pwm.set_pwm(2, 0, pwm2+max_wiggle) #<out>&in		
		elif pos == 2:
			'''
			    1
			<2>-3--4
			'''
			if Set_Direction:
				pwm.set_pwm(0, 0, pwm0+wiggle) #back&<forth>
				pwm.set_pwm(1, 0, pwm1+wiggle) #up&<down>
				pwm.set_pwm(2, 0, pwm2-reach_wiggle) #<out>&in
			else:
				pwm.set_pwm(0, 0, pwm0-wiggle) #back&<forth>
				pwm.set_pwm(1, 0, pwm1-wiggle) #up&<down>
				pwm.set_pwm(2, 0, pwm2+reach_wiggle) #<out>&in
		elif pos == 3:
			'''
			    1
			 2-<3>-4
			'''
			if Set_Direction:
				pwm.set_pwm(0, 0, pwm0) #<back&forth>
				pwm.set_pwm(1, 0, pwm1+int(wiggle/2)) #<up&down>
				pwm.set_pwm(2, 0, pwm2-int(reach_wiggle/2)) #<out&in>
			else:
				pwm.set_pwm(0, 0, pwm0) #<back&forth>
				pwm.set_pwm(1, 0, pwm1-int(wiggle/2)) #<up&down>
				pwm.set_pwm(2, 0, pwm2+int(reach_wiggle/2)) #<out&in>
		elif pos == 4:
			'''
			    1
			 2--3-<4>
			'''
			if Set_Direction:
				pwm.set_pwm(0, 0, pwm0-wiggle) #<back>&forth
				pwm.set_pwm(1, 0, pwm1+int(wiggle/4)) #up&<down>
				pwm.set_pwm(2, 0, pwm2) #out&<in>
			else:
				pwm.set_pwm(0, 0, pwm0+wiggle) #<back&forth>
				pwm.set_pwm(1, 0, pwm1-int(wiggle/4)) #up&<down>
				pwm.set_pwm(2, 0, pwm2) #out&<in>

	elif name == 'II':
		if pos == 1:
			'''
			   <1>
			 2--3--4
			'''
			if Set_Direction:
				pwm.set_pwm(3, 0, pwm3) #<back&forth>
				pwm.set_pwm(4, 0, pwm4+wiggle) #<up>&down
				pwm.set_pwm(5, 0, pwm5+max_wiggle) #<out>&in
			else:
				pwm.set_pwm(3, 0, pwm3) #<back&forth>
				pwm.set_pwm(4, 0, pwm4+wiggle) #<up>&down
				pwm.set_pwm(5, 0, pwm5-max_wiggle) #<out>&in		
		elif pos == 2:
			'''
			    1
			<2>-3--4
			'''
			if Set_Direction:
				pwm.set_pwm(3, 0, pwm3-wiggle) #back&<forth>
				pwm.set_pwm(4, 0, pwm4-int(wiggle/4)) #<up&down>
				pwm.set_pwm(5, 0, pwm5) #out&<in>
			else:
				pwm.set_pwm(3, 0, pwm3+wiggle) #back&<forth>
				pwm.set_pwm(4, 0, pwm4+int(wiggle/4)) #up&<down>
				pwm.set_pwm(5, 0, pwm5) #<out>&in
		elif pos == 3:
			'''
			    1
			 2-<3>-4
			'''
			if Set_Direction:
				pwm.set_pwm(3, 0, pwm3) #<back&forth>
				pwm.set_pwm(4, 0, pwm4-int(wiggle/2)) #<up&down>
				pwm.set_pwm(5, 0, pwm5+int(reach_wiggle/2)) #<out&in>
			else:
				pwm.set_pwm(3, 0, pwm3) #<back&forth>
				pwm.set_pwm(4, 0, pwm4+int(wiggle/2)) #<up&down>
				pwm.set_pwm(5, 0, pwm5-int(reach_wiggle/2)) #<out&in>
		elif pos == 4:
			'''
			    1
			 2--3-<4>
			'''
			if Set_Direction:
				pwm.set_pwm(3, 0, pwm3+wiggle) #<back>&forth
				pwm.set_pwm(4, 0, pwm4-wiggle) #up&<down>
				pwm.set_pwm(5, 0, pwm5+reach_wiggle) #out&<in>
			else:
				pwm.set_pwm(3, 0, pwm3-wiggle) #<back&forth>
				pwm.set_pwm(4, 0, pwm4+wiggle) #up&<down>
				pwm.set_pwm(5, 0, pwm5-reach_wiggle) #out&<in>

	elif name == 'III':
		if pos == 1:
			'''
			   <1>
			 2--3--4
			'''
			if Set_Direction:
				pwm.set_pwm(6, 0, pwm6) #<back&forth>
				pwm.set_pwm(7, 0, pwm7+wiggle) #<up>&down
				pwm.set_pwm(8, 0, pwm8+max_wiggle) #<out>&in
			else:
				pwm.set_pwm(6, 0, pwm6) #<back&forth>
				pwm.set_pwm(7, 0, pwm7-wiggle) #<up>&down
				pwm.set_pwm(8, 0, pwm8-reach_wiggle) #<out>&in		
		elif pos == 2:
			'''
			    1
			<2>-3--4
			'''
			if Set_Direction:
				pwm.set_pwm(6, 0, pwm6-wiggle) #back&<forth>
				pwm.set_pwm(7, 0, pwm7-wiggle) #up&<down>
				pwm.set_pwm(8, 0, pwm8+reach_wiggle) #<out>&in
			else:
				pwm.set_pwm(6, 0, pwm6+wiggle) #back&<forth>
				pwm.set_pwm(7, 0, pwm7+wiggle) #up&<down>
				pwm.set_pwm(8, 0, pwm8-reach_wiggle) #<out>&in
		elif pos == 3:
			'''
			    1
			 2-<3>-4
			'''
			if Set_Direction:
				pwm.set_pwm(6, 0, pwm6) #<back&forth>
				pwm.set_pwm(7, 0, pwm7-int(wiggle/2)) #<up&down>
				pwm.set_pwm(8, 0, pwm8+int(reach_wiggle/2)) #<out&in>
			else:
				pwm.set_pwm(6, 0, pwm6) #<back&forth>
				pwm.set_pwm(7, 0, pwm7+int(wiggle/2)) #<up&down>
				pwm.set_pwm(8, 0, pwm8-int(reach_wiggle/2)) #<out&in>
		elif pos == 4:
			'''
			    1
			 2--3-<4>
			'''
			if Set_Direction:
				pwm.set_pwm(6, 0, pwm6+wiggle) #<back>&forth
				pwm.set_pwm(7, 0, pwm7-int(wiggle/4)) #up&<down>
				pwm.set_pwm(8, 0, pwm8) #out&<in>
			else:
				pwm.set_pwm(6, 0, pwm6-wiggle) #<back&forth>
				pwm.set_pwm(7, 0, pwm7+int(wiggle/4)) #up&<down>
				pwm.set_pwm(8, 0, pwm8) #out&<in>

	elif name == 'IV':
		if pos == 1:
			'''
			   <1>
			 2--3--4
			'''
			if Set_Direction:
				pwm.set_pwm(9, 0, pwm9) #<back&forth>
				pwm.set_pwm(10, 0, pwm10-wiggle) #<up>&down
				pwm.set_pwm(11, 0, pwm11-max_wiggle) #<out>&in
			else:
				pwm.set_pwm(9, 0, pwm9) #<back&forth>
				pwm.set_pwm(10, 0, pwm10+wiggle) #<up>&down
				pwm.set_pwm(11, 0, pwm11+max_wiggle) #<out>&in		
		elif pos == 2:
			'''
			    1
			<2>-3--4
			'''
			if Set_Direction:
				pwm.set_pwm(9, 0, pwm9+wiggle) #back&<forth>
				pwm.set_pwm(10, 0, pwm10+int(wiggle/4)) #up&<down>
				pwm.set_pwm(11, 0, pwm11) #<out>&in
			else:
				pwm.set_pwm(9, 0, pwm9-wiggle) #back&<forth>
				pwm.set_pwm(10, 0, pwm10-int(wiggle/4)) #up&<down>
				pwm.set_pwm(11, 0, pwm11) #<out>&in
		elif pos == 3:
			'''
			    1
			 2-<3>-4
			'''
			if Set_Direction:
				pwm.set_pwm(9, 0, pwm9) #<back&forth>
				pwm.set_pwm(10, 0, pwm10+int(wiggle/2)) #<up&down>
				pwm.set_pwm(11, 0, pwm11-int(reach_wiggle/2)) #<out&in>
			else:
				pwm.set_pwm(9, 0, pwm9) #<back&forth>
				pwm.set_pwm(10, 0, pwm10-int(wiggle/2)) #<up&down>
				pwm.set_pwm(11, 0, pwm11+int(reach_wiggle/2)) #<out&in>
		elif pos == 4:
			'''
			    1
			 2--3-<4>
			'''
			if Set_Direction:
				pwm.set_pwm(9, 0, pwm9-wiggle) #<back>&forth
				pwm.set_pwm(10, 0, pwm10+wiggle) #up&<down>
				pwm.set_pwm(11, 0, pwm11-reach_wiggle) #<out>&in
			else:
				pwm.set_pwm(9, 0, pwm9+wiggle) #<back&forth>
				pwm.set_pwm(10, 0, pwm10-wiggle) #up&<down>
				pwm.set_pwm(11, 0, pwm11+reach_wiggle) #<out>&in

	else:
		print("the names of the legs is 'I II III IV")
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
			'''
			         <1>
			-2--3--4--5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(0, 0, int(pwm0-wiggle+increase*wiggle))

				pwm.set_pwm(1, 0, int(pwm1+wiggle/4-(increase*wiggle*5/4)))

				pwm.set_pwm(2, 0, int(pwm2-increase*max_wiggle))
			else:
				pwm.set_pwm(0, 0, int(pwm0+wiggle-increase*wiggle))

				pwm.set_pwm(1, 0, int(pwm1+wiggle-2*increase*wiggle))

				pwm.set_pwm(2, 0, int(pwm2-reach_wiggle-increase*(max_wiggle-reach_wiggle)))
				pass

		elif pos == 2:
			'''
			          1
			<2>-3--4--5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(0, 0, int(pwm0+increase*wiggle))

				pwm.set_pwm(1, 0, int(pwm1-wiggle+increase*wiggle*2))

				pwm.set_pwm(2, 0, int(pwm2-max_wiggle+increase*(max_wiggle-reach_wiggle)))
			else:
				pwm.set_pwm(0, 0, int(pwm0-increase*wiggle))

				pwm.set_pwm(1, 0, int(pwm1-wiggle+5*increase*wiggle/4))

				pwm.set_pwm(2, 0, int(pwm2-max_wiggle+increase*max_wiggle))
				pass

		elif pos == 3:
			'''
			          1
			-2-<3>-4--5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(0, 0, int(pwm0+wiggle-increase*wiggle/3))

				pwm.set_pwm(1, 0, int(pwm1+wiggle-increase*wiggle/6))

				pwm.set_pwm(2, 0, int(pwm2-reach_wiggle+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(0, 0, int(pwm0-wiggle+increase*wiggle/3))

				pwm.set_pwm(1, 0, int(pwm1+wiggle/4+increase*wiggle/12))

				pwm.set_pwm(2, 0, int(pwm2-increase*reach_wiggle/6))
				pass

		elif pos == 4:
			'''
			          1
			-2--3-<4>-5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(0, 0, int(pwm0+2*wiggle/3-increase*wiggle/3))

				pwm.set_pwm(1, 0, int(pwm1+5*wiggle/6-increase*wiggle/6))

				pwm.set_pwm(2, 0, int(pwm2-5*reach_wiggle/6+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(0, 0, int(pwm0-2*wiggle/3+increase*wiggle/3))

				pwm.set_pwm(1, 0, int(pwm1+wiggle/3+increase*wiggle/12))

				pwm.set_pwm(2, 0, int(pwm2-reach_wiggle/6-increase*reach_wiggle/6))
				pass

		elif pos == 5:
			'''
			          1
			-2--3--4-<5>-6--7--8-
			'''
			if direction:
				pwm.set_pwm(0, 0, int(pwm0+wiggle/3-increase*wiggle/3))

				pwm.set_pwm(1, 0, int(pwm1+4*wiggle/6-increase*wiggle/6))

				pwm.set_pwm(2, 0, int(pwm2-2*reach_wiggle/3+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(0, 0, int(pwm0-wiggle/3+increase*wiggle/3))

				pwm.set_pwm(1, 0, int(pwm1+5*wiggle/12+increase*wiggle/12))

				pwm.set_pwm(2, 0, int(pwm2-reach_wiggle/3-increase*reach_wiggle/6))
				pass

		elif pos == 6:
			'''
			          1
			-2--3--4--5-<6>-7--8-
			'''
			if direction:
				pwm.set_pwm(0, 0, int(pwm0-increase*wiggle/3))

				pwm.set_pwm(1, 0, int(pwm1+wiggle/2-wiggle/12))

				pwm.set_pwm(2, 0, int(pwm2-reach_wiggle/2+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(0, 0, int(pwm0+increase*wiggle/3))

				pwm.set_pwm(1, 0, int(pwm1+wiggle/2+increase*wiggle/6))

				pwm.set_pwm(2, 0, int(pwm2-reach_wiggle/2-increase*reach_wiggle/6))
				pass

		elif pos == 7:
			'''
			          1
			-2--3--4--5--6-<7>-8-
			'''
			if direction:
				pwm.set_pwm(0, 0, int(pwm0-wiggle/3-increase*wiggle/3))

				pwm.set_pwm(1, 0, int(pwm1+5*wiggle/12-increase*wiggle/12))

				pwm.set_pwm(2, 0, int(pwm2-2*reach_wiggle/6+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(0, 0, int(pwm0+wiggle/3+increase*wiggle/3))

				pwm.set_pwm(1, 0, int(pwm1+2*wiggle/3+increase*wiggle/6))

				pwm.set_pwm(2, 0, int(pwm2-2*reach_wiggle/3-increase*reach_wiggle/6))
				pass

		elif pos == 8:
			'''
			          1
			-2--3--4--5--6--7-<8>
			'''
			if direction:
				pwm.set_pwm(0, 0, int(pwm0-2*wiggle/3-increase*wiggle/3))

				pwm.set_pwm(1, 0, int(pwm1+4*wiggle/12-wiggle/12))

				pwm.set_pwm(2, 0, int(pwm2-reach_wiggle/6+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(0, 0, int(pwm0+2*wiggle/3+increase*wiggle/3))

				pwm.set_pwm(1, 0, int(pwm1+5*wiggle/6+increase*wiggle/6))

				pwm.set_pwm(2, 0, int(pwm2-5*reach_wiggle/6-increase*reach_wiggle/6))
				pass

		else:
			pass

	elif name == 'II':
		if pos == 1:
			'''
			         <1>
			-2--3--4--5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(3, 0, int(pwm3+wiggle-increase*wiggle))

				pwm.set_pwm(4, 0, int(pwm4-wiggle+increase*wiggle*2))

				pwm.set_pwm(5, 0, int(pwm5+reach_wiggle+increase*(max_wiggle-reach_wiggle)))
			else:
				pwm.set_pwm(3, 0, int(pwm3-wiggle+increase*wiggle))

				pwm.set_pwm(4, 0, int(pwm4-wiggle/4+5*increase*wiggle/4))

				pwm.set_pwm(5, 0, int(pwm5+increase*max_wiggle))
				pass

		elif pos == 2:
			'''
			          1
			<2>-3--4--5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(3, 0, int(pwm3-increase*wiggle))

				pwm.set_pwm(4, 0, int(pwm4+wiggle-5*increase*wiggle/4))

				pwm.set_pwm(5, 0, int(pwm5+max_wiggle-increase*max_wiggle))
			else:
				pwm.set_pwm(3, 0, int(pwm3+increase*wiggle))

				pwm.set_pwm(4, 0, int(pwm4+wiggle-2*increase*wiggle))

				pwm.set_pwm(5, 0, int(pwm5+max_wiggle-increase*(max_wiggle-reach_wiggle)))
				pass

		elif pos == 3:
			'''
			          1
			-2-<3>-4--5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(3, 0, int(pwm3-wiggle+increase*wiggle/3))

				pwm.set_pwm(4, 0, int(pwm4-wiggle/4-increase*wiggle/12))

				pwm.set_pwm(5, 0, int(pwm5+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(3, 0, int(pwm3+wiggle-increase*wiggle/3))

				pwm.set_pwm(4, 0, int(pwm4-wiggle+increase*wiggle/6))

				pwm.set_pwm(5, 0, int(pwm5+reach_wiggle-increase*reach_wiggle/6))
				pass

		elif pos == 4:
			'''
			          1
			-2--3-<4>-5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(3, 0, int(pwm3-2*wiggle/3+increase*wiggle/3))

				pwm.set_pwm(4, 0, int(pwm4-4*wiggle/12-increase*wiggle/12))

				pwm.set_pwm(5, 0, int(pwm5+reach_wiggle/6+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(3, 0, int(pwm3+2*wiggle/3-increase*wiggle/3))

				pwm.set_pwm(4, 0, int(pwm4-5*wiggle/6+increase*wiggle/6))

				pwm.set_pwm(5, 0, int(pwm5+5*reach_wiggle/6-increase*reach_wiggle/6))
				pass

		elif pos == 5:
			'''
			          1
			-2--3--4-<5>-6--7--8-
			'''
			if direction:
				pwm.set_pwm(3, 0, int(pwm3-wiggle/3+increase*wiggle/3))

				pwm.set_pwm(4, 0, int(pwm4-5*wiggle/12-increase*wiggle/12))

				pwm.set_pwm(5, 0, int(pwm5+reach_wiggle/3+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(3, 0, int(pwm3+wiggle/3-increase*wiggle/3))

				pwm.set_pwm(4, 0, int(pwm4-2*wiggle/3+increase*wiggle/6))

				pwm.set_pwm(5, 0, int(pwm5+2*reach_wiggle/3-increase*reach_wiggle/6))
				pass

		elif pos == 6:
			'''
			          1
			-2--3--4--5-<6>-7--8-
			'''
			if direction:
				pwm.set_pwm(3, 0, int(pwm3+increase*wiggle/3))

				pwm.set_pwm(4, 0, int(pwm4-wiggle/2-increase*wiggle/6))

				pwm.set_pwm(5, 0, int(pwm5+reach_wiggle/2+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(3, 0, int(pwm3-increase*wiggle/3))

				pwm.set_pwm(4, 0, int(pwm4-wiggle/2+increase*wiggle/12))

				pwm.set_pwm(5, 0, int(pwm5+reach_wiggle/2-increase*reach_wiggle/6))
				pass

		elif pos == 7:
			'''
			          1
			-2--3--4--5--6-<7>-8-
			'''
			if direction:
				pwm.set_pwm(3, 0, int(pwm3+wiggle/3+increase*wiggle/3))

				pwm.set_pwm(4, 0, int(pwm4-4*wiggle/6-increase*wiggle/6))

				pwm.set_pwm(5, 0, int(pwm5+2*reach_wiggle/3+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(3, 0, int(pwm3-wiggle/3-increase*wiggle/3))

				pwm.set_pwm(4, 0, int(pwm4-5*wiggle/12+increase*wiggle/12))

				pwm.set_pwm(5, 0, int(pwm5+reach_wiggle/3-increase*reach_wiggle/6))
				pass

		elif pos == 8:
			'''
			          1
			-2--3--4--5--6--7-<8>
			'''
			if direction:
				pwm.set_pwm(3, 0, int(pwm3+2*wiggle/3+increase*wiggle/3))

				pwm.set_pwm(4, 0, int(pwm4-5*wiggle/6-increase*wiggle/6))

				pwm.set_pwm(5, 0, int(pwm5+5*reach_wiggle/6+increase*reach_wiggle/6))
			else:
				pwm.set_pwm(3, 0, int(pwm3-2*wiggle/3-increase*wiggle/3))

				pwm.set_pwm(4, 0, int(pwm4-wiggle/3+increase*wiggle/12))

				pwm.set_pwm(5, 0, int(pwm5+reach_wiggle/6-increase*reach_wiggle/6))
				pass

	elif name == 'III':
		if pos == 1:
			'''
			         <1>
			-2--3--4--5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(6, 0, int(pwm6+wiggle-increase*wiggle))

				pwm.set_pwm(7, 0, int(pwm7-wiggle/4+5*increase*wiggle/4))

				pwm.set_pwm(8, 0, int(pwm8+increase*max_wiggle))
			else:
				pwm.set_pwm(6, 0, int(pwm6-wiggle+increase*wiggle))

				pwm.set_pwm(7, 0, int(pwm7-wiggle+2*increase*wiggle))

				pwm.set_pwm(8, 0, int(pwm8+reach_wiggle+increase*(max_wiggle-reach_wiggle)))
				pass

		elif pos == 2:
			'''
			          1
			<2>-3--4--5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(6, 0, int(pwm6-increase*wiggle))

				pwm.set_pwm(7, 0, int(pwm7+wiggle-2*increase*wiggle))

				pwm.set_pwm(8, 0, int(pwm8+max_wiggle-increase*(max_wiggle-reach_wiggle)))
			else:
				pwm.set_pwm(6, 0, int(pwm6+increase*wiggle))

				pwm.set_pwm(7, 0, int(pwm7+wiggle-5*increase*wiggle/4))

				pwm.set_pwm(8, 0, int(pwm8+max_wiggle-increase*max_wiggle))
				pass

		elif pos == 3:
			'''
			          1
			-2-<3>-4--5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(6, 0, int(pwm6-wiggle+increase*wiggle/3))

				pwm.set_pwm(7, 0, int(pwm7-wiggle+increase*wiggle/6))

				pwm.set_pwm(8, 0, int(pwm8+reach_wiggle-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(6, 0, int(pwm6+wiggle-increase*wiggle/3))

				pwm.set_pwm(7, 0, int(pwm7-wiggle/4-increase*wiggle/12))

				pwm.set_pwm(8, 0, int(pwm8+increase*reach_wiggle/6))
				pass

		elif pos == 4:
			'''
			          1
			-2--3-<4>-5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(6, 0, int(pwm6-2*wiggle/3+increase*wiggle/3))

				pwm.set_pwm(7, 0, int(pwm7-5*wiggle/6+increase*wiggle/6))

				pwm.set_pwm(8, 0, int(pwm8+5*reach_wiggle/6-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(6, 0, int(pwm6+2*wiggle/3-increase*wiggle/3))

				pwm.set_pwm(7, 0, int(pwm7-wiggle/4-increase*wiggle/12))

				pwm.set_pwm(8, 0, int(pwm8+reach_wiggle/6+increase*reach_wiggle/6))
				pass

		elif pos == 5:
			'''
			          1
			-2--3--4-<5>-6--7--8-
			'''
			if direction:
				pwm.set_pwm(6, 0, int(pwm6-wiggle/3+increase*wiggle/3))

				pwm.set_pwm(7, 0, int(pwm7-2*wiggle/3+increase*wiggle/6))

				pwm.set_pwm(8, 0, int(pwm8+2*reach_wiggle/3-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(6, 0, int(pwm6+wiggle/3-increase*wiggle/3))

				pwm.set_pwm(7, 0, int(pwm7-5*wiggle/12-increase*wiggle/12))

				pwm.set_pwm(8, 0, int(pwm8+reach_wiggle/3+increase*reach_wiggle/6))
				pass

		elif pos == 6:
			'''
			          1
			-2--3--4--5-<6>-7--8-
			'''
			if direction:
				pwm.set_pwm(6, 0, int(pwm6+increase*wiggle/3))

				pwm.set_pwm(7, 0, int(pwm7-wiggle/2+increase*wiggle/12))

				pwm.set_pwm(8, 0, int(pwm8+reach_wiggle/2-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(6, 0, int(pwm6-increase*wiggle/3))

				pwm.set_pwm(7, 0, int(pwm7-wiggle/2-increase*wiggle/6))

				pwm.set_pwm(8, 0, int(pwm8+reach_wiggle/2+increase*reach_wiggle/6))
				pass

		elif pos == 7:
			'''
			          1
			-2--3--4--5--6-<7>-8-
			'''
			if direction:
				pwm.set_pwm(6, 0, int(pwm6+wiggle/3+increase*wiggle/3))

				pwm.set_pwm(7, 0, int(pwm7-5*wiggle/12+increase*wiggle/12))

				pwm.set_pwm(8, 0, int(pwm8+reach_wiggle/3-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(6, 0, int(pwm6-wiggle/3-increase*wiggle/3))

				pwm.set_pwm(7, 0, int(pwm7-2*wiggle/3-increase*wiggle/6))

				pwm.set_pwm(8, 0, int(pwm8+2*reach_wiggle/3+increase*reach_wiggle/6))
				pass

		elif pos == 8:
			'''
			          1
			-2--3--4--5--6--7-<8>
			'''
			if direction:
				pwm.set_pwm(6, 0, int(pwm6+2*wiggle/3+increase*wiggle/3))

				pwm.set_pwm(7, 0, int(pwm7-4*wiggle/12+increase*wiggle/12))

				pwm.set_pwm(8, 0, int(pwm8+reach_wiggle/6-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(6, 0, int(pwm6-2*wiggle/3-increase*wiggle/3))

				pwm.set_pwm(7, 0, int(pwm7-5*wiggle/6-increase*wiggle/6))

				pwm.set_pwm(8, 0, int(pwm8+5*reach_wiggle/6+increase*reach_wiggle/6))
				pass

	elif name == 'IV':
		if pos == 1:
			'''
			         <1>
			-2--3--4--5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(9, 0, int(pwm9-wiggle+increase*wiggle))

				pwm.set_pwm(10, 0, int(pwm10+wiggle-2*increase*wiggle))

				pwm.set_pwm(11, 0, int(pwm11-reach_wiggle-increase*(max_wiggle-reach_wiggle)))
			else:
				pwm.set_pwm(9, 0, int(pwm9+wiggle-increase*wiggle))

				pwm.set_pwm(10, 0, int(pwm10+wiggle/4-5*increase*wiggle/4))

				pwm.set_pwm(11, 0, int(pwm11-increase*max_wiggle))
				pass

		elif pos == 2:
			'''
			          1
			<2>-3--4--5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(9, 0, int(pwm9+increase*wiggle))

				pwm.set_pwm(10, 0, int(pwm10-wiggle+5*increase*wiggle/4))

				pwm.set_pwm(11, 0, int(pwm11-max_wiggle+increase*max_wiggle))
			else:
				pwm.set_pwm(9, 0, int(pwm9-increase*wiggle))

				pwm.set_pwm(10, 0, int(pwm10-wiggle+2*wiggle*increase))

				pwm.set_pwm(11, 0, int(pwm11-max_wiggle+increase*(max_wiggle-reach_wiggle)))
				pass

		elif pos == 3:
			'''
			          1
			-2-<3>-4--5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(9, 0, int(pwm9+wiggle-increase*wiggle/3))

				pwm.set_pwm(10, 0, int(pwm10+wiggle/4+increase*wiggle/12))

				pwm.set_pwm(11, 0, int(pwm11-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(9, 0, int(pwm9-wiggle+increase*wiggle/3))

				pwm.set_pwm(10, 0, int(pwm10+wiggle-increase*wiggle/6))

				pwm.set_pwm(11, 0, int(pwm11-reach_wiggle+increase*reach_wiggle/6))
				pass

		elif pos == 4:
			'''
			          1
			-2--3-<4>-5--6--7--8-
			'''
			if direction:
				pwm.set_pwm(9, 0, int(pwm9+2*wiggle/3-increase*wiggle/3))

				pwm.set_pwm(10, 0, int(pwm10+wiggle/3+increase*wiggle/12))

				pwm.set_pwm(11, 0, int(pwm11-reach_wiggle/6-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(9, 0, int(pwm9-2*wiggle/3+increase*wiggle/3))

				pwm.set_pwm(10, 0, int(pwm10+5*wiggle/6-increase*wiggle/6))

				pwm.set_pwm(11, 0, int(pwm11-5*reach_wiggle/6+increase*reach_wiggle/6))
				pass

		elif pos == 5:
			'''
			          1
			-2--3--4-<5>-6--7--8-
			'''
			if direction:
				pwm.set_pwm(9, 0, int(pwm9+wiggle/3-increase*wiggle/3))

				pwm.set_pwm(10, 0, int(pwm10+5*wiggle/12+increase*wiggle/12))

				pwm.set_pwm(11, 0, int(pwm11-reach_wiggle/3-increase*reach_wiggle/6))
			else:
				pwm.set_pwm(9, 0, int(pwm9-wiggle/3+increase*wiggle/3))

				pwm.set_pwm(10, 0, int(pwm10+2*wiggle/3-increase*wiggle/6))

				pwm.set_pwm(11, 0, int(pwm11-2*reach_wiggle/3+increase*reach_wiggle/6))
				pass

		elif pos == 6:
			'''
			          1
			-2--3--4--5-<6>-7--8-
			'''
			if direction:
				pwm.set_pwm(9, 0, int(pwm9-increase*wiggle/3))

				pwm.set_pwm(10, 0, int(pwm10+wiggle/2+increase*wiggle/6))

				pwm.set_pwm(11, 0, int(pwm11-reach_wiggle/2-increase*wiggle/6))
			else:
				pwm.set_pwm(9, 0, int(pwm9+increase*wiggle/3))

				pwm.set_pwm(10, 0, int(pwm10+wiggle/2-increase*wiggle/12))

				pwm.set_pwm(11, 0, int(pwm11-reach_wiggle/2+increase*reach_wiggle/6))
				pass

		elif pos == 7:
			'''
			          1
			-2--3--4--5--6-<7>-8-
			'''
			if direction:
				pwm.set_pwm(9, 0, int(pwm9-wiggle/3-increase*wiggle/3))

				pwm.set_pwm(10, 0, int(pwm10+4*wiggle/6+increase*wiggle/6))

				pwm.set_pwm(11, 0, int(pwm11-2*reach_wiggle/3-increase*wiggle/6))
			else:
				pwm.set_pwm(9, 0, int(pwm9+wiggle/3+increase*wiggle/3))

				pwm.set_pwm(10, 0, int(pwm10+5*wiggle/12-increase*wiggle/12))

				pwm.set_pwm(11, 0, int(pwm11-reach_wiggle/3+increase*reach_wiggle/6))
				pass

		elif pos == 8:
			'''
			          1
			-2--3--4--5--6--7-<8>
			'''
			if direction:
				pwm.set_pwm(9, 0, int(pwm9-2*wiggle/3-increase*wiggle/3))

				pwm.set_pwm(10, 0, int(pwm10+5*wiggle/6+increase*wiggle/6))

				pwm.set_pwm(11, 0, int(pwm11-5*reach_wiggle/6-increase*wiggle/6))
			else:
				pwm.set_pwm(9, 0, int(pwm9+2*wiggle/3+increase*wiggle/3))

				pwm.set_pwm(10, 0, int(pwm10+wiggle/3-increase*wiggle/12))

				pwm.set_pwm(11, 0, int(pwm11-reach_wiggle/6+increase*reach_wiggle/6))
				pass


def dove_move_tripod(step, speed, command):
	step_I  = step
	step_II = step+2
	step_III= step+4
	step_IV = step+6
	if step_II > 8:
		step_II = step_II - 8
	if step_III> 8:
		step_III= step_III- 8
	if step_IV > 8:
		step_IV = step_IV - 8

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
	if step_II > 8:
		step_II = step_II - 8
	if step_III> 8:
		step_III= step_III- 8
	if step_IV > 8:
		step_IV = step_IV - 8

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
	pwm.set_pwm(0, 0, int(pwm0-wiggle+2*wiggle*amp/100))

	pwm.set_pwm(3, 0, int(pwm3-wiggle+2*wiggle*amp/100))

	pwm.set_pwm(6, 0, int(pwm6+wiggle-2*wiggle*amp/100))

	pwm.set_pwm(9, 0, int(pwm9+wiggle-2*wiggle*amp/100))


def robot_hight(wiggle, amp):
	'''
	when amp is 0, robot <heighest>.
	when amp is 100, robot <lowest>.
	'''
	pwm.set_pwm(1, 0, int(pwm1+wiggle-2*wiggle*amp/100))

	pwm.set_pwm(4, 0, int(pwm4-wiggle+2*wiggle*amp/100))

	pwm.set_pwm(7, 0, int(pwm7-wiggle+2*wiggle*amp/100))

	pwm.set_pwm(10, 0, int(pwm10+wiggle-2*wiggle*amp/100))


def look_home():
	robot_stand(150)


def robot_stand(wiggle_input):
	robot_X(wiggle_input, 50)
	robot_hight(wiggle_input, 0)

	pwm.set_pwm(2, 0, pwm2)
	pwm.set_pwm(5, 0, pwm5)
	pwm.set_pwm(8, 0, pwm8)
	pwm.set_pwm(11, 0, pwm11)


def ctrl_range(raw, max_genout, min_genout):
	if raw > max_genout:
		raw_output = max_genout
	elif raw < min_genout:
		raw_output = min_genout
	else:
		raw_output = raw
	return int(raw_output)


def ctrl_pitch_roll(wiggle, pitch, roll):
	'''
	look up <- pitch -> look down.
	lean right <- roll -> lean left.
	default values are 0.
	range(-100, 100)
	'''
	pwm.set_pwm(1, 0, ctrl_range((pwm1-wiggle*pitch/100-wiggle*roll/100), pwm1_max, pwm1_min))

	pwm.set_pwm(4, 0, ctrl_range((pwm4-wiggle*pitch/100+wiggle*roll/100), pwm4_max, pwm4_min))

	pwm.set_pwm(7, 0, ctrl_range((pwm7+wiggle*pitch/100-wiggle*roll/100), pwm7_max, pwm7_min))

	pwm.set_pwm(10, 0, ctrl_range((pwm10+wiggle*pitch/100+wiggle*roll/100), pwm10_max, pwm10_min))


def ctrl_yaw(wiggle, yaw):
	'''
	look left <- yaw -> look right
	default value is 0
	'''
	pwm.set_pwm(2, 0, pwm2)

	pwm.set_pwm(5, 0, pwm5)

	pwm.set_pwm(8, 0, pwm8)

	pwm.set_pwm(11, 0, pwm11)


def steady():
	global X_fix_output, Y_fix_output
	accelerometer_data = sensor.get_accel_data()
	X = accelerometer_data['x']
	X = kalman_filter_X.kalman(X)
	Y = accelerometer_data['y']
	Y = kalman_filter_Y.kalman(Y)

	X_fix_output -= X_pid.GenOut(X - X_steady)
	Y_fix_output += Y_pid.GenOut(Y - Y_steady)
	X_fix_output = ctrl_range(X_fix_output, 100, -100)
	Y_fix_output = ctrl_range(Y_fix_output, 100, -100)
	#ctrl_pitch_roll(150, -X_fix_output, 0)
	#print(X)
	ctrl_pitch_roll(150, -X_fix_output, Y_fix_output)


def relesae():
	pwm.set_all_pwm(0,0)


def clean_all():
	pwm.set_all_pwm(0, 0)


def init_servos():
	pwm.set_all_pwm(0, 300)


step_input = 1
move_stu = 1
if __name__ == '__main__':	
	try:
		'''
		while 1:
			#dove_move_tripod(step_input, 150, 'forward')
			dove_move_diagonal(step_input, 150, 'left')
			step_input += 1
			if step_input == 9:
				step_input = 1
		'''
		'''
		robot_X(150, 100)
		while 1:
			for i in range (-100, 100):
				ctrl_pitch_roll(150, 0, i)
			for i in range (100, -100, -1):
				ctrl_pitch_roll(150, 0, i)
			for i in range (-100, 100):
				ctrl_pitch_roll(150, i, 0)
			for i in range (100, -100, -1):
				ctrl_pitch_roll(150, i, 0)
		'''
		'''
		while 1:
			for i in range (-100, 100):
				ctrl_pitch_roll(150, i, 0)
			for i in range (100, -100, -1):
				ctrl_pitch_roll(150, i, 0)
		'''

		#robot_X(150, 100)
		#robot_hight(150, 0)
		'''
		while 1:
			robot_hight(150, 0)
			time.sleep(2)
			ctrl_pitch_roll(150, 0, 100)
			time.sleep(2)
			ctrl_pitch_roll(150, 0, -100)
			time.sleep(2)
		'''
		
		while 1:
			steady()
			#time.sleep(0.1)
			#pass
		
		#mpu6050Test()
	except KeyboardInterrupt:
		#pwm.set_all_pwm(0, 300)
		time.sleep(1)
		clean_all()
	

