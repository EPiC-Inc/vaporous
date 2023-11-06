from app_flask import app, CONFIG

app.run(
    host=CONFIG.host,
    port=CONFIG.port,
    debug=True
)