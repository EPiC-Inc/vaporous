from tornado import ioloop

from app_tornado import app, CONFIG

app.listen(int(CONFIG.port or 8080))
print("Starting server")
ioloop.IOLoop.instance().start()
