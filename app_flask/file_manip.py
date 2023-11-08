from math import floor, log, pow
from os import PathLike, path, scandir

from flask import send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.wrappers.response import Response

from . import CONFIG


def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(floor(log(size_bytes, 1024)))
   p = pow(1024, i)
   s = round(size_bytes / p, 2)
   return f"{s}{size_name[i]}"

def list_files(current_directory: str | PathLike) -> dict:
    # Might not hurt to cache the results of this function
    current_directory = secure_filename(str(current_directory))
    current_directory = path.join(CONFIG.upload_directory, current_directory)
    results = {}
    with scandir(current_directory) as files:
        for entry in files:
            match path.splitext(entry.name)[1]:
                case '.txt':
                    icon = 'icon-text'
                case '.png' | '.jpg' | '.jpeg' | '.gif' | '.ico' | '.webp':
                    icon = 'icon-image'
                case '.wav' | '.mp3':
                    icon = 'icon-audio'
                case '.mp4' | '.webm':
                    icon = 'icon-video'
                case '.zip' | '.7z' | '.rar':
                    icon = 'icon-zip'
                case _:
                    if entry.is_dir():
                        icon = 'icon-dir'
                    else:
                        icon = 'icon-file'
            results[entry.name] = {
                'type': 'file' if entry.is_file() else 'dir',
                'icon': icon,
                'size': convert_size(entry.stat().st_size)
                }

    return results

def retrieve(filename: str | PathLike) -> Response:
    # filename = secure_filename(str(filename))
    return send_from_directory(CONFIG.upload_directory,
                               filename,
                               as_attachment=False)
