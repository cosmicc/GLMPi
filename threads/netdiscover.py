from time import sleep
from datetime import datetime
from threads.threadqueues import strip_queue
from configparser import ConfigParser
from modules.extras import str2bool, End
from loguru import logger as log

config = ConfigParser()
config.read('/etc/glmpi.conf')
loopdelay = float(config.get('network_discovery', 'loopdelay'))
discover_timeout = int(config.get('network_discovery', 'timeout'))


class networkDiscovery():
    def __init__(self):
        self.master = None
        self.slaves = None



    def __repr__(self):
        return f'<motionPir object on bcmpin:{self.channel} mode:{self.mode}>'

    def __str__(self):
        return f'MotionPIR - BCMPin:{self.channel}, Mode:{self.mode}'

    def getmotion(self):
        self.inmotion = bool(GPIO.input(self.channel))
        if self.inmotion:
            self.lastmotion_timestamp = datetime.now().timestamp()
        return self.inmotion


def discovery_thread():
    log.info('Network discovery thread is starting')
    discovery = networkDiscovery()
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
            log.exception(f'Exception in Motion Detection Thread', exc_info=True)
            End('Exception in Motion Detection thread')
    End('Motion Detection thread loop ended prematurely')
