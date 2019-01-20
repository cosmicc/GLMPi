from time import sleep
from datetime import datetime
from threads.threadqueues import strip_queue
from configparser import ConfigParser
from modules.extras import str2bool, End
import RPi.GPIO as GPIO
import logging
from socket import gethostname

config = ConfigParser()
config.read('/etc/glmpi.conf')
loopdelay = float(config.get('motion', 'loopdelay'))
mdelay = int(config.get('motion', 'stopdelay'))
stoploopdelay = float(config.get('motion', 'stoploopdelay'))
isenabled = str2bool(config.get('motion', 'enabled'))
warmupdelay = int(config.get('motion', 'warmupdelay'))
motionlight = str2bool(config.get('motion', 'light'))

host_name = gethostname()
log = logging.getLogger(name=host_name)


class motionPir():
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self.mode = GPIO.getmode()
        GPIO.setwarnings(True)
        self.channel = 12
        self.inmotion = False
        self.lastmotion_timestamp = 0
        GPIO.setup(self.channel, GPIO.IN)

    def __repr__(self):
        return f'<motionPir object on bcmpin:{self.channel} mode:{self.mode}>'

    def __str__(self):
        return f'MotionPIR - BCMPin:{self.channel}, Mode:{self.mode}'

    def getmotion(self):
        self.inmotion = bool(GPIO.input(self.channel))
        if self.inmotion:
            self.lastmotion_timestamp = datetime.now().timestamp()
        return self.inmotion


def motionpir_thread():
    log.info('Motion detection thread is starting')
    motion_sensor = motionPir()
    log.info(f'Waiting {warmupdelay} seconds for PIR warmup delay')
    sleep(warmupdelay)
    log.info('PIR warmup complete. Starting motion detection loop')
    while True:
        try:
            if motion_sensor.getmotion():
                # START MOTION ROUTINE
                if motionlight:
                    strip_queue.put((0, 'motion', 'on'))
                #
                log.debug('* Motion Detected *')
                while motion_sensor.lastmotion_timestamp + mdelay > datetime.now().timestamp():
                    sleep(stoploopdelay)
                    motion_sensor.getmotion()
                # STOP MOTION ROUTINE
                if motionlight:
                    strip_queue.put((0, 'motion', 'off'))
                #
                log.debug('* Motion Stopped *')
            sleep(loopdelay)
        except:
            log.critical(f'Exception in Motion Detection Thread', exc_info=True)
            End('Exception in Motion Detection thread')
    End('Motion Detection thread loop ended prematurely')
