"""Environment configuration for the API and the single-instance scheduler."""

import os
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Settings:
    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./devai.db")
    )
    admin_api_key: str = field(default_factory=lambda: os.getenv("ADMIN_API_KEY", "local-dev-only"))
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
            if origin.strip()
        )
    )
    daily_timezone: str = field(
        default_factory=lambda: os.getenv("DAILY_TIMEZONE", "America/Chicago")
    )
    daily_hour: int = field(default_factory=lambda: int(os.getenv("DAILY_HOUR", "8")))

    background_worker_enabled: bool = field(
        default_factory=lambda: os.getenv("BACKGROUND_WORKER_ENABLED", "true").lower() == "true"
    )
    daily_enabled: bool = field(
        default_factory=lambda: os.getenv("DAILY_ENABLED", "false").lower() == "true"
    )

    daily_generate_carousel: bool = field(
        default_factory=lambda: os.getenv("DAILY_GENERATE_CAROUSEL", "false").lower() == "true"
    )

    def __post_init__(self):
        if not self.admin_api_key:
            raise ValueError("ADMIN_API_KEY must not be empty")
        if not 0 <= self.daily_hour <= 23:
            raise ValueError("DAILY_HOUR must be between 0 and 23")
        ZoneInfo(self.daily_timezone)
