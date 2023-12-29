# /compose API
These "frontend" API methods require a user session cookie and often return an HTML response to be displayed by the browser. Most often POST data is expected to be of type `application/json`.
There is currently no way to obtain a session cookie under this API.
All operations occur under the user's "base" directory, usually their home folder, or the `upload_directory` as specified in `config.toml`.

## Endpoints
### GET /dir_view/{directory} and POST /dir_view/
- `directory` (optional): the directory to display to the user.
Omission of `directory` will simply default to the user's base directory.
Returns an HTML depiction of all files and folders in the given `directory` that the user has access to.

### POST /upload
- `file` (required): files to upload. Must be a list of file objects.
- `uploadPath` (optional): the relative directory to store the files.
Uploads the files in the request to `uploadPath` under the user's base directory.

### POST /new_folder
- `folder_name` (required): the name of the new folder.
- `current_path` (optional): the relative directory in which to create the new folder.
Creates a new folder named `folder_name` under `current_path` under the user's base directory.

### POST /rename
Returns a blank string with a 501 error code.

### POST /delete
Returns a blank string with a 501 error code.