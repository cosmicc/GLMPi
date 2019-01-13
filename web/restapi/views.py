from flask import request, Blueprint
from flask_restplus import Api, Resource, fields
from threads.statusled import stled
from threads.threadqueues import restapi_queue, strip_queue
from modules.timehelper import calcbright
from configparser import ConfigParser
import subprocess
import logging
import socket

restapi = Blueprint('api', __name__)
api = Api(restapi, title='Galaxy Lighting Module RestAPI', version='1.0', doc='/')  # doc=False


host_name = socket.gethostname()
log = logging.getLogger(name=host_name)

config = ConfigParser()
config.read('/etc/glmpi.conf')

def getconfig():
    printconfig = {}
    for section in config.sections():
        a = dict(config[section])
        b = {f'{section}': a}
        printconfig.update(b)
    return printconfig

@api.route('/reset')
@api.doc(params={'type': 'soft/hard'})
class DeviceReset(Resource):
    def post(self):
        if request.args.get("type") == 'soft':
            log.warning('SOFT RESET recieved from restapi, restarting glmpi service')
            subprocess.run(['/bin/systemctl', 'restart', 'glmpi'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
            return 'SUCCESS'
        elif request.args.get("type") == 'hard':
            log.warning('HARD RESET recieved from restapi, restarting pi')
            subprocess.run(['/sbin/reboot'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
            return 'SUCCESS'
        else:
            return 'ERROR'

@api.route('/night')
@api.doc(params={'night': 'on/off'})
class DeviceNight(Resource):
    def post(self):
        if request.args.get("night") == 'on' or request.args.get("night") == '1' or request.args.get("night") == 'true':
            strip_queue.put((5, 'nighton'),)
            return 'SUCCESS'
        elif request.args.get("night") == 'off' or request.args.get("night") == '0' or request.args.get("night") == 'false':
            strip_queue.put((5, 'nightoff'),)
            return 'SUCCESS'
        else:
            return 'ERROR'
    def get(self):
        strip_queue.put((18, 'getnight'),)
        return restapi_queue.get()

@api.route('/away')
@api.doc(params={'away': 'on/off'})
class DeviceAway(Resource):
    def post(self):
        if request.args.get("away") == 'on' or request.args.get("away") == '1' or request.args.get("away") == 'true':
            strip_queue.put((5, 'awayon'),)
            return 'SUCCESS'
        elif request.args.get("away") == 'off' or request.args.get("away") == '0' or request.args.get("away") == 'false':
            strip_queue.put((5, 'awayoff'),)
            return 'SUCCESS'
        else:
            return 'INVALID REQUEST'
    def get(self):
        strip_queue.put((18, 'getaway'),)
        return restapi_queue.get()


@api.route('/enable')
@api.doc(params={'enable': 'on/off'})
class DeviceEnable(Resource):
    def post(self):
        if request.args.get("enable") == 'on' or request.args.get("enable") == '1' or request.args.get("enable") == 'true':
            strip_queue.put((5, 'enable'),)
            return 'SUCCESS'
        elif request.args.get("enable") == 'off' or request.args.get("enable") == '0' or request.args.get("enable") == 'false':
            strip_queue.put((5, 'disable'),)
            return 'SUCCESS'
        else:
            return 'ERROR'
    def get(self):
        strip_queue.put((18, 'getenable'),)
        return restapi_queue.get()


@api.route('/rgbcolor')
@api.doc(params={'red': '255', 'green': '255', 'blue': '255'})
class RGBColor(Resource):
    def post(self):
        try:
            if int(request.args.get("red")) < 0 or int(request.args.get("red")) > 255:
                return 'INVALID RED VALUE'
            if int(request.args.get("green")) < 0 or int(request.args.get("green")) > 255:
                return 'INVALID GREEN VALUE'
            if int(request.args.get("blue")) < 0 or int(request.args.get("blue")) > 255:
                return 'INVALID BLUE VALUE'
            strip_queue.put((15, 'rgbcolor', request.args.get("red"), request.args.get("green"), request.args.get("blue")),)
        except:
            return 'ERROR'
        return 'SUCCESS'
    def get(self):
        strip_queue.put((18, 'getrgb'),)
        return restapi_queue.get()

@api.route('/hsvcolor')
@api.doc(params={'hue': '359', 'saturation': '100', 'lightness': '100'})
class HSVColor(Resource):
    def post(self):
        try:
            if int(request.args.get("hue")) < 0 or int(request.args.get("hue")) > 359:
                return 'INVALID HUE VALUE'
            if int(request.args.get("saturation")) < 0 or int(request.args.get("saturation")) > 100:
                return 'INVALID GREEN VALUE'
            if int(request.args.get("lightness")) < 0 or int(request.args.get("lightness")) > 100:
                return 'INVALID LIGHTNESS VALUE'
            strip_queue.put((15, 'hsvcolor', request.args.get("hue"), request.args.get("saturation"), request.args.get("lightness")),)
        except:
            return 'ERROR'
        return 'SUCCESS'
    def get(self):
        strip_queue.put((18, 'gethsv'),)
        return restapi_queue.get()

@api.route('/whitetemp')
@api.doc(params={'kelvin': '6500'})
class Whitetemp(Resource):
    def post(self):
        strip_queue.put((15, 'whitetemp', request.args.get("kelvin")),)
        return 'SUCCESS'
    def get(self):
        strip_queue.put((18, 'getwhitetemp'),)
        return restapi_queue.get()

@api.route('/mode')
@api.doc(params={'mode': '1'})
class Mode(Resource):
    def post(self):
        if int(request.args.get("mode")) > 0 and int(request.args.get("mode")) < 10:
            strip_queue.put((15, 'mode', request.args.get("mode")),)
            return 'SUCCESS'
        else:
            return 'INVALID MODE'
    def get(self):
        strip_queue.put((18, 'getmode'),)
        return restapi_queue.get()

@api.route('/cyclehue')
@api.doc(params={'hue': '359'})
class Cyclecolor(Resource):
    def post(self):
        if int(request.args.get("hue")) >= 0 and int(request.args.get("hue")) < 360:
            strip_queue.put((10, 'cyclehue', request.args.get("hue")),)
            return 'SUCCESS'
        else:
            return 'INVALID MODE'
    def get(self):
        strip_queue.put((18, 'getcyclehue'),)
        return restapi_queue.get()


@api.route('/info')
class Info(Resource):
    def get(self):
        strip_queue.put((18, 'getinfo'),)
        return restapi_queue.get()

@api.route('/config')
class Config(Resource):
    def get(self):
        return getconfig()

@api.route('/time')
class Time(Resource):
    def get(self):
        return calcbright(data=True)
