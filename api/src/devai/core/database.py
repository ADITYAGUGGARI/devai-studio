"""Database construction and request-scoped access; imports never create tables."""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str):
    options = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=options, pool_pre_ping=True)


def initialize_database(engine):
    # Import all models before creating the development schema.
    import devai.models  # noqa: F401

    Base.metadata.create_all(engine)


def get_session_factory(request: Request) -> sessionmaker:
    return request.app.state.session_factory


SessionFactory = Annotated[sessionmaker, Depends(get_session_factory)]
