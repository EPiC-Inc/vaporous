from tomllib import load as toml_load
from types import SimpleNamespace

CONFIG = {}
with open('app/config.toml', 'rb') as config_file:
    CONFIG = toml_load(config_file)
CONFIG = SimpleNamespace(**CONFIG)