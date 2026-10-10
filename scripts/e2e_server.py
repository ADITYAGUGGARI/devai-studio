"""Real API server for browser/native tests; isolated PostgreSQL schema, no provider mocks."""

import json
import os
import uuid
from pathlib import Path

import uvicorn
from sqlalchemy import create_engine, text

os.environ.update(
    ALLOW_DEV_API_KEY="false",
    ADMIN_EMAIL="e2e@devai.test",
    ADMIN_PASSWORD="Isolated-e2e-password-12345",
)
from devai.core.config import Settings
from devai.main import create_app

url = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://devai:devai_local_only@127.0.0.1:5433/devai",
)
admin = create_engine(url)
if admin.dialect.name != "postgresql":
    raise SystemExit("E2E requires PostgreSQL")
schema = "devai_e2e_" + uuid.uuid4().hex
with admin.begin() as connection:
    connection.execute(text(f'CREATE SCHEMA "{schema}"'))
engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
app = create_app(
    Settings(
        background_worker_enabled=False,
        daily_enabled=False,
        cors_origins=("http://127.0.0.1:5182",),
    ),
    engine=engine,
)
fixture = os.getenv("LIVE_CAROUSEL_FIXTURE")
reel_fixture = None
if os.getenv("E2E_REEL_FIXTURE") == "true":
    from devai.core.database import initialize_database
    from e2e_reel_fixture import seed_reel

    initialize_database(engine)
    reel_fixture = seed_reel(app.state.session_factory)
if fixture:
    # Optional real provider output, copied into an isolated acceptance workspace.
    from devai.core.database import initialize_database
    from devai.models import ArticleEvidence, Post, Slide
    from devai.services.artwork import slide_hash

    initialize_database(engine)
    data = json.loads(Path(fixture).read_text())
    if len(data["slides"]) != 8 or not data.get("verification", {}).get("supported"):
        raise ValueError(
            "Fixture must be a verified real eight-slide provider artifact"
        )
    with app.state.session_factory.begin() as db:
        db.add(
            Post(
                id=data["id"],
                title=data["title"],
                caption=data["caption"],
                verification_json=json.dumps(data["verification"]),
            )
        )
        db.flush()
        evidence = data["evidence"]
        db.add(
            ArticleEvidence(
                id=str(uuid.uuid4()),
                post_id=data["id"],
                source_url=evidence["source_url"],
                source_title=evidence["source_title"],
                source_name=evidence["source_name"],
                excerpt=evidence["excerpt"],
                topic=evidence["topic"],
                editorial_angle=evidence["editorial_angle"],
            )
        )
        for slide in data["slides"]:
            path = str((Path(fixture).parent / f"{slide['position']}.png").resolve())
            db.add(
                Slide(
                    id=slide["id"],
                    post_id=data["id"],
                    position=f"{slide['position']:03d}",
                    headline=slide["headline"],
                    body=slide["body"],
                    visual_direction=slide.get("visual_direction"),
                    composition_mode="ai_native",
                    artwork_path=path,
                    content_hash=slide_hash(data["title"], slide),
                    validation_json=json.dumps(slide["validation"]),
                )
            )
try:
    uvicorn.run(app, host="127.0.0.1", port=8124)
finally:
    if reel_fixture:
        reel_fixture.cleanup()
    engine.dispose()
    with admin.begin() as connection:
        connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    admin.dispose()
