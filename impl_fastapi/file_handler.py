"""Module to handle file manipulation, usable from the main server as well as APIs."""

from datetime import datetime
from os import PathLike
from pathlib import Path
from re import compile as regex_compile
from typing import Generator, Optional

from config import CONFIG

from database import SessionMaker
from objects import Share

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
    uuid = safe_path_regex.sub(".", uuid)  # Also maybe unnecessary
    new_folder = get_upload_directory() / uuid
    if new_folder.exists():
        if new_folder.is_dir():
            return
        raise FileExistsError("Collision?? Home folder already exists and is not a directory!")
    new_folder.mkdir()


def list_files(
    base: PathLike[str] | str, subfolder: Optional[PathLike[str] | str] = None, access_level: int = 0
) -> list[dict] | None:
    UPLOAD_DIRECTORY = get_upload_directory()
    base = UPLOAD_DIRECTORY / base
    PUBLIC_DIRECTORY: Path | None = CONFIG.get("public_directory")

    if PUBLIC_DIRECTORY:
        PUBLIC_DIRECTORY = UPLOAD_DIRECTORY / safe_path_regex.sub(
            ".", str(PUBLIC_DIRECTORY)
        )  # NOTE - may be unnecessary?

    files: list[dict] = []
    if subfolder:
        subfolder = safe_path_regex.sub(".", str(subfolder))
        base = base / subfolder
    else:
        if (
            (base != UPLOAD_DIRECTORY)
            and PUBLIC_DIRECTORY
            and (base != PUBLIC_DIRECTORY)
            and PUBLIC_DIRECTORY.exists(follow_symlinks=False)
            and (PUBLIC_DIRECTORY.is_dir())
            and access_level >= CONFIG.get("public_access_level", -1)
        ):
            files.append(
                {
                    "name": PUBLIC_DIRECTORY.name,
                    "path": r"/".join(PUBLIC_DIRECTORY.parts[1:]),
                    "is_directory": True,
                    "type": "public_directory",
                }
            )
    if not base.exists() or not base.is_dir():
        return None
    for child in base.iterdir():
        if child.is_dir():
            type_ = "dir"
        else:
            match child.suffix:
                case ".txt" | ".pdf" | ".md" | ".rtf" | ".rst" | ".odt" | ".doc" | ".docx" | ".xls" | ".xlsx":
                    type_ = "document"
                case ".jpg" | ".jpeg" | ".png" | ".webp" | ".gif" | ".bmp" | ".tiff" | ".avif" | ".apng":
                    type_ = "image"
                case ".mp3" | ".wav" | ".flac" | ".ogg" | ".aiff" | ".aac" | ".alac" | ".pcm" | ".dsd":
                    type_ = "audio"
                case ".mp4" | ".wmv" | ".webm" | ".mov" | ".avi" | ".mkv":
                    type_ = "video"
                case ".zip" | ".7z" | ".xz" | ".rar" | ".gz" | ".bz2":
                    type_ = "archive"
                case _:
                    type_ = "file"
        files.append({"name": child.name, "path": r"/".join(child.parts[2:]), "type": type_})
    files.sort(key=lambda f: f.get("name", ''))
    files.sort(key=lambda f: f.get("type") == "dir", reverse=True)
    files.sort(key=lambda f: f.get("type") == "public_directory", reverse=True)
    return files


def get_file(base: PathLike[str] | str, file_path: PathLike[str] | str) -> FileResponse | None:
    file_path = safe_path_regex.sub(".", str(file_path))
    file_path = get_upload_directory() / base / file_path
    if not file_path.exists() or not file_path.is_file():
        return None
    return FileResponse(file_path)


def create_share(
    user_id: str,
    file_path: PathLike[str] | str,
    expires: Optional[datetime] = None,
    anonymous_access: bool = True,
    whitelist: Optional[list[str]] = None,
) -> tuple[bool, str]:
    # NOTE - since this method forces the share to be created under the user's home folder,
    #   remember to have anything shared from /public to return that canonical url
    #   I.E. DO NOT USE THIS METHOD FOR THE PUBLIC FOLDER
    # NOTE - The allow list overrides anonymous_access=True
    file_path = safe_path_regex.sub(".", str(file_path))
    file_path_to_save = Path(user_id) / file_path
    if file_path == Path(user_id):
        return (False, "You cannot share your whole home folder!")
    file_path = get_upload_directory() / user_id / file_path
    if not file_path.exists():
        return (False, "File does not seem to exist!")
    new_share = Share(
        owner=bytes.fromhex(user_id),
        expires=expires,
        path=str(file_path_to_save),
        anonymous_access=anonymous_access,
        user_whitelist="$".join(whitelist) if whitelist else None,
    )
    new_share_link = new_share.share_id.hex()
    with SessionMaker() as engine:
        engine.add(new_share)
        engine.commit()
    return (True, new_share_link)


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
