from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from .models import CurrentTrackState, SuggestedTrack


class FileStateBridge:
    def __init__(self, path: str) -> None:
        self.path = Path(path).expanduser()

    def publish(self, state: CurrentTrackState | None, suggestions: List[SuggestedTrack]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "current": asdict(state) if state else None,
            "suggestions": [
                {
                    "track": asdict(item.track),
                    "score": item.score,
                    "reasons": item.reasons,
                }
                for item in suggestions
            ],
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
