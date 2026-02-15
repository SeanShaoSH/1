from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FrameSample:
    """A labeled screenshot and its map coordinate."""

    image_path: str
    x: float
    y: float
    label: str


@dataclass(slots=True)
class MatchResult:
    """Similarity result against a sample."""

    sample: FrameSample
    score: float
