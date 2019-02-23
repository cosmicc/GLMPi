import socket
from configparser import ConfigParser

import time
import serial
from loguru import logger as log
from modules.extras import End
from web.masterapi.views import sendrequest
from threads.threadqueues import serial_queue, mqtt_queue

config = ConfigParser()
config.read('/var/opt/ircodes.conf')

def process_serial(buf):
   log.warning(buf) 


class Trinket():
    def __init__(self):
        log.info(f'Initilizing Serial connection')
        self.buffer = ""
        try:
            self.ser = serial.Serial('/dev/ttyS0', 9600)
        except:
            log.exception('Error initilizing Serial connection')

    def listen(self):
        while self.ser.in_waiting > 0:
            bufchar = self.ser.read().decode('ASCII')
            if bufchar != "\\":
                self.buffer = self.buffer + self.ser.read().decode('ASCII')
            elif bufchar == "\\":
                self.ser.read()
                process_serial(self.buffer)
                self.buffer = ""

def irreader_thread():
    log.info('Serial communication thread is starting')
    ser = Trinket()
    while True:
        try:
            ser.listen()
        except:
            log.exception(f'Exception in Serial Thread', exc_info=True)
            End('Exception in Serial thread')
    End('Serial thread loop ended prematurely')
