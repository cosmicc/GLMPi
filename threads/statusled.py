from time import sleep
from rpi_ws281x import *
from threads.threadqueues import status_queue
from configparser import ConfigParser
import threading
import logging
import socket

config = ConfigParser()
config.read('/etc/glmpi.conf')
loopdelay = float(config.get('status_led', 'loopdelay'))

host_name = socket.gethostname()
log = logging.getLogger(name=host_name)

class statusLed():
    black = Color(0, 0, 0)
    red = Color(0, 255, 0)
    magenta = Color(0, 255, 255)
    yellow = Color(255, 255, 0)
    cyan = Color(255, 0, 255)
    green = Color(255, 0, 0)
    blue = Color(0, 0, 255)
    white = Color(255, 255, 255)
    def __init__(self):
        config = ConfigParser()
        config.read('/etc/glmpi.conf')
        self.brightness = int(config.get('status_led', 'brightness'))
        self.invert = bool(config.get('status_led', 'invert'))
        self.channel = int(config.get('status_led', 'channel'))
        self.frequency = int(config.get('status_led', 'frequency'))
        self.dma = int(config.get('status_led', 'dma'))
        self.pin = int(config.get('status_led', 'pin'))
        strip = Adafruit_NeoPixel(1, self.pin, self.frequency, self.dma, False, self.brightness, self.channel)
        self.blinking = False
        self.strip = strip
        self.strip.begin()
        self.strip.setPixelColor(0, statusLed.black)
        self.strip.setBrightness(self.brightness)
        self.color = 'black'
        self.strip.show()
    def off(self):
        self.blinking = Falsie
        self.strip.setPixelColor(0, statusLed.black)
        self.color = 'black'
        self.strip.show()
    def on(self, color, flashes, flashrate):
        if color != self.color or (color == self.color and flashes != 0):
            log.debug(f'Status led ON color: {color}, flashes:{flashes}, flashrate:{flashrate}')
            self.color = color
            if color == 'green':
                color = statusLed.green
            elif color == 'red':
                color = statusLed.red
            elif color == 'yellow':
                color = statusLed.yellow
            elif color == 'magenta':
                color = statusLed.magenta
            elif color == 'white':
                color = statusLed.white
            elif color == 'blue':
                color = statusLed.blue
            elif color == 'cyan':
                color = statusLed.cyan
            if flashes == 0:
                self.blinking = False
                self.strip.setPixelColor(0, color)
                self.strip.show()
            else:
                self.blinking = True
                if flashrate == 'fast':
                    self.blinkrate = .1
                elif flashrate == 'slow':
                    self.blinkrate = .5

                def blinkthread(self, color, flashes):
                    log.debug(f'starting status led blink thread color: {self.color}')
                    self.strip.setPixelColor(0, color)
                    def blinkit(self, bright):
                        self.strip.setBrightness(bright)
                        self.strip.show()
                        sleep(.025)
                    for flash in range(flashes):
                        blinkit(self, self.brightness)
                        sleep(self.blinkrate)
                        blinkit(self, int(self.brightness/2))
                        blinkit(self, int(self.brightness/4))
                        blinkit(self, 0)
                        blinkit(self, int(self.brightness/4))
                        blinkit(self, int(self.brightness/2))
                    self.strip.setPixelColor(0, color)
                    self.strip.setBrightness(self.brightness)
                    self.strip.show()
                    self.blinking = False
                    log.debug(f'stopping status led blink thread color {self.color}')

                bthread = threading.Thread(name='status-blink', target=blinkthread, args=(self, color, flashes))
                bthread.start()

def stled(color, flash=0, flashrate='slow'):
    log.debug(f'Status led queue adding color:{color}, flash:{flash}, flashrate:{flashrate}')
    status_queue.put({'color': color, 'flash': flash, 'flashrate': flashrate})

def statusled_thread():
    log.debug('Status led thread is starting')
    sled = statusLed()
    while True:
        try:
            if not status_queue.empty():
                ststatus = status_queue.get()
                sled.on(ststatus['color'], int(ststatus['flash']), ststatus['flashrate'])
            sleep(loopdelay)
        except:
            log.critical(f'Critical Error in Status Led Thread', exc_info=True)
            sleep(60)
