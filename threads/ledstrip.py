from time import sleep
from rpi_ws281x import *
from threads.threadqueues import strip_queue
from configparser import ConfigParser
import threading
import logging
import socket

host_name = socket.gethostname()
log = logging.getLogger(name=host_name)

class ledStrip():
    black = Color(0, 0, 0)
    blue = Color(0, 0, 255)
    nlcolor Color()
    def __init__(self):
        config = ConfigParser()
        config.read('/etc/glmpi.conf')
        self.nightlight = bool(config.get('features', 'nightlight'))
        self.ledcount = int(config.get('led_strip', 'ledcount'))
        self.invert = bool(config.get('led_strip', 'invert'))
        self.channel = int(config.get('led_strip', 'channel'))
        self.frequency = int(config.get('led_strip', 'frequency'))
        self.dma = int(config.get('led_strip', 'dma'))
        self.pin = int(config.get('led_strip', 'pin'))
        self.mode = 0
        self.away = False
        self.night = False
        strip = Adafruit_NeoPixel(self.ledcount, self.pin, self.frequency, self.dma, False, 255, self.channel)
        self.strip = strip
        self.strip.begin()
        for led in range(self.ledcount):
            self.strip.setPixelColor(led, ledStrip.black)
        self.color = Color(0, 0, 0)
        self.strip.show()
        for led in range(int(self.ledcount/2)+1):
            self.strip.setPixelColor(int(self.ledcount/2)+led, ledStrip.blue)
            self.strip.setPixelColor(int(self.ledcount/2)+led+1, Color(0, 0, 100))
            self.strip.setPixelColor(int(self.ledcount/2)+led+2, Color(0, 0, 30))
            self.strip.setPixelColor(int(self.ledcount/2)-led, ledStrip.blue)
            self.strip.setPixelColor(int(self.ledcount/2)-led-1, Color(0, 0, 100))
            self.strip.setPixelColor(int(self.ledcount/2)-led-2, Color(0, 0, 30))
            self.strip.show()
            sleep(.02)
        sleep(.3)
        for led in range(int(self.ledcount/2)+1):
            self.strip.setPixelColor(led, ledStrip.black)
            if led < (int(self.ledcount/2))-1:
                self.strip.setPixelColor(led+1, Color(0, 0, 100))
                self.strip.setPixelColor(led+2, Color(0, 0, 30))
                self.strip.setPixelColor(self.ledcount-led-1, Color(0, 0, 100))
                self.strip.setPixelColor(self.ledcount-led-2, Color(0, 0, 30))
            self.strip.setPixelColor(self.ledcount-led, ledStrip.black)
            self.strip.show()
            sleep(.02)
    def on(self, color):
        log.debug(f'Led Strip color: {color}')
        self.color = color
        for led in range(self.ledcount):
            self.strip.setPixelColor(led, color)
        self.strip.show()

def ledstrip(*args):
    a = ()
    for each in args:
        a = a + ((each),)
    strip_queue.put(a)

def ledstrip_thread():
    log.debug('Led strip thread is starting')
    stripled = ledStrip()
    while True:
        try:
            if not strip_queue.empty():
                ststatus = strip_queue.get()
                if ststatus[0] == 'color':
                    stripled.on(Color(ststatus[1], ststatus[2], ststatus[3]))
            sleep(.1)
        except:
            log.critical(f'Critical Error in Led Strip Thread', exc_info=True)
            sleep(60)
