import json
from datetime import UTC

from devai.models import ArticleEvidence, Slide
from devai.services.artwork import slide_hash


def utc_iso(value):
    return (value.replace(tzinfo=UTC) if value.tzinfo is None else value).isoformat()


def serialize(db, p):
    evidence = db.query(ArticleEvidence).filter_by(post_id=p.id).first()
    return dict(
        id=p.id,
        title=p.title,
        caption=p.caption,
        status=p.status,
        version=p.version,
        created=utc_iso(p.created),
        verification=json.loads(p.verification_json) if p.verification_json else None,
        slides=[
            dict(
                id=s.id,
                headline=s.headline,
                body=s.body,
                position=int(s.position),
                visual_direction=s.visual_direction,
                has_artwork=bool(s.artwork_path),
                composition_mode=s.composition_mode,
                validation=json.loads(s.validation_json) if s.validation_json else None,
                artwork_current=s.content_hash
                == slide_hash(
                    p.title,
                    {
                        "headline": s.headline or "",
                        "body": s.body or "",
                        "visual_direction": s.visual_direction,
                    },
                ),
            )
            for s in db.query(Slide).filter_by(post_id=p.id).order_by(Slide.position).all()
        ],
        evidence=(
            {
                "source_title": evidence.source_title,
                "source_name": evidence.source_name,
                "source_url": evidence.source_url,
                "published_at": utc_iso(evidence.published_at) if evidence.published_at else None,
                "retrieved_at": utc_iso(evidence.retrieved_at),
                "topic": evidence.topic,
                "editorial_angle": evidence.editorial_angle,
                "excerpt": evidence.excerpt,
            }
            if evidence
            else None
        ),
    )
