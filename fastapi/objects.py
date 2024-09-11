from datetime import datetime
from uuid import uuid1

from sqlalchemy import BLOB, Boolean, DateTime, String, ForeignKey
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
    reset_token: Mapped[str] = mapped_column(String(36))
    name: Mapped[str] = mapped_column(String(32))


class Share(Base):
    __tablename__ = "Shares"

    owner: Mapped[bytes] = mapped_column(ForeignKey("Users.id"))
    expires: Mapped[datetime] = mapped_column(DateTime(), nullable=True)
    path: Mapped[str] = mapped_column(String(1024))
    anonymous_access: Mapped[bool] = mapped_column(Boolean())
    user_whitelist: Mapped[str] = mapped_column(String(), nullable=True) #TODO - Maybe make it an "association" class?
    id: Mapped[bytes] = mapped_column(BLOB(16), primary_key=True, default_factory=lambda: uuid1().bytes)


class User(Base):
    __tablename__ = "Users"

    username: Mapped[str] = mapped_column(String(32), unique=True)
    password: Mapped[bytes | None] = mapped_column(BLOB(64), nullable=True, default=None)
    public_keys: Mapped[list[PublicKey]] = relationship("PublicKey", default_factory=list)
    shares: Mapped[list[Share]] = relationship("Share", default_factory=list)
    id: Mapped[bytes] = mapped_column(BLOB(16), primary_key=True, default_factory=lambda: uuid1().bytes)
