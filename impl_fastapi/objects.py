from datetime import datetime
from uuid import uuid1

from sqlalchemy import BLOB, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column, relationship


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class PublicKey(Base):
    __tablename__ = "PublicKeys"

    owner: Mapped[bytes] = mapped_column(ForeignKey("Users.user_id"))
    key: Mapped[bytes] = mapped_column(BLOB(), primary_key=True)
    name: Mapped[str] = mapped_column(String(32))


class Share(Base):
    __tablename__ = "Shares"

    owner: Mapped[bytes] = mapped_column(ForeignKey("Users.user_id"))
    expires: Mapped[datetime] = mapped_column(DateTime(), nullable=True)
    path: Mapped[str] = mapped_column(String(1024))
    anonymous_access: Mapped[bool] = mapped_column(Boolean())
    user_whitelist: Mapped[str] = mapped_column(String(), nullable=True)  # TODO - Maybe make it an "association" class?
    share_id: Mapped[bytes] = mapped_column(BLOB(16), primary_key=True, default_factory=lambda: uuid1().bytes)


class User(Base):
    __tablename__ = "Users"

    username: Mapped[str] = mapped_column(String(24), unique=True)
    password: Mapped[str] = mapped_column(String(128), nullable=True, default=None)
    public_keys: Mapped[list[PublicKey]] = relationship("PublicKey", default_factory=list)
    reset_token: Mapped[str] = mapped_column(String(36), nullable=True, default=None)
    shares: Mapped[list[Share]] = relationship("Share", default_factory=list)
    user_id: Mapped[bytes] = mapped_column(BLOB(16), primary_key=True, default_factory=lambda: uuid1().bytes)
