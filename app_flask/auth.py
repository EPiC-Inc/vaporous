"""Authentication module."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import scrypt
from re import compile
from uuid import uuid4

from . import user_table
from .file_api import new_folder
from .objects import User


@dataclass(slots=True)
class Session:
    username: str
    user_level: int
    home: str
    expires: datetime


valid_username_regex = compile(r"^\w+$")

SCRYPT_SETTINGS = {"n": 2**12, "r": 8, "p": 1}

# TODO - implement in redis?
SESSIONS = {}
SESSION_EXPIRY = timedelta(hours=24)


def login(username: str, password: str | bytes):
    if not (username and password):
        return False
    username = username.lower()
    if isinstance(password, str):
        password = password.encode()
    result = user_table.query(
        "username, password, level", where_column="username", where_data=[username]
    )
    if not result:
        return False
    stored_username, stored_hash, user_level = result[0]
    password_hash = scrypt(password, salt=username.encode(), **SCRYPT_SETTINGS)
    if not str(password_hash) == str(stored_hash):
        return False
    # Prevents duplicate uuids just in case
    while SESSIONS.get(id := str(uuid4())):
        pass
    SESSIONS[id] = Session(
        username=username,
        user_level=user_level,
        home=f"home/{username}" if user_level > 0 else ".",
        expires=datetime.now() + SESSION_EXPIRY,
    )
    return id


def update_password(
    username: str, old_password: str | bytes, new_password: str | bytes
) -> tuple[bool, str]:
    result = user_table.query(
        "username, password", where_column="username", where_data=[username]
    )
    if not result:
        return False, "Somehow, you aren't a user!"
    stored_username, stored_hash = result[0]
    if isinstance(old_password, str):
        old_password = old_password.encode()
    if isinstance(new_password, str):
        new_password = new_password.encode()
    old_password_hash = scrypt(old_password, salt=username.encode(), **SCRYPT_SETTINGS)
    if not str(old_password_hash) == str(stored_hash):
        return False, "Invalid password"
    new_password_hash = scrypt(new_password, salt=username.encode(), **SCRYPT_SETTINGS)
    user_table.update_property(
        "password", str(new_password_hash), where_column="username", where_data=username
    )
    return True, "Success"


def add_user(
    username: str, password: str | bytes, *, user_level: int = 99
) -> tuple[bool, str]:
    if not (username and password):
        return False, "Blank username and password"
    if len(username) > 40:
        return False, "Username too long"
    if not valid_username_regex.fullmatch(username):
        return False, "Invalid username"
    username = username.lower()
    user_already_exists = user_table.query(
        "username", where_column="username", where_data=[username]
    )
    if user_already_exists:
        return False, "Username already exists"
    if isinstance(password, str):
        password = password.encode()
    password_hash = scrypt(password, salt=username.encode(), **SCRYPT_SETTINGS)
    new_user = User(username, password_hash, user_level)
    user_table.insert_object(new_user)
    new_folder("home", username)
    return True, "Success"


def get_session(session_id: str) -> Session | None:
    if not (session := SESSIONS.get(session_id)):
        return None
    if session.expires < datetime.now():
        del SESSIONS[session_id]
        return None
    return session
