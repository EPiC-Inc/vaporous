"""Module to ensure config can be accessed from multiple modules."""

from pathlib import Path
from tomllib import load as toml_load

CONFIG: dict

config_path = Path(__file__).parent / "config.toml"

if not config_path.exists():
    config_path.write_text((Path(__file__).parent / "config_default.toml").read_text())

with open(config_path, "rb") as config_file:
    CONFIG = toml_load(config_file)

if not CONFIG.get("upload_directory"):
    raise KeyError("upload_directory not found in config")

if not Path(CONFIG.get("upload_directory")).exists():
    # TODO - maybe create it automatically
    raise FileNotFoundError("Upload directory specified in the config does not exist!")

if CONFIG.get("public_directory") and not (public_path := Path(CONFIG.get("upload_directory")) / CONFIG.get("public_directory")).exists():
    public_path.mkdir()
