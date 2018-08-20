#!/usr/bin/python

import argparse
from datetime import datetime
from datetime import timedelta
import RPi.GPIO as GPIO
import time

from RpiMotorLib import RpiMotorLib

# Use BCM GPIO references
# instead of physical pin numbers
GPIO.setmode(GPIO.BCM)

# 28BYJ have 512 ticks per revolution with RpiMotorLib
#
motor = {
	'hour': {
		'pins': [20,26,16,19],
		'motor': RpiMotorLib.BYJMotor("Hour", "28BYJ"),
		'ccwise': False
	},
	'minute_h': {
		'pins': [13,12,6,5],
		'motor': RpiMotorLib.BYJMotor("Minute_H", "28BYJ"),
		'ccwise': False
	},
	'minute_l': {
		'pins': [4,25,24,23],
		'motor': RpiMotorLib.BYJMotor("Minute_L", "28BYJ"),
		'ccwise': True
	},
	'MO': {
		'pins': [17,18,27,22],
		'motor': RpiMotorLib.BYJMotor("TestMotor", "28BYJ"),
		'ccwise': False
	}
}

# Nudge the motor forward by 8 ticks
#
def run_nudge(args):
	print(args.motor)
	args.motor['motor'].motor_run(args.motor['pins'], .0009, 8, args.motor['ccwise'], False, "half", .05)
	GPIO.cleanup()

# Calculate how many steps away each number is from the current position
#
def calculate_offsets(current):
	offsets = { 'hour': {}, 'minute_h': {}, 'minute_l': {} }

	print(current)

	# Calculate hour
	for x in range(12):
		offsets['hour'][int((current.hour + x) % 12)] = int(512 * x / 12)
	print(offsets['hour'])

	# Calculate minute_h
	for x in range(10):
		offsets['minute_h'][int(((current.minute // 10) + x) % 10)] = int(512 * x / 10)
	print(offsets['minute_h'])

	# Calculate minute_l
	for x in range(10):
		offsets['minute_l'][int((current.minute + x) % 10)] = int(512 * x / 10)
	print(offsets['minute_l'])

	return offsets

def run_show_time(args):
	# Always have the desired in the future
	if args.desired < args.current:
		args.desired = args.desired + timedelta(hours=12)

	# Calculate offsets from current time
	offsets = calculate_offsets(args.current)

	# Spin the wheels the correct amount for desired time
	m = motor['hour']
	desired_hour = int((args.desired.hour + 11) % 12 + 1)
	m['motor'].motor_run(m['pins'], .002, offsets['hour'][desired_hour], m['ccwise'], False, "half", .05)

	m = motor['minute_h']
	desired_minute_h = int(args.desired.minute // 10)
	m['motor'].motor_run(m['pins'], .002, offsets['minute_h'][desired_minute_h], m['ccwise'], False, "half", .05)

	m = motor['minute_l']
	desired_minute_l = int(args.desired.minute % 10)
	m['motor'].motor_run(m['pins'], .002, offsets['minute_l'][desired_minute_l], m['ccwise'], False, "half", .05)

	GPIO.cleanup()

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

def main():
	parser = argparse.ArgumentParser(
		description='Run control logic for split-flap clock'
	)

	subparsers = parser.add_subparsers()

	parser_nudge = subparsers.add_parser('nudge')
	parser_nudge.set_defaults(func=run_nudge)
	parser_nudge.add_argument('--motor', required=True, type=valid_motor)

	parser_show_time = subparsers.add_parser('set_time')
	parser_show_time.set_defaults(func=run_show_time)
	parser_show_time.add_argument('--current', required=True, type=valid_time)
	parser_show_time.add_argument('--desired', required=True, type=valid_time)

	args = parser.parse_args()
	args.func(args)

if __name__ == '__main__':
	main()
