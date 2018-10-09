#!/usr/bin/python

import argparse
import datetime as dt
from datetime import timedelta, date, time
import RPi.GPIO as GPIO
import time
import threading
import logging
from RpiMotorLib import RpiMotorLib

logger = logging.getLogger(__name__)
logging.basicConfig(filename='split-flap.log', level=logging.INFO)

# Use BCM GPIO references
# instead of physical pin numbers
GPIO.setmode(GPIO.BCM)

# 28BYJ have 512 ticks per revolution with RpiMotorLib
#
motor = {
	'hour': {
		'pins': [20,26,16,19],
		'motor': RpiMotorLib.BYJMotor("Hour", "28BYJ"),
		'ccwise': False,
		'counts_per_flap': 42
	},
	'minute_h': {
		'pins': [13,12,6,5],
		'motor': RpiMotorLib.BYJMotor("Minute_H", "28BYJ"),
		'ccwise': False,
		'counts_per_flap': 51
	},
	'minute_l': {
		'pins': [4,25,24,23],
		'motor': RpiMotorLib.BYJMotor("Minute_L", "28BYJ"),
		'ccwise': True,
		'counts_per_flap': 51
	},
	'MO': {
		'pins': [17,18,27,22],
		'motor': RpiMotorLib.BYJMotor("TestMotor", "28BYJ"),
		'ccwise': False,
		'counts_per_flap': 51
	}
}

# Nudge the motor forward by 8 ticks
#
def run_nudge(args):
	print(args.motor)
	args.motor['motor'].motor_run(args.motor['pins'], .0009, 8, args.motor['ccwise'], False, "half", .05)
	GPIO.cleanup()

# Move the motor forward to the next flap
#
def run_flip(args):
	print(args.motor)
	args.motor['motor'].motor_run(args.motor['pins'], .002, args.motor['counts_per_flap'], args.motor['ccwise'], False, "half", .05)
	GPIO.cleanup()

