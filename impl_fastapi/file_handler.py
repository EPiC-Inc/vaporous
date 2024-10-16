"""Module to handle file manipulation, usable from the main server as well as APIs."""

from os import PathLike
from pathlib import Path
from re import compile as regex_compile
from typing import Generator, Optional

from config import CONFIG
# from database import SessionMaker
# from objects import Share

from fastapi.responses import FileResponse

safe_path_regex = regex_compile(r"\.\.+")

# NOTE - Class based file handling uses a bit more memory (~3%) but is about 30% faster.
#       Limited memory on the server _may_ be an issue, will look at later.
#       Will also check for uploads / downloads

def get_upload_directory() -> Path:
    if not (UPLOAD_DIRECTORY := CONFIG.get("upload_directory")):  # type: ignore
        raise KeyError("upload_directory not set in config")
    if not (UPLOAD_DIRECTORY := Path(UPLOAD_DIRECTORY)).exists():
        raise FileNotFoundError("Upload directory specified in the config does not exist!")
    return UPLOAD_DIRECTORY

def create_home_folder(uuid: str) -> None:
    uuid = safe_path_regex.sub(".", uuid) # Also maybe unnecessary
    new_folder = get_upload_directory() / uuid
    if new_folder.exists():
        if new_folder.is_dir():
            return
        raise FileExistsError("Collision?? Home folder already exists and is not a directory!")
    new_folder.mkdir()

def list_files(base: PathLike[str] | str, subfolder: Optional[PathLike[str] | str] = None) -> list[dict] | None:
    UPLOAD_DIRECTORY = get_upload_directory()
    base = UPLOAD_DIRECTORY / base
    PUBLIC_DIRECTORY: Path | None = CONFIG.get("public_directory")

    if PUBLIC_DIRECTORY:
        PUBLIC_DIRECTORY = UPLOAD_DIRECTORY / safe_path_regex.sub(".", str(PUBLIC_DIRECTORY)) # NOTE - may be unnecessary?

    files = []
    if subfolder:
        subfolder = safe_path_regex.sub(".", str(subfolder))
        base = base / subfolder
    else:
        if (base != UPLOAD_DIRECTORY) and PUBLIC_DIRECTORY and (base != PUBLIC_DIRECTORY):
            if PUBLIC_DIRECTORY.exists(follow_symlinks=False) and (PUBLIC_DIRECTORY.is_dir()):
                files.append({
                    "name": PUBLIC_DIRECTORY.name,
                    "path": r"/".join(PUBLIC_DIRECTORY.parts[1:]),
                    "is_directory": True,
                    "type": "public_directory"
                })
    if not base.exists() or not base.is_dir():
        return None
    for child in base.iterdir():
        if (is_directory := child.is_dir()):
            type_ = "directory"
        else:
            match child.suffix:
                case ".txt":
                    type_ = "document"
                case _:
                    type_ = "file"
        files.append({
            "name": child.name,
            "path": r"/".join(child.parts[2:]),
            "is_directory": is_directory,
            "type": type_
        })
    files.sort(key=lambda f: f.get("name"))
    files.sort(key=lambda f: f.get("is_directory"))
    files.sort(key=lambda f: f.get("type") == "public_directory", reverse=True)
    return files

def get_file(base: PathLike[str] | str, file_path: PathLike[str] | str) -> FileResponse | None:
    file_path = safe_path_regex.sub(".", str(file_path))
    file_path = get_upload_directory() / base / file_path
    if not file_path.exists() or not file_path.is_file():
        return None
    return FileResponse(file_path)

class FileHandler:
    __slots__ = ("base",)

    if not (UPLOAD_DIRECTORY := CONFIG.get("upload_directory")):  # type: ignore
        raise KeyError("upload_directory not set in config")
    UPLOAD_DIRECTORY: Path = Path(UPLOAD_DIRECTORY)
    PUBLIC_DIRECTORY: Path | None = CONFIG.get("public_directory")
    if PUBLIC_DIRECTORY:
        PUBLIC_DIRECTORY = Path(safe_path_regex.sub(".", str(PUBLIC_DIRECTORY)))  # NOTE - may be unnecessary?

    def __init__(self, base: PathLike[str] | str):
        if not self.UPLOAD_DIRECTORY.exists(follow_symlinks=False):
            raise FileNotFoundError("Upload directory does not exist!")
        self.base: Path = self.UPLOAD_DIRECTORY / base

    def list_files(self, subfolder: Optional[PathLike[str] | str] = None) -> Generator[Path]:
        if subfolder:
            subfolder = safe_path_regex.sub(".", str(subfolder))
            yield from (self.base / subfolder).iterdir()
        else:
            yield from self.base.iterdir()
            if (self.base != self.UPLOAD_DIRECTORY) and (self.PUBLIC_DIRECTORY):
                if (public_directory := (self.UPLOAD_DIRECTORY / self.PUBLIC_DIRECTORY)).exists(follow_symlinks=False):
                    yield public_directory
