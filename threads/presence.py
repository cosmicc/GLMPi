from configparser import ConfigParser
from time import sleep
import logging
from socket import gethostname
import subprocess
from bluepy.btle import Scanner, DefaultDelegate, Peripheral, BTLEDisconnectError
from threads.threadqueues import restapi_queue
from modules.extras import str2bool, End

host_name = gethostname()
log = logging.getLogger(name=host_name)

class ExtConfigParser(ConfigParser):
    def getlist(self, section, option):
        value = self.get(section, option)
        return list(filter(None, (x.strip() for x in value.split(','))))

    def getlistint(self, section, option):
        return [int(x) for x in self.getlist(section, option)]

config = ConfigParser()
config.read('/etc/glmpi.conf')
loopdelay = int(config.get('presence', 'scandelay'))
ismaster = str2bool(config.get('master_controller', 'enabled'))

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
        self.beacon = str2bool(config.get('presence', 'bluetooth_beacon'))
        self.whitelist = config.getlist('presence', 'bluetooth_names')
        self.scantime = int(config.get('presence', 'bluetooth_scantime'))
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
            log.debug(f'Bluetooth device disconnected')
        else:
            for dev in devices:
                if dev.connectable:
                    try:
                        ndev = Peripheral(dev)
                    except BTLEDisconnectError:
                        log.debug(f'Cannot connect to device: {dev.addr} {dev.rssi} dB')
                    else:
                        try:
                            device_name = ndev.getCharacteristics(uuid='00002a00-0000-1000-8000-00805f9b34fb')[0].read().decode('UTF-8')
                            device_appr = ndev.getCharacteristics(uuid='00002a01-0000-1000-8000-00805f9b34fb')[0].read().decode('UTF-8')
                        except BTLEDisconnectError:
                            log.debug(f'Cannot connect to device: {dev.addr} {dev.rssi} dB')
                        #print(f'Device Name: {device_name}')
                        #print(f'Device Appr: {device_appr}')
                        #print(f'Device Addr: {dev.addr}')
                        #print(f'Device Type: {dev.addrType}')
                        #print(f'Device Signal: {dev.rssi} dB')
                        if device_name in self.whitelist or device_appr in self.whitelist:
                            log.info(f'Device {device_name} IN BLUETOOTH RANGE! {dev.rssi} dB')

class arpListener():
    def __init__(self):
        config = ExtConfigParser()
        config.read('/etc/glmpi.conf')
        self.arpmacs = config.getlist('presence', 'wifiMACs')
    def scan(self):
        p = subprocess.Popen("arp-scan -l", stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        p_status = p.wait()
        output = output.decode('UTF-8').split('\n')
        for each in output:
            line = (each.split('\t'))
            if len(line) > 2:
                if line[1] in self.arpmacs:
                    log.info(f'Device {line[1]} SEEN ON WIFI!')


def pres_thread():
    log.info('Presence detection thread is starting')
    btdevice = btListener()
    arpscanner = arpListener()
    while True:
        try:
            if ismaster:
                arpscanner.scan()
            btdevice.scan()
            sleep(loopdelay)
        except:
            log.critical(f'Exception in Presence Thread', exc_info=True)
            End('Exception in Presence Thread')
    End('Presence thread loop ended prematurely')
