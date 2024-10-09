"""Handles authentication and updating users in the DB."""

from hashlib import scrypt
from re import compile as regex_compile
from secrets import token_bytes
from typing import Optional

from database import engine
from objects import User

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


def checkpw(password: str, stored_hash: str) -> bool:
    (
        stored_salt,
        stored_cost_parameter,
        stored_block_size,
        stored_parallelization,
        stored_hash,
    ) = stored_hash.split("$", 4)

    computed_hash = scrypt(
        password.encode(),
        salt=bytes.fromhex(stored_salt),
        n=int(stored_cost_parameter),
        r=int(stored_block_size),
        p=int(stored_parallelization),
        dklen=len(stored_hash) // 2,
    )
    return stored_hash == computed_hash.hex()


def add_user(username: str, *, password: Optional[str] = None, passkey_token=None) -> tuple[bool, str | set[str]]:
    username = username[:USERNAME_LENGTH]

    if not passkey_token and not password:
        return (False, "No way for the user to log in!")
    if not validate_username(username):
        return (False, "Username is not valid!")

    results: set[str] = set()
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
        print(stored_hash)  # TEMP
        print(checkpw(password, stored_hash))  # TEMP
        results.add("password")
    if passkey_token:
        results.add("passkey")
    # TODO - create User object and add it to database
    return (True, results)


if __name__ == "__main__":
    print(add_user("test", password="test2"))  # TEMP # nosec
