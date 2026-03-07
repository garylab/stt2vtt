"""Minimal Pydantic models for fast-whisper STT input. Formal format: tests/test_data/jp2-input.json."""

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class Word(BaseModel):
    """Word-level timestamp. Minimal required: start, end, word."""

    model_config = ConfigDict(extra="ignore")

    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    word: str = Field(..., description="Word text")


class Segment(BaseModel):
    """Segment. Minimal required: start, end, text. Optional: words."""

    model_config = ConfigDict(extra="ignore")

    start: float = Field(..., description="Segment start time in seconds")
    end: float = Field(..., description="Segment end time in seconds")
    text: str = Field(..., description="Segment text")
    words: List[Word] = Field(default_factory=list, description="Word-level timestamps (optional)")
