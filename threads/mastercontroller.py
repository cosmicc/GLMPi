from configparser import ConfigParser
from time import sleep
from loguru import logger
from datetime import datetime
from modules.extras import End
from web.masterapi.views import sendrequest

log = logger()

config = ConfigParser()
config.read('/etc/glmpi.conf')
cycledelay = int(config.get('master_controller', 'cycledelay'))
loopdelay = int(config.get('master_controller', 'loopdelay'))


def mastercontroller_thread():
    cyclespeedtime = datetime.now().timestamp()
    log.info('Master Controller thread is starting')
    hue = 0
    while True:
        try:
            if cyclespeedtime + cycledelay < datetime.now().timestamp():
                cyclespeedtime = datetime.now().timestamp()
                if hue == 359:
                    hue = 0
                else:
                    hue += 1
                log.debug(f'Sending new hue {hue} to all controllers')
                sendrequest('cyclehue', 'hue', hue)

            sleep(loopdelay)
        except:
            log.critical('Exception in master controller thread', exc_info=True)
            End('Exception in master controller thread')
    End('Master contoller loop ended prematurely')
