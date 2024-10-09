"""Handles authentication and updating users in the DB."""

from hashlib import scrypt
from re import compile as regex_compile
from secrets import token_bytes
from typing import Optional

from sqlalchemy import select

from database import SessionMaker
from objects import User, PublicKey

INVALID_USERNAME_CHARACTERS = regex_compile(r'<|>|:|"|\?|\/|\\|\||\*')
USERNAME_LENGTH: int = 24

COST_PARAMETER: int = 2**12
BLOCK_SIZE: int = 8
PARALLELIZATION: int = 4
HASH_LENGTH: int = 32


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
    return stored_hash == computed_hash.hex()


def login_with_password(username: str, password: str) -> bool:
    """Used for password authentication."""
    username = username[:USERNAME_LENGTH]
    stored_hash: str | None = None
    with SessionMaker() as session:
        result = session.execute(select(User).where(User.username == username))
        for row in result:
            if len(row) > 1:
                print("THIS SHOULD NEVER OCCUR IF CONSTRAINTS ARE PROPERLY SET.")
                return False
            user: User = row[0]
            stored_hash = user.password
    return checkpw(password, stored_hash)


def add_user(username: str, *, password: Optional[str] = None, passkey_token=None) -> tuple[bool, str | set[str]]:
    username = username[:USERNAME_LENGTH]
    # TODO - check if username already exists
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
        stored_hash = f"{salt.hex()}${COST_PARAMETER}${BLOCK_SIZE}${PARALLELIZATION}${password_hash.hex()}"
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
