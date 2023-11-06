from os import environ
from types import SimpleNamespace

from flask import Flask

app = Flask(__name__)

# Read in the configuration file
from .config import CONFIG

app.secret_key = environ['MGMT_SECRET_KEY']

from . import routes

from .api import api
app.register_blueprint(api, url_prefix='/api')