from tomllib import load as toml_load

CONFIG = {}
with open('config.toml', 'rb') as config_file:
    CONFIG = toml_load(config_file)