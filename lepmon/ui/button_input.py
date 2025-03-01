try:
    import RPi.GPIO as GPIO
except ImportError: 
    import VPi.GPIO as GPIO
    # from lepmon.devices.MockGPIO import MockGPIO as GPIO
import time

class ButtonInput:
    def __init__(self, pin):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def wait_for_press(self, timeout=None):
        """
        Blocks until the button is pressed, or until timeout (seconds).
        Returns True if pressed, False if timed out.
        """
        start = time.time()
        while True:
            if GPIO.input(self.pin) == GPIO.LOW:
                return True
            if timeout and (time.time() - start) > timeout:
                return False
            time.sleep(0.01)
            
    def is_released(self):
        return GPIO.input(self.pin) == GPIO.HIGH

    def is_pressed(self):
        return GPIO.input(self.pin) == GPIO.LOW