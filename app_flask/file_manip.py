from math import floor, log, pow
from os import PathLike, path, scandir
from pathlib import Path
from re import compile
from types import SimpleNamespace

from flask import send_from_directory
from werkzeug.wrappers.response import Response

from . import CONFIG

dot_re = compile(r'\.\.+')

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(floor(log(size_bytes, 1024)))
   p = pow(1024, i)
   s = round(size_bytes / p, 2)
   return f"{s}{size_name[i]}"

def list_files(current_directory: str | PathLike) -> dict:
    current_directory = dot_re.sub(r'.', str(current_directory))
    full_directory = path.join(path.abspath(CONFIG.upload_directory), current_directory)
    results = {}
    with scandir(full_directory) as files:
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
                    icon = 'icon-archive'
                case _:
                    if entry.is_dir():
                        icon = 'icon-dir'
                    else:
                        icon = 'icon-file'
            results[entry.name] = SimpleNamespace(**{
                'type': 'file' if entry.is_file() else 'dir',
                'icon': icon,
                'size': convert_size(entry.stat().st_size),
                'path': Path(path.join(current_directory, entry.name)).as_posix()
                })

    return results

def retrieve(file_path: str | PathLike) -> Response:
    #TODO - verify access of user
    file_path = dot_re.sub(r'.', str(file_path))
    return send_from_directory(CONFIG.upload_directory,
                               file_path,
                               as_attachment=False)
