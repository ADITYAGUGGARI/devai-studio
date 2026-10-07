from devai.models import Slide


def serialize(db, p):
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
    )
