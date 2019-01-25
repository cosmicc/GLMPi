import threading
from configparser import ConfigParser
from datetime import datetime

import requests
from flask import Blueprint, request
from flask_restplus import Api, Resource
from loguru import logger as log
from threads.netdiscover import discovery
from threads.presence import Presence

masterapi = Blueprint('masterapi', __name__)
api = Api(masterapi, title='Galaxy Lighting Module Master Controller RestAPI', version='1.0', doc='/')  # doc=False


class ExtConfigParser(ConfigParser):
    def getlist(self, section, option):
        value = self.get(section, option)
        return list(filter(None, (x.strip() for x in value.split(','))))

    def getlistint(self, section, option):
        return [int(x) for x in self.getlist(section, option)]


configfile = '/etc/glmpi.conf'
config = ExtConfigParser()
config.read(configfile)


@log.catch()
def sendrequest(request, **kwargs):
    def sendrequest_thread(host, request, sreq):
        sreq = sreq.replace('HOST', host)
        try:
            r = requests.put(sreq)
        except requests.exceptions.ConnectionError:
            log.debug(f'Master controller connection failed to: {host} - {sreq}')
        else:
            if r.status_code != 200:
                log.debug(f'Master controller send error {r.status_code} to: {sreq}')
            else:
                log.debug(f'Master controller send successful to: {sreq}')
    log.debug(f'Sending to hosts: {discovery.slaves}')
    sreq = f'http://HOST:51500/api/{request}'
    a = True
    for key, value in kwargs.items():
        if a:
            sreq = sreq + f'?{key}={value}'
        else:
            sreq = sreq + f'&{key}={value}'
        a = False
    log.debug(f'URL: {sreq}')
    if len(discovery.slaves) > 0:
        for host in discovery.slaves:
            cont_send_thread = threading.Thread(target=sendrequest_thread, args=(host, request, sreq), daemon=True)
            cont_send_thread.start()
    if discovery.master is not None:
        cont_sendmst_thread = threading.Thread(target=sendrequest_thread, args=(discovery.master, request, sreq), daemon=True)
        cont_sendmst_thread.start()


@log.catch()
@api.route('/reset')
@api.doc(params={'type': 'soft/hard'})
class DeviceReset(Resource):
    def put(self):
        if request.args.get("type") == 'soft':
            log.warning('SOFT RESET recieved from Masterapi, restarting glmpi service')
            sendrequest('reset', 'type', 'soft')
            return 'Success', 200
        elif request.args.get("type") == 'hard':
            log.warning('HARD RESET recieved from restapi, restarting pi')
            # subprocess.run(['/sbin/reboot'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
            return 'Success', 200
        else:
            return 'Error', 400


@log.catch()
@api.route('/cyclehue')
@api.doc(params={'hue': '359'})
class CycleHue(Resource):
    def put(self):
        log.debug('Cycle hue change received by the masterapi')
        sendrequest('cyclehue', 'hue', request.args.get("hue"))
        return 'Success', 200


@log.catch()
@api.route('/presence')
class Presence_(Resource):
    def put(self):
        log.debug(f'Presence update {request.args.get("device")} timestamp {request.args.get("timestamp")}')
        Presence.people.update({'device': request.args.get("device"), 'timestamp': datetime.fromisoformat(request.args.get("timestamp"))})
        return 'Success', 200

    def get(self):
        log.debug(f'Presence update request')
        return Presence.people
