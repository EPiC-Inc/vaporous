from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.wrappers.response import Response

from . import CONFIG, app
from .file_manip import retrieve


@app.route('/', methods=["GET", "POST"])
def index() -> str | Response:
    if session.get('authentic'):
        return render_template('files.html',
                           anchor_navigation = CONFIG.anchor_navigation
                           )
    if request.method == "POST":
        if request.form.get('challenge-response') == "manifesto destiny":
            session['authentic'] = True
            return redirect(url_for('index'))
    return render_template('challenge.html')

@app.post('/challenge')
def challenge_response() -> Response:
    # if passwd correct set cookie
    return redirect(url_for('index'))

@app.route('/file', methods=["GET", "POST"])
@app.route('/file/<path:filename>')
def retrieve_file(filename=None) -> str | Response:
    #TODO - verify user access
    if request.method == "POST":
        return ''
    if not filename:
        return 'No file selected'
    return retrieve(filename)

@app.errorhandler(404)
def page_not_found(e) -> tuple[str, int]:
    return render_template('404.html'), 404
