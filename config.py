class BaseConfig(object):
    DEBUG = False
    SECRET_KEY = 'testing_seckey'
    SWAGGER_UI_JSONEDITOR = True
    SECURITY_PASSWORD_SALT = 'secsalt'
    SECURITY_TRACKABLE = True
    SECURITY_REGISTERABLE = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_ECHO = True
