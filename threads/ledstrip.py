from time import sleep
from datetime import datetime
from rpi_ws281x import *
from threads.threadqueues import strip_queue, restapi_queue
from configparser import ConfigParser
from pathlib import Path
from pickle import dump as pdump, load as pload
from modules.timehelper import calcbright
import threading
import logging
import socket

host_name = socket.gethostname()
log = logging.getLogger(name=host_name)

config = ConfigParser()
config.read('/etc/glmpi.conf')
loopdelay = float(config.get('led_strip', 'cmddelay'))

def i2rgb(RGBint, string=True):
    blue =  RGBint & 255
    green = (RGBint >> 8) & 255
    red =   (RGBint >> 16) & 255
    if string:
        return f'({red}, {green}, {blue})'
    else:
        return (red, green, blue)

def hsv_to_rgb(h, s, v):
    h = h / 360.
    s = (s / float(100) ) * 1
    v = (v / float(100) ) * 1
    if s == 0.0: v*=255; return (v, v, v)
    i = int(h*6.)
    f = (h*6.)-i; p,q,t = int(255*(v*(1.-s))), int(255*(v*(1.-s*f))), int(255*(v*(1.-s*(1.-f)))); v*=255; i%=6
    if i == 0: return (v, t, p)
    if i == 1: return (q, v, p)
    if i == 2: return (p, v, t)
    if i == 3: return (p, q, v)
    if i == 4: return (t, p, v)
    if i == 5: return (v, p, q)

