import socket
import base64
import json
import threading
from time import sleep
from random import uniform as rnd
from datetime import datetime
from threads.threadqueues import strip_queue
from configparser import ConfigParser
from modules.extras import str2bool, End
from loguru import logger as log
from queue import SimpleQueue

discovery_queue = SimpleQueue()

host_name = socket.gethostname()

config = ConfigParser()
config.read('/etc/glmpi.conf')

is_master = str2bool(config.get('master_controller', 'enabled'))
salt = config.get('network_discovery', 'bcast_salt')

#discovery = None

def dict_to_binary(the_dict):
    str = json.dumps(the_dict)
    binary = ' '.join(format(ord(letter), 'b') for letter in str)
    return binary


def binary_to_dict(the_binary):
    jsn = ''.join(chr(int(x, 2)) for x in the_binary.split())
    d = json.loads(jsn)
    return d


def encrypt(key, string):
    encoded_chars = []
    for i in range(len(string)):
        key_c = key[i % len(key)]
        encoded_c = chr(ord(string[i]) + ord(key_c) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = ''.join(encoded_chars)
    encoded_string = encoded_string.encode('UTF-8')
    return base64.urlsafe_b64encode(encoded_string).rstrip(b'=')


def decrypt(key, string):
    string = base64.urlsafe_b64decode(string + b'===')
    string = string.decode()
    encoded_chars = []
    for i in range(len(string)):
        key_c = key[i % len(key)]
        encoded_c = chr((ord(string[i]) - ord(key_c) + 256) % 256)
        encoded_chars.append(encoded_c)
    encoded_string = ''.join(encoded_chars)
    return encoded_string


class networkDiscovery():
    def __init__(self):
        if not is_master:
            self.slaves = [host_name,]
        else:
            self.slaves = []
        self.is_master = is_master
        if self.is_master:
            self.master = host_name
        else:
            self.master = None
        self.hostname = host_name
        log.info(f'Starting broadcast listener thread')
        self.lsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.lsock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.lsock.bind(("", 65530))
        self.ssock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ssock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.ssock.bind(("", 45454))
        broadcast_thread = threading.Thread(name='broadcast_thread', target=networkDiscovery.broadcast_listener, args=(self,), daemon=True)
        broadcast_thread.start()

    def __repr__(self):
        return f'<networkDiscovery object - Master: {self.master} Slaves: {self.slaves}>'

    def __str__(self):
        return f'Master: {self.master}  Slaves: {self.slaves}'

    def broadcast_listener(self):
        while True:
            data, addr = self.lsock.recvfrom(4096)
            resp = binary_to_dict(decrypt(salt, data))
            log.debug(f"Broadcast Listener recieved from {addr[0]}: {resp}")
            resp.update({'addr': addr[0]})
            discovery_queue.put(resp)

    def broadcast_send(self, dictmsg):
        log.debug(f'Sending broadcast message: {dictmsg}')
        sleep(rnd(0, 1))
        message = encrypt(salt, dict_to_binary(dictmsg))
        self.ssock.sendto(message, ('<broadcast>', 65530))

    def slave_request(self):
        dictmsg = {'type': 'SLAVEREQUEST', 'from': self.hostname}
        self.broadcast_send(dictmsg)

    def master_request(self):
        dictmsg = {'type': 'MASTERREQUEST', 'from': self.hostname}
        self.broadcast_send(dictmsg)


def discovery_thread():
    log.info('Network discovery thread is starting')
    #discovery = networkDiscovery()
    if is_master:
        log.info('Sending out slave request broadcast')
        discovery.slave_request()
    else:
        log.info('Sending out master request broadcast')
        discovery.master_request()
    while True:
        try:
            bcast = discovery_queue.get()
            if bcast['type'] == 'MASTERREQUEST' and discovery.is_master:
                if bcast["from"] not in discovery.slaves:
                    log.info(f'Slave device discovered: {bcast["from"]} at {bcast["addr"]}')
                    discovery.slaves.append(bcast['from'])
                dictmsg = {'type': 'MASTER', 'from': host_name, 'slaves': discovery.slaves}
                discovery.broadcast_send(dictmsg)
            elif bcast['type'] == 'SLAVEREQUEST' and not discovery.is_master:
                dictmsg = {'type': 'SLAVE', 'from': host_name}
                discovery.broadcast_send(dictmsg)
            elif bcast['type'] == 'SLAVE' and discovery.is_master:
                if bcast["from"] not in discovery.slaves:
                    log.info(f'Slave device discovered: {bcast["from"]} at {bcast["addr"]}')
                    discovery.slaves.append(bcast['from'])
            elif bcast['type'] == 'MASTER' and not discovery.is_master:
                log.info(f'Master device announce {bcast["from"]} at {bcast["addr"]}')
                if discovery.master != bcast["from"]:
                    discovery.master = bcast["from"]
                if discovery.slaves != bcast["slaves"]:
                    if host_name not in bcast["slaves"]:
                        dictmsg = {'type': 'SLAVE', 'from': host_name}
                        discovery.broadcast_send(dictmsg)
                        discovery.slaves = bcast["slaves"]
                        discovery.slaves.append(host_name)
                    else:
                        discovery.slaves = bcast["slaves"]
            log.debug(f'master: {discovery.master}  slaves: {discovery.slaves}')
        except:
            log.exception(f'Exception in Network Discovery Thread', exc_info=True)
            End('Exception in Network Discovery thread')
    End('Network Discovery thread loop ended prematurely')

discovery = networkDiscovery()
