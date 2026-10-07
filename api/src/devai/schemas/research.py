from pydantic import BaseModel


class ResearchDraftInput(BaseModel):
    title: str
    url: str
    source: str = "Primary source"


class GenerateInput(BaseModel):
    title: str
    url: str
    excerpt: str
