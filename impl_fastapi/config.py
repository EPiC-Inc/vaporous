"""Module to ensure config can be accessed from multiple modules."""

from pathlib import Path
from tomllib import load as toml_load
from types import SimpleNamespace

with open(Path(__file__).parent / "config.toml", "rb") as config_file:
    CONFIG = SimpleNamespace(**toml_load(config_file))
