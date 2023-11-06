from tornado import ioloop, web

from . import api, handlers
from .config import CONFIG

app = web.Application([
        web.url(r'/', handlers.SiteHandler, name="index"),
        web.url(r'/api/(.*)', api.GetDirectory),
        web.url(r'/upload', handlers.UploadHandler),
        web.url(r'/file', handlers.FileHandler),
        web.url(r'/static/(.*)', web.StaticFileHandler, {
            "path": r"static"
        })
    ],
    template_path = r'app/templates',
    default_handler_class = handlers.ErrorHandler,
    debug = True
)

if __name__ == "__main__":
    app.listen(int(CONFIG.port))
    print(f"Starting server")
    ioloop.IOLoop.instance().start()
