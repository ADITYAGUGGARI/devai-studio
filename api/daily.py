"""Daily ingestion of source-linked editorial candidates. Never auto-approves or publishes."""
import datetime as dt
import uuid
from sqlalchemy import Column, String, DateTime
from research import discover, create_editorial_draft
from source_urls import canonical_source_url

def register_source_model(Base):
    class SourceCandidate(Base):
        __tablename__ = 'source_candidates'
        id = Column(String, primary_key=True)
        url = Column(String(2048), nullable=False, unique=True)
        title = Column(String(500), nullable=False)
        source = Column(String(200), nullable=False)
        post_id = Column(String, nullable=False)
        created = Column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))
    return SourceCandidate

def ingest(session_factory, source_model, post_model, slide_model, audit_model, *, articles=None, limit=5):
    """Idempotent per canonical URL; callers must serialize concurrent invocations."""
    if articles is None:
        report = discover()
        articles = report['articles']
        errors = report['errors']
    else:
        errors = []
    created=[]; skipped=[]
    for article in articles[:limit]:
        try:
            url = canonical_source_url(article.get('url', ''))
        except ValueError:
            continue
        with session_factory.begin() as db:
            if db.query(source_model).filter_by(url=url).first():
                skipped.append(url)
                continue
            payload=create_editorial_draft({**article,'url':url})
            pid=str(uuid.uuid4())
            db.add(post_model(id=pid,title=payload['title'],caption=payload['caption'],status='draft'))
            for i, slide in enumerate(payload['slides'], 1):
                db.add(slide_model(id=str(uuid.uuid4()),post_id=pid,position=f'{i:03d}',headline=slide['headline'],body=slide['body']))
            db.add(source_model(id=str(uuid.uuid4()),url=url,title=article['title'][:500],source=article.get('source','Unknown')[:200],post_id=pid))
            db.add(audit_model(id=str(uuid.uuid4()),post_id=pid,event='daily discovery: unverified editorial scaffold; approval required'))
            created.append(pid)
    return {'created_post_ids':created,'skipped_urls':skipped,'feed_errors':errors,'verification_required':True}
