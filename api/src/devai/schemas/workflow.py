from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["news", "tutorial", "architecture", "tools", "insight"]


class TopicInput(BaseModel):
    title: str = Field(min_length=5, max_length=500)
    url: str
    excerpt: str = Field(min_length=240, max_length=10000)
    source: str = Field(default="Manual source", max_length=200)
    category: Category = "news"
    published_at: datetime | None = None
    priority: int = Field(default=70, ge=0, le=100)


class TopicUpdate(BaseModel):
    priority: int | None = Field(default=None, ge=0, le=100)
    category: Category | None = None
    status: Literal["queued", "archived"] | None = None


class GenerateTopicInput(BaseModel):
    slide_count: int = Field(default=8, ge=6, le=8)
    artwork: bool = True
