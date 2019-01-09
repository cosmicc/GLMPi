from astral import Astral
from datetime import datetime, time, timedelta
import pytz
from configparser import ConfigParser
from datetime import time as Time
import socket
import logging

config = ConfigParser()
config.read('/etc/glmpi.conf')
lowbright = int(config.get('led_strip', 'lowbright'))
medbright = int(config.get('led_strip', 'medbright'))
highbright = int(config.get('led_strip', 'highbright'))
fullbright = int(config.get('led_strip', 'fullbright'))

host_name = socket.gethostname()
log = logging.getLogger(name=host_name)

ast = Astral()
ast.solar_depression = 'civil'
city = ast['Detroit']
timezone = pytz.timezone("America/Detroit")


def calcbright(stdout=False, data=False):
    dtnow = datetime.now(timezone)
    sun = city.sun(date=dtnow, local=True)
    nowtime = dtnow.time()
    sunrise = sun['sunrise']
    sunrise_offset = (sunrise + timedelta(hours=2)).time()
    sunrise = sunrise.time()
    sunset = sun['dusk'].time()
    solarnoon = sun['noon']
    solarnoon_offset = (solarnoon - timedelta(hours=2)).time()
    solarnoon = solarnoon.time()
    solarmidnight = city.solar_midnight(date=dtnow, local=True)
    solarmidnight_offset = (solarmidnight - timedelta(hours=2)).time()
    solarmidnight = solarmidnight.time()
    lastminute = datetime.strptime('23:59', '%H:%M').time()
    midnight = datetime.strptime('00:00', '%H:%M').time()

    if nowtime > solarmidnight and nowtime <= sunrise:
        if not stdout and not data:
            log.debug(f'Brightness: {lowbright} (lowbright) - past: solarmidnight {solarmidnight} next: sunrise {sunrise}')
            return lowbright
        day = False
        bright = lowbright
        lastpast = 'solarmidnight'
        nextpast = 'sunrise'
    elif nowtime > sunrise and nowtime <= sunrise_offset:
        if not stdout and not data:
            log.debug(f'Brightness: {midbright} (midbright) - past: sunrise {sunrise} next: sunrise_offset {sunrise_offset}')
            return medbright
        day = False
        bright = medbright
        lastpast = 'sunrise'
        nextpast = 'sunrise_offset'
    elif nowtime > sunrise_offset and nowtime <= solarnoon_offset:
        if not stdout and not data:
            log.debug(f'Brightness: {highbright} (highbright) - past: sunrise_offset {sunrise_offset} next: solarmoon_offset {solarmoon_offset}')
            return highbright
        day = True
        bright = highbright
        lastpast = 'sunrise_offset'
        nextpast = 'solarnoon_offset (solarnoon is skipped)'
    elif nowtime > solarnoon_offset and nowtime <= sunset:
        if not stdout and not data:
            log.debug(f'Brightness: {fullbright} (fullbright) - past: solarnoon_offset {solarnoon_offset} next: sunset {sunset}')
            return fullbright
        day = True
        bright = fullbright
        lastpast = 'solarnoon_offset (solarnoon is skipped)'
        nextpast = 'sunset'
    elif nowtime > sunset and nowtime <= lastminute:
        if not stdout and not data:
            log.debug(f'Brightness: {highbright} (highbright) - past: sunset {sunset} next: solarmidnight {solarmidnight}')
            return highbright
        day = False
        bright = highbright
        lastpast = 'sunset'
        nextpast = 'solarmidnight'
    elif nowtime >= midnight and nowtime <= solarmidnight_offset:
        if not stdout and not data:
            log.debug(f'Brightness: {highbright} (highbright) - past: sunset {sunset} next: solarmidnight {solarmidnight}')
            return highbright
        day = False
        bright = highbright
        lastpast = 'sunset'
        nextpast = 'solarmodnight'
    else:
        if not stdout and not data:
            log.error(f'Error in brightness determination from time: {nowtime}')
            return 0
        else:
            print(f'*ERROR* in brightness determination from time: {nowtime}')

    if stdout and not data:
        print(' ')
        print(f'Brightness: {bright}')
        print(f'Is Daytime: {day}')
        print(f'Lastpast: {lastpast}')
        print(f'Nextpast: {nextpast}')
        print(' ')
        print(f'Current Time:   {nowtime} {type(nowtime)}')
        print(f'Sunrise:        {sunrise} {type(sunrise)}')
        print(f'Sunrise_ofst:   {sunrise_offset} {type(sunrise_offset)}')
        print(f'Solar Noon_ofst:{solarnoon_offset} {type(solarnoon_offset)}')
        print(f'Solar Noon:     {solarnoon} {type(solarnoon)}')
        print(f'Sunset:         {sunset} {type(sunset)}')
        print(f'Solar Midn_ofst:{solarmidnight_offset} {type(solarmidnight_offset)}')
        print(f'Solar Midnight: {solarmidnight} {type(solarmidnight)}')
        print(' ')

    if data:
        return {'localdatetime': str(dtnow), 'localtime': str(nowtime), 'brightness': bright, 'daytime': day, 'lastpast': lastpast, 'nextpast': nextpast, 'sunrise': str(sunrise), 'sunrise_offset': str(sunrise_offset), 'solarnoon_offset' : str(solarnoon_offset), 'solarnoon': str(solarnoon), 'sunset': str(sunset), 'solarmidnight_offset': str(solarmidnight_offset), 'solarmidnight': str(solarmidnight)}

if __name__ == '__main__':
    calcbright(stdout=True)
