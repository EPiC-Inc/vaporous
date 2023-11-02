from tornado.web import RequestHandler

from config import CONFIG


class FileHandler(RequestHandler):
    def get(self):
        self.write("TEST")