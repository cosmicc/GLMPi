from configparser import ConfigParser
from time import sleep
from loguru import logging
from socket import gethostname
import Adafruit_DHT
from threads.threadqueues import strip_queue
from modules.extras import c2f, float_trunc_1dec, End

host_name = gethostname()
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
        self.units = config.get('general', 'temp_units')
        self.temp = 0.0
        self.humidity = 0.0
        if self.sensor_type == "DHT11":
            self.sensor = Adafruit_DHT.DHT11
        elif self.sensor_type == "DHT22":
            self.sensor = Adafruit_DHT.DHT22
        elif self.sensor_type == "AM2302":
            self.sensor = Adafruit_DHT.AM2302
        else:
            log.error(f'1wire temp sensor - invalid sensor type: {self.sensor_type}')
            exit(1)
        log.info(f'Initialized 1wire temp sensor: {self.sensor_type} on pin: {self.pin}')

    def check(self):
        try:
            hum, tmp = Adafruit_DHT.read_retry(self.sensor, self.pin)
        except:
            log.error(f'Error polling temp/humidity sensor')
        if hum is not None and tmp is not None:
            if self.units == 'C':
                self.temp = float_trunc_1dec(tmp)
            elif self.units == 'F':
                self.temp = float_trunc_1dec(c2f(tmp))
            else:
                log.error(f'Invalid temp units in config file {self.units}')
            self.humidity = float_trunc_1dec(hum)
            strip_queue.put((20, 'tempupdate', self.temp, self.humidity))
            log.debug(f'Tempurature={self.temp}*{self.units}  Humidity={self.humidity}%')
        else:
            log.warning(f'Failed getting temp/humidity sensor reading')


def tempsensor_thread():
    log.info('Temp/Humidity thread is starting')
    tempsensor = tempSensor()
    sleep(10)
    while True:
        try:
            tempsensor.check()
            sleep(loopdelay)
        except:
            log.critical('Exception in temp sensor thread', exc_info=True)
            End('Exception in temp sensor thread')
    End('Temp Sensor thread loop ended prematurely')