def rgb_to_hsv(r, g, b):
    r, g, b = r/255.0, g/255.0, b/255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx-mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g-b)/df) + 360) % 360
    elif mx == g:
        h = (60 * ((b-r)/df) + 120) % 360
    elif mx == b:
        h = (60 * ((r-g)/df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = (df/mx)*100
    v = mx*100
    return h, s, v

class ledStrip():
    black = Color(0, 0, 0)
    blue = Color(0, 0, 255)
    nlcolor = Color(20, 10, 0) # Nightlight color

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
        self.cyclecolor = Color(0, 0, 0)
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
            self.pricolor = state_dict['pricolor']
            self.whitetemp = state_dict['whitetemp']
            self.brightness = state_dict['brightness']
            log.debug(f'Savestate file found with data: {state_dict}')
        else:
            self.mode = 1
            self.lastmode = 0
            self.away = False
            self.on = True
            self.night = False
            self.color = Color(0, 0, 0)
            self.lastcolor = Color(0, 0, 0)
            self.pricolor = Color(0, 0, 0)
            self.whitetemp = 6500
            self.brightness = 255
            log.debug('NO savestate file found, using defaults')
        strip = Adafruit_NeoPixel(self.ledcount, self.pin, self.frequency, self.dma, False, 255, self.channel)
        self.strip = strip
        self.strip.begin()
        for led in range(self.ledcount):
            self.strip.setPixelColor(led, ledStrip.black)
        self.strip.show()
        ledStrip.updatebrightness(self)
        self.illuminated = False

    def __repr__(self):
        return f'<ledStrip object on pin:{self.pin} dma:{self.dma} channel:{self.channel}>'

    def __str__(self):
        return f'{self.ledcount} leds, ON:{self.on}, Mode:{self.mode}, Night:{self.night}, Away:{self.away}, Color:{i2rgb(self.color)}, Lastcolor:{self.lastcolor}, Pricolor:{self.pricolor}, is_nightlight:{self.nightlight}, is_illuminated:{self.illuminated}'

    def info(self):
        return {'hostname': host_name, 'nightlight': self.nightlight, 'ledcount': self.ledcount, 'invert': self.invert, 'channel': self.channel, 'frequency': self.frequency, 'dma': self.dma, 'pin': self.pin, 'cyclecolor': i2rgb(self.cyclecolor), 'statefile': self.statefile, 'brightness': self.brightness, 'mode': self.mode, 'lastmode': self.lastmode, 'away': self.away, 'on': self.on, 'night': self.night, 'color': i2rgb(self.color), 'lastcolor': i2rgb(self.lastcolor), 'pricolor': i2rgb(self.pricolor), 'whitetemp': self.whitetemp, 'illuminated': self.illuminated}

    def updatebrightness(self):
        newbright = calcbright()
        if self.brightness != newbright and newbright != 0:
            log.info(f'Auto-brightness level change from {self.brightness} to {newbright}')
            self.brightness = newbright
            self.strip.setBrightness(self.brightness)
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

        sleep(2)

        if ledStrip.preprocess(self, force=True):
            ledStrip.modeset(self, self.mode, savestate=False)

    def savestate(self):
        statedata = {'mode': self.mode, 'lastmode': self.lastmode, 'away': self.away, 'on': self.on, 'night': self.night, 'color': self.color, 'lastcolor': self.lastcolor, 'pricolor': self.pricolor, 'whitetemp': self.whitetemp, 'brightness': self.brightness}
        outfile = open(self.statefile,'wb')
        pdump(statedata,outfile)
        outfile.close()
        log.debug(f'Saving state data: {statedata}')

    def modeset(self, mode, savestate=True):
        if mode == 1:
            log.info(f'Led strip mode {mode} started')
            self.mode = mode
            if ledStrip.preprocess(self):
                 ledStrip.colorchange(self, self.pricolor, sticky=True, savestate=savestate)
        elif mode == 2:
            log.info(f'Led strip mode {mode} started')
            self.mode = mode
            if ledStrip.preprocess(self):
                ledStrip.whitetempchange(self.whitetemp, sticky=True, savestate=savestate)
        elif mode == 3:
            log.info(f'Led strip mode {mode} started')
            self.mode = mode
            if ledStrip.preprocess(self):
                ledStrip.colorchange(self, self.cyclecolor, sticky=False, savestate=savestate)
        else:
            log.warning(f'Invalid mode received: {mode}')

    def colorchange(self, color, sticky=True, savestate=True):
        for led in range(self.ledcount):
            self.strip.setPixelColor(led, color)
        self.strip.show()
        log.debug(f'Led strip color changed to: {i2rgb(color)}')
        ledStrip.updatebrightness(self)
        if color == ledStrip.black:
            self.illuminated = False
        else:
            self.illuminated = True
        if sticky:
            self.lastcolor = color
        self.color = color
        if savestate:
            ledStrip.savestate(self)

    def whitetempchange(self, whiteness): # 2000 - 6500 
        bluemin = 40
        whitemin = 2000
        whitemax  = 6500
        self.whitetemp = whiteness
        newvalue = (((whiteness - whitemin) * (255 - bluemin)) / (whitemax - whitemin)) + bluemin
        ledStrip.colorchange(self, Color(255, 255, int(newvalue)), sticky=True, savestate=True)

    def preprocess(self, force=False):
        log.debug(f'Led strip pre process check running')
        if not self.on or self.away or (self.night and not self.nightlight):
            if self.color != ledStrip.black or force:
                log.info(f'Led Strip shutting OFF')
                ledStrip.colorchange(self, ledStrip.black, sticky=False, savestate=False)
                return False
            return False
        elif self.night and self.nightlight:
            if self.color != ledStrip.nlcolor or force:
                log.info(f'Led Strip turning on nightlight')
                ledStrip.colorchange(self, ledStrip.nlcolor, sticky=False, savestate=False)
                self.strip.setBrightness(255)
                self.strip.show()
                return False
            return False
        else:
            return True

    def rgbcolor(self, r, g, b):
        newcolor = Color(int(r), int(g), int(b))
        self.pricolor = newcolor
        if newcolor != self.color:
            if ledStrip.preprocess(self):
                ledStrip.colorchange(self, newcolor)

    def hsvcolor(self, h, s, v):
       r, g, b = hsv_to_rgb(float(h),float(s),float(v))
       log.warning(f'r: {r} g: {g} b: {b}')
       newcolor = Color(int(r), int(g), int(b))
       self.pricolor = newcolor
       if newcolor != self.color:
            if ledStrip.preprocess(self):
                ledStrip.colorchange(self, newcolor)

    def cyclecolorhue(self, hue):
       r, g, b = hsv_to_rgb(float(hue),1.0,100.0)
       self.cyclecolor = Color(r, g, b)
       if self.cyclecolor != self.color and self.mode == 1:
            if ledStrip.preprocess(self):
                ledStrip.colorchange(self, self.cyclecolor, sticky=False, savestate=False)

    def device_enable(self):
        if self.on == False:
            self.on = True
            log.info('Device ON')
            if ledStrip.preprocess(self):
                ledStrip.modeset(self, self.mode, savestate=False)
            ledStrip.savestate(self)

    def device_disable(self):
        if self.on == True:
            self.on = False
            log.info('Device OFF')
            ledStrip.preprocess(self)
            ledStrip.savestate(self)

    def awayon(self):
        if self.away == False:
            self.away = True
            log.info('Device AWAY ON')
            ledStrip.preprocess(self)
            ledStrip.savestate(self)

    def awayoff(self):
        if self.away == True:
            self.away = False
            log.info('Device AWAY OFF')
            if ledStrip.preprocess(self):
                ledStrip.modeset(self, self.mode, savestate=False)
            ledStrip.savestate(self)

    def nighton(self):
        if self.night == False:
            self.night = True
            log.info('Device NIGHT ON')
            ledStrip.preprocess(self)
            ledStrip.savestate(self)

    def nightoff(self):
        if self.night == True:
            self.night = False
            log.info('Device NIGHT OFF')
            if ledStrip.preprocess(self):
                ledStrip.modeset(self, self.mode, savestate=False)
            ledStrip.savestate(self)


def ledstrip(*args):
    a = ()
    for each in args:
        a = a + ((each),)
    strip_queue.put(a)

def ledstrip_thread():
    log.debug('Led strip thread is starting')
    stripled = ledStrip()
    stripled.startup()
    stime = int(datetime.now().timestamp())
    while True:
        try:
            if not strip_queue.empty():
                ststatus = strip_queue.get()
                log.debug(f'Led strip queue received: {ststatus}')
                if ststatus[0] == 'rgbcolor':
                    stripled.rgbcolor(ststatus[1], ststatus[2], ststatus[3])
                elif ststatus[0] == 'hsvcolor':
                    stripled.hsvcolor(ststatus[1], ststatus[2], ststatus[3])
                elif ststatus[0] == 'enable':
                    stripled.device_enable()
                elif ststatus[0] == 'disable':
                    stripled.device_disable()
                elif ststatus[0] == 'awayon':
                    stripled.awayon()
                elif ststatus[0] == 'awayoff':
                    stripled.awayoff()
                elif ststatus[0] == 'nighton':
                    stripled.nighton()
                elif ststatus[0] == 'nightoff':
                    stripled.nightoff()
                elif ststatus[0] == 'stripoff':
                    stripled.colorchange(Color(0, 0, 0), sticky=False, savestate=False)
                elif ststatus[0] == 'mode':
                    stripled.modeset(int(ststatus[0]))
                elif ststatus[0] == 'getinfo':
                    restapi_queue.put(stripled.info())
                elif ststatus[0] == 'getnight':
                    restapi_queue.put(stripled.night)
                elif ststatus[0] == 'getaway':
                    restapi_queue.put(stripled.away)
                elif ststatus[0] == 'getenable':
                    restapi_queue.put(stripled.on)
                elif ststatus[0] == 'whitetemp':
                    stripled.whitetempchange(int(ststatus[1]))
                elif ststatus[0] == 'getrgb':
                    a = {}
                    rc = i2rgb(stripled.color, string=False)
                    a.update({'red': rc[0]})
                    a.update({'green': rc[1]})
                    a.update({'blue': rc[2]})
                    restapi_queue.put(a)
                elif ststatus[0] == 'gethsv':
                    a = {}
                    r, g, b = i2rgb(stripled.color, string=False)
                    h, s, v = rgb_to_hsv(r, g, b)
                    a.update({'hue': h})
                    a.update({'saturation': s})
                    a.update({'value': v})
                    restapi_queue.put(a)
                else:
                    log.warning(f'led strip queue message is invalid: {ststatus}')
            if stime+60 < int(datetime.now().timestamp()):
                stime = int(datetime.now().timestamp())
                stripled.updatebrightness()
            sleep(loopdelay)
        except:
            log.critical(f'Critical Error in Led Strip Thread', exc_info=True)
            sleep(60)
