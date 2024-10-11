"""Module to handle file manipulation, usable from the main server as well as APIs."""

from os import PathLike
from pathlib import Path
from re import compile as regex_compile
from typing import Generator, Optional

from config import CONFIG
# from database import SessionMaker
# from objects import Share


safe_path_regex = regex_compile(r"\.\.+")

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

if __name__ == "__main__":
    fh = FileHandler("")
    print(*fh.list_files())
