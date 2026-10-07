"""FastAPI application assembly; run with `uvicorn devai.main:app`."""

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker

from devai.core.config import Settings
from devai.core.database import build_engine, initialize_database
from devai.routes import exports, posts, publishing, research, workflow
from devai.services.jobs import run_worker


def create_app(settings: Settings | None = None, *, engine=None) -> FastAPI:
    config = settings or Settings()
    database = engine if engine is not None else build_engine(config.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize_database(database)
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
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    # Exact publish path must precede the /posts/{id}/{action} workflow route.
    app.include_router(publishing.router, tags=["publishing"])
    app.include_router(posts.router, tags=["posts"])
    app.include_router(exports.router, tags=["exports"])
    app.include_router(research.router, tags=["research"])
    app.include_router(workflow.router, tags=["workflow"])
    return app


app = create_app()
