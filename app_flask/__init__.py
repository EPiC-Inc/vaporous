from os import environ

from flask import Flask

app = Flask(__name__)

# Read in the configuration file
from .config import CONFIG

app.secret_key = 'insecure key please change'

from . import routes

# from .api import api
# app.register_blueprint(api, url_prefix=r'/api')
from .composer import composer
app.register_blueprint(composer, url_prefix=r'/compose')