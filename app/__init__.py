from tornado import ioloop, web

from . import handlers
from .config import CONFIG

app = web.Application([
        web.url(r'/', handlers.SiteHandler),
        web.url(r'/upload', handlers.UploadHandler),
        web.url(r'/file', handlers.FileHandler),
        web.url(r'/static/(.*)', web.StaticFileHandler, {
            "path": "static"
        })
    ],
    template_path = 'templates',
    # debug = True
)

if __name__ == "__main__":
    app.listen(int(CONFIG.get('port', 8080)))
    print(f"Starting server")
    ioloop.IOLoop.instance().start()
