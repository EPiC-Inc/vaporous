"""Handles authentication and updating users in the DB."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import scrypt
from re import compile as regex_compile
from secrets import token_bytes
from typing import Optional
from uuid import uuid1

from sqlalchemy import select

from database import SessionMaker
from objects import User, PublicKey

INVALID_USERNAME_CHARACTERS = regex_compile(r'<|>|:|"|\?|\/|\\|\||\*')
USERNAME_LENGTH: int = 24

COST_PARAMETER: int = 2**12
BLOCK_SIZE: int = 8
PARALLELIZATION: int = 4
HASH_LENGTH: int = 32

SESSION_EXPIRY: timedelta = timedelta(days=3)

@dataclass(slots=True)
class Session:
    username: str
    expires: datetime


sessions: dict[str, Session] = {}


def passkey_challenge() -> bytes:
    return token_bytes(14)


def validate_username(username: str) -> bool:
    if len(username) > USERNAME_LENGTH:
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
    with SessionMaker() as session:
        user: User | None = session.execute(select(User).filter_by(username=username)).scalar_one_or_none()
        if user:
            stored_hash = user.password
    return checkpw(password, stored_hash)


def add_user(username: str, *, password: Optional[str] = None, passkey_token=None) -> tuple[bool, str | set[str]]:
    username = username[:USERNAME_LENGTH]
    with SessionMaker() as session:
        result = session.execute(select(User).where(User.username == username))
        for _ in result:
            return (False, "Username already exists!")

    if not passkey_token and not password:
        return (False, "No way for the user to log in!")
    if not validate_username(username):
        return (False, "Username is not valid!")

    authentication_methods: set[str] = set()
    stored_hash = None
    passkeys: list[PublicKey] = []
    if password:
        stored_hash = hashpw(password)
        authentication_methods.add("password")
    new_user = User(username=username, password=stored_hash)
    if passkey_token:
        authentication_methods.add("passkey")
        passkeys.append(PublicKey(owner=new_user.user_id, key=passkey_token, name="Initial Passkey"))
    # TODO - if passkey add and associate passkey
    with SessionMaker() as session:
        session.add(new_user)
        for key in passkeys:
            session.add(key)
        session.commit()
    return (True, authentication_methods)

def new_session(username: str, *, invalidate: bool = True):
    if invalidate:
        for session_id, session in sessions.items():
            if session.username == username:
                del sessions[session_id]
    session_id = uuid1().hex
    sessions[session_id] = Session(username=username, expires=datetime.now() + SESSION_EXPIRY)
    return session_id

def check_session(session_id) -> str | None:
    if (session := sessions.get(session_id)):
        if datetime.now() > session.expires:
            del sessions[session_id]
        else:
            return session.username
    return None

def change_password(username: str, *, new_password: str, old_password: Optional[str] = None) -> tuple[bool, str]:
    with SessionMaker() as session:
        user: User | None = session.execute(select(User).filter_by(username=username)).scalar_one_or_none()
        if user is not None:
            if (old_password is not None) and (not checkpw(old_password, user.password)):
                return (False, "Existing password is incorrect!")
        else:
            return (False, "User does not exist!")
        user.password = hashpw(new_password)
        session.commit()
    return (True, "Password changed")
    # with SessionMaker() as session:
    #     session.execute()

def change_username(old_username: str, new_username: str) -> tuple[bool, str]:
    with SessionMaker() as session:
        user_already_exists: User | None = session.execute(select(User).filter_by(username=new_username)).scalar_one_or_none()
        if user_already_exists:
            return (False, "New username is already in use!")
        user: User | None = session.execute(select(User).filter_by(username=old_username)).scalar_one_or_none()
        if not user:
            return (False, "User does not exist!")
        user.username = new_username
        session.commit()
    for session_id in sessions:
        if sessions[session_id].username == old_username:
            sessions[session_id].username = new_username
    return (True, "Username changed")

if __name__ == '__main__':
    choice = "choice"
    while choice:
        print("")
        print("Authentication Menu")
        print("1. Add user")
        print("2. Reset password")
        print("3. Change username")
        print("q. Quit")
        print("")
        choice = input("> ")
        match choice:
            case "1":
                new_username = input("Please provide the new username: ")
                new_password = token_bytes(8).hex()
                success, message = add_user(new_username, password=new_password)
                if success:
                    print("User added successfully")
                    print(f"New password: {new_password}")
                else:
                    print("Unable to add a new user!")
                    print(f"Reason: {message}")
            case "2":
                username = str(input("Please provide the username to reset: "))
                new_password = token_bytes(8).hex()
                success, message = change_password(username, new_password=new_password)
                if success:
                    print(f"Password reset to: {new_password}")
                else:
                    print("Unable to reset password!")
                    print(f"Reason: {message}")
            case "3":
                old = input("Old username: ")
                new = input("New username: ")
                success, message = change_username(old, new)
                if success:
                    print("Username changed")
                else:
                    print("Unable to change username!")
                    print(f"Reason: {message}")
            case _:
                break

        print("")
        print("Authentication Menu")
        print("1. Add user")
        print("2. Reset password")
        print("3. Change username")
        print("q. Quit")
        print("")