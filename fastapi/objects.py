from uuid import uuid1

from sqlalchemy import BLOB, String, ForeignKey
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class PublicKey(Base):
    __tablename__ = "PublicKeys"

    owner: Mapped[bytes] = mapped_column(ForeignKey("Users.id"))
    key: Mapped[bytes] = mapped_column(BLOB(), primary_key=True)
    name: Mapped[str] = mapped_column(String(32))


class User(Base):
    __tablename__ = "Users"

    username: Mapped[str] = mapped_column(String(32))
    password: Mapped[bytes] = mapped_column(BLOB(64))
    public_keys: Mapped[list[PublicKey]] = relationship(back_populates="owner", default_factory=list)
    id: Mapped[bytes] = mapped_column(BLOB(16), primary_key=True, default_factory=lambda: uuid1().bytes)
