import subprocess
from configparser import ConfigParser

from flask import Blueprint, request
from flask_restplus import Api, Resource
from loguru import logger as log
from modules.extras import config_update
from modules.timehelper import calcbright
from threads.threadqueues import (alarm_queue, presence_queue, restapi_queue,
                                  strip_queue)

restapi = Blueprint('api', __name__)
api = Api(restapi, title='Galaxy Lighting Module RestAPI', version='1.0', doc='/')  # doc=False

configfile = '/etc/glmpi.conf'
config = ConfigParser()
config.read(configfile)


def getconfig():
    printconfig = {}
    for section in config.sections():
        a = dict(config[section])
        b = {f'{section}': a}
        printconfig.update(b)
    return printconfig


@log.catch()
@api.route('/reset')
@api.doc(params={'type': 'soft/hard'})
class DeviceReset(Resource):
    def put(self):
        if request.args.get("type") == 'soft':
            log.warning('SOFT RESET recieved from restapi, restarting glmpi service')
            subprocess.run(['/bin/systemctl', 'restart', 'glmpi'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
            return 'Success', 200
        elif request.args.get("type") == 'hard':
            log.warning('HARD RESET recieved from restapi, restarting pi')
            subprocess.run(['/sbin/reboot'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
            return 'Success', 200
        else:
            return 'Invalid Type', 400


@log.catch()
@api.route('/night')
@api.doc(params={'night': 'on/off'})
class DeviceNight(Resource):
    def put(self):
        if request.args.get("night") == 'on' or request.args.get("night") == '1' or request.args.get("night") == 'true':
            strip_queue.put((5, 'nighton'),)
            return 'Success', 200
        elif request.args.get("night") == 'off' or request.args.get("night") == '0' or request.args.get("night") == 'false':
            strip_queue.put((5, 'nightoff'),)
            return 'Success', 200
        else:
            return 'Error', 400

    def get(self):
        strip_queue.put((18, 'getnight'),)
        return restapi_queue.get()


@log.catch()
@api.route('/away')
@api.doc(params={'away': 'on/off'})
class DeviceAway(Resource):
    @log.catch()
    def put(self):
        if request.args.get("away") == 'on' or request.args.get("away") == '1' or request.args.get("away") == 'true':
            strip_queue.put((5, 'awayon'),)
            presence_queue.put(('awayon'),)
            return 'Success', 200
        elif request.args.get("away") == 'off' or request.args.get("away") == '0' or request.args.get("away") == 'false':
            strip_queue.put((5, 'awayoff'),)
            presence_queue.put(('awayoff'),)
            return 'Success', 200
        else:
            return 'Invalid Request', 400

    def get(self):
        strip_queue.put((18, 'getaway'),)
        return restapi_queue.get()


@log.catch()
@api.route('/enable')
@api.doc(params={'enable': 'on/off'})
class DeviceEnable(Resource):
    def put(self):
        if request.args.get("enable") == 'on' or request.args.get("enable") == '1' or request.args.get("enable") == 'true':
            strip_queue.put((5, 'enable'),)
            return 'Success', 200
        elif request.args.get("enable") == 'off' or request.args.get("enable") == '0' or request.args.get("enable") == 'false':
            strip_queue.put((5, 'disable'),)
            return 'Success', 200
        else:
            return 'Error', 400

    def get(self):
        strip_queue.put((18, 'getenable'),)
        return restapi_queue.get()


@log.catch()
@api.route('/rgbcolor')
@api.doc(params={'red': '255', 'green': '255', 'blue': '255'})
class RGBColor(Resource):
    def put(self):
        try:
            if int(request.args.get("red")) < 0 or int(request.args.get("red")) > 255:
                return 'Invalid Red Value', 400
            if int(request.args.get("green")) < 0 or int(request.args.get("green")) > 255:
                return 'Invalid Green Value', 400
            if int(request.args.get("blue")) < 0 or int(request.args.get("blue")) > 255:
                return 'Invalid Blue Value', 400
            strip_queue.put((15, 'rgbcolor', request.args.get("red"), request.args.get("green"), request.args.get("blue")),)
        except:
            return 'Error', 400
        return 'Success', 200

    def get(self):
        strip_queue.put((18, 'getrgb'),)
        return restapi_queue.get()


@log.catch()
@api.route('/hsvcolor')
@api.doc(params={'hue': '359', 'saturation': '100', 'lightness': '100'})
class HSVColor(Resource):
    def put(self):
        try:
            if int(request.args.get("hue")) < 0 or int(request.args.get("hue")) > 359:
                return 'Invalid Hue Value', 400
            if int(request.args.get("saturation")) < 0 or int(request.args.get("saturation")) > 100:
                return 'Invalid Saturation Value', 400
            if int(request.args.get("lightness")) < 0 or int(request.args.get("lightness")) > 100:
                return 'Invalid Lightness Value', 400
            strip_queue.put((15, 'hsvcolor', request.args.get("hue"), request.args.get("saturation"), request.args.get("lightness")),)
        except:
            return 'Error', 400
        return 'Success', 200

    def get(self):
        strip_queue.put((18, 'gethsv'),)
        return restapi_queue.get()


@log.catch()
@api.route('/whitetemp')
@api.doc(params={'kelvin': '6500'})
class Whitetemp(Resource):
    def put(self):
        strip_queue.put((15, 'whitetemp', request.args.get("kelvin")),)
        return 'Success', 200

    def get(self):
        strip_queue.put((18, 'getwhitetemp'),)
        return restapi_queue.get()


@log.catch()
@api.route('/mode')
@api.doc(params={'mode': '1'})
class Mode(Resource):
    def put(self):
        if int(request.args.get("mode")) > 0 and int(request.args.get("mode")) < 10:
            strip_queue.put((15, 'mode', request.args.get("mode")),)
            return 'Success', 200
        else:
            return 'Invalid Mode', 400

    def get(self):
        strip_queue.put((18, 'getmode'),)
        return restapi_queue.get()


@log.catch()
@api.route('/cyclehue')
@api.doc(params={'hue': '359'})
class Cyclecolor(Resource):
    def put(self):
        if request.args.get("hue") is None:
            return 'Invalid Hue Value', 400
        if int(request.args.get("hue")) >= 0 and int(request.args.get("hue")) < 360:
            strip_queue.put((10, 'cyclehue', request.args.get("hue")),)
            return 'Success', 200
        else:
            return'Invalid Hue Value', 400

    def get(self):
        strip_queue.put((18, 'getcyclehue'),)
        return restapi_queue.get()


@log.catch()
@api.route('/info')
class Info(Resource):
    def get(self):
        strip_queue.put((18, 'getinfo'),)
        return restapi_queue.get()


@log.catch()
@api.route('/alarms')
class Alarms(Resource):
    def get(self):
        alarm_queue.put(['getalarms', ])
        return restapi_queue.get()


@log.catch()
@api.route('/alarms/reset')
class Alarmsreset(Resource):
    def put(self):
        alarm_queue.put(['alarmsreset', ])
        return restapi_queue.get()


@log.catch()
@api.route('/config')
@api.doc(params={'section': 'section', 'option': 'option', 'value': 'value'})
class Config(Resource):
    def get(self):
        return getconfig()

    def put(self):
        if config.has_section(request.args.get("section")):
            if config.has_option(request.args.get("section"), request.args.get("option")):
                log.debug(f'Received config setting change: [{request.args.get("section")}] {request.args.get("option")} = {request.args.get("value")}')
                config_update(request.args.get("section"), request.args.get("option"), request.args.get("value"))
                return 'Success', 200
            else:
                return 'Invalid Option', 400
        else:
            return 'Invalid Section', 400


@log.catch()
@api.route('/time')
class Time(Resource):
    def get(self):
        return calcbright(data=True)
