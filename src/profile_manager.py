from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml


def load_profile(path: str) -> Dict[str, Any]:
    profile_path = Path(path).expanduser()
    with profile_path.open("r", encoding="utf-8") as handle:
        if profile_path.suffix.lower() == ".json":
            return json.load(handle)
        return yaml.safe_load(handle) or {}


def save_profile(profile: Dict[str, Any], path: str) -> None:
    profile_path = Path(path).expanduser()
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    with profile_path.open("w", encoding="utf-8") as handle:
        if profile_path.suffix.lower() == ".json":
            json.dump(profile, handle, indent=2)
            return
        yaml.safe_dump(profile, handle, sort_keys=False)
