from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.wrappers.response import Response

from . import CONFIG
from .auth import get_session
from .file_api import list_files, new_folder, retrieve, save_file

composer = Blueprint("composer", __name__)


@composer.route("/dir_view/")
@composer.route("/dir_view/<path:base_directory>")
def compose_file_list(base_directory="") -> str | Response:
    # TODO - check if user has access
    user = get_session(session.get("id", ""))
    if not user:
        return redirect(url_for("login_page"))
    home = user.home if user.user_level > 0 else "."
    viewable_files = list_files(f"{home}/{base_directory}")
    for file_ in viewable_files.values():
        file_.path = file_.path[len(user.home) :] if user.user_level > 0 else file_.path
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
def upload_file() -> tuple[str, int]:
    user = get_session(session.get("id", ""))
    if not user:
        return "Not authenticated", 401
    files = request.files.getlist("file")
    upload_path = request.form.get("uploadPath")
    if upload_path is None:
        return "No uploadPath!", 422
    if "file" not in request.files:
        return "No file part!", 422

    for file in files:
        save_file(f"{user.home}/{upload_path}", file)
    return "Success", 200


@composer.route("/new_folder", methods=["POST"])
def add_new_folder():
    user = get_session(session.get("id", ""))
    if not user:
        return "Not authenticated", 401
    data = request.json
    if not data:
        return "Data in invalid format, must be JSON", 400
    current_path = data.get("current_path")
    folder_name = data.get("folder_name")
    if not folder_name:
        return [False, "Folder name cannot be blank"]
    current_path = f"{user.home}/{current_path}"
    success = new_folder(current_path, folder_name)
    if success:
        return [True, "Success"]
    return [False, "Unable to create folder"]


@composer.route("/rename", methods=["POST"])
@composer.route("/rename/<path:to_rename>", methods=["POST"])
def rename_file(to_rename: str = "") -> tuple[str, int]:
    if not get_session(session.get("id", "")):
        return "Not authenticated", 401
    return "", 501


@composer.route("/delete", methods=["GET", "POST"])
@composer.route("/delete/<path:to_delete>", methods=["GET", "POST"])
def delete_file(to_delete: str = "") -> tuple[str, int]:
    if not get_session(session.get("id", "")):
        return "Not authenticated", 401
    return "", 501


@composer.errorhandler(FileNotFoundError)
def handle_FileNotFoundError(e) -> str:
    return render_template("_file_list.html", files={})
