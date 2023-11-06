from tornado import ioloop

from app_tornado import app, CONFIG

app.listen(int(CONFIG.get('port', 8080)))
print("Starting server")
ioloop.IOLoop.instance().start()