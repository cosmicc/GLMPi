from time import sleep
from rpi_ws281x import *
from threads.threadqueues import status_queue
import threading
import logging
import socket

config = ConfigParser()
config.read('/etc/glmpi.conf')

LED_PIN = config.get('status_led', 'pin')
brightness = config.get('status_led', 'brightness')
LED_FREQ_HZ = config.get('status_led', 'frequency')
LED_DMA = config.get('status_led', 'dma')
LED_INVERT = config.get('status_led', 'invert')
LED_CHANNEL = config.get('status_led', 'channel')
loopdelay = config.get('status_led', 'loopdelay')

host_name = socket.gethostname()
log = logging.getLogger(name=host_name)

class statusLed():
    black = Color(0, 0, 0)
    red = Color(255, 0, 0)
    magenta = Color(255, 0, 255)
    yellow = Color(255, 255, 0)
    cyan = Color(0, 255, 255)
    green = Color(0, 255, 0)
    blue = Color(0, 0, 255)
    white = Color(255, 255, 255)
    def __init__(self, LED_PIN, brightness):
        self.brightness = brightness
        strip = Adafruit_NeoPixel(1, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, brightness, LED_CHANNEL)
        self.blinking = False
        self.strip = strip
        self.strip.begin()
        self.strip.setPixelColor(0, statusLed.black)
        self.strip.setBrightness(20)
        self.strip.show()
    def color(self, color, chgbright=-1):
        self.blinking = False
        self.strip.setPixelColor(0, color)
        if chgbright != -1:
            self.strip.setBrightness(chgbright)
        self.strip.show()
    def off(self):
        self.blinking = False
        self.strip.setPixelColor(0, statusLed.black)
        self.strip.show()
    def resetbrightness(self):
        self.strip.setBrightness(self.brightness)
        self.strip.show()
    def setbrightness(self, chgbright):
        self.strip.setBrightness(chgbright)
        self.strip.show()
    def stopblink(self):
        self.blinking = False
        self.strip.setPixelColor(0, statusLed.black)
        self.strip.show()
    def blink(self, color, fast=False):
        self.blinking = True
        if fast:
            self.blinkrate = 0
        else:
            self.blinkrate = .5
        def blinkthread(self, color):
            self.strip.setPixelColor(0, color)
            def blinkit(self, bright):
                self.strip.setBrightness(bright)
                self.strip.show()
                sleep(.1)
            while self.blinking:
                blinkit(self, self.brightness)
                blinkit(self, int(self.brightness/2))
                #blinkit(self, int(self.brightness/4))
                blinkit(self, 0)
                sleep(self.blinkrate)
                #blinkit(self, int(self.brightness/4))
                blinkit(self, int(self.brightness/2))
            self.strip.setPixelColor(0, statusLed.black)
            self.strip.setBrightness(self.brightness)
            self.strip.show()

        bthread = threading.Thread(target=blinkthread, args=(self, color))
        bthread.start()

def stled(color, flash=0, flashrate='slow'):
    status_led.put({'color': color, 'flash': flash, 'flashrate': flashrate})

def statusled_thread():
    sled = statusLed()
    while True:
        try:
            if not bthread.is_alive() and not status_queue.empty():
                ststatus = status_queue.get()
                if 
            sleep(loopdelay)
        except:
            log.critical(f'Critical Error in Status Led Thread', exc_info=True)
