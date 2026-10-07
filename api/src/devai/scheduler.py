"""Single-instance discovery worker. Restart history is not yet persisted."""

import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

from devai.core.config import Settings
from devai.core.database import build_engine, initialize_database
from devai.services.editorial_queue import collect_topics

logger = logging.getLogger(__name__)


def should_run(now, last_date, hour: int = 8):
    return now.hour >= hour and now.date() != last_date


def run_forever():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    timezone = ZoneInfo(settings.daily_timezone)
    engine = build_engine(settings.database_url)
    initialize_database(engine)
    session_factory = sessionmaker(bind=engine)
    last_date = None
    try:
        while True:
            now = datetime.now(timezone)
            if should_run(now, last_date, settings.daily_hour):
                try:
                    result = collect_topics(session_factory, now=now)
                    logger.info("Daily editorial run: %s", result)
                    last_date = now.date()
                except Exception:
                    logger.exception("Daily discovery failed")
            time.sleep(60)
    finally:
        engine.dispose()


if __name__ == "__main__":
    run_forever()
