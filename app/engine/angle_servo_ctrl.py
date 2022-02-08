import sys
import time
import RPi.GPIO as GPIO

import numpy as np

def angle_to_duty(ang):
    # mapping duty cycle to angle
    pwm_range = np.linspace(2.0, 12.0)
    pwm_span = pwm_range[-1] - pwm_range[0]
    ang_range = np.linspace(0.0, 180.0)
    ang_span = ang_range[-1] - ang_range[0]

    # rounding to approx 0.01 - the max resolution
    # (based on 10-bits, 2%-12% PWM period)
    # print('Duty Cycle: '+str(round((((ang - ang_range[0])/ang_span)*pwm_span)+pwm_range[0],1)))
    return round((((ang - ang_range[0]) / ang_span) * pwm_span) + pwm_range[0], 1)


def move(servo, angle, delay=0.5):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)
    GPIO.setup(servo, GPIO.OUT)
    # set_servo_angle(servo, angle)
    pwm = GPIO.PWM(servo, 50)
    pwm.start(8)
    # dutyCycle = angle / 18. + 3.
    duty_cycle = angle_to_duty(angle)
    pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(delay)
    pwm.stop()
    GPIO.cleanup()


if __name__ == '__main__':
    servo = int(sys.argv[1])
    angle = int(sys.argv[2])
    move(servo, angle)
