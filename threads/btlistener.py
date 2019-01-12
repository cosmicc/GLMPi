from configparser import ConfigParser
from time import sleep
import logging
import socket
import subprocess
from bluepy.btle import Scanner, DefaultDelegate, Peripheral, BTLEDisconnectError
from threads.threadqueues import restapi_queue
from modules.extras import str2bool

host_name = socket.gethostname()
log = logging.getLogger(name=host_name)

class ExtConfigParser(ConfigParser):
    def getlist(self, section, option):
        value = self.get(section, option)
        return list(filter(None, (x.strip() for x in value.split(','))))

    def getlistint(self, section, option):
        return [int(x) for x in self.getlist(section, option)]

config = ConfigParser()
config.read('/etc/glmpi.conf')
loopdelay = int(config.get('bluetooth', 'scandelay'))

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
        config = ExtConfigParser()
        config.read('/etc/glmpi.conf')
        self.beacon = str2bool(config.get('bluetooth', 'beacon'))
        self.whitelist = config.getlist('bluetooth', 'presence')
        self.scantime = int(config.get('bluetooth', 'scantime'))
        log.debug(f'Initializing bluetooth interface HCI0')
        subprocess.run(['/bin/hciconfig', 'hci0', 'up'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        if self.beacon:
            log.info(f'Initializing bluetooth beacon mode')
            subprocess.run(['/bin/hciconfig', 'hci0', 'leadv', '3'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        else:
            log.info(f'Initializing bluetooth non-beacon mode')
            subprocess.run(['/bin/hciconfig', 'hci0', 'noleadv'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        self.scanner = Scanner().withDelegate(ScanDelegate())
    def scan(self):
        try:
            devices = self.scanner.scan(self.scantime)
        except BTLEDisconnectError:
            log.warning(f'Bluetooth device disconnected')
        else:
            for dev in devices:
                if dev.connectable:
                    try:
                        ndev = Peripheral(dev)
                    except BTLEDisconnectError:
                        log.warning(f'Cannot connect to device: {dev.addr} {dev.rssi} dB')
                    else:
                        device_name = ndev.getCharacteristics(uuid='00002a00-0000-1000-8000-00805f9b34fb')[0].read().decode('UTF-8')
                        device_appr = ndev.getCharacteristics(uuid='00002a01-0000-1000-8000-00805f9b34fb')[0].read().decode('UTF-8')
                        #print(f'Device Name: {device_name}')
                        #print(f'Device Appr: {device_appr}')
                        #print(f'Device Addr: {dev.addr}')
                        #print(f'Device Type: {dev.addrType}')
                        #print(f'Device Signal: {dev.rssi} dB')
                        if device_name in self.whitelist or device_appr in self.whitelist:
                            log.info(f'{device_name} IN RANGE! {dev.rssi}')


def btlistener_thread():
    log.info('Bluetooth listener thread is starting')
    btdevice = btListener()
    while True:
        btdevice.scan()
        sleep(loopdelay)
