import socket
import json
import threading
from time import sleep
from datetime import datetime
from threads.threadqueues import strip_queue
from configparser import ConfigParser
from modules.extras import str2bool, End
from loguru import logger as log
from queue import SimpleQueue

discovery_queue = SimpleQueue()

config = ConfigParser()
config.read('/etc/glmpi.conf')

is_master = str2bool(config.get('master_controller', 'enabled'))
loopdelay = float(config.get('network_discovery', 'loopdelay'))
salt = int(config.get('network_discovery', 'bcast_salt'))


def dict_to_binary(the_dict):
    str = json.dumps(the_dict)
    binary = ' '.join(format(ord(letter), 'b') for letter in str)
    return binary


def binary_to_dict(the_binary):
    jsn = ''.join(chr(int(x, 2)) for x in the_binary.split())
    d = json.loads(jsn)
    return d


class networkDiscovery():
    def __init__(self):
        self.master = None
        self.slaves = None
        self.is_master = is_master
        if is_master:
            log.info(f'Device is MASTER, starting master broadcast listen thread')
            broadcast_thread = threading.Thread(name='broadcast_thread', target=networkDiscovery.master_broadcast_listen, args=(self,), daemon=True)
            broadcast_thread.start()
        else:
            log.info(f'Device is SLAVE, starting master broadcast listen thread')
            broadcast_thread = threading.Thread(name='broadcast_thread', target=networkDiscovery.slave_broadcast_listen, args=(self,), daemon=True)
            broadcast_thread.start()

    def __repr__(self):
        return f'<motionPir object on bcmpin:{self.channel} mode:{self.mode}>'

    def __str__(self):
        return f'MotionPIR - BCMPin:{self.channel}, Mode:{self.mode}'

    def master_broadcast_listen(self):
        self.bsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bsock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.bsock.bind(("", 65530))
        #self.bsock.setblocking(0)
        while True:
            data, addr = self.bsock.recvfrom(1024)
            log.info(f"Master's Broadcast Listener recieved: {data}")
            discovery_queue.put(binary_to_dict(data))

    def slave_broadcast_listen(self):
        self.bsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bsock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.bsock.bind(("", 65531))
        #self.bsock.setblocking(0)
        while True:
            data, addr = self.bsock.recvfrom(1024)
            log.info(f"Slave's Broadcast Listener recieved: {data}")
            discovery_queue.put(binary_to_dict(data))


def discovery_thread():
    log.info('Network discovery thread is starting')
    discovery = networkDiscovery()
    while True:
        try:
            resp = discovery_queue.get()
            print(type(resp))
            print(resp)
        except:
            log.exception(f'Exception in Network Discovery Thread', exc_info=True)
            End('Exception in Network Discovery thread')
    End('Network Discovery thread loop ended prematurely')
