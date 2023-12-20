"""Adds a user to the database"""

from app_flask import auth

NEW_USER = input("new username: ")
NEW_PASS = input("password: ")
NEW_LEVEL = input("user level (0 is admin, 99 default): ") or 99
success, msg = auth.add_user(NEW_USER, NEW_PASS, user_level=int(NEW_LEVEL))
assert success, f"User add failed: {msg}"
