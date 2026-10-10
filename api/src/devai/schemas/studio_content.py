"""Validated editorial setup, timeline, and independent review contracts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContentOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    audience: str = Field(default="Software engineers", min_length=1, max_length=160)
    tone: Literal["Clear", "Analytical", "Conversational", "Editorial"] = "Clear"
    language: Literal["English"] = "English"
    slideCount: int = Field(default=8, ge=6, le=8)
    durationSec: int = Field(default=35, ge=30, le=40)
    voiceId: Literal["coral", "marin", "cedar", "alloy", "nova", "sage"] | None = "coral"
    subtitles: bool = True


class SetupInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topicId: str = Field(min_length=1, max_length=100)
    formats: list[Literal["carousel", "reel"]] = Field(min_length=1, max_length=2)
    options: ContentOptions = Field(default_factory=ContentOptions)

    @model_validator(mode="after")
    def unique_formats(self):
        if len(set(self.formats)) != len(self.formats):
            raise ValueError("Choose each output format once")
        return self


class SetupEdit(SetupInput):
    expectedRevision: int = Field(ge=1)


class GenerateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expectedRevision: int = Field(ge=1)
    confirmedFormats: list[Literal["carousel", "reel"]] = Field(min_length=1, max_length=2)
    capabilityRevision: str
    confirmedBudget: int = Field(ge=1, le=100)
    confirmed: Literal[True]


class SceneInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=100)
    headline: str = Field(min_length=3, max_length=100)
    body: str = Field(default="", max_length=200)
    script: str = Field(min_length=1, max_length=1000)
    durationSec: float = Field(ge=1, le=15, allow_inf_nan=False)


class SubtitleCue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str | None = Field(default=None, min_length=1, max_length=100)
    start: float = Field(ge=0, le=40, allow_inf_nan=False)
    end: float = Field(gt=0, le=40, allow_inf_nan=False)
    text: str = Field(min_length=1, max_length=1000)


class SubtitleStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fontSize: int = Field(default=52, ge=36, le=80)
    position: Literal["lower", "middle"] = "lower"
    bold: bool = False
    background: bool = False


class TimelineInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expectedRevision: int = Field(ge=1)
    scenes: list[SceneInput] = Field(min_length=3, max_length=12)
    caption: str = Field(min_length=1, max_length=2200)
    voiceId: Literal["coral", "marin", "cedar", "alloy", "nova", "sage"] | None = "coral"
    subtitles: bool = True
    subtitleCues: list[SubtitleCue] | None = Field(default=None, max_length=120)
    subtitleStyle: SubtitleStyle | None = None
    musicAssetId: str | None = Field(default=None, min_length=1, max_length=100)
    voiceGainDb: float = Field(default=0, ge=-60, le=6, allow_inf_nan=False)
    musicGainDb: float = Field(default=-18, ge=-60, le=6, allow_inf_nan=False)
    ducking: bool = True

    @model_validator(mode="after")
    def valid_timeline(self):
        if len(set(scene.id for scene in self.scenes)) != len(self.scenes):
            raise ValueError("Every scene must have a unique stable identifier")
        if not 30 <= sum(scene.durationSec for scene in self.scenes) <= 40:
            raise ValueError("Scene durations must total 30–40 seconds")
        previous = 0.0
        ids = [cue.id for cue in self.subtitleCues or [] if cue.id]
        if len(set(ids)) != len(ids):
            raise ValueError("Each subtitle cue needs a unique stable identifier")
        for cue in self.subtitleCues or []:
            if not previous <= cue.start < cue.end <= sum(s.durationSec for s in self.scenes):
                raise ValueError("Subtitle cues must be ordered, non-overlapping and fit the Reel")
            if not cue.text.strip():
                raise ValueError("Subtitle text must not be blank")
            previous = cue.end
        if self.subtitles and self.subtitleCues == []:
            raise ValueError("Add subtitle cues or reset them to the script")
        return self


class OutputAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expectedRevision: int = Field(ge=1)
    confirmed: Literal[True]
    confirmedBudget: int = Field(default=0, ge=0, le=100)


class ReviewInput(OutputAction):
    reviewedAssetIds: list[str] = Field(min_length=1, max_length=20)
    checklist: dict[Literal["sources", "claims", "assets", "caption"], Literal[True]]

    @model_validator(mode="after")
    def complete_checklist(self):
        if set(self.checklist) != {"sources", "claims", "assets", "caption"}:
            raise ValueError("Review sources, claims, every asset and the caption")
        return self


class ChangesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expectedRevision: int = Field(ge=1)
    notes: str = Field(min_length=3, max_length=2000)


class RestoreInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expectedRevision: int = Field(ge=1)
    targetRevision: int = Field(ge=1)
    confirmed: Literal[True]
