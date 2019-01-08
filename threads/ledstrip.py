from time import sleep
from rpi_ws281x import *
from threads.threadqueues import strip_queue
from configparser import ConfigParser
from pathlib import Path
from pickle import dump as pdump, load as pload
import threading
import logging
import socket

host_name = socket.gethostname()
log = logging.getLogger(name=host_name)

config = ConfigParser()
config.read('/etc/glmpi.conf')
loopdelay = float(config.get('led_strip', 'cmddelay'))

def hsv_to_rgb(h, s, v):
    h = h / 360.
    v = ( v / float(100) ) * 1
    if s == 0.0: v*=255; return (v, v, v)
    i = int(h*6.) # XXX assume int() truncates!
    f = (h*6.)-i; p,q,t = int(255*(v*(1.-s))), int(255*(v*(1.-s*f))), int(255*(v*(1.-s*(1.-f)))); v*=255; i%=6
    if i == 0: return (v, t, p)
    if i == 1: return (q, v, p)
    if i == 2: return (p, v, t)
    if i == 3: return (p, q, v)
    if i == 4: return (t, p, v)
    if i == 5: return (v, p, q)

class ledStrip():
    black = Color(0, 0, 0)
    blue = Color(0, 0, 255)
    nlcolor = Color(220, 10, 0)

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

        self.statefile = config.get('general', 'savestate')

        if Path(self.statefile).is_file():
            infile = open(self.statefile,'rb')
            state_dict = pload(infile)
            infile.close()
            self.mode = state_dict['mode']
            self.lastmode = state_dict['lastmode']
            self.away = state_dict['away']
            self.on = state_dict['on']
            self.night = state_dict['night']
            self.color = state_dict['color']
            self.lastcolor = state_dict['lastcolor']
            log.debug(f'Savestate file found with data: {state_dict}')
        else:
            self.mode = 1
            self.lastmode = 0
            self.away = False
            self.on = True
            self.night = False
            self.color = Color(0, 0, 0)
            self.lastcolor = Color(0, 0, 0)
            log.debug('NO savestate file found, using defaults')

        self.illuminated = False
        strip = Adafruit_NeoPixel(self.ledcount, self.pin, self.frequency, self.dma, False, 255, self.channel)
        self.strip = strip
        self.strip.begin()
        for led in range(self.ledcount):
            self.strip.setPixelColor(led, ledStrip.black)
        self.strip.show()

    def startup(self):
        self.illuminated = True
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
        self.illuminated = False
        if ledStrip.preprocess(self):
            ledStrip.color(self, self.lastcolor, sticky=False)

    def savestate(self):
        statedata = {'mode': self.mode, 'lastmode': self.lastmode, 'away': self.away, 'on': self.on, 'night': self.night, 'color': self.color, 'lastcolor': self.lastcolor}
        outfile = open(self.statefile,'wb')
        pdump(statedata,outfile)
        outfile.close()
        log.debug(f'Saving state data: {statedata}')


    def color(self, color, sticky=True):
        for led in range(self.ledcount):
            self.strip.setPixelColor(led, color)
        self.strip.show()
        log.debug(f'Led strip color: {color}')
        if color == ledStrip.black:
            self.illuminated = False
        else:
            self.illuminated = True
        if sticky:
            self.lastcolor = self.color
        self.color = color
        ledStrip.savestate(self)

    def preprocess(self):
        log.debug(f'Led Strip pre process')
        if not self.on or self.away or (self.night and not self.nightlight):
            if self.color != ledStrip.black:
                log.info(f'Led Strip shutting OFF')
                ledStrip.color(self, ledStrip.black, sticky=False)
                return False
            return False
        elif self.night and self.nightlight:
            if self.color != ledStrip.nlcolor:
                log.info(f'Led Strip turning on nightlight')
                ledStrip.color(self, ledStrip.nlcolor, sticky=False)
                return False
            return False
        else:
            return True

    def rgbcolor(self, r, g, b):
        newcolor = Color(int(r), int(g), int(b))
        if newcolor != self.color:
            if ledStrip.preprocess(self):
                ledStrip.color(self, newcolor)

    def hsvcolor(self, h, s, v):
       r, g, b = hsv_to_rgb(float(h),float(s),float(v))
       newcolor = Color(r, g, b)
       if newcolor != self.color:
            if ledStrip.preprocess(self):
                ledStrip.color(self, newcolor)

    def pon(self):
        if self.on == False:
            self.on = True
            log.info('Device ON')
            if ledStrip.preprocess(self):
                ledStrip.color(self, self.lastcolor)

    def poff(self):
        if self.on == True:
            self.on = False
            log.info('Device OFF')
            ledStrip.preprocess(self)

def ledstrip(*args):
    a = ()
    for each in args:
        a = a + ((each),)
    strip_queue.put(a)

def ledstrip_thread():
    log.debug('Led strip thread is starting')
    stripled = ledStrip()
    stripled.startup()
    while True:
        try:
            if not strip_queue.empty():
                ststatus = strip_queue.get()
                if ststatus[0] == 'rgbcolor':
                    stripled.rgbcolor(ststatus[1], ststatus[2], ststatus[3])
                if ststatus[0] == 'hsvcolor':
                    stripled.hsvcolor(ststatus[1], ststatus[2], ststatus[3])
                if ststatus[0] == 'on':
                    stripled.pon()
                if ststatus[0] == 'off':
                    stripled.poff()
            sleep(loopdelay)
        except:
            log.critical(f'Critical Error in Led Strip Thread', exc_info=True)
            sleep(60)
