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
