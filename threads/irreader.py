from time import sleep
from configparser import ConfigParser
from modules.extras import End
from loguru import logger as log
import socket

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
            if ircode == 'KEY_RED':
                log.warning('RED!!!!')
        except:
            log.exception(f'Exception in Motion Detection Thread', exc_info=True)
            End('Exception in Motion Detection thread')
    End('Motion Detection thread loop ended prematurely')
