from os import environ

from flask import Flask

from . import routes
from .composer import composer
from .config import CONFIG

app = Flask(__name__)


app.secret_key = 'insecure key please change'
app.config['SESSION_COOKIE_SAMESITE'] = "Strict"
app.config['MAX_CONTENT_LENGTH'] = CONFIG.max_upload_size_mb * 1024 * 1024


# Set up API endpoints
# from .api import api
# app.register_blueprint(api, url_prefix=r'/api')
app.register_blueprint(composer, url_prefix=r'/compose')
