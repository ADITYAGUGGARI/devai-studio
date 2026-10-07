"""Single-instance daily draft discovery worker. Run exactly one replica."""
import datetime as dt
import os
import time
from zoneinfo import ZoneInfo
from daily import ingest
from main import Session, SourceCandidate, Post, Slide, Audit

TZ=ZoneInfo(os.getenv('DAILY_TIMEZONE','America/Chicago'))
HOUR=int(os.getenv('DAILY_HOUR','8'))

def should_run(now, last_date):
    return now.hour >= HOUR and now.date() != last_date

def run_forever():
    last_date=None
    while True:
        now=dt.datetime.now(TZ)
        if should_run(now,last_date):
            try:
                result=ingest(Session,SourceCandidate,Post,Slide,Audit)
                print('daily ingest',result,flush=True)
                last_date=now.date()
            except Exception as exc:
                print('daily ingest error',type(exc).__name__,flush=True)
        time.sleep(60)

if __name__=='__main__':
    run_forever()
