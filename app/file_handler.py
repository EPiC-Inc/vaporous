"""Module to handle file manipulation, usable from the main server as well as APIs."""

import lzma
from datetime import datetime
from os import PathLike
from pathlib import Path
from re import compile as regex_compile
from typing import Optional

from fastapi import UploadFile
from fastapi.responses import FileResponse
from functools import lru_cache
from sqlalchemy import select
from typing import Literal

from .config import CONFIG
from .database import SessionMaker
from .objects import Share, User


safe_path_regex = regex_compile(r"\.\.+")


def get_upload_directory() -> Path:
    if not (UPLOAD_DIRECTORY := CONFIG.get("upload_directory")):  # type: ignore
        raise KeyError("upload_directory not set in config")
    if not (UPLOAD_DIRECTORY := Path(UPLOAD_DIRECTORY)).exists():
        raise FileNotFoundError("Upload directory specified in the config does not exist!")
    return UPLOAD_DIRECTORY


def safe_join(base: PathLike[str] | str, subfolder: PathLike[str] | str) -> Path:
    base = safe_path_regex.sub(".", str(base))
    subfolder = safe_path_regex.sub(".", str(subfolder))
    subfolder = (Path(base) / subfolder).relative_to(base)
    return base / subfolder


def get_file_type(extension: str):
    match extension:
        case ".txt" | ".pdf" | ".md" | ".rtf" | ".rst" | ".odt" | ".doc" | ".docx" | ".xls" | ".xlsx":
            return "document"
        case ".jpg" | ".jpeg" | ".png" | ".webp" | ".gif" | ".bmp" | ".tiff" | ".avif" | ".apng":
            return "image"
        case ".mp3" | ".wav" | ".flac" | ".ogg" | ".aiff" | ".aac" | ".alac" | ".pcm" | ".dsd" | ".wma":
            return "audio"
        case ".mp4" | ".wmv" | ".webm" | ".mov" | ".avi" | ".mkv":
            return "video"
        case ".zip" | ".7z" | ".xz" | ".rar" | ".gz" | ".bz2":
            return "archive"
        case _:
            return "file"


def create_home_folder(uuid: str) -> None:
    uuid = safe_path_regex.sub(".", uuid)  # Also maybe unnecessary
    new_folder = get_upload_directory() / uuid
    if new_folder.exists():
        if new_folder.is_dir():
            return
        raise FileExistsError("Collision?? Home folder already exists and is not a directory!")
    new_folder.mkdir()


def mark_home_folder_as_deleted(uuid: str) -> None:
    uuid = safe_path_regex.sub(".", uuid)  # Also maybe unnecessary
    home_folder = get_upload_directory() / uuid
    new_folder = home_folder.with_name(f"acct_del-{home_folder.name}")
    if new_folder.exists():
        raise FileExistsError("Collision?? Deleted!!! home folder already exists!")
    home_folder.rename(new_folder)

@lru_cache
def get_file_size(file_path: Path) -> str:
    if file_path.is_dir():
        size_bytes = sum(f.stat().st_size for f in file_path.glob("**/*") if f.is_file())
    else:
        size_bytes = file_path.stat().st_size
    if size_bytes < 1_000:
        return f"{size_bytes}B"
    if size_bytes < 1_000_000:
        return f"{size_bytes / 1_000:.2f}KB"
    if size_bytes < 1_000_000_000:
        return f"{size_bytes / 1_000_000:.2f}MB"
    if size_bytes < 1_000_000_000_000:
        return f"{size_bytes / 1_000_000_000:.2f}GB"
    return "TB+"


