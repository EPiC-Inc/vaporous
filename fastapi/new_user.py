from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from objects import User


DATABASE_PATH = r"fastapi/database.db"
URL = r"sqlite+pysqlite:///" + DATABASE_PATH


engine = create_engine(URL, echo=True)

new_user = User(username="test_tester")

with Session(engine) as session:
    session.add(new_user)
    session.commit()
