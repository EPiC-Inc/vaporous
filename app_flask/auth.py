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
    print(username, stored_username, password_hash, stored_hash)
    # Prevents duplicate uuids just in case
    while SESSIONS.get(id := str(uuid4())):
        pass
    SESSIONS[id] = Session(
        username=username,
        user_level=user_level,
        home=f"home/{username}" if user_level > 0 else '.',
        expires=datetime.now() + SESSION_EXPIRY,
    )
    return id


def add_user(username: str, password: str | bytes) -> tuple[bool, str]:
    if not (username and password):
        return False, "Blank username and password"
    if len(username) > 40:
        return False, "Username too long"
    if not valid_username_regex.fullmatch(username):
        return False, "Invalid username"
    username = username.lower()
    if isinstance(password, str):
        password = password.encode()
    password_hash = scrypt(password, salt=username.encode(), **SCRYPT_SETTINGS)
    new_user = User(username, password_hash)
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
