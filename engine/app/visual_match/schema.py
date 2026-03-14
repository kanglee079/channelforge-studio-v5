"""Visual Match Engine — Schema definitions for scene matching."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SceneIntent:
    """A single scene decomposed from a script."""
    scene_index: int
    spoken_text: str
    visual_intent: str  # e.g. "close-up of shark teeth / underwater predator motion"
    must_have_objects: list[str] = field(default_factory=list)
    must_not_show: list[str] = field(default_factory=list)
    mood: str = "neutral"
    location_hint: str = ""
    time_period: str = "modern"
    asset_preference: str = "video"  # video, image, both
    fallback_strategy: str = "photo_parallax"
    duration_sec: float = 5.0

    def to_dict(self) -> dict:
        return {
            "scene_index": self.scene_index,
            "spoken_text": self.spoken_text,
            "visual_intent": self.visual_intent,
            "must_have_objects": self.must_have_objects,
            "must_not_show": self.must_not_show,
            "mood": self.mood,
            "location_hint": self.location_hint,
            "time_period": self.time_period,
            "asset_preference": self.asset_preference,
            "fallback_strategy": self.fallback_strategy,
            "duration_sec": self.duration_sec,
        }


@dataclass
class CandidateAsset:
    """A candidate media asset for scene matching."""
    asset_id: int = 0
    source_provider: str = ""
    source_url: str = ""
    source_id: str = ""
    local_path: str = ""
    asset_type: str = "video"
    width: int = 0
    height: int = 0
    duration_sec: float = 0.0
    tags: list[str] = field(default_factory=list)
    license_notes: str = ""

    # Scores (populated by scorer)
    semantic_score: float = 0.0
    object_match_score: float = 0.0
    style_match_score: float = 0.0
    quality_score: float = 0.0
    negative_penalty: float = 0.0
    duplicate_penalty: float = 0.0
    final_score: float = 0.0
    explain: dict = field(default_factory=dict)


@dataclass
class SceneMatchResult:
    """Result of matching a scene to media assets."""
    scene_index: int
    scene: SceneIntent
    candidates: list[CandidateAsset] = field(default_factory=list)
    selected: CandidateAsset | None = None
    selected_clip_start: float = 0.0
    selected_clip_end: float = 0.0
    confidence_label: str = "low"  # low, medium, high
    status: str = "pending"  # pending, matched, pinned, review, failed


@dataclass
class TimelineEntry:
    """A single entry in the render timeline."""
    scene_index: int
    asset_id: int
    asset_type: str
    src_path: str
    trim_start: float = 0.0
    trim_end: float = 0.0
    motion_effect: str = "none"
    transition: str = "cut"
