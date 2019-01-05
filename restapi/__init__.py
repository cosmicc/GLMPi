from flask import Flask

def create_app(config_object):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    #security.init_app(app, register_blueprint=True)
    return app

def register_blueprints(app):
    from .views.views import webapi
    app.register_blueprint(webapi, url_prefix='/api')

def register_extensions(app):
    if app.debug:
        try:
            from flask_debugtoolbar import DebugToolbarExtension
            DebugToolbarExtension(app)
        except ImportError:
            pass
