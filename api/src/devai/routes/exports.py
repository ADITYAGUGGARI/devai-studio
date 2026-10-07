import hashlib
import json
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models import ArticleEvidence, Post, Slide
from devai.services.artwork import slide_hash

router = APIRouter(dependencies=[Depends(require_api_key)])


def read_image(post: Post, slide: Slide) -> bytes:
    if not slide.artwork_path or not Path(slide.artwork_path).is_file():
        raise HTTPException(409, "Generate the complete AI-native slide image first")
    return Path(slide.artwork_path).read_bytes()


@router.get("/posts/{id}/slides/{slide_id}/image")
def slide_image(id: str, slide_id: str, session_factory: SessionFactory):
    with session_factory() as db:
        post, slide = db.get(Post, id), db.get(Slide, slide_id)
        if not post or not slide or slide.post_id != id:
            raise HTTPException(404)
        return Response(
            read_image(post, slide), media_type="image/png", headers={"Cache-Control": "no-store"}
        )


@router.get("/posts/{id}/export")
def export_post(id: str, session_factory: SessionFactory):
    with session_factory() as db:
        post = db.get(Post, id)
        if not post:
            raise HTTPException(404)
        slides = db.query(Slide).filter_by(post_id=id).order_by(Slide.position).all()
        if not slides:
            raise HTTPException(409, "No slides to export")
        stream = BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            reports = []
            for index, slide in enumerate(slides, 1):
                if slide.composition_mode != "ai_native" or slide.content_hash != slide_hash(
                    post.title,
                    {
                        "headline": slide.headline or "",
                        "body": slide.body or "",
                        "visual_direction": slide.visual_direction,
                    },
                ):
                    raise HTTPException(
                        409, f"Slide {index} needs regeneration from the current copy"
                    )
                raw = read_image(post, slide)
                if hashlib.sha256(raw).hexdigest() != json.loads(slide.validation_json or "{}").get(
                    "image_sha256"
                ):
                    raise HTTPException(409, f"Slide {index} image integrity changed; regenerate")
                archive.writestr(f"slide_{index:02d}.png", raw)
                reports.append(
                    {
                        "slide": index,
                        "headline": slide.headline,
                        "body": slide.body,
                        "validation": json.loads(slide.validation_json or "{}"),
                    }
                )
            archive.writestr("caption.txt", post.caption or "")
            evidence = db.query(ArticleEvidence).filter_by(post_id=id).first()
            archive.writestr(
                "sources.json",
                json.dumps(
                    {
                        "source_url": evidence.source_url,
                        "source_title": evidence.source_title,
                        "source_name": evidence.source_name,
                        "published_at": str(evidence.published_at),
                        "retrieved_at": str(evidence.retrieved_at),
                        "excerpt": evidence.excerpt,
                    }
                    if evidence
                    else {},
                    indent=2,
                ),
            )
            archive.writestr(
                "review.json",
                json.dumps(
                    {
                        "post_id": id,
                        "version": post.version,
                        "status": post.status,
                        "verification": json.loads(post.verification_json or "{}"),
                        "slides": reports,
                    },
                    indent=2,
                ),
            )
        return Response(
            stream.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="devai-{id}-v{post.version}.zip"'
            },
        )
