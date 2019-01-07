from flask import request, Blueprint
from flask_restplus import Api, Resource, fields
from threads.statusled import stled
from threads.ledstrip import ledstrip

webapi = Blueprint('api', __name__)
api = Api(webapi, title='Galaxy Lighting Module RestAPI', version='1.0', doc='/')  # doc=False

@api.route('/sleep')
class DeviceSleep(Resource):
    def post(self):
        stled('green', 1)
        return 'SUCCESS'

@api.route('/color')
class Color(Resource):
    def post(self):
        ledstrip('color', 255, 0, 0)
        return 'SUCCESS'
