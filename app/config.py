"""Module to ensure config can be accessed from multiple modules."""

from pathlib import Path
from tomllib import load as toml_load

CONFIG: dict

config_path = Path(__file__).parent / "config.toml"

if not config_path.exists():
    config_path.write_text((Path(__file__).parent / "config_default.toml").read_text())

with open(config_path, "rb") as config_file:
    CONFIG = toml_load(config_file)
