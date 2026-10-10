"""Synthetic editorial/media fixture ONLY for isolated automated E2E servers.

Uses an actual decoded MP4. Does not simulate an AI provider or production success.
"""

import hashlib
import os
import tempfile
import uuid
from pathlib import Path

from devai.core.workspaces import scoped_factory
from devai.models import Topic, TopicApproval
from devai.models.studio import LEGACY_WORKSPACE
from devai.services.operations import topic_fingerprint
from devai.services.studio_content import timeline_hash, topic_packet
from devai.services.studio_documents import create_document, save_document
from devai.services.video import render_video
from PIL import Image


def seed_reel(factory):
    temporary = tempfile.TemporaryDirectory(prefix="devai-e2e-reel-")
    root = Path(temporary.name)
    os.environ["STUDIO_MEDIA_DIR"] = str(root)
    image = root / "test-only-image.png"
    Image.new("RGB", (1080, 1920), (23, 61, 50)).save(image)
    result = render_video(
        [{"image_path": str(image), "duration": 7} for _ in range(5)],
        audio_path=None,
        output_directory=root,
        progress=lambda *_: None,
    )
    scoped = scoped_factory(factory, LEGACY_WORKSPACE)
    with scoped.begin() as db:
        topic = Topic(
            id=uuid.uuid4().hex,
            url="https://example.com/test-only-reel-codec",
            title="Reel codec acceptance fixture",
            source="Isolated test fixture",
            excerpt="This is synthetic editorial evidence for automated codec and UI tests only. "
            * 10,
            category="architecture",
            verification="human_verified",
        )
        db.add(topic)
        db.flush()
        db.add(
            TopicApproval(
                topic_id=topic.id,
                fingerprint=topic_fingerprint(topic),
                approved_by="test-fixture",
            )
        )
        db.flush()
        source = topic_packet(db, topic.id)
        content = create_document(
            db,
            kind="content",
            actor="test-fixture",
            data={"title": topic.title, "topicId": topic.id, "source": source},
        )
        data = {
            "format": "reel",
            "source": source,
            "caption": "Synthetic fixture for E2E only. Source: " + source["url"],
            "scenes": [
                {
                    "id": uuid.uuid4().hex,
                    "headline": f"Codec test scene {index + 1}",
                    "body": "Test fixture only",
                    "script": "This is synthetic editorial evidence for automated codec and UI tests only.",
                    "durationSec": 7,
                }
                for index in range(5)
            ],
            "voiceId": None,
            "subtitles": False,
            "stage": "mp4_validated",
            "budgetRemaining": 0,
            "grounding": {
                "supported": True,
                "issues": [],
                "claims": [
                    {
                        "claim": "Test fixture",
                        "evidence_quote": "This is synthetic editorial evidence for automated codec and UI tests only.",
                    }
                ],
            },
        }
        output = create_document(
            db, kind="output", parent_id=content.id, actor="test-fixture", data=data
        )
        # Fixture lifetime is controlled by this isolated server, never by production.
        video = create_document(
            db,
            kind="asset",
            parent_id=output.id,
            actor="test-fixture",
            data={
                "kind": "video",
                "privatePath": result["path"],
                "sha256": hashlib.sha256(Path(result["path"]).read_bytes()).hexdigest(),
                "validation": result["validation"],
                "contentHash": timeline_hash(data),
            },
            state="validated",
        )
        data.update(
            renderId=video.id,
            renderHash=timeline_hash(data),
            renderValidation=result["validation"],
        )
        save_document(
            db,
            output.id,
            revision=output.revision,
            data=data,
            actor="test-fixture",
            state="draft",
            reason="Actual MP4 validated",
        )
    return temporary
