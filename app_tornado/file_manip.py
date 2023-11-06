from os import PathLike, path, scandir
from re import compile

from . import CONFIG

# Compile a regex to find and replace directory traversal attacks
dot_re = compile(r'\.\.+')

def list_files(current_directory: str | PathLike) -> dict:
    # Might not hurt to cache the results of this function
    current_directory = dot_re.sub(r'.', str(current_directory))
    current_directory = path.join(CONFIG.upload_directory, current_directory)
    with scandir(current_directory) as can_see:
        result = {entry.name: 'file' if entry.is_file() else 'dir' for entry in can_see}
    return result
