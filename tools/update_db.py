"""Updates the database with the proper columns."""
from sys import path
from pathlib import Path
from sqlite3 import connect

path.append("app_flask")

from objects import User, Share  # type: ignore

DB_LOCATION: str = str(Path("database.db"))


def gen_command(object_: object, object_name: str, alterations: dict | None = None):
    table_commands = []
    cols = {}
    object_name = object_name.replace(".", "_")
    try:
        attributes = object_.__slots__  # type: ignore
    except AttributeError:
        attributes = object_.__dict__
    for attribute in attributes:
        cols[attribute] = "TEXT"

    with connect(DB_LOCATION) as connection:
        cursor = connection.cursor()
        old_columns_result = cursor.execute(
            f'select * from pragma_table_info("{object_name}") as tblInfo;'
        )
    old_columns = [entry[1] for entry in old_columns_result]
    print(old_columns)

    if alterations and (alterations_items := alterations.items()):
        for alt_col, alt_data in alterations_items:
            cols[alt_col] = alt_data

    cols = [f"{col_name} {data_type}" for col_name, data_type in cols.items()]
    table_commands.append(
        f"CREATE TABLE IF NOT EXISTS {object_name}_tmp({', '.join(cols)}) WITHOUT ROWID"
    )
    table_commands.append(
        f"INSERT INTO {object_name}_tmp ({', '.join(old_columns)}) SELECT {', '.join(old_columns)} FROM {object_name}"
    )
    table_commands.append(f"DROP TABLE {object_name}")
    table_commands.append(f"ALTER TABLE {object_name}_tmp RENAME TO {object_name}")
    return table_commands


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
    table_commands = gen_command(o, f"{name}", alts)
    print(table_commands)

    with connect(DB_LOCATION) as connection:
        cursor = connection.cursor()
        for cmd in table_commands:
            cursor.execute(cmd)
        connection.commit()
