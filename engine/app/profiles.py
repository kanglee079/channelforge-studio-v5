from __future__ import annotations

import json
from pathlib import Path

from .config import settings
from .db import save_profile_json
from .models import ChannelProfile


def _profile_path(name: str) -> Path:
    return settings.profiles_root / f"{name}.json"


def list_profiles() -> list[str]:
    return sorted(p.stem for p in settings.profiles_root.glob("*.json"))


def load_profile(name: str) -> ChannelProfile:
    path = _profile_path(name)
    if not path.exists():
        raise RuntimeError(f"Profile not found: {name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    profile = ChannelProfile(**data)
    save_profile_json(profile.name, profile.to_dict())
    return profile


def sync_profiles() -> list[ChannelProfile]:
    profiles: list[ChannelProfile] = []
    for name in list_profiles():
        profiles.append(load_profile(name))
    return profiles
