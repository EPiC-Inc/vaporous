"""Adds a user to the database"""
from importlib import import_module
from os import getcwd

print(getcwd())

from app_flask import auth

NEW_USER = input("new username: ")
NEW_PASS = input("password: ")
auth.add_user(NEW_USER, NEW_PASS)
