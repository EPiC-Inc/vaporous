"""Module to handle file manipulation, usable from the main server as well as APIs."""

from pathlib import Path

from database import engine
from objects import Share


class FileHandler:
    __slots__ = ("base",)

    def __init__(self, base):
        self.base = Path(base)
