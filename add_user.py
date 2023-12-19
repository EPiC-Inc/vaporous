"""Adds a user to the database"""

from app_flask import auth

NEW_USER = input("new username: ")
NEW_PASS = input("password: ")
success, msg = auth.add_user(NEW_USER, NEW_PASS)
assert success, f"User add failed: {msg}"
