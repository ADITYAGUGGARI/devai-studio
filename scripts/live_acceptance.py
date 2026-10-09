"""Read and verify a real local carousel, without approving or publishing it."""

import argparse
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("post_id")
parser.add_argument("--job-id")
parser.add_argument("--base-url", default="http://127.0.0.1:8000")
args = parser.parse_args()
values = {
    k.strip().lower(): v.strip()
    for k, v in (
        line.split(":", 1)
        for line in Path(".local-data/admin-login.txt").read_text().splitlines()
        if ":" in line
    )
}
with httpx.Client(base_url=args.base_url, timeout=30) as client:
    response = client.post(
        "/auth/login", json={"email": values["email"], "password": values["password"]}
    )
    response.raise_for_status()
    client.headers["Authorization"] = "Bearer " + response.json()["token"]
    if args.job_id:
        job = client.get("/jobs/" + args.job_id).json()
        print({k: job[k] for k in ["status", "step", "progress", "total", "error"]})
        if job["status"] not in {"completed", "completed_with_warnings"}:
            raise SystemExit(2)
    post = next(p for p in client.get("/posts").json() if p["id"] == args.post_id)
    assert len(post["slides"]) == 8
    assert post["status"] != "published"
    assert post["verification"]["supported"]
    assert post["evidence"]["source_url"] in post["caption"]
    directory = Path(".local-data/live-acceptance") / post["id"]
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "post.json").write_text(json.dumps(post, indent=2))
    for slide in post["slides"]:
        assert slide["composition_mode"] == "ai_native"
        assert slide["artwork_current"] and slide["validation"]["passed"]
        response = client.get(f"/posts/{post['id']}/slides/{slide['id']}/image")
        response.raise_for_status()
        raw = response.content
        with Image.open(BytesIO(raw)) as image:
            assert image.size == (1080, 1350)
        (directory / f"{slide['position']}.png").write_bytes(raw)
    response = client.get(f"/posts/{post['id']}/export")
    response.raise_for_status()
    with ZipFile(BytesIO(response.content)) as archive:
        names = archive.namelist()
        assert len([n for n in names if n.endswith(".png")]) == 8
    (directory / "carousel.zip").write_bytes(response.content)
    evidence = {
        "post_id": post["id"],
        "version": post["version"],
        "slides": 8,
        "validated": True,
        "source_url": post["evidence"]["source_url"],
        "export_files": names,
        "status": post["status"],
    }
    (directory / "evidence.json").write_text(json.dumps(evidence, indent=2))
    print(evidence)
    client.post("/auth/logout").raise_for_status()
