"""Secure local Compose backup; optionally verify recovery in a disposable database."""

import argparse
import hashlib
import json
import os
import subprocess
import tarfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

load_dotenv(".env")
parser = argparse.ArgumentParser()
parser.add_argument("--verify-restore", action="store_true")
args = parser.parse_args()
url = make_url(os.environ["DATABASE_URL"])
if (
    url.host not in {"localhost", "127.0.0.1"}
    or url.database != "devai"
    or url.username != "devai"
):
    raise SystemExit(
        "This tool is restricted to the local Compose devai database. Use managed pg_dump/pg_restore for production."
    )
engine = create_engine(url)
with engine.connect() as connection:
    original_count = connection.execute(
        text("SELECT count(*) FROM public.posts")
    ).scalar()
directory = Path(".local-data/backups") / datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
directory.mkdir(parents=True, mode=0o700)
command = ["docker", "compose", "exec", "-T", "postgres"]
result = subprocess.run(
    command
    + [
        "pg_dump",
        "-U",
        "devai",
        "-d",
        "devai",
        "-Fc",
        "--schema=public",
        "--no-owner",
        "--no-privileges",
    ],
    capture_output=True,
    check=True,
)
dump = directory / "database.dump"
dump.write_bytes(result.stdout)
dump.chmod(0o600)
assets = directory / "assets.tar.gz"
with tarfile.open(assets, "w:gz") as archive:
    for name in ["carousel-artwork", "publishing-media"]:
        path = Path(".local-data") / name
        if path.exists():
            archive.add(path, arcname=str(path))
assets.chmod(0o600)
manifest = {
    path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in [dump, assets]
}
(directory / "manifest.json").write_text(
    json.dumps(
        {
            "created_at": datetime.now(UTC).isoformat(),
            "files": manifest,
            "posts": original_count,
        },
        indent=2,
    )
)
if args.verify_restore:
    database = "devai_restore_" + uuid.uuid4().hex
    subprocess.run(
        command + ["createdb", "-U", "devai", database], check=True, capture_output=True
    )
    try:
        subprocess.run(
            command
            + [
                "pg_restore",
                "-U",
                "devai",
                "-d",
                database,
                "--no-owner",
                "--no-privileges",
                "--clean",
                "--if-exists",
            ],
            input=dump.read_bytes(),
            check=True,
            capture_output=True,
        )
        restored = create_engine(url.set(database=database))
        with restored.connect() as connection:
            count = connection.execute(
                text("SELECT count(*) FROM public.posts")
            ).scalar()
            assert count == original_count
            assert connection.execute(
                text("SELECT version_num FROM public.alembic_version")
            ).scalar()
        restored.dispose()
        print("Disposable PostgreSQL restore verified; posts:", count)
    finally:
        subprocess.run(
            command + ["dropdb", "-U", "devai", database],
            check=True,
            capture_output=True,
        )
engine.dispose()
print("Backup saved:", directory)
