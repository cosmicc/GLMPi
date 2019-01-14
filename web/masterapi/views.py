from flask import request, Blueprint
from flask_restplus import Api, Resource, fields
from threads.statusled import stled
from threads.threadqueues import restapi_queue, strip_queue, alarm_queue
from modules.timehelper import calcbright
from configparser import ConfigParser
import subprocess
import logging
import socket
import requests

masterapi = Blueprint('masterapi', __name__)
api = Api(masterapi, title='Galaxy Lighting Module Master Controller RestAPI', version='1.0', doc='/')  # doc=False

host_name = socket.gethostname()
log = logging.getLogger(name=host_name)

class ExtConfigParser(ConfigParser):
    def getlist(self, section, option):
        value = self.get(section, option)
        return list(filter(None, (x.strip() for x in value.split(','))))

    def getlistint(self, section, option):
        return [int(x) for x in self.getlist(section, option)]

configfile = '/etc/glmpi.conf'
config = ExtConfigParser()
config.read(configfile)

hosts = config.getlist('master_controller', 'slaves')

def sendrequest(request, opt, val):
    for host in hosts:
        sreq = f'http://{host}:51500/api/{request}'
        log.warning(f'{sreq} - {opt} - {val}')
        r = requests.post(sreq, data={opt: val})
        return r.status_code, r.reason

@api.route('/reset')
@api.doc(params={'type': 'soft/hard'})
class DeviceReset(Resource):
    def post(self):
        if request.args.get("type") == 'soft':
            log.warning('SOFT RESET recieved from Masterapi, restarting glmpi service')
            sendrequest('reset', 'type', 'soft')
            return 'SUCCESS'
        elif request.args.get("type") == 'hard':
            log.warning('HARD RESET recieved from restapi, restarting pi')
            #subprocess.run(['/sbin/reboot'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
            return 'SUCCESS'
        else:
            return 'ERROR'


