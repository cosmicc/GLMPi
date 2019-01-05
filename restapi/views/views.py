from flask import request, Blueprint
from flask_restplus import Api, Resource, fields

webapi = Blueprint('api', __name__)
api = Api(webapi, title='Galaxy Lighting Module RestAPI', version='1.0', doc='/')  # doc=False

@api.route('/sleep')
class DeviceSleep(Resource):
    def post(self):
        pass

