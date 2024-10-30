"""Handles authentication and updating users in the DB."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import scrypt
from os import environ
from re import compile as regex_compile
from sched import scheduler
from secrets import token_bytes
from threading import Lock, Thread
from typing import Optional
from uuid import uuid1

from sqlalchemy import select

from .database import SessionMaker
from .file_handler import create_home_folder, mark_home_folder_as_deleted
from .objects import PublicKey, User

# REVIEW - Now that we're using uuids as folder names, this should be fine to remove?
INVALID_USERNAME_CHARACTERS = regex_compile(r'<|>|:|"|\?|\/|\\|\||\*')
USERNAME_LENGTH: int = 24

COST_PARAMETER: int = 2**12
BLOCK_SIZE: int = 8
PARALLELIZATION: int = 4
HASH_LENGTH: int = 32

SECRET_KEY = environ.get("VAPOROUS_SECRET_KEY") or token_bytes(32).hex()
SESSION_EXPIRY: timedelta = timedelta(days=3)

invalidator = scheduler()


@dataclass(slots=True)
class Session:
    username: str
    user_id: str
    access_level: int
    expires: datetime
    session_id: str


sessions_lock = Lock()
sessions: dict[str, Session] = {}


def passkey_challenge() -> bytes:
    return token_bytes(14)


def validate_username(username: str) -> bool:
    if len(username) < 3 or len(username) > USERNAME_LENGTH:
        return False
    return not bool(INVALID_USERNAME_CHARACTERS.search(username))


def checkpw(password: str, stored_hash: str | None = None) -> bool:
    """Checks a password against an already computed hash.
    Will check even if stored_hash is None to avoid timing attacks.
    """
    if stored_hash:
        (
            stored_salt,
            stored_cost_parameter,
            stored_block_size,
            stored_parallelization,
            stored_hash,
        ) = stored_hash.split("$", 4)
    else:
        stored_salt = None
        stored_cost_parameter = None
        stored_block_size = None
        stored_parallelization = None

    computed_hash = scrypt(
        password.encode(),
        salt=bytes.fromhex(stored_salt) if stored_salt else b"",
        n=int(stored_cost_parameter) if stored_cost_parameter else 2,
        r=int(stored_block_size) if stored_block_size else 2,
        p=int(stored_parallelization) if stored_parallelization else 2,
        dklen=len(stored_hash) // 2 if stored_hash else 2,
    )
    return str(stored_hash) == computed_hash.hex()


def hashpw(password: str) -> str:
    password = password[:512]
    salt = token_bytes(16)
    password_hash = scrypt(
        password.encode(),
        salt=salt,
        n=COST_PARAMETER,
        r=BLOCK_SIZE,
        p=PARALLELIZATION,
        dklen=HASH_LENGTH,
    )
    return f"{salt.hex()}${COST_PARAMETER}${BLOCK_SIZE}${PARALLELIZATION}${password_hash.hex()}"


def login_with_password(username: str, password: str) -> bool:
    """Used for password authentication."""
    username = username[:USERNAME_LENGTH]
    stored_hash: str | None = None
    with SessionMaker() as engine:
        user: User | None = engine.execute(select(User).filter_by(username=username)).scalar_one_or_none()
        if user:
            stored_hash = user.password
    if user and checkpw(password, stored_hash):
        return True
    return False


def add_user(
    username: str, *, password: Optional[str] = None, passkey_token=None, user_level: Optional[int] = None
) -> tuple[bool, str | set[str]]:
    username = username.strip()
    with SessionMaker() as engine:
        result = engine.execute(select(User).where(User.username == username))
        for _ in result:
            return (False, "Username already exists!")

    if not passkey_token and not password:
        return (False, "No way for the user to log in!")
    if not validate_username(username):
        return (
            False,
            f"Username must be between 3 and {USERNAME_LENGTH} characters!",
        )

    authentication_methods: set[str] = set()
    stored_hash = None
    passkeys: list[PublicKey] = []
    if password:
        stored_hash = hashpw(password)
        authentication_methods.add("password")
    new_user = User(username=username, password=stored_hash)
    if user_level:
        new_user.user_level = user_level
    if passkey_token:
        authentication_methods.add("passkey")
        passkeys.append(PublicKey(owner=new_user.user_id, key=passkey_token, name="Initial Passkey"))
    create_home_folder(new_user.user_id.hex())
    # TODO - if passkey add and associate passkey
    with SessionMaker() as engine:
        engine.add(new_user)
        for key in passkeys:
            engine.add(key)
        engine.commit()
    return (True, authentication_methods)


def remove_user(username: str) -> tuple[bool, str]:
    user_id: str
    with SessionMaker() as engine:
        user: User | None = engine.execute(select(User).filter_by(username=username)).scalar_one_or_none()
        if not user:
            return (False, "User does not exist to be deleted!")
        engine.delete(user)
        engine.commit()
        user_id = user.user_id.hex()
    with sessions_lock:
        sessions_to_delete: list = []
        for session_id, session in sessions.items():
            if session.username == username:
                sessions_to_delete.append(session_id)
        for session_id in sessions_to_delete:
            del sessions[session_id]
    mark_home_folder_as_deleted(user_id)
    return (True, "User has been deleted")


def list_users() -> dict[str, dict]:
    users = {}
    with SessionMaker() as engine:
        result = engine.execute(select(User)).scalars()
        for user in result:
            users[user.username] = {
                "Access level": user.user_level,
                "# public keys": len(user.public_keys),
                "# shares": len(user.shares),
            }
    return users


def new_session(username: str, *, invalidate_previous_sessions: bool = True):
    if invalidate_previous_sessions:
        with sessions_lock:
            sessions_to_delete: list = []
            for session_id, session in sessions.items():
                if session.username == username:
                    sessions_to_delete.append(session_id)
            for session_id in sessions_to_delete:
                del sessions[session_id]
    with SessionMaker() as engine:
        user = engine.execute(select(User).where(User.username == username)).scalar_one()
        session_id = uuid1().hex
        with sessions_lock:
            sessions[session_id] = Session(
                username=username,
                user_id=user.user_id.hex(),
                access_level=user.user_level,
                expires=datetime.now() + SESSION_EXPIRY,
                session_id=session_id,
            )
    return session_id


def check_session(session_id) -> Session | None:
    with sessions_lock:
        if session := sessions.get(session_id):
            if datetime.now() > session.expires:
                del sessions[session_id]
            else:
                return session
    return None


def invalidate_session(session_id) -> None:
    with sessions_lock:
        try:
            del sessions[session_id]
        except:
            pass


def invalidate_sessions() -> None:
    sessions_to_delete = []
    with sessions_lock:
        for session_id, session in sessions.items():
            if datetime.now() > session.expires:
                sessions_to_delete.append(session_id)
        for session_id in sessions_to_delete:
            del sessions[session_id]
    invalidator.enter(36000, 1, invalidate_sessions)
    invalidator.run()


def change_password(username: str, *, new_password: str, old_password: Optional[str] = None) -> tuple[bool, str]:
    with SessionMaker() as engine:
        user: User | None = engine.execute(select(User).filter_by(username=username)).scalar_one_or_none()
        if user is not None:
            if (old_password is not None) and (not checkpw(old_password, user.password)):
                return (False, "Existing password is incorrect!")
        else:
            return (False, "User does not exist!")
        user.password = hashpw(new_password)
        engine.commit()
    return (True, "Password changed")
    # TODO - invalidate other sessions?


def change_username(old_username: str, new_username: str) -> tuple[bool, str]:
    with SessionMaker() as engine:
        user_already_exists: User | None = engine.execute(
            select(User).filter_by(username=new_username)
        ).scalar_one_or_none()
        if user_already_exists:
            return (False, "New username is already in use!")
            engine.expunge(user_already_exists)
        user: User | None = engine.execute(select(User).filter_by(username=old_username)).scalar_one_or_none()
        if not user:
            return (False, "User does not exist!")
        user.username = new_username
        engine.commit()
    with sessions_lock:
        for session in sessions.values():
            if session.username == old_username:
                session.username = new_username
    return (True, "Username changed")


def change_access_level(username: str, access_level: int) -> tuple[bool, str]:
    try:
        access_level = int(access_level)
    except ValueError:
        return (False, "Invalid access level - must be an integer")
    with SessionMaker() as engine:
        user: User | None = engine.execute(select(User).filter_by(username=username)).scalar_one_or_none()
        if not user:
            return (False, "User does not exist!")
        user.user_level = max(access_level, 0)
        engine.commit()
    with sessions_lock:
        for session in sessions.values():
            if session.username == username:
                session.access_level = access_level
    return (True, "User access level has changed")

Thread(target=invalidate_sessions, daemon=True).start()
