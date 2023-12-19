from datetime import datetime, timedelta
from threading import Lock
from uuid import uuid4
from hashlib import scrypt

from . import user_table
from .objects import User

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
        "username, password", where_column="username", where_data=[username]
    )
    if not result:
        return False
    stored_username, stored_hash = result[0]
    password_hash = scrypt(password, salt=username.encode(), **SCRYPT_SETTINGS)
    print(username, stored_username, password_hash, stored_hash)
    # Prevents duplicate uuids just in case
    while SESSIONS.get(id := str(uuid4())):
        pass
    SESSIONS[id] = (username, datetime.now() + SESSION_EXPIRY)
    return id

def add_user(username: str, password: str | bytes):
    if not (username and password):
        return False
    username = username.lower()
    if isinstance(password, str):
        password = password.encode()
    password_hash = scrypt(password, salt=username.encode(), **SCRYPT_SETTINGS)
    new_user = User(username, password_hash)
    user_table.insert_object(new_user)

def get_session(session_id: str):
    if not (session := SESSIONS.get(session_id)):
        return None
    user, expiry = session
    if expiry < datetime.now():
        return None
    return user
