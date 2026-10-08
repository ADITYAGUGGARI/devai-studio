"""Daily scheduler: persistent deduplicated jobs, no provider work in its loop."""

import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

from devai.core.config import Settings
from devai.core.database import build_engine, prepare_database
from devai.services.jobs import enqueue_daily
from devai.services.operations import settings_values


def should_run(now, last_date, hour: int = 8):
    return now.hour >= hour and now.date() != last_date


def run_forever():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    engine = build_engine(settings.database_url)
    prepare_database(engine)
    session_factory = sessionmaker(bind=engine)
    try:
        while True:
            schedule = settings_values(session_factory, settings)
            now = datetime.now(ZoneInfo(schedule["timezone"]))
            if schedule["daily_enabled"] and should_run(now, None, schedule["daily_hour"]):
                try:
                    job = enqueue_daily(
                        session_factory,
                        schedule["timezone"],
                        now=now,
                        generate_carousel=schedule["daily_generate_carousel"],
                    )
                    logging.info("Daily job %s: %s", job["id"], job["status"])
                except Exception:
                    logging.exception("Could not enqueue daily job")
            time.sleep(60)
    finally:
        engine.dispose()


if __name__ == "__main__":
    run_forever()
