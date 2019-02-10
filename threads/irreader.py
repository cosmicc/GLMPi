import socket
from configparser import ConfigParser

from loguru import logger as log
from modules.extras import End
from web.masterapi.views import sendrequest
from threads.threadqueues import mqtt_queue

config = ConfigParser()
config.read('/etc/glmpi.conf')


class irReader():
    def __init__(self):
        log.info(f'Initilizing IR sensor reciever')
        self.lastcode = None
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect("/var/run/lirc/lircd")
        except:
            log.exception('Error initilizing IR sensor')

    def listen(self):
        data = self.sock.recv(128)
        data = data.strip()
        if data:
            rdata = data.split()[2].decode()
            if rdata == self.lastcode:
                return None
            else:
                self.lastcode = rdata
                return rdata


def irreader_thread():
    log.info('IR sensor reciever thread is starting')
    ir = irReader()
    while True:
        try:
            ircode = ir.listen()
            if ircode == 'KEY_POWER':
                log.info('POWER ON recieved from IR')
                sendrequest('away', away='off')
                mqtt_queue.put((1, ['smartthings/Away Mode/switch', 'off']))
            elif ircode == 'KEY_POWER2':
                log.info('POWER OFF recieved from IR')
                sendrequest('away', away='on')
                mqtt_queue.put((1, ['smartthings/Away Mode/switch', 'on']))
            elif ircode == 'KEY_UP':
                log.info('BRIGHT UP recieved from IR')
                sendrequest('night', night='off')
                mqtt_queue.put((1, ['smartthings/Night Mode/switch', 'off']))
            elif ircode == 'KEY_DOWN':
                log.info('BRIGHT DOWN recieved from IR')
                sendrequest('night', night='on')
                mqtt_queue.put((1, ['smartthings/Night Mode/switch', 'on']))
            elif ircode == 'KEY_RED':
                log.info('RED recieved from IR')
                sendrequest('rgbcolor', red=255, green=0, blue=0)
            elif ircode == 'KEY_GREEN':
                log.info('GREEN recieved from IR')
                sendrequest('rgbcolor', red=0, green=255, blue=0)
            elif ircode == 'KEY_BLUE':
                log.info('BLUE recieved from IR')
                sendrequest('rgbcolor', red=0, green=0, blue=255)
            elif ircode == 'KEY_W':
                log.info('WHITE recieved from IR')
                sendrequest('mode', mode=2)
            elif ircode == 'KEY_PROG1':
                log.info('CYCLE COLOR recieved from IR')
                sendrequest('mode', mode=3)
            elif ircode == 'KEY_PROG2':
                log.info('RAINBOW recieved from IR')
                sendrequest('mode', mode=3)
            elif ircode == 'KEY_PROG3':
                log.info('PROG3 recieved from IR')
                sendrequest('mode', mode=4)
            elif ircode == 'KEY_PROG4':
                log.info('PROG4 recieved from IR')
            elif ircode == 'KEY_F1':
                log.info('COLOR1 recieved from IR')
                sendrequest('rgbcolor', red=255, green=127, blue=0)
            elif ircode == 'KEY_F2':
                log.info('COLOR2 recieved from IR')
                sendrequest('rgbcolor', red=63, green=255, blue=25)
            elif ircode == 'KEY_F3':
                log.info('COLOR3 recieved from IR')
                sendrequest('rgbcolor', red=0, green=84, blue=255)
            elif ircode == 'KEY_F4':
                log.info('COLOR4 recieved from IR')
                sendrequest('rgbcolor', red=255, green=63, blue=0)
            elif ircode == 'KEY_F5':
                log.info('COLOR5 recieved from IR')
                sendrequest('rgbcolor', red=0, green=255, blue=212)
            elif ircode == 'KEY_F6':
                log.info('COLOR6 recieved from IR')
                sendrequest('rgbcolor', red=42, green=0, blue=255)
            elif ircode == 'KEY_F7':
                log.info('COLOR7 recieved from IR')
                sendrequest('rgbcolor', red=255, green=38, blue=218)
            elif ircode == 'KEY_F8':
                log.info('COLOR8 recieved from IR')
                sendrequest('rgbcolor', red=0, green=255, blue=127)
            elif ircode == 'KEY_F9':
                log.info('COLOR9 recieved from IR')
                sendrequest('rgbcolor', red=127, green=0, blue=255)
            elif ircode == 'KEY_F10':
                log.info('COLOR10 recieved from IR')
                sendrequest('rgbcolor', red=255, green=233, blue=0)
            elif ircode == 'KEY_F11':
                log.info('COLOR11 recieved from IR')
                sendrequest('rgbcolor', red=0, green=100, blue=80)
            elif ircode == 'KEY_F12':
                log.info('COLOR12 recieved from IR')
                sendrequest('rgbcolor', red=212, green=0, blue=255)
            else:
                log.debug(f'INVALID CODE [{ircode}] recieved from IR')
        except:
            log.exception(f'Exception in IR reader Thread', exc_info=True)
            End('Exception in IR reader thread')
    End('IR reader thread loop ended prematurely')
