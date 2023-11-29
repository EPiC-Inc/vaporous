try:
    from tomllib import load as toml_load
except:
    from tomli import load as toml_load # type: ignore
from types import SimpleNamespace

CONFIG = {}
with open(r'app_tornado/config.toml', 'rb') as config_file:
    CONFIG = toml_load(config_file)
CONFIG = SimpleNamespace(**CONFIG)
