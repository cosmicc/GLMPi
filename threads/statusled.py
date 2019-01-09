from time import sleep
from rpi_ws281x import *
from threads.threadqueues import status_queue
from configparser import ConfigParser
import threading
import logging
import socket

config = ConfigParser()
config.read('/etc/glmpi.conf')
loopdelay = float(config.get('status_led', 'cmddelay'))

host_name = socket.gethostname()
log = logging.getLogger(name=host_name)

def i2rgb(RGBint, string=True):
    blue =  RGBint & 255
    green = (RGBint >> 8) & 255
    red =   (RGBint >> 16) & 255
    if string:
        return f'({red}, {green}, {blue})'
    else:
        return (red, green, blue)

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
        self.fastblink = float(config.get('status_led', 'blinkrate_fast'))
        self.slowblink = float(config.get('status_led', 'blinkrate_slow'))
        strip = Adafruit_NeoPixel(1, self.pin, self.frequency, self.dma, False, self.brightness, self.channel)
        self.blinking = False
        self.strip = strip
        self.strip.begin()
        self.strip.setPixelColor(0, statusLed.black)
        self.strip.setBrightness(self.brightness)
        self.color = statusLed.black
        self.strip.show()
    def __repr__(self):
        return f'<statusLed object on pin:{self.pin} dma:{self.dma} channel:{self.channel}>'
    def __str__(self):
        return f'StatusLED - Brightness:{self.brightness}, Color:{i2rgb(self.color)}, Blinking:{self.blinking}'

    def changecolor(self, color, flashes, flashrate='fast'):
        if color != self.color or (color == self.color and flashes != 0):
            log.debug(f'Status led color change: {i2rgb(color)}, flashes:{flashes}, flashrate:{flashrate}')
            self.strip.setPixelColor(0, color)
            self.strip.show()
            self.color = color
        elif flashes > 0:
            log.debug(f'Status led color change: {i2rgb(color)}, flashes:{flashes}, flashrate:{flashrate}')
            self.blinking = True
            def blinkthread(self, flashes=0, flashrate='fast'):

                def lightit(self, bright):
                    self.strip.setBrightness(bright)
                    self.strip.show()
                    sleep(.025)
                log.debug(f'starting status led blink thread color: {i2rgb(self.color)}')
                self.strip.setPixelColor(0, self.color)
                self.strip.show()
                for flash in range(flashes):
                    lightit(self, self.brightness)
                    if flashrate == 'fast':
                        sleep(self.blinkfast)
                    elif flashrate == 'slow':
                        sleep(self.blinkslow)
                    else:
                        log.error('Invalid flashrate specified for status led')
                    lightit(self, int(self.brightness/2))
                    lightit(self, int(self.brightness/4))
                    lightit(self, 0)
                    sleep(.05)
                    lightit(self, int(self.brightness/4))
                    lightit(self, int(self.brightness/2))
                    lightit(self, self.brightness)
                self.blinking = False
                log.debug(f'stopping status led blink thread color {i2rgb(self.color)}')

            bthread = threading.Thread(name='status-blink', target=blinkthread, args=(self, flashes, flashrate))
            bthread.start()

    def off(self):
        self.blinking = False
        statusLed.changecolor(self, statusLed.black)
    def on(self, color, flashes=0, flashrate='fast'):
            if color == 'green':
                statusLed.changecolor(self, statusLed.green, flashes=flashes, flashrate=flashrate)
            elif color == 'red':
                statusLed.changecolor(self, statusLed.red, flashes=flashes, flashrate=flashrate)
            elif color == 'yellow':
                statusLed.changecolor(self, statusLed.yellow, flashes=flashes, flashrate=flashrate)
            elif color == 'magenta':
                statusLed.changecolor(self, statusLed.magenta, flashes=flashes, flashrate=flashrate)
            elif color == 'white':
                statusLed.changecolor(self, statusLed.white, flashes=flashes, flashrate=flashrate)
            elif color == 'blue':
                statusLed.changecolor(self, statusLed.blue, flashes=flashes, flashrate=flashrate)
            elif color == 'cyan':
                statusLed.changecolor(self, statusLed.cyan, flashes=flashes, flashrate=flashrate)
            else:
                log.error('Invalid status led color specified')

def stled(color, flashes=0, flashrate='fast'):
    #log.debug(f'Status led queue adding color:{color}, flash:{flash}, flashrate:{flashrate}')
    status_queue.put({'color': color, 'flashes': flashes, 'flashrate': flashrate})

def statusled_thread():
    log.debug('Status led thread is starting')
    sled = statusLed()
    while True:
        try:
            if not status_queue.empty():
                ststatus = status_queue.get()
                sled.on(ststatus['color'], int(ststatus['flashes']), ststatus['flashrate'])
            sleep(loopdelay)
        except:
            log.critical(f'Critical Error in Status Led Thread', exc_info=True)
            sleep(60)
