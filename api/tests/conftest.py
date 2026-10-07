"""Each HTTP test owns its database and never changes process configuration."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from devai.core.config import Settings
from devai.main import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("INSTAGRAM_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("INSTAGRAM_ACCOUNT_ID", raising=False)
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    app = create_app(Settings(admin_api_key="test-secret"), engine=engine)
    with TestClient(app) as test_client:
        yield test_client
