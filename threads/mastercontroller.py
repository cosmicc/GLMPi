from configparser import ConfigParser
from time import sleep

from timeit import default_timer as timer
from loguru import logger as log
from modules.extras import End
from threads.ledstrip import hsv_to_rgb
from web.masterapi.views import sendrequest
import paho.mqtt.client as mqtt

config = ConfigParser()
config.read('/etc/glmpi.conf')
cycledelay = int(config.get('master_controller', 'cycledelay'))
loopdelay = float(config.get('master_controller', 'loopdelay'))
presencetime = float(config.get('master_controller', 'presence_away_check'))
mqtt_server = config.get('master_controller', 'mqtt_server')


def check_presence_away():
    pass


def mastercontroller_thread():
    cyclespeedtime = timer()
    log.info('Master Controller thread is starting')
    hue = 0
    pchecktime = timer()
    client = mqtt.Client(client_id='GLM-MASTER')
    log.info('Connecting to MQTT Server...')
    try:
        client.connect(mqtt_server, 1883, 60)
    except ConnectionRefusedError:
        log.error('Error connecting to MQTT server')
    sleep(10)
    client.loop_start()
    while True:
        try:
            if cyclespeedtime + cycledelay < timer():
                cyclespeedtime = timer()
                if hue == 359:
                    hue = 0
                else:
                    hue += 1
                log.debug(f'Sending new hue {hue} to all controllers')
                sendrequest('cyclehue', hue=hue)
                r, g, b = hsv_to_rgb(hue, 100, 100)
                client.publish('glm/color', payload='%s, %s, %s' % (r, g, b), retain=False, qos=0)

            if pchecktime + presencetime < timer():
                pchecktime = timer()
                check_presence_away()

            sleep(loopdelay)
        except:
            log.exception('Exception in master controller thread', exc_info=True)
            End('Exception in master controller thread')
    End('Master contoller loop ended prematurely')
