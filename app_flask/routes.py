from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.wrappers.response import Response

from . import CONFIG, app


@app.get('/')
def index() -> str:
    if session.get('logged_in'):
        return render_template('index.html')
    # return render_template('challenge.html')
    return render_template('files.html')

@app.post('/challenge')
def challenge_response() -> Response:
    # if passwd correct set cookie
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e) -> tuple[str, int]:
    return render_template('404.html'), 404
