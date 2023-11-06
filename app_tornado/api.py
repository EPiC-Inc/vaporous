from tornado.web import RequestHandler

class GetDirectory(RequestHandler):
    def get(self, path):
        self.write({"test":True})