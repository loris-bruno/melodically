import RPi.GPIO as GPIO
import time
from threading import Thread

BUTTON_PIN = 16
GPIO.setmode(GPIO.BCM)

GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


"""
Thread to check GPIO button input
trigger: LOW -> HIGH
"""
class GPIOThread(Thread):
    def __init__(self, startMethod):
        Thread.__init__(self)
        self.prev_state = GPIO.HIGH
        self.startMethod = startMethod
        
    def run(self):
        try: 
            while True:
                time.sleep(0.1)
                btn_state = GPIO.input(BUTTON_PIN)
                if btn_state != self.prev_state:
                    self.prev_state = btn_state
                    if btn_state == GPIO.HIGH:
                        print("just released")
                        self.startMethod()
        except KeyboardInterrupt:
            GPIO.cleanup()
