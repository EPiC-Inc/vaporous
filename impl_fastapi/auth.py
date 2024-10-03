"""Handles authentication and updating users in the DB."""

from hashlib import scrypt
from re import compile as regex_compile
from secrets import token_bytes
from typing import Optional

from database import engine
from objects import User

invalid_username_characters = regex_compile(r'<|>|:|"|\?|\/|\\|\||\*')

cost_parameter: int = 2**3
block_size: int = 8
parallelization: int = 4


def passkey_challenge() -> bytes:
    return token_bytes(14)


def validate_username(username: str) -> bool:
    return not bool(invalid_username_characters.search(username))


def add_user(username: str, /, password: Optional[str] = None, passkey_token=None) -> tuple[bool, str | set[str]]:
    username = username[:24]

    if not passkey_token and not password:
        return (False, "No way for the user to log in!")
    if not validate_username(username):
        return (False, "Username is not valid!")

    results: set[str] = set()
    if password:
        password = password[:512]
        password_hash = scrypt(
            password.encode(),
            salt=username.encode(),
            n=cost_parameter,
            r=block_size,
            p=parallelization,
            dklen=64,
        )
        print(password_hash)
        results.add("password")
    if passkey_token:
        results.add("passkey")
    return (True, results)
    # print(User(username=username, password=password_hash))


# print(add_user("test", password="test2")) # TEMP
