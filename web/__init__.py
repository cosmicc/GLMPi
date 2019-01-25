import logging
from configparser import ConfigParser

from flask import Flask
from loguru import logger as log
from modules.extras import str2bool

config = ConfigParser()
config.read('/etc/glmpi.conf')
ismaster = str2bool(config.get('master_controller', 'enabled'))
access_log = str2bool(config.get('general', 'access_log'))


@log.catch
def create_app(config_object):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    app.logger.disabled = True
    flog = logging.getLogger('werkzeug')
    if access_log:
        flog.addHandler(logging.FileHandler('/var/log/access.log'))
    else:
        flog.disabled = True
    register_extensions(app)
    register_blueprints(app)
    # security.init_app(app, register_blueprint=True)
    return app


@log.catch
def register_blueprints(app):
    from .restapi.views import restapi
    app.register_blueprint(restapi, url_prefix='/api')
    if ismaster:
        from .masterapi.views import masterapi
        app.register_blueprint(masterapi, url_prefix='/masterapi')


def register_extensions(app):
    if app.debug:
        try:
            from flask_debugtoolbar import DebugToolbarExtension
            DebugToolbarExtension(app)
        except ImportError:
            pass
