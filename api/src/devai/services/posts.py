from devai.models import ArticleEvidence, Slide


def serialize(db, p):
    evidence = db.query(ArticleEvidence).filter_by(post_id=p.id).first()
    return dict(
        id=p.id,
        title=p.title,
        caption=p.caption,
        status=p.status,
        version=p.version,
        created=p.created.isoformat(),
        slides=[
            dict(id=s.id, headline=s.headline, body=s.body, position=int(s.position))
            for s in db.query(Slide).filter_by(post_id=p.id).order_by(Slide.position).all()
        ],
        evidence=(
            {
                "source_title": evidence.source_title,
                "source_name": evidence.source_name,
                "source_url": evidence.source_url,
                "published_at": evidence.published_at.isoformat()
                if evidence.published_at
                else None,
                "retrieved_at": evidence.retrieved_at.isoformat(),
                "topic": evidence.topic,
                "editorial_angle": evidence.editorial_angle,
                "excerpt": evidence.excerpt[:1200],
            }
            if evidence
            else None
        ),
    )
