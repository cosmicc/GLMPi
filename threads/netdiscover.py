import socket
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
# loopdelay = float(config.get('network_discovery', 'loopdelay'))
# discover_timeout = int(config.get('network_discovery', 'timeout'))


class networkDiscovery():
    def __init__(self):
        self.master = None
        self.slaves = None
        self.is_master = is_master
        if is_master:
            broadcast_thread = threading.Thread(name='broadcast_thread', target=networkDiscovery.master_broadcast_listen, args=(self,), daemon=True)
            broadcast_thread.start()
        else:
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
        self.bsock.setblocking(0)
        while True:
            data = self.bsock.recv(1024)
            log.info(f"Master's Broadcast Listener recieved: {data}")
            discovery_queue.put('SLAVE', data)

    def slave_broadcast_listen(self):
        self.bsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bsock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.bsock.bind(("", 65531))
        self.bsock.setblocking(0)
        while True:
            data = self.bsock.recv(1024)
            log.info(f"Slave's Broadcast Listener recieved: {data}")
            discovery_queue.put('MASTER', data)


def discovery_thread():
    log.info('Network discovery thread is starting')
    discovery = networkDiscovery()
    while True:
        try:
            print(discovery_queue.get())
            sleep(1)
        except:
            log.exception(f'Exception in Network Discovery Thread', exc_info=True)
            End('Exception in Network Discovery thread')
    End('Network Discovery thread loop ended prematurely')
