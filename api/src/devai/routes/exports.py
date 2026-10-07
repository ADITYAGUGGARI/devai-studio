import zipfile
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from devai.core.auth import require_api_key
from devai.core.database import SessionFactory
from devai.models import Post, Slide
from devai.services.rendering import draw_slide as render_slide


def draw_slide(*args, **kwargs):
    try:
        return render_slide(*args, **kwargs)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/posts/{id}/slides/{slide_id}/image")
def slide_image(id: str, slide_id: str, session_factory: SessionFactory):
    with session_factory() as db:
        p = db.get(Post, id)
        s = db.get(Slide, slide_id)
        if not p or not s or s.post_id != id:
            raise HTTPException(404)
        slides = db.query(Slide).filter_by(post_id=id).order_by(Slide.position).all()
        return Response(
            draw_slide(
                s.headline or "",
                s.body or "",
                next((i for i, v in enumerate(slides, 1) if v.id == slide_id)),
                len(slides),
                artwork_path=s.artwork_path,
            ),
            media_type="image/png",
        )


@router.get("/posts/{id}/export")
def export_post(id: str, session_factory: SessionFactory):
    with session_factory() as db:
        p = db.get(Post, id)
        if not p:
            raise HTTPException(404)
        slides = db.query(Slide).filter_by(post_id=id).order_by(Slide.position).all()
        if not slides:
            raise HTTPException(409, "No slides to export")
        stream = BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for i, s in enumerate(slides, 1):
                z.writestr(
                    f"slide_{i:02d}.png",
                    draw_slide(
                        s.headline or "",
                        s.body or "",
                        i,
                        len(slides),
                        artwork_path=s.artwork_path,
                    ),
                )
            z.writestr("caption.txt", p.caption or "")
        return Response(
            stream.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="devai-{id}.zip"'},
        )
