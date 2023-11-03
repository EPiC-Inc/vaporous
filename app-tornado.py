from tornado import ioloop, web

import handlers

from config import CONFIG


app = web.Application([
        web.url(r'/', handlers.FileHandler),
        web.url(r'/upload', handlers.FileHandler),
        web.url(r'/static/(.*)', web.StaticFileHandler, {
            "path": "static"
        })
    ],
    template_path = 'templates'
)

if __name__ == "__main__":
    app.listen(int(CONFIG.get('port', 8080)))
    print("Starting server")
    ioloop.IOLoop.instance().start()