async def list_files(
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
    directory_to_list = base
    if subfolder:
        directory_to_list = safe_join(base, subfolder)
    else:
        if (
            (directory_to_list != UPLOAD_DIRECTORY)
            and PUBLIC_DIRECTORY
            and (directory_to_list != PUBLIC_DIRECTORY)
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
    if not directory_to_list.exists() or not directory_to_list.is_dir():
        return None
    for child in directory_to_list.iterdir():
        is_protected = False
        if child.is_dir():
            type_ = "dir"
        else:
            type_ = get_file_type(child.suffix)
        for protected_path in CONFIG.get("protected_public_directories", []):
            if child.is_relative_to(PUBLIC_DIRECTORY / protected_path):
                is_protected = True
                break
        files.append(
            {
                "name": child.name,
                "path": str(child.relative_to(base)),
                "type": type_,
                "protected": is_protected,
                "size": get_file_size(child),
            }
        )
    files.sort(key=lambda f: f.get("name", ""))
    files.sort(key=lambda f: f.get("type") == "dir", reverse=True)
    files.sort(key=lambda f: f.get("type") == "public_directory", reverse=True)
    return files


async def get_file(
    base: PathLike[str] | str, file_path: PathLike[str] | str, direct: bool = False
) -> FileResponse | Literal["||video||"] | None:
    file_path = get_upload_directory() / safe_join(base, file_path)
    if not file_path.exists() or not file_path.is_file():
        return None
    if not direct:
        if get_file_type(file_path.suffix) == "video":
            return "||video||"
    return FileResponse(file_path)


async def upload_files(
    base: PathLike[str] | str,
    file_path: PathLike[str] | str,
    files: list[UploadFile],
    *,
    compression: Optional[int] = None,
) -> list[tuple[bool, str]]:
    results = []
    file_path = get_upload_directory() / safe_join(base, file_path)
    for file_object in files:
        filename = file_object.filename
        if not filename:
            results.append((False, "No filename??"))
            continue
        filename = safe_path_regex.sub(".", filename)
        if (file_path / filename).exists():
            results.append((False, "Already exists!"))
            continue
        if compression:
            with lzma.open(file_path / f"{filename}.xz", "wb", preset=compression) as compressed_file:
                compressed_file.write(await file_object.read())
        else:
            (file_path / filename).write_bytes(await file_object.read())
        results.append((True, "Success!"))
    return results


async def delete_file(base: PathLike[str] | str, file_path: PathLike[str] | str) -> tuple[bool, str]:
    share_path = safe_join(base, file_path)
    file_path = get_upload_directory() / share_path
    if not file_path.exists():
        return (False, "Cannot delete nonexistent file")
    if file_path.is_dir():
        for root, directories, files in file_path.walk():
            for file_ in files:
                (root / file_).unlink()
            for directory in directories:
                (root / directory).rmdir()
        file_path.rmdir()
    else:
        file_path.unlink()
    with SessionMaker() as engine:
        shares = engine.execute(select(Share).filter(Share.path.startswith(str(share_path)))).scalars()
        for share in shares:
            engine.delete(share)
        engine.commit()
    return (True, "File deleted")


async def new_folder(base: PathLike[str] | str, file_path: PathLike[str] | str, folder_name: str) -> tuple[bool, str]:
    file_path = get_upload_directory() / safe_join(base, file_path) / "new_folder"
    try:
        new_folder = file_path.with_name(folder_name)
    except ValueError:
        return (False, "Invalid folder name!")
    if new_folder.exists():
        return (False, "Name already exists!")
    new_folder.mkdir()
    return (True, "Folder created!")


async def rename(base: PathLike[str] | str, file_path: PathLike[str] | str, new_name: str) -> tuple[bool, str]:
    share_path = safe_join(base, file_path)
    file_path = get_upload_directory() / share_path
    if not file_path.exists():
        return (False, "Cannot rename nonexistent file / folder!")
    try:
        new_path = file_path.with_name(new_name)
    except ValueError:
        return (False, "Invalid name!")
    if new_path.exists():
        return (False, "Name already exists!")
    file_path.rename(new_path)
    with SessionMaker() as engine:
        shares = engine.execute(select(Share).filter(Share.path.startswith(str(share_path)))).scalars()
        for share in shares:
            share.path = share.path.replace(str(share_path), str(share_path.with_stem(new_name)))
        engine.commit()
    return (True, "Renamed!")


async def move(
    base: PathLike[str] | str, to_base: PathLike[str] | str, file_path: PathLike[str] | str, to: PathLike[str] | str
) -> tuple[bool, str]:
    file_path = get_upload_directory() / safe_join(base, file_path)
    to = get_upload_directory() / safe_join(to_base, to) / file_path.name
    if file_path == to:
        return (True, "Already here!")
    if to.exists():
        return (False, "A file or folder with the same name already exists here!")
    file_path.rename(to)
    return (True, "Renamed!")


async def list_shares(owner: str, filter: Optional[str] = None) -> list[dict]:
    if filter:
        filter = str(Path(owner) / filter)
    owned_shares: list[dict] = []
    with SessionMaker() as engine:
        shares = engine.execute(select(Share).filter_by(owner=bytes.fromhex(owner)).order_by(Share.path)).scalars()
        for share in shares:
            allow_list: list[str] = []
            if share.user_whitelist:
                for user_id in share.user_whitelist.split("$"):
                    if user := engine.execute(
                        select(User).filter_by(user_id=bytes.fromhex(user_id))
                    ).scalar_one_or_none():
                        allow_list.append(user.username)
            if filter and not share.path == filter:
                continue
            owned_shares.append(
                {
                    "id": share.share_id.hex(),
                    "shared_filename": Path(share.path).name,
                    "shared_file": "/".join(Path(share.path).parts[1:]),
                    "anonymous_access": share.anonymous_access,
                    "collaborative": share.collaborative,
                    "allowed_users": allow_list,
                }
            )
    return owned_shares


async def create_share(
    user_id: str,
    file_path: PathLike[str] | str,
    expires: Optional[datetime] = None,
    anonymous_access: bool = True,
    collaborative: bool = False,
    whitelist: Optional[list[str]] = None,
) -> tuple[bool, str]:
    # NOTE - since this method forces the share to be created under the user's home folder,
    #   remember to have anything shared from /public to return that canonical url
    #   I.E. DO NOT USE THIS METHOD FOR THE PUBLIC FOLDER
    # NOTE - The allow list overrides anonymous_access=True
    file_path = safe_path_regex.sub(".", str(file_path))
    file_path_to_save = safe_join(user_id, file_path)
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
        collaborative=collaborative if collaborative and file_path.is_dir() else False,
        user_whitelist="$".join(whitelist) if whitelist else None,
    )
    new_share_link = new_share.share_id.hex()
    with SessionMaker() as engine:
        engine.add(new_share)
        engine.commit()
    return (True, new_share_link)


async def delete_share(share_id: str, owner_id: str) -> tuple[bool, str]:
    with SessionMaker() as engine:
        share: Share | None = engine.execute(
            select(Share).filter_by(share_id=bytes.fromhex(share_id))
        ).scalar_one_or_none()
        if share and share.owner.hex() == owner_id:
            engine.delete(share)
            engine.commit()
        else:
            return (False, "Cannot delete nonexistent share!")
    return (True, "Share deleted")
