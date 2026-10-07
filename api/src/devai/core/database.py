"""Database construction and request-scoped access; imports never create tables."""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import DateTime, create_engine, inspect, text
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
    # `create_all` does not add columns to existing development databases. Keep
    # this narrowly scoped compatibility migration until versioned migrations
    # replace startup schema creation.
    inspector = inspect(engine)
    if "article_evidence" in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns("article_evidence")}
        if "created_at" not in existing_columns:
            column_type = DateTime(timezone=True).compile(dialect=engine.dialect)
            with engine.begin() as connection:
                connection.execute(
                    text(f"ALTER TABLE article_evidence ADD COLUMN created_at {column_type}")
                )
                connection.execute(
                    text(
                        "UPDATE article_evidence SET created_at = retrieved_at "
                        "WHERE created_at IS NULL"
                    )
                )
    if "slides" in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns("slides")}
        missing_columns = {"visual_direction", "artwork_path"} - existing_columns
        if missing_columns:
            with engine.begin() as connection:
                for column_name in sorted(missing_columns):
                    connection.execute(text(f"ALTER TABLE slides ADD COLUMN {column_name} TEXT"))


def get_session_factory(request: Request) -> sessionmaker:
    return request.app.state.session_factory


SessionFactory = Annotated[sessionmaker, Depends(get_session_factory)]
