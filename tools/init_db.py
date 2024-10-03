"""Initializes the database with the proper columns."""

from pathlib import Path
from sqlite3 import connect
from sys import path
from typing import Optional

path.append("app_flask")

from objects import Share, User  # type: ignore

DB_LOCATION: str = str(Path("database.db"))


def gen_command(object_: object, object_name: str, alterations: Optional[dict] = None):
    cols = {}
    try:
        attributes = object_.__slots__  # type: ignore
    except AttributeError:
        attributes = object_.__dict__
    for attribute in attributes:
        cols[attribute] = "TEXT"

    if alterations and (alterations_items := alterations.items()):
        for alt_col, alt_data in alterations_items:
            cols[alt_col] = alt_data

    cols = [f"{col_name} {data_type}" for col_name, data_type in cols.items()]
    table_command = f"CREATE TABLE IF NOT EXISTS {object_name.replace('.', '_')}({', '.join(cols)}) WITHOUT ROWID"
    return table_command


objects = [User, Share]
object_names = ["Users", "Shares"]
alterations = [
    {"username": "TEXT PRIMARY KEY", "password": "BLOB", "level": "INTEGER"},
    {
        "id": "TEXT PRIMARY KEY",
        "user": 'TEXT NOT NULL REFERENCES "Users"("username")',
        "anonymous_access": "INTEGER",
    },
]

for o, name, alts in zip(objects, object_names, alterations):
    table_command = gen_command(o, name, alts)
    print(table_command)

    connection = connect(DB_LOCATION)
    cursor = connection.cursor()
    cursor.execute(table_command)
    connection.commit()
