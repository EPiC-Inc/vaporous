from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.wrappers.response import Response

from .config import CONFIG
from .file_manip import list_files, retrieve, save_file

composer = Blueprint("composer", __name__)


@composer.route("/dir_view/")
@composer.route("/dir_view/<path:base_directory>")
def compose_file_list(base_directory="") -> str | Response:
    # TODO - check if user has access
    # if not session.get("logged_in"):
    #     return redirect(url_for('index'))
    # session['current_path'] = base_directory
    viewable_files = list_files(base_directory)
    paths = []
    current_path = ""
    for path in base_directory.split("/"):
        if not path:
            continue
        current_path += path
        paths.append((current_path, path))
        current_path += "/"
    return render_template(
        "_file_list.html",
        paths=paths,
        files=viewable_files,
        anchor_navigation=CONFIG.anchor_navigation,
    )


@composer.post("/upload")
def upload_file():
    files = request.files.getlist("file")
    upload_path = request.form.get("uploadPath")
    if upload_path is None:
        return "No uploadPath!", 422
    if "file" not in request.files:
        return "No file part!", 422

    for file in files:
        save_file(upload_path, file)
    return "Success"


@composer.errorhandler(FileNotFoundError)
def handle_FileNotFoundError(e) -> str:
    return render_template("_file_list.html", files={})
