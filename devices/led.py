import RPi.GPIO as GPIO
import time

class LEDDimmer:
    def __init__(self, pin, frequency=350):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, frequency)
        self.pwm_started = False

    def start(self, duty_cycle=0):
        if not self.pwm_started:
            self.pwm.start(duty_cycle)
            self.pwm_started = True

    def dim_up(self, step_time=0.05):
        self.start(0)
        for dc in range(0, 100):
            self.pwm.ChangeDutyCycle(dc)
            time.sleep(step_time)

    def dim_down(self, step_time=0.05):
        self.start(100)
        for dc in reversed(range(0, 100)):
            self.pwm.ChangeDutyCycle(dc)
            time.sleep(step_time)

    def stop(self):
        self.pwm.stop()
        self.pwm_started = False
