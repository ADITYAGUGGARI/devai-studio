from pydantic import BaseModel, Field


class SlideInput(BaseModel):
    headline: str = ""
    body: str = ""


class PostInput(BaseModel):
    title: str
    caption: str = ""
    slides: list[SlideInput] = Field(default_factory=list)


class UpdateInput(BaseModel):
    title: str | None = None
    caption: str | None = None


class SlideUpdate(BaseModel):
    headline: str | None = None
    body: str | None = None


class PublishInput(BaseModel):
    image_urls: list[str]
