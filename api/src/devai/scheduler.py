"""Single-instance discovery worker. Restart history is not yet persisted."""

import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

from devai.core.config import Settings
from devai.core.database import build_engine, initialize_database
from devai.services.daily import run_daily_pipeline

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
    retry_after = None
    try:
        while True:
            now = datetime.now(timezone)
            if should_run(now, last_date, settings.daily_hour):
                if retry_after:
                    retry_at = datetime.fromisoformat(retry_after)
                    if retry_at.tzinfo is None:
                        retry_at = retry_at.replace(tzinfo=timezone)
                    if now < retry_at:
                        time.sleep(60)
                        continue
                try:
                    result = run_daily_pipeline(
                        session_factory, timezone=settings.daily_timezone, now=now
                    )
                    logger.info("Daily editorial run: %s", result)
                    if (
                        result["status"] in ("completed", "completed_with_warnings")
                        or result["attempt_count"] >= 3
                    ):
                        last_date = now.date()
                        retry_after = None
                    elif result["status"] == "failed":
                        retry_after = result.get("retry_after")
                except Exception:
                    logger.exception("Daily discovery failed")
            time.sleep(60)
    finally:
        engine.dispose()


if __name__ == "__main__":
    run_forever()
