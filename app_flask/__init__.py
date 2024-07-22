"""DO NOT AUTO-FORMAT THIS FILE."""
from pathlib import Path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .config import CONFIG
from .objects import Base


app = Flask(__name__)

app.secret_key = "insecure key please change"
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["MAX_CONTENT_LENGTH"] = CONFIG.max_upload_size_mb * 1024 * 1024
app.config["SQLALCHEMY_DATABASE_URI"] = CONFIG.database_uri

# Set up the database
db = SQLAlchemy(model_class=Base)
db.init_app(app)
with app.app_context():
    db.create_all()


#TODO - restore what is necessary
# from .db_api import Database, Table
# DB_PATH = "database.db"
# db = Database(DB_PATH)
# user_table = Table("Users")
# share_table = Table("Shares")

# from . import routes

# Set up API endpoints
# from .api import api
# app.register_blueprint(api, url_prefix=r'/api')
# from .composer import composer
# app.register_blueprint(composer, url_prefix=r"/compose")
