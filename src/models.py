from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TrackMetadata:
    title: str
    artist: str = ""
    bpm: Optional[float] = None
    key: Optional[str] = None
    duration_seconds: Optional[int] = None
    energy: Optional[float] = None
    crate: Optional[str] = None
    path: Optional[str] = None


@dataclass
class CurrentTrackState:
    title: str
    bpm: Optional[float]
    key: Optional[str]
    time_remaining_seconds: Optional[int]
    set_elapsed_seconds: int = 0
    set_total_seconds: int = 3600

    @property
    def set_progress(self) -> float:
        if self.set_total_seconds <= 0:
            return 0.0
        return max(0.0, min(1.0, self.set_elapsed_seconds / self.set_total_seconds))


@dataclass
class SuggestedTrack:
    track: TrackMetadata
    score: float
    reasons: List[str] = field(default_factory=list)
