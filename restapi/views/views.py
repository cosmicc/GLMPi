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

@api.route('/rgbcolor')
@api.doc(params={'red': '255', 'green': '255', 'blue': '255'})
class RGBColor(Resource):
    def post(self):
        ledstrip('rgbcolor', request.args.get("red"), request.args.get("green"), request.args.get("blue"))
        return 'SUCCESS'

@api.route('/hsvcolor')
@api.doc(params={'hue': '360', 'saturation': '1', 'lightness': '100'})
class HSVColor(Resource):
    def post(self):
        ledstrip('hsvcolor', request.args.get("hue"), request.args.get("saturation"), request.args.get("lightness"))
        return 'SUCCESS'


