"""FastAPI application assembly; run with `uvicorn devai.main:app`."""

import logging
import os
import threading
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker

from devai.core.config import Settings
from devai.core.database import build_engine, prepare_database
from devai.routes import (
    accounts,
    editorial,
    exports,
    operations,
    posts,
    publishing,
    research,
    workflow,
)
from devai.services.jobs import run_worker


def create_app(settings: Settings | None = None, *, engine=None) -> FastAPI:
    config = settings or Settings()
    database = engine if engine is not None else build_engine(config.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
        prepare_database(database)
        accounts.bootstrap_admin(app.state.session_factory)
        stop = threading.Event()
        worker = None
        if config.background_worker_enabled:
            worker = threading.Thread(
                target=run_worker, args=(app.state.session_factory, stop, config), daemon=True
            )
            worker.start()
        yield
        stop.set()
        if worker:
            worker.join(5)
        if not worker or not worker.is_alive():
            database.dispose()

    app = FastAPI(title="DevAI Studio API", lifespan=lifespan)
    app.state.settings = config
    app.state.session_factory = sessionmaker(bind=database)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type", "X-API-Key", "Authorization"],
    )

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    @app.get("/ready", tags=["health"])
    def ready():
        from sqlalchemy import text

        with database.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready", "database": database.dialect.name}

    @app.middleware("http")
    async def request_metrics(request, call_next):
        request_id = str(uuid.uuid4())
        started = time.monotonic()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        logging.getLogger("devai.requests").info(
            "request_id=%s method=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            response.status_code,
            int((time.monotonic() - started) * 1000),
        )
        return response

    # Exact publish path must precede the /posts/{id}/{action} workflow route.
    app.include_router(publishing.router, tags=["publishing"])
    app.include_router(accounts.router, tags=["accounts"])
    app.include_router(operations.router, tags=["operations"])
    app.include_router(posts.router, tags=["posts"])
    app.include_router(exports.router, tags=["exports"])
    app.include_router(research.router, tags=["research"])
    app.include_router(workflow.router, tags=["workflow"])
    app.include_router(editorial.router, tags=["editorial"])
    return app


app = create_app()
