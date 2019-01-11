from time import sleep
from datetime import datetime
from rpi_ws281x import *
from threads.threadqueues import strip_queue, restapi_queue
from configparser import ConfigParser
from pathlib import Path
from pickle import dump as pdump, load as pload
from modules.timehelper import calcbright
from modules.extras import str2bool
import threading
import logging
import socket
from bluepy.btle import Scanner, DefaultDelegate, Peripheral, BTLEDisconnectError


host_name = socket.gethostname()
log = logging.getLogger(name=host_name)

config = ConfigParser()
config.read('/etc/glmpi.conf')
loopdelay = float(config.get('bluetooth', 'loopdelay'))

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev and dev.connectable:
            pass

                #print(f"Discovered device {dev.addr}")
        elif isNewData:
            pass
                #print(f"Received new data from {dev.addr}")

class btListener():
    def __init__(self):
        config = ConfigParser()
        config.read('/etc/glmpi.conf')
        self.beacon = str2bool(config.get('bluetooth', 'beacon'))
        log.debug(f'Initializing bluetooth interface HCI0')
        subprocess.run('hciconfig hci0 up', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        if self.beacon:
            log.debug(f'Initializing bluetooth beacon mode')
            subprocess.run('hciconfig hci0 leadv 3', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        else:
            log.debug(f'Initializing bluetooth non-beacon mode')
            subprocess.run('hciconfig hci0 noleadv', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        self.scanner = Scanner().withDelegate(ScanDelegate())


def btlistener_thread():
    log.debug('Bluetooth listener thread is starting')
    while True:

    devices = scanner.scan(15.0)

        for dev in devices:
            if dev.connectable:
                    try:
                        ndev = Peripheral(dev)
                    except BTLEDisconnectError:
                        print(f'Cannot connect to device: {dev.addr} {dev.rssi} dB')
                    else:
                        device_name = ndev.getCharacteristics(uuid='00002a00-0000-1000-8000-00805f9b34fb')[0].read().decode('UTF-8')
                        device_appr = ndev.getCharacteristics(uuid='00002a01-0000-1000-8000-00805f9b34fb')[0].read().decode('UTF-8')
                        if device_name is None: device_name = 'None'
                        if device_appr is None: device_appr = 'None'
                        print(f'Device Name: {device_name}')
                        print(f'Device Appr: {device_appr}')
                        print(f'Device Addr: {dev.addr}')
                        print(f'Device Type: {dev.addrType}')
                        print(f'Device Signal: {dev.rssi} dB')




#hciconfig hci0 up
#hciconfig hci0 leadv 3

#hciconfig hci0 noleadv
#hciconfig hci0 down
