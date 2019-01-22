from time import sleep
from datetime import datetime
from configparser import ConfigParser
from modules.extras import str2bool, End
from loguru import logger as log
import socket

config = ConfigParser()
config.read('/etc/glmpi.conf')
loopdelay = float(config.get('irreader', 'loopdelay'))
motionlight = str2bool(config.get('motion', 'light'))


class irReader():
    def __init__(self):
        log.info(f'Initilizing IR sensor reciever')
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect("/var/run/lirc/lircd")
        except:
            log.exception('Error initilizing IR sensor')

    def listen(self):
        data = sock.recv(128)
        data = data.strip()
        if data:
            return data.split()[2].decode()


def irreader_thread():
    log.info('IR sensor reciever thread is starting')
    ir = irReader()
    while True:
        try:
            sleep(loopdelay)
        except:
            log.exception(f'Exception in Motion Detection Thread', exc_info=True)
            End('Exception in Motion Detection thread')
    End('Motion Detection thread loop ended prematurely')
