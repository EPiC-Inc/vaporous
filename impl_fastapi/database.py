"""A separate module for the database to be accessed from other modules as needed."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import CONFIG
from objects import Base

if not (database_uri := CONFIG.get("database_uri")):
    raise KeyError("database_uri not found in config")

engine = create_engine(database_uri, connect_args={"check_same_thread": False})
SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
