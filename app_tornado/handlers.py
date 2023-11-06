from typing import Awaitable, Optional
from tornado.web import RequestHandler

from .config import CONFIG


class SiteHandler(RequestHandler):
    def get(self):
        self.render('index.html')

class FileHandler(RequestHandler):
    def get(self):
        self.render('index.html')

class UploadHandler(RequestHandler):
    def get(self):
        self.render('index.html')

class ErrorHandler(RequestHandler):
    def prepare(self):
        self.set_status(404)
        self.render("404.html")