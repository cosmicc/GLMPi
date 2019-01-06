from flask import request, Blueprint
from flask_restplus import Api, Resource, fields
from threads.threadqueues import strip_queue, status_queue

webapi = Blueprint('api', __name__)
api = Api(webapi, title='Galaxy Lighting Module RestAPI', version='1.0', doc='/')  # doc=False

@api.route('/sleep')
class DeviceSleep(Resource):
    def post(self):
        d = {'type': 'brightness', 'data': 'some data shit'}
        status_queue.put(d)
        return 'SUCCESS'

@api.route('/color')
class Color(Resource):
    def post(self):
        pass
