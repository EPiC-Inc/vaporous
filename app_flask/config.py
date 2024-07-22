from tomllib import load as toml_load
from pathlib import Path
from types import SimpleNamespace

CONFIG = {}
with open(Path(__file__).parent / "config.toml", "rb") as config_file:
    CONFIG = toml_load(config_file)
CONFIG = SimpleNamespace(**CONFIG)
