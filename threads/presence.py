from configparser import ConfigParser
from datetime import datetime
from time import sleep
from loguru import logger as log
import requests
import subprocess
import threading
from bluepy.btle import Scanner, DefaultDelegate, Peripheral, BTLEDisconnectError
from modules.extras import str2bool, End
from threads.netdiscover import discovery


class ExtConfigParser(ConfigParser):
    def getlist(self, section, option):
        value = self.get(section, option)
        return list(filter(None, (x.strip() for x in value.split(','))))

    def getlistint(self, section, option):
        return [int(x) for x in self.getlist(section, option)]


config = ConfigParser()
config.read('/etc/glmpi.conf')
loopdelay = float(config.get('presence', 'scandelay'))
ismaster = str2bool(config.get('master_controller', 'enabled'))


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev and dev.connectable:
            pass
            # log.debug(f"Discovered BLE device {dev.addr}")
        elif isNewData:
            pass
            # print(f"Received new data from {dev.addr}")


class presenceListener():
    def __init__(self):
        config = ExtConfigParser()
        config.read('/etc/glmpi.conf')
        self.beacon = str2bool(config.get('presence', 'bluetooth_beacon'))
        self.whitelist = config.getlist('presence', 'bluetooth_names')
        self.scantime = int(config.get('presence', 'bluetooth_scantime'))
        self.arpmacs = config.getlist('presence', 'wifiMACs')
        self.scanlist = {}
        log.debug(f'Initializing bluetooth interface HCI0')
        subprocess.run(['/bin/hciconfig', 'hci0', 'up'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        if self.beacon:
            log.info(f'Initializing bluetooth beacon mode')
            subprocess.run(['/bin/hciconfig', 'hci0', 'leadv', '3'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        else:
            log.info(f'Initializing bluetooth non-beacon mode')
            subprocess.run(['/bin/hciconfig', 'hci0', 'noleadv'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        self.scanner = Scanner().withDelegate(ScanDelegate())

    def btscan(self):
        @log.catch
        def connect_ble_device(self, dev):
            log.debug(f'Starting connect thread for BLE device: {dev.addr} {dev.rssi} dB')
            try:
                ndev = Peripheral(dev)
            except BTLEDisconnectError:
                log.debug(f'Cannot connect to device (btledisconnect): {dev.addr} {dev.rssi} dB')
            else:
                try:
                    device_name = ndev.getCharacteristics(uuid='00002a00-0000-1000-8000-00805f9b34fb')[0].read().decode('UTF-8')
                    device_appr = ndev.getCharacteristics(uuid='00002a01-0000-1000-8000-00805f9b34fb')[0].read().decode('UTF-8')
                except BTLEDisconnectError:
                    log.debug(f'Cannot connect to device (btledisconnect2): {dev.addr} {dev.rssi} dB')
                # print(f'Device Name: {device_name}')
                # print(f'Device Appr: {device_appr}')
                # print(f'Device Addr: {dev.addr}')
                # print(f'Device Type: {dev.addrType}')
                # print(f'Device Signal: {dev.rssi} dB')
                try:
                    if device_name in self.whitelist or device_appr in self.whitelist:
                        log.info(f'Device {device_name} IN BLUETOOTH RANGE! {dev.rssi} dB')
                        dtn = datetime.now()
                        self.scanlist.update({'device': device_name, 'timestamp': dtn})
                        if not discovery.is_master:
                            sendpresence(device=device_name, timestamp=dtn)
                except:
                    log.debug(f'Cannot get device name: {dev.addr} {dev.rssi} dB')
            log.debug(f'Ending connect thread for BLE device: {dev.addr} {dev.rssi} dB')

        try:
            bledevs = self.scanner.scan(self.scantime)
        except BTLEDisconnectError:
            log.debug(f'Bluetooth device disconnected')
        else:
            bleconns = []
            for bledev in bledevs:
                log.debug(f'found ble: {bledev.addr} {bledev.connectable}')
                if bledev.connectable:
                    #connect_ble_device(self, bledev)
                    t = threading.Thread(target=connect_ble_device, args=(self,bledev,), daemon=True)
                    bleconns.append(t)
                    t.start()
            for bleconthread in bleconns:
                bleconthread.join()


    def arpscan(self):
        p = subprocess.Popen("arp-scan -l", stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        output = output.decode('UTF-8').split('\n')
        for each in output:
            line = (each.split('\t'))
            if len(line) > 2:
                if line[1] in self.arpmacs:
                    log.info(f'Device {line[1]} SEEN ON WIFI!')
                    dtn = datetime.now()
                    self.scanlist.update({'device': line[1], 'timestamp': dtn})
                    if not discovery.is_master:
                        sendpresence(device=line[1], timestamp=dtn)

@log.catch
def sendpresence(device, timestamp):
        if discovery.master is not None:
            sreq = f'http://{discovery.master}:51500/masterapi/presence?device={device}&timestamp={timestamp.isoformat()}'
            log.warning(sreq)
            try:
                r = requests.put(sreq)
            except:
                log.warning(f'Master send connection failed to: {discovery.master} - {sreq}')
            else:
                if r.status_code != 200:
                    log.warning(f'Master send error {r.status_code} to {discovery.master}: {sreq}')
                else:
                    log.warning(f'Master send successful to {discovery.master}: {sreq}')
            log.warning('4')


def pres_thread():
    global Presence
    log.info('Presence detection thread is starting')
    while True:
        try:
            if ismaster:
                Presence.arpscan()
            Presence.btscan()
            sleep(loopdelay)
        except:
            log.exception(f'Exception in Presence Thread', exc_info=True)
            End('Exception in Presence Thread')
    End('Presence thread loop ended prematurely')


Presence = presenceListener()
