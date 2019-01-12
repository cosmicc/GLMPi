from time import sleep
from datetime import datetime
from rpi_ws281x import *
from threads.threadqueues import strip_queue, restapi_queue
from configparser import ConfigParser
from pathlib import Path
from pickle import dump as pdump, load as pload
from modules.timehelper import calcbright
from modules.extras import str2bool, c2f
import modules.rpiboard as rpi
import threading
import logging
import socket

host_name = socket.gethostname()
log = logging.getLogger(name=host_name)

config = ConfigParser()
config.read('/etc/glmpi.conf')
loopdelay = float(config.get('led_strip', 'loopdelay'))

def colorwheel(pos):
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)


def colorDistance(currentColor, targetColor):
    distance = [0, 0, 0]
    for i in range(len(currentColor)):
        distance[i] = abs(currentColor[i] - targetColor[i])
    return distance

def calculateIncrement(distance, fps, duration):
    increment = [0, 0, 0]
    for i in range(len(distance)):
        inc = abs(distance[i] / fps)
        increment[i] = inc
    return increment


def hexPercent(color):
    percent = (color / float(0xFF)) * 100
    return percent


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

    def __init__(self):
        config = ConfigParser()
        config.read('/etc/glmpi.conf')
        self.nightlight = str2bool(config.get('nightlight', 'enabled'))
        self.ledcount = int(config.get('led_strip', 'ledcount'))
        self.invert = str2bool(config.get('led_strip', 'invert'))
        self.channel = int(config.get('led_strip', 'channel'))
        self.frequency = int(config.get('led_strip', 'frequency'))
        self.dma = int(config.get('led_strip', 'dma'))
        self.pin = int(config.get('led_strip', 'pin'))
        self.statefile = config.get('general', 'savestate')
        self.fadespeed = float(config.get('led_strip', 'fadespeed'))
        self.motionlight = str2bool(config.get('motion', 'light'))
        self.rainbowspeed = int(config.get('animations', 'rainbow_speed'))
        self.temp_units = config.get('general', 'temp_units')
        self.cyclehue = 0
        self.tempurature = 0.0
        self.humidity = 0.0
        self.nightlight_color = Color(int(config.get('nightlight', 'red')), int(config.get('nightlight', 'green')), int(config.get('nightlight', 'blue')))
        self.motion = False
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
            self.white = state_dict['white']
            self.brightness = state_dict['brightness']
            self.lastmotion = state_dict['lastmotion']
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
            self.white = Color(255, 255, 255)
            self.brightness = 255
            self.lastmotion = datetime.now()
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
        return f'{self.ledcount} leds, ON:{self.on}, Mode:{self.mode}, Night:{self.night}, Away:{self.away}, Color:{i2rgb(self.color)}, Lastcolor:{self.lastcolor}, Pricolor:{self.pricolor}, is_nightlight:{self.nightlight}, is_illuminated:{self.illuminated}, motion:{self.motion}'

    def info(self):
        if self.temp_units == 'C':
            ttemp = rpi.cpu_temp()
        elif self.temp_units == 'F':
            ttemp = c2f(rpi.cpu_temp())
        return {'hostname': host_name, 'nightlight': self.nightlight, 'ledcount': self.ledcount, 'cputemp': ttemp, 'cyclehue': self.cyclehue, 'statefile': self.statefile, 'brightness': self.brightness, 'mode': self.mode, 'lastmode': self.lastmode, 'away': self.away, 'on': self.on, 'night': self.night, 'color': i2rgb(self.color), 'lastcolor': i2rgb(self.lastcolor), 'pricolor': i2rgb(self.pricolor), 'white': i2rgb(self.white), 'illuminated': self.illuminated, 'tempurature': self.tempurature, 'humidity': self.humidity, 'motion': self.motion, 'lastmotion': self.lastmotion.strftime("%Y-%m-%d %H:%M:%S"), 'uptime': rpi.system_uptime(), 'cpuload': rpi.get_load(), 'memory': rpi.get_freemem(), 'diskspace': rpi.get_diskspace(), 'system': rpi.rpi_info()}

    def transition(self, currentColor, targetColor, duration, fps):
        distance = colorDistance(currentColor, targetColor)
        increment = calculateIncrement(distance, fps, duration)
        for i in range(0, int(fps)):
            ledStrip.transitionStep(self, currentColor, targetColor, increment)
            sleep(duration/fps)

    def transitionStep(self, currentColor, targetColor, increment):
        for i in range(len(currentColor)):
            if currentColor[i] > targetColor[i]:
                currentColor[i] -= increment[i]
                if currentColor[i] <= targetColor[i]:
                    increment[i] = 0
            else:
                currentColor[i] += increment[i]
                if currentColor[i] >= targetColor[i]:
                    increment[i] = 0

        #print(f'r:{int(color[0])} g:{int(color[1])} b:{int(color[2])}')
        ncolor = Color(int(currentColor[0]), int(currentColor[1]), int(currentColor[2]))
        for led in range(self.ledcount):
            self.strip.setPixelColor(led, ncolor)
        self.strip.show()



    def updatebrightness(self):
        newbright = calcbright()
        if self.brightness != newbright and newbright != 0:
            log.info(f'Auto-brightness level change from {self.brightness} to {newbright}')
            self.brightness = newbright
            if not self.night or not self.motion or not self.away or not self.on:
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
        statedata = {'mode': self.mode, 'lastmode': self.lastmode, 'away': self.away, 'on': self.on, 'night': self.night, 'color': self.color, 'lastcolor': self.lastcolor, 'pricolor': self.pricolor, 'white': self.white, 'brightness': self.brightness, 'lastmotion': self.lastmotion}
        outfile = open(self.statefile,'wb')
        pdump(statedata,outfile)
        outfile.close()
        log.debug(f'Saving state data: {statedata}')

    def modeset(self, mode, savestate=True):
        if mode == 1:
            if mode != self.mode:
                log.info(f'Led strip mode {mode} (primary color) started')
                self.mode = mode
            if ledStrip.preprocess(self):
                ledStrip.colorchange(self, self.pricolor, sticky=True, savestate=savestate)
        elif mode == 2:
            if mode != self.mode:
                log.info(f'Led strip mode {mode} (white) started')
                self.mode = mode
            if ledStrip.preprocess(self):
                ledStrip.colorchange(self, self.white, sticky=True, savestate=savestate)
        elif mode == 3:
            if mode != self.mode:
                log.info(f'Led strip mode {mode} (color cycle) started')
                self.mode = mode
            ledStrip.savestate(self)
            ledStrip.processcyclehue(self)
        elif mode == 4:
            if mode != self.mode:
                log.info(f'Led strip mode {mode} (rainbow) started')
                self.mode = mode
            ledStrip.savestate(self)
            if ledStrip.preprocess(self):
                rainbow_thread = threading.Thread(name='rainbow_thread', target=ledStrip.rainbowCycle, args=(self,), daemon = True)
                rainbow_thread.start()
        elif mode == 5:
            if mode != self.mode:
                log.info(f'Led strip mode {mode} (new shit) started')
                self.mode = mode
            if ledStrip.preprocess(self):
                pass
                #ledStrip.rainbowCycle(self)
        else:
            log.warning(f'Invalid mode received: {mode}')

    def colorchange(self, color, sticky=True, blend=True, bright=0, savestate=True):
        if blend:
            r, g, b = i2rgb(color, string=False)
            x, y, z = i2rgb(self.color, string=False)
            ledStrip.transition(self, [x, y, z], [r, g, b], self.fadespeed, 100)
            if bright == 0:
                self.strip.setBrightness(self.brightness)
            else:
                self.strip.setBrightness(bright)
            self.strip.show()
        else:
            for led in range(self.ledcount):
                self.strip.setPixelColor(led, color)
            if bright == 0:
                self.strip.setBrightness(self.brightness)
            else:
                self.strip.setBrightness(bright)
            self.strip.show()

        log.info(f'Led strip color changed to: {i2rgb(color)}')
        if color == ledStrip.black:
            self.illuminated = False
        else:
            self.illuminated = True
        if sticky:
            self.lastcolor = color
        self.color = color
        if savestate:
            ledStrip.savestate(self)

    def processcyclehue(self, chue=999):
        if int(chue) == 999:
            chue = self.cyclehue
        else:
            log.debug(f'Updating cycle hue to: {chue}')
            self.cyclehue = int(chue)
        if self.mode == 3:
            if ledStrip.preprocess(self):
                r, g, b = hsv_to_rgb(int(chue), 100, 100)
                ledStrip.colorchange(self, Color(int(r), int(g), int(b)), sticky=False, blend=False, savestate=False)

    def whitetempchange(self, kelvin):
        bluemin = 40
        kelvinmin = 2000
        kelvinmax  = 6500
        newblue = (((kelvin - kelvinmin) * (255 - bluemin)) / (kelvinmax - kelvinmin)) + bluemin
        self.white = Color(255, 255, int(newblue))
        ledStrip.modeset(self, 2)

    def preprocess(self, force=False):
        log.debug(f'Led strip pre process check running')
        if not self.on or self.away or (self.night and not self.nightlight):
            if self.color != ledStrip.black or force:
                log.info(f'Led Strip shutting OFF')
                ledStrip.colorchange(self, ledStrip.black, sticky=False, savestate=False)
                return False
            return False
        elif self.night and self.nightlight:
            if self.color != self.nightlight_color or force:
                log.info(f'Led Strip turning on nightlight')
                ledStrip.colorchange(self, self.nightlight_color, sticky=False, savestate=False)
                self.strip.setBrightness(255)
                self.strip.show()
                return False
            return False
        elif self.motion and self.motionlight:
            return False
        else:
            return True

    def rainbowCycle(self):
        rwait = (((self.rainbowspeed - 100) * (100 - 1)) / (1 - 100)) + 1
        try:
            log.info(f'Starting rainbow cycle thread with ms delay: {rwait/1000}')
            self.strip.setBrightness(self.brightness)
            while True:
                if self.mode != 4 or self.night or not self.on or self.away or (self.motion and self.motionlight):
                    log.info('Rainbow cycle thread ending')
                    break
                for j in range(256):
                    for i in range(self.ledcount):
                        self.strip.setPixelColor(i, colorwheel((int(i * 256 / self.ledcount) + j) & 255))
                    self.strip.show()
                    if self.mode != 4 or self.night or not self.on or self.away or (self.motion and self.motionlight):
                        break
                    sleep(rwait/1000)
        except:
            log.critical(f'Critical Error in rainbow cycle Thread', exc_info=True)


    def processmotion(self, cmotion):
        self.lastmotion = datetime.now()
        if cmotion == 'on':
            self.motion = True
        elif cmotion == 'off':
            self.motion = False
        else:
            log.error('Error in ledstrip processmotion')
        if self.motion:
            if not self.away:
                ledStrip.colorchange(self, self.white, sticky=False, blend=True, bright=255, savestate=False)
        else:
            if ledStrip.preprocess(self, force=False):
                ledStrip.modeset(self, self.mode, savestate=False)

    def rgbcolor(self, r, g, b):
        newcolor = Color(int(r), int(g), int(b))
        self.pricolor = newcolor
        ledStrip.modeset(self, 1)

    def hsvcolor(self, h, s, v):
       r, g, b = hsv_to_rgb(float(h),float(s),float(v))
       log.warning(f'r: {r} g: {g} b: {b}')
       newcolor = Color(int(r), int(g), int(b))
       self.pricolor = newcolor
       ledStrip.modeset(self, 1)

    def device_enable(self):
        if not self.on:
            self.on = True
            log.info('Device ON')
            if ledStrip.preprocess(self):
                ledStrip.modeset(self, self.mode, savestate=False)
            ledStrip.savestate(self)

    def device_disable(self):
        if self.on:
            self.on = False
            log.info('Device OFF')
            ledStrip.preprocess(self)
            ledStrip.savestate(self)

    def awayon(self):
        if not self.away:
            self.away = True
            log.info('Device AWAY ON')
            ledStrip.preprocess(self)
            ledStrip.savestate(self)

    def awayoff(self):
        if self.away:
            self.away = False
            log.info('Device AWAY OFF')
            if ledStrip.preprocess(self):
                ledStrip.modeset(self, self.mode, savestate=False)
            ledStrip.savestate(self)

    def nighton(self):
        if not self.night:
            self.night = True
            log.info('Device NIGHT ON')
            ledStrip.preprocess(self)
            ledStrip.savestate(self)

    def nightoff(self):
        if self.night:
            self.night = False
            log.info('Device NIGHT OFF')
            if ledStrip.preprocess(self):
                ledStrip.modeset(self, self.mode, savestate=False)
            ledStrip.savestate(self)

    def tempupdate(self, temp, humidity):
        self.tempurature = temp
        self.humidity = humidity

