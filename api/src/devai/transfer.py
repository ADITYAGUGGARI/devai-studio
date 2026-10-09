"""Preserve and import a quiescent legacy SQLite workspace into an empty PostgreSQL DB."""

import argparse
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select

import devai.models  # noqa: F401
from devai.core.database import Base, build_engine, initialize_database


def transfer(source_path: str, target_url: str) -> dict:
    source_path = str(Path(source_path).resolve())
    source = build_engine("sqlite:///" + source_path)
    with source.connect() as connection:
        from devai.models import Job

        if connection.execute(
            select(func.count())
            .select_from(Job)
            .where(Job.status.in_(["running", "queued", "retry_wait"]))
        ).scalar():
            raise ValueError("Finish or stop active jobs before importing this workspace")
    backup = (
        Path(source_path).parent
        / ".local-data"
        / "backups"
        / f"workspace-{datetime.now(UTC):%Y%m%dT%H%M%S}.sqlite"
    )
    backup.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source_path) as original, sqlite3.connect(backup) as copy:
        original.backup(copy)
    initialize_database(source)
    target = build_engine(target_url)
    if target.dialect.name != "postgresql":
        raise ValueError("Target must be PostgreSQL")
    initialize_database(target)
    counts = {}
    with source.connect() as original, target.begin() as destination:
        for table in Base.metadata.sorted_tables:
            if destination.execute(select(func.count()).select_from(table)).scalar():
                raise ValueError(f"Target table {table.name} is not empty; import aborted")
        for table in Base.metadata.sorted_tables:
            rows = [dict(row) for row in original.execute(select(table)).mappings()]
            if rows:
                destination.execute(table.insert(), rows)
            counts[table.name] = len(rows)
    source.dispose()
    target.dispose()
    return {"backup": str(backup), "counts": counts}


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv(".env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="devai.db")
    args = parser.parse_args()
    import json

    print(json.dumps(transfer(args.source, os.environ["DATABASE_URL"]), indent=2))