def calculate_offsets(current):
	offsets = { 'hour': {}, 'minute_h': {}, 'minute_l': {} }

	print(current)

	# Calculate hour
	for x in range(12):
		offsets['hour'][int((current.hour + x) % 12)] = int(512 * x / 12)
	print("hour offset = ")
	print(offsets['hour'])

	# Calculate minute_h
	for x in range(10):
		offsets['minute_h'][int(((current.minute // 10) + x) % 10)] = int(512 * x / 10)
	print("minute high offset = ")
	print(offsets['minute_h'])

	# Calculate minute_l
	for x in range(10):
		offsets['minute_l'][int((current.minute + x) % 10)] = int(512 * x / 10)
	print("minute low offset = ")
	print(offsets['minute_l'])

	return offsets

def run_show_time(current, desired):
	logger.info('++++++++++ run_show_time')

	# Always have the desired in the future
	if desired < current:
		desired = dt.time(desired.hour + 12, desired.minute)

	# Calculate offsets from current time
	offsets = calculate_offsets(current)

	# Spin the wheels the correct amount for desired time
	m = motor['hour']
	desired_hour = int((desired.hour + 12) % 12)
	m['motor'].motor_run(m['pins'], .002, offsets['hour'][desired_hour], m['ccwise'], False, "half", .05)

	m = motor['minute_h']
	desired_minute_h = int(desired.minute // 10)
	print(desired_minute_h)
	m['motor'].motor_run(m['pins'], .002, offsets['minute_h'][desired_minute_h], m['ccwise'], False, "half", .05)

	m = motor['minute_l']
	desired_minute_l = int((desired.minute) % 10)
	print(desired_minute_l)
	m['motor'].motor_run(m['pins'], .002, offsets['minute_l'][desired_minute_l], m['ccwise'], False, "half", .05)
	logger.info('time after calibration = %s', dt.datetime.now())

	write_time_to_log(desired_hour, desired_minute_h, desired_minute_l)
	time.sleep(60-1)
	test(desired_hour, desired_minute_h, desired_minute_l)
	logger.info('---------- run_show_time\n')


	# Log current time to file
def write_time_to_log(hour, minute_h, minute_l):
	logger.info('++++++++++ write_time_to_log')

	f = open("current_time.txt", "w")
	hour = hour % 12;
	f.write("{0} {1}{2}".format(hour,minute_h,minute_l))
	f.close()

	logger.info('getRealTimeEST = %s', getRealTimeEST())
	logger.info(' hour, minute_h and minute_l written to log = %s %s %s', hour, minute_h, minute_l)
	logger.info('---------- write_time_to_log\n')

def valid_time(s):
	try:
		return datetime.strptime(s, "%H:%M")
	except ValueError:
		msg = "Not a valid time: '{0}'.".format(s)
		raise argparse.ArgumentTypeError(msg)

def valid_motor(s):
	try:
		return motor[s]
	except ValueError:
		msg = "Not a valid motor: '{0}'.".format(s)
		raise argparse.ArgumentTypeError(msg)

def test(hour, minute_h, minute_l):
	logger.info('++++++++++ test')

	clk_t = readCurrentState()
	rt_EST = getRealTimeEST()
	logger.info('%s %s', clk_t.minute, rt_EST.minute)
	logger.info('%s', -(clk_t.minute - rt_EST.minute) % 60 < 3)

	if  -(clk_t.minute - rt_EST.minute) % 60 <= 1 :
		logger.info("-(clk_t.minute - rt_est.minute) % 60 <= 1")

		if minute_h < 5 and minute_l == 9:
			logger.info('XX:<59, updating minute_h and minute_l')
			logger.info('previously %s:%s%s', hour, minute_h, minute_l)

			m = motor['minute_h']
			m['motor'].motor_run(m['pins'], .002, m['counts_per_flap'], m['ccwise'], False, "half", .05)

			m = motor['minute_l']
			m['motor'].motor_run(m['pins'], .002, m['counts_per_flap'], m['ccwise'], False, "half", .05)

			minute_h += 1
			minute_l = 0
			logger.info('now %s:%s%s', hour, minute_h, minute_l)

		elif minute_h == 5 and minute_l == 9:
			logger.info('XX:%s%s, updating 5 x minute_h and minute_l',minute_h, minute_l)
			logger.info('previously %s:%s%s', hour, minute_h, minute_l)

			m = motor['hour']
			m['motor'].motor_run(m['pins'], .002, m['counts_per_flap'], m['ccwise'], False, "half", .05)
			if hour == 12:
				hour = 1
			else:
				hour+=1

			m = motor['minute_h']
			m['motor'].motor_run(m['pins'], .002, m['counts_per_flap']*5, m['ccwise'], False, "half", .05)
			minute_h = 0

			m = motor['minute_l']
			m['motor'].motor_run(m['pins'], .002, m['counts_per_flap'], m['ccwise'], False, "half", .05)
			minute_l = 0

			logger.info('now %s:%s%s', hour, minute_h, minute_l)

		else:
			logger.info('XX:X%s, updating minute_l', minute_l)
			logger.info('previously %s:%s%s', hour, minute_h, minute_l)
			m = motor['minute_l']
			m['motor'].motor_run(m['pins'], .002, m['counts_per_flap'], m['ccwise'], False, "half", .05)
			minute_l+=1
			logger.info('now %s:%s%s', hour, minute_h, minute_l)
	else:
		logger.info("-(clk_t.minute - rt_est.minute) % 60 > 1")
		run_show_time(clk_t,rt_EST)

	hour = hour % 12
	write_time_to_log(hour, minute_h, minute_l)

	time.sleep(60-1)

	test(hour, minute_h, minute_l)
	logger.info('---------- test\n')

def readCurrentState():
	logger.info('++++++++++ readCurrentState')
	filename = "current_time.txt"
	file = open(filename, 'r')
	test = file.readline()
	time = test.split(' ',1)
	logger.info('current time read from current_time.txt')
	hour = int(time[0]);
	if hour >= 24 :
		hour = hour % 12
	minutes = int(time[1])
	clock_time = dt.time(hour,minutes)
	logger.info('curr state  = %s',clock_time)
	logger.info('---------- readCurrentState\n')

	return clock_time

def getRealTimeEST():
	logger.info('++++++++++ getRealTimeEST')

	#convert from UTC to EST
	realtime = dt.datetime.now()
	realtime_EST = dt.time((realtime.hour+12-4) % 12, realtime.minute)

	logger.info(' %s', realtime_EST)
	logger.info('---------- getRealTimeEST\n')

	return realtime_EST

def startClock():
	logger.info('startClock() \n')
	clock_time = readCurrentState()
	realtime_EST = getRealTimeEST()
	run_show_time(clock_time, realtime_EST)

def main():
	startClock()

if __name__ == '__main__':
	main()
