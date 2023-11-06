from os import PathLike, listdir, path

try:
    from . import CONFIG
except:
    from config import CONFIG

def list_files(current_directory: str | PathLike) -> zip:
    current_directory = path.join(CONFIG.upload_directory, current_directory)
    can_see = listdir(current_directory)
    files = map(lambda f: path.join(current_directory, f), can_see)
    return zip(can_see, [path.isfile(f) for f in files])

print(*list_files(''), sep=',')