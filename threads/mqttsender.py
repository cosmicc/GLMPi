from time import sleep

from configparser import ConfigParser
from loguru import logger as log
from modules.extras import End
from threads.threadqueues import mqtt_queue
import paho.mqtt.client as mqtt
from socket import gethostname

host_name = gethostname()

config = ConfigParser()
config.read('/etc/glmpi.conf')
mqtt_server = config.get('master_controller', 'mqtt_server')


def mqtt_sender_thread():
    log.info('mqtt sender thread is starting')
    client = mqtt.Client(client_id=f'{host_name}cl')
    log.info('Connecting to MQTT Server...')
    try:
        client.connect(mqtt_server, 1883, 60)
    except ConnectionRefusedError:
        log.error('Error connecting to MQTT server')
    sleep(10)
    client.loop_start()
    while True:
        try:
            mqtt_msg = mqtt_queue.get()
            log.debug(f'Sending MQTT msg: {mqtt_msg}')
            client.publish(mqtt_msg[1][0], payload=mqtt_msg[1][1], retain=False, qos=0)
        except:
            log.exception('Exception in mqtt sender thread', exc_info=True)
            End('Exception in mqtt sender thread')
    End('MQTT sender loop ended prematurely')
