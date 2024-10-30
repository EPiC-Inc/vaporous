# vaporous

This is a file server written in Python, created since Google Drive does not provide the necessary space for videos for my friends.
(Also, I wanted to challenge myself and not use an off-the-shelf file server)

[Check out their channel on YouTube](https://www.youtube.com/@ricebomb) (profanity abound)

## setup
Once everything is downloaded, you may need to add an initial user with `control_panel.py`.

Additionally, you may want to alter `config.toml` to store files in a different directory.

## config.toml specification
- `host`: The host to listen on.
- `port`: The port to listen on.
- `database_uri`: A SQLAlchemy database connection identifier.
- `banner`: A banner message to display. Optional.
- `upload_directory`: The directory to store and browse users' files from.
- `public_directory`: The directory within upload_directory where public files will be placed.
	Optional. When not defined, public files will be disabled.
- `public_access_requires_login`: Whether or not public file access needs an account. Optional, default is True.
- `public_access_level`: The minimum user access level to be able to access public files. Optional, default is all accounts can access. Setting this field to 1 or more means that public_access_requires_login will be True.
- `protected_public_directories`: Subfolders inside the public_directory that are write-protected to non-admins (access level 2). Optional.
- `self_enrollment`: Whether users can make an account themselves.
- `self_enrollment_passcode`: A passcode asked on the signup page.
