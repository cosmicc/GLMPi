from configparser import ConfigParser
from time import sleep
import logging
import socket
import subprocess
import Adafruit_DHT
from bluepy.btle import Scanner, DefaultDelegate, Peripheral, BTLEDisconnectError
from threads.threadqueues import restapi_queue
from modules.extras import str2bool

host_name = socket.gethostname()
log = logging.getLogger(name=host_name)

config = ConfigParser()
config.read('/etc/glmpi.conf')
loopdelay = int(config.get('temp_sensor', 'loopdelay'))

class tempSensor():
    def __init__(self):
        config = ConfigParser()
        config.read('/etc/glmpi.conf')
        self.sensor_type = config.get('temp_sensor', 'sensor_type')
        self.pin = int(config.get('temp_sensor', 'pin'))
        self.temp = 0
        self.humidity = 0
        if self.sensor_type == "DHT11":
            self.sensor = Adafruit_DHT.DHT11
        elif self.sensor_type == "DHT22":
            self.sensor = Adafruit_DHT.DHT22
        elif self.sensor_type == "AM2302":
            self.sensor = Adafruit_DHT.AM2302
        else:
            log.error(f'1wire temp sensor - invalid sensor type: {self.sensor_type}')
            exit(1)
        log.debug(f'Initialized 1wire temp sensor: {self.sensor_type} on pin: {self.pin}')
    def check(self):
        try:
            hum, tmp = Adafruit_DHT.read_retry(self.sensor, self.pin)
        except:
            log.error(f'Error polling temp/humidity sensor')
        if hum is not None and tmp is not None:
            self.temp = tmp
            self.humidity = hum
            log.debug('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(self.temp, self.humidity))
        else:
            log.warning(f'Failed getting temp/humidity sensor reading')

def tempsensor_thread():
    log.debug('Temp/Humidity thread is starting')
    tempsensor = tempSensor()
    sleep(10)
    while True:
        tempsensor.check()
        sleep(loopdelay)
