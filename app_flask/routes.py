from flask import flash, redirect, render_template, request, session, url_for

from . import CONFIG, app
from .file_api import retrieve
from .auth import login, get_session


@app.route("/", methods=["GET", "POST"])
def index():
    if get_session(session.get("id", "")):
        return render_template("files.html", anchor_navigation=CONFIG.anchor_navigation)
    session.clear()
    return redirect(url_for("login_page"))


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        username = request.form.get("username", "")[:40]
        password = request.form.get("password", "")[:100]
        if session_id := login(username, password):
            session["id"] = session_id
            return redirect(url_for("index"))
        flash("invalid username or password", category="error")
    return render_template("login.html")


@app.route("/file", methods=["GET", "POST"])
@app.route("/file/<path:filename>")
def retrieve_file(filename=None):
    # Check token and/or access
    if not get_session(session.get("id", "")):
        return redirect(url_for("login_page"))
    if request.method == "POST":
        return "Not implemented", 501
    if not filename:
        return "No file selected"
    return retrieve(filename)


@app.errorhandler(404)
def page_not_found(e) -> tuple[str, int]:
    return render_template("404.html"), 404
