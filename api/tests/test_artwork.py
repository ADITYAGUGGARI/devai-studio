import uuid
from io import BytesIO

from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from devai.core.database import Base
from devai.models import Audit, Post, Slide
from devai.services import artwork


def _png_bytes(index=0):
    output = BytesIO()
    Image.new("RGB", (1080, 1350), (62 + index, 92, 142)).save(output, format="PNG")
    return output.getvalue()


def test_artwork_is_unique_persisted_and_invalidates_approval(monkeypatch, tmp_path):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    post_id = str(uuid.uuid4())
    slide_ids = [str(uuid.uuid4()) for _ in range(2)]
    with session.begin() as db:
        db.add(
            Post(
                id=post_id,
                title="A useful AI engineering story",
                caption="Source linked",
                status="approved",
                version="4",
            )
        )
        for index, slide_id in enumerate(slide_ids, 1):
            db.add(
                Slide(
                    id=slide_id,
                    post_id=post_id,
                    position=f"{index:03d}",
                    headline=f"Slide {index}",
                    body=f"A specific engineering idea for slide {index}.",
                    visual_direction=f"Distinct visual metaphor {index}",
                )
            )

    prompts = []

    def fake_generate(prompt, *, api_key=None, model=None):
        prompts.append(prompt)
        return _png_bytes(len(prompts))

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("CAROUSEL_ARTWORK_DIR", str(tmp_path))
    monkeypatch.setattr(artwork, "_generate_image", fake_generate)
    monkeypatch.setattr(artwork, "validate_image", lambda *_: {"passed": True, "issues": []})

    result = artwork.generate_post_artwork(session, post_id)

    assert result["generated_count"] == 2
    assert prompts[0] != prompts[1]
    with session() as db:
        post = db.get(Post, post_id)
        assert (post.status, post.version) == ("draft", "5")
        slides = db.query(Slide).filter_by(post_id=post_id).all()
        assert all(slide.artwork_path for slide in slides)
        assert all(Image.open(slide.artwork_path).size == (1080, 1350) for slide in slides)
        assert db.query(Audit).filter_by(post_id=post_id).count() == 2
