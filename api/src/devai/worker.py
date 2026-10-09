"""Standalone worker; share the API database and asset directories."""

import logging
import threading

from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

from devai.core.config import Settings
from devai.core.database import build_engine, prepare_database
from devai.services.jobs import run_worker


def run_forever():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    engine = build_engine(settings.database_url)
    prepare_database(engine)
    try:
        run_worker(sessionmaker(bind=engine), threading.Event(), settings)
    finally:
        engine.dispose()


if __name__ == "__main__":
    run_forever()
