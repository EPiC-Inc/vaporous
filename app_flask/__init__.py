"""DO NOT AUTO-FORMAT THIS FILE."""
from flask import Flask
app = Flask(__name__)

# Read in the configuration file
from .config import CONFIG
app.secret_key = "insecure key please change"
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["MAX_CONTENT_LENGTH"] = CONFIG.max_upload_size_mb * 1024 * 1024

# Set up the database
from .db_api import Database, Table
DB_PATH = "database.db"
db = Database(DB_PATH)
user_table = Table("Users")
share_table = Table("Shares")

from . import routes

# Set up API endpoints
# from .api import api
# app.register_blueprint(api, url_prefix=r'/api')
from .composer import composer

app.register_blueprint(composer, url_prefix=r"/compose")
