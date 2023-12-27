from math import floor, log, pow
from pathlib import Path
from re import compile
from types import SimpleNamespace

from flask import send_from_directory
from werkzeug.datastructures import FileStorage
from werkzeug.security import safe_join
from werkzeug.wrappers.response import Response

from . import CONFIG

dot_re = compile(r"\.\.+")

EXTENSIONS = {
    ".txt": "icon-text",
    ".pdf": "icon-text",
    ".png": "icon-image",
    ".jpg": "icon-image",
    ".jpeg": "icon-image",
    ".gif": "icon-image",
    ".ico": "icon-image",
    ".webp": "icon-image",
    ".wav": "icon-audio",
    ".mp3": "icon-audio",
    ".mp4": "icon-video",
    ".webm": "icon-video",
    ".zip": "icon-archive",
    ".7z": "icon-archive",
    ".rar": "icon-archive",
}


def secure_filename(filename: str) -> str:
    return "".join(filter(lambda char: char not in "\\/?%*:|\"<>.", filename))


def convert_size(size_bytes: int) -> str:
    """Human-readable size string."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(floor(log(size_bytes, 1024)))
    p = pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s}{size_name[i]}"


def list_files(current_directory: str | Path) -> dict:
    """List the files under current_directory."""
    current_directory = dot_re.sub(r".", str(current_directory))
    full_directory = Path(CONFIG.upload_directory).absolute() / current_directory

    results = {}
    for entry in full_directory.iterdir():
        if entry.is_dir():
            icon = "icon-dir"
        else:
            extension = Path(entry.name).suffix
            icon = EXTENSIONS.get(extension, "icon-file")
        results[entry.name] = SimpleNamespace(
            **{
                "type": "file" if entry.is_file() else "dir",
                "icon": icon,
                "size": convert_size(entry.stat().st_size),
                "path": Path(current_directory).joinpath(entry.name).as_posix(),
            }
        )
    # This annoying conglomerate makes sure the folders are always first
    results = dict(sorted(results.items(), key=lambda entry: entry[0].casefold()))
    results = dict(sorted(results.items(), key=lambda entry: entry[1].type))

    return results


def save_file(directory: str | Path, file_obj: FileStorage) -> None:
    """Saves a file under directory."""
    directory = dot_re.sub(r".", str(directory))
    file_name = dot_re.sub(r".", str(file_obj.filename))
    file_name = secure_filename(file_name)
    file_name = safe_join(directory, file_name)
    file_name = safe_join(str(Path(CONFIG.upload_directory).absolute()), str(file_name))
    if file_name is None:
        raise ValueError("Invalid file name or upload path")

    c = 0
    while Path(file_name).exists():
        c += 1
        old_name = Path(str(file_obj.filename)).stem
        file_name = Path(file_name).with_stem(f"{old_name}_{c}")
    file_obj.save(file_name)


def retrieve(file_path: str | Path) -> Response:
    """Retrieves a file at file_path."""
    file_path = dot_re.sub(r".", str(file_path))
    return send_from_directory(
        Path(CONFIG.upload_directory).absolute(), file_path, as_attachment=False
    )


def new_folder(current_directory: str | Path, folder_name: str) -> Path | None:
    """Creates a new folder under the file tree."""
    current_directory = dot_re.sub(r".", str(current_directory))
    folder_name = secure_filename(folder_name[:40])
    if not folder_name:
        return None
    new_path = safe_join(CONFIG.upload_directory, current_directory)
    if not new_path:
        return None
    new_path = Path(new_path) / folder_name
    if new_path.exists():
        return None
    new_path.mkdir()
    if not new_path.exists():
        return None
    return new_path
