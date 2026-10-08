"""Each HTTP test owns its database and never changes process configuration."""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from devai.core.config import Settings
from devai.main import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("INSTAGRAM_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("INSTAGRAM_ACCOUNT_ID", raising=False)
    monkeypatch.setenv("ALLOW_DEV_API_KEY", "true")
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    database_url = os.getenv("TEST_DATABASE_URL")
    admin_engine, schema = None, None
    if database_url:
        admin_engine = create_engine(database_url)
        if admin_engine.dialect.name != "postgresql":
            raise ValueError("TEST_DATABASE_URL must use PostgreSQL")
        schema = "devai_test_" + uuid.uuid4().hex
        with admin_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(database_url, connect_args={"options": f"-csearch_path={schema}"})
    else:
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    app = create_app(
        Settings(admin_api_key="test-secret", background_worker_enabled=False, daily_enabled=False),
        engine=engine,
    )
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        engine.dispose()
        if admin_engine:
            with admin_engine.begin() as connection:
                connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
            admin_engine.dispose()


@pytest.fixture
def ready_post(client, tmp_path):
    """Synthetic provider assets for approval/publishing tests; no external calls."""
    import hashlib
    import json
    import uuid
    from io import BytesIO

    from PIL import Image

    from devai.models import ArticleEvidence, Post, Slide
    from devai.services.artwork import slide_hash

    def create():
        source_url = "https://example.com/verified-source/" + str(uuid.uuid4())
        response = client.post(
            "/posts",
            headers={"x-api-key": "test-secret"},
            json={
                "title": "AI review",
                "caption": f"Original engineering analysis. Source: {source_url}",
                "slides": [
                    {"headline": f"Slide {index}", "body": f"Engineering explanation {index}."}
                    for index in range(1, 7)
                ],
            },
        )
        post_id = response.json()["id"]
        with client.app.state.session_factory.begin() as db:
            post = db.get(Post, post_id)
            post.verification_json = json.dumps(
                {"supported": True, "issues": [], "human_review_required": True}
            )
            db.add(
                ArticleEvidence(
                    id=str(uuid.uuid4()),
                    post_id=post_id,
                    source_url=source_url,
                    source_title="Source",
                    source_name="Fixture",
                    excerpt="Verified source evidence. " * 30,
                    topic="news",
                    editorial_angle="Practical engineering impact",
                )
            )
            for index, slide in enumerate(db.query(Slide).filter_by(post_id=post_id).all()):
                stream = BytesIO()
                Image.new("RGB", (1080, 1350), (20 + index, 80, 160)).save(stream, format="PNG")
                raw = stream.getvalue()
                path = tmp_path / f"{slide.id}.png"
                path.write_bytes(raw)
                slide.artwork_path, slide.composition_mode = str(path), "ai_native"
                slide.validation_json = json.dumps(
                    {
                        "passed": True,
                        "issues": [],
                        "image_sha256": hashlib.sha256(raw).hexdigest(),
                        "human_review_required": True,
                    }
                )
                slide.content_hash = slide_hash(
                    post.title,
                    {
                        "headline": slide.headline,
                        "body": slide.body,
                        "visual_direction": slide.visual_direction,
                    },
                )
        return post_id

    return create
