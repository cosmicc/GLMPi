from configparser import ConfigParser
from time import sleep

from timeit import default_timer as timer
from loguru import logger as log
from modules.extras import End
from modules.timehelper import calcbright
from threads.ledstrip import hsv_to_rgb
from threads.threadqueues import mqtt_queue
from web.masterapi.views import sendrequest

config = ConfigParser()
config.read('/etc/glmpi.conf')
cycledelay = int(config.get('master_controller', 'cycledelay'))
loopdelay = float(config.get('master_controller', 'loopdelay'))
presencetime = float(config.get('master_controller', 'presence_away_check'))

brightness = 255

def check_presence_away():
    pass


def mastercontroller_thread():
    global brightness
    cyclespeedtime = timer()
    log.info('Master Controller thread is starting')
    hue = 0
    pchecktime = timer()
    while True:
#        if not master_controller_queue.empty():
#            bget = master_controller_queue.get()
#            log.debug(f'Master Controller queue received: {bget}')

#            brightness = bget[1]
        try:
            if cyclespeedtime + cycledelay < timer():
                cyclespeedtime = timer()
                if hue == 359:
                    hue = 0
                else:
                    hue += 1
                log.debug(f'Sending new hue {hue} to all devices')
                sendrequest('cyclehue', hue=hue)
                brightness = calcbright()
                if brightness == 255:
                    brightness = 100
                elif brightness == 191:
                    brightness = 75
                elif brightness == 127:
                    brightness = 50
                elif brightness == 64:
                    brightness = 25
                r, g, b = hsv_to_rgb(hue, 100, brightness)
                msg = ['glm/color', f'{int(r)}, {int(g)}, {int(b)}']
                mqtt_queue.put((5, msg))

            if pchecktime + presencetime < timer():
                pchecktime = timer()
                check_presence_away()

            sleep(loopdelay)
        except:
            log.exception('Exception in master controller thread', exc_info=True)
            End('Exception in master controller thread')
    End('Master contoller loop ended prematurely')
