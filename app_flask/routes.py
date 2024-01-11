"""This module contains routes for the application."""
from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from . import CONFIG, app, share_table
from .auth import del_session, get_session, login, update_password
from .file_api import check_exists, list_files, retrieve


@app.route("/", methods=["GET", "POST"])
def index():
    user = get_session(session.get("id", ""))
    if user:
        return render_template(
            "files.html",
            anchor_navigation=CONFIG.anchor_navigation,
            username=user.username,
            user_level=user.user_level,
            user_home=f"home/{user.username}",
        )
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


@app.route("/user", methods=["GET", "POST"])
def user_settings():
    user = get_session(session.get("id", ""))
    if not user:
        return redirect(url_for("login_page"))
    if request.method == "POST":
        old_password = request.form.get("old_password", "")[:100]
        new_password = request.form.get("new_password", "")[:100]
        new_password_confirm = request.form.get("new_password_confirm", "")[:100]
        if old_password and new_password and new_password_confirm:
            if new_password == new_password_confirm:
                success, message = update_password(
                    user.username, old_password, new_password
                )
                if success:
                    flash("password successfully changed", category="success")
                else:
                    flash(f"error changing password: {message}", category="error")
            else:
                flash("new passwords do not match", category="error")
        else:
            flash("please fill out all fields", category="error")
    return render_template("user.html", username=user.username)


@app.route("/file", methods=["GET", "POST"])
@app.route("/file/<path:filename>")
def retrieve_file(filename=None):
    # Check token and/or access
    user = get_session(session.get("id", ""))
    if not user:
        return redirect(url_for("login_page"))
    if request.method == "POST":
        return "Not implemented", 501
    if not filename:
        return "No file selected"
    return retrieve(f"{user.base_dir}/{filename}", user_home=user.home_dir)


@app.route("/s/<id>")
@app.route("/s/<id>/<path:filename>")
def show_share(id: str, filename=None):
    print("SHARE")#TEMP
    if not id:
        abort(404)
    share = share_table.query(
        "sub_path, anonymous_access", where_column="id", where_data=[id]
    )
    if not share:
        abort(404)
    share_path, anon_access_allowed = share[0]
    original_share = share_path
    if filename:
        share_path = f"{share_path}/{filename}"
    if anon_access_allowed or get_session(session.get("id", "")):
        if (path := check_exists(share_path, absolute=False)) and (
            abs_path := check_exists(share_path)
        ):
            print(path)
            print(abs_path)
            if abs_path.is_file():
                return retrieve(path)
            folder_contents = list_files(path)
            return render_template(
                "shared_folder.html",
                share_id=id,
                share_name=check_exists(original_share).name,  # type: ignore
                folder_name=path.name,
                files=folder_contents,
            )
    return abort(401)


@app.route("/logout")
def logout():
    session_id = session.get("id")
    if session_id:
        del_session(session_id)
    session.clear()
    return redirect(url_for("login_page"))


@app.errorhandler(404)
def page_not_found(e) -> tuple[str, int]:
    return render_template("404.html"), 404
