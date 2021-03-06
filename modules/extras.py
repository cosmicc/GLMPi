from threads.threadqueues import strip_queue, status_queue, alarm_queue
from time import sleep
from loguru import logger as log
import subprocess


def str2bool(v):
    return str(v).lower() in ("yes", "true", "t", "1")


def float_trunc_1dec(num):
    try:
        tnum = num // 0.1 / 10
    except:
        return False
    else:
        return tnum


def c2f(c):
    return float_trunc_1dec((c * 9 / 5) + 32)


def End(why, alarm=True):
    log.critical(f'Exiting: {why}')
    status_queue.put({'color': 'red', 'flashes': 1, 'flashrate': 'fast'})
    if alarm:
        alarm_queue.put([f'Critical Error: {why}'])
    sleep(0.5)
    strip_queue.put((0, 'stripoff'),)
    sleep(0.2)
    exit(0)


def get_wifi_info():
    child = subprocess.Popen(['iwconfig'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=False)
    streamdata = child.communicate()[0].decode('UTF-8').split('\n')
    if child.returncode == 0:
        for each in streamdata:
            if each.find('ESSID:') != -1:
                ssid = each.split(':')[1].replace('"', '').strip()
            elif each.find('Frequency') != -1:
                apmac = each.split('Access Point: ')[1].strip()
                channel = each.split('Frequency:')[1].split(' Access Point:')[0].strip()
            elif each.find('Link Quality') != -1:
                linkqual = each.split('=')[1].split(' Signal level')[0].strip()
                signal = int(each.split('=')[2].split(' ')[0].strip())
                # -80 -30  0 100
                signal_percent = int(0 + (100 - 0) * ((signal - -80) / (-35 - -80)))
                if signal_percent > 100:
                    signal_percent = 100
            elif each.find('Bit Rate') != -1:
                bitrate = each.split('=')[1].split('Tx-Power')[0].strip()

        return {'ssid': ssid, 'apmac': apmac, 'channel': channel, 'signal': signal, 'signal_percent': signal_percent, 'quality': linkqual, 'bitrate': bitrate}
    else:
        return False