def ledstrip_thread():
    log.info('Led strip thread is starting')
    stripled = ledStrip()
    stripled.startup()
    stime = int(datetime.now().timestamp())
    while True:
        try:
            if not strip_queue.empty():
                ststatus = strip_queue.get()
                log.debug(f'Led strip queue received: {ststatus}')
                if ststatus[1] == 'motion':
                    stripled.processmotion(ststatus[2])
                elif ststatus[1] == 'rgbcolor':
                    stripled.rgbcolor(ststatus[2], ststatus[3], ststatus[4])
                elif ststatus[1] == 'hsvcolor':
                    stripled.hsvcolor(ststatus[2], ststatus[3], ststatus[4])
                elif ststatus[1] == 'enable':
                    stripled.device_enable()
                elif ststatus[1] == 'disable':
                    stripled.device_disable()
                elif ststatus[1] == 'awayon':
                    stripled.awayon()
                elif ststatus[1] == 'awayoff':
                    stripled.awayoff()
                elif ststatus[1] == 'nighton':
                    stripled.nighton()
                elif ststatus[1] == 'nightoff':
                    stripled.nightoff()
                elif ststatus[1] == 'stripoff':
                    stripled.on = False
                    stripled.colorchange(Color(0, 0, 0), sticky=False, blend=False, savestate=False)
                elif ststatus[1] == 'mode':
                    stripled.modeset(int(ststatus[2]))
                elif ststatus[1] == 'getinfo':
                    restapi_queue.put(stripled.info())
                elif ststatus[1] == 'getnight':
                    restapi_queue.put(stripled.night)
                elif ststatus[1] == 'getaway':
                    restapi_queue.put(stripled.away)
                elif ststatus[1] == 'getenable':
                    restapi_queue.put(stripled.on)
                elif ststatus[1] == 'whitetemp':
                    stripled.whitetempchange(int(ststatus[2]))
                elif ststatus[1] == 'getwhitetemp':
                    restapi_queue.put(stripled.white)
                elif ststatus[1] == 'getmode':
                    restapi_queue.put(stripled.mode)
                elif ststatus[1] == 'getcyclehue':
                    restapi_queue.put(stripled.cyclehue)
                elif ststatus[1] == 'cyclehue':
                    stripled.processcyclehue(ststatus[2])
                elif ststatus[1] == 'getrgb':
                    a = {}
                    rc = i2rgb(stripled.pricolor, string=False)
                    a.update({'red': rc[0]})
                    a.update({'green': rc[1]})
                    a.update({'blue': rc[2]})
                    restapi_queue.put(a)
                elif ststatus[1] == 'gethsv':
                    a = {}
                    r, g, b = i2rgb(stripled.pricolor, string=False)
                    h, s, v = rgb_to_hsv(r, g, b)
                    a.update({'hue': h})
                    a.update({'saturation': s})
                    a.update({'value': v})
                    restapi_queue.put(a)
                elif ststatus[1] == 'tempupdate':
                    stripled.tempupdate(ststatus[2],ststatus[3])
                else:
                    log.warning(f'led strip queue message is invalid: {ststatus}')
            if stime+60 < int(datetime.now().timestamp()):
                stime = int(datetime.now().timestamp())
                stripled.updatebrightness()
            sleep(loopdelay)
        except:
            log.critical(f'Critical Error in Led Strip Thread', exc_info=True)
            sleep(60)
