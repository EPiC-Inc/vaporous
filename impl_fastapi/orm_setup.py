from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from objects import Base

DATABASE_PATH = r"fastapi/database.db"
URL = r"sqlite+pysqlite:///" + DATABASE_PATH

if (db_path := Path(DATABASE_PATH)).exists():
    if (
        input("Database already exits!!! Clear database? > ")
        .casefold()
        .startswith("y")
    ):
        db_path.unlink()

engine = create_engine(URL, echo=True)
Base.metadata.create_all(engine)

# with Session(engine) as session:
#     result = session.execute(text("SELECT * FROM test"))
#     print(result.all())
