import subprocess
import threading
from configparser import ConfigParser
from datetime import datetime
from time import sleep

import requests
from socket import gethostname
from ast import literal_eval
from bluepy.btle import BTLEDisconnectError, DefaultDelegate, Peripheral, Scanner
from loguru import logger as log
from modules.codetime import codetime
from modules.extras import End, str2bool
from threads.netdiscover import discovery
from threads.threadqueues import presence_queue


class ExtConfigParser(ConfigParser):
    def getlist(self, section, option):
        value = self.get(section, option)
        return list(filter(None, (x.strip() for x in value.split(','))))

    def getlistint(self, section, option):
        return [int(x) for x in self.getlist(section, option)]

host_name = gethostname()

config = ConfigParser()
config.read('/etc/glmpi.conf')
loopdelay_home = float(config.get('presence', 'scandelay_home'))
loopdelay_away = float(config.get('presence', 'scandelay_away'))
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
        self.away = True
        self.beacon = str2bool(config.get('presence', 'bluetooth_beacon'))
        self.scantime = int(config.get('presence', 'bluetooth_scantime'))
        self.people = {}
        self.people_count = 0
        k = 1
        while config.has_option('master_controller', f'presence_{k}'):
            self.people_count += 1
            person = config.getlist('master_controller', f'presence_{k}')
            log.warning(f'adding person: {person[0]} {person}')
            self.people.update({person[0]: {'blename': person[1], 'wifimac': person[2], 'timestamp': 0, 'from': host_name}})
            k += 1
        log.debug(f'Initializing bluetooth interface HCI0')
        subprocess.run(['/bin/hciconfig', 'hci0', 'up'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        if self.beacon:
            log.info(f'Initializing bluetooth beacon mode')
            subprocess.run(['/bin/hciconfig', 'hci0', 'leadv', '3'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        else:
            log.info(f'Initializing bluetooth non-beacon mode')
            subprocess.run(['/bin/hciconfig', 'hci0', 'noleadv'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        self.scanner = Scanner().withDelegate(ScanDelegate())

    def checkqueue(self):
        if not presence_queue.empty():
            ststatus = presence_queue.get()
            if ststatus == 'awayon':
                self.away = True
            elif ststatus == 'awayoff':
                self.away = False

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
                    for person, info in self.people.items():
                        if device_name == info['blename'] or device_appr == info['blename']:
                            log.info(f"""{person}'s Device {device_name} IN BLUETOOTH RANGE! {dev.rssi} dB""")
                            dtn = datetime.now().isoformat()
                            self.people.update({person: {'blename': info['blename'], 'wifimac': info['wifimac'], 'timestamp': dtn, 'from': host_name}})
                            if not ismaster:
                                sendpresence(person, info['blename'], info['wifimac'], dtn)
                except:
                    log.debug(f'Cannot get device name: {dev.addr} {dev.rssi} dB')
            log.debug(f'Ending connect thread for BLE device: {dev.addr} {dev.rssi} dB')

        try:
            self.checkqueue()
            bledevs = self.scanner.scan(self.scantime)
        except BTLEDisconnectError:
            log.debug(f'Bluetooth device disconnected')
        else:
            bleconns = []
            # a = codetime('connections')
            for bledev in bledevs:
                log.debug(f'found ble: {bledev.addr} {bledev.connectable}')
                if bledev.connectable:
                    # connect_ble_device(self, bledev)
                    t = threading.Thread(target=connect_ble_device, args=(self, bledev, ), daemon=True)
                    bleconns.append(t)
                    t.start()
            for bleconthread in bleconns:
                bleconthread.join()
            # a.stop(debug=True)
            self.checkqueue()

    def arpscan(self):
        p = subprocess.Popen("arp-scan -l", stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        output = output.decode('UTF-8').split('\n')
        for each in output:
            line = (each.split('\t'))
            if len(line) > 2:
                for person, info in self.people.items():
                    if line[1] == info['wifimac']:
                        log.info(f"""{person}'s Device {info["wifimac"]} ON WIFI!""")
                        dtn = datetime.now().isoformat()
                        self.people.update({person: {'blename': info['blename'], 'wifimac': info['wifimac'], 'timestamp': dtn, 'from': host_name}})
                        if not ismaster:
                            sendpresence(person, info['blename'], info['wifimac'], dtn)


@log.catch
def sendpresence(name, blename, wifimac, timestamp):
    if discovery.master is not None:
        sreq = f'http://{discovery.master}:51500/masterapi/presence?name={name}&blename={blename}&wifimac={wifimac}&timestamp={timestamp}&from={host_name}'
        try:
            r = requests.put(sreq)
        except:
            log.warning(f'Master send connection failed to: {discovery.master} - {sreq}')
        else:
            if r.status_code != 200:
                log.warning(f'Master send error {r.status_code} to {discovery.master}: {sreq}')
            else:
                log.debug(f'Master send successful to {discovery.master}: {sreq}')


@log.catch
def request_master_presence():
    if discovery.master is not None:
        sreq = f'http://{discovery.master}:51500/masterapi/presence'
        try:
            r = requests.get(sreq)
        except:
            log.warning(f'Master send connection failed to: {discovery.master} - {sreq}')
        else:
            if r.status_code != 200:
                log.warning(f'Master send error {r.status_code} to {discovery.master}: {sreq}')
            else:
                log.debug(f'Master send successful to {discovery.master}: {sreq}')
                return literal_eval(r.text)


def pres_thread():
    global Presence
    log.info('Presence detection thread is starting')
    while True:
        b = codetime('total')
        try:
            log.warning(Presence.people)
            if ismaster:
                Presence.arpscan()
            Presence.btscan()
            Presence.checkqueue()
            if Presence.away:
                looptime = loopdelay_away
            else:
                looptime = loopdelay_home
            while datetime.now().timestamp() - b.starttime < looptime:
                Presence.checkqueue()
                sleep(1)
            if not Presence.people and not ismaster:
                Presence.people = request_master_presence()
        except:
            log.exception(f'Exception in Presence Thread', exc_info=True)
            End('Exception in Presence Thread')
        b.stop(debug=False)
    End('Presence thread loop ended prematurely')


Presence = presenceListener()
