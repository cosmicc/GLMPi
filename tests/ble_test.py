from bluepy.btle import Scanner, DefaultDelegate, Peripheral, BTLEDisconnectError

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

scanner = Scanner().withDelegate(ScanDelegate())

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
