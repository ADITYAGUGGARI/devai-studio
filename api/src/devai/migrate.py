"""Explicit migration CLI: python -m devai.migrate [upgrade|downgrade] [revision]."""

import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

from devai.core.database import build_engine


def migration_config(connection):
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parent / "migrations"))
    config.attributes["connection"] = connection
    return config


def run(engine, action="upgrade", revision="head"):
    with engine.begin() as connection:
        getattr(command, action)(migration_config(connection), revision)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(".env")
    action = sys.argv[1] if len(sys.argv) > 1 else "upgrade"
    target = sys.argv[2] if len(sys.argv) > 2 else "head" if action == "upgrade" else "-1"
    if action not in {"upgrade", "downgrade"}:
        raise SystemExit("Use upgrade or downgrade")
    run(build_engine(os.environ["DATABASE_URL"]), action, target)
