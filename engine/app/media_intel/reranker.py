"""Reranker — Multi-factor scoring and reranking of asset candidates.

Final score = semantic_score * 0.45 + must_have_score * 0.20 + mood * 0.10
+ quality * 0.10 + aspect_ratio * 0.05 + duration * 0.05
- negative_penalty * 0.03 - duplicate_penalty * 0.02
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from typing import Any

from .scene_spec_builder import SceneSpec

logger = logging.getLogger(__name__)


@dataclass
class RankedCandidate:
    """Reranked asset candidate with detailed scoring."""
    asset_key: str = ""
    provider: str = ""
    source: str = ""
    local_path: str = ""
    asset_type: str = ""
    width: int = 0
    height: int = 0
    duration_sec: float = 0
    semantic_score: float = 0
    must_have_score: float = 0
    mood_style_score: float = 0
    quality_score: float = 0
    aspect_ratio_fit: float = 0
    duration_fit: float = 0
    negative_penalty: float = 0
    duplicate_penalty: float = 0
    final_score: float = 0
    confidence_label: str = "low"
    reasons: dict = None

    def to_dict(self) -> dict:
        return asdict(self)


class Reranker:
    """Multi-factor reranker for matching candidates against scene specs."""

    def __init__(self, recent_used_assets: set[str] | None = None):
        self.recent_used = recent_used_assets or set()

    def rerank(self, candidates: list[dict], spec: SceneSpec, target_aspect: str = "landscape") -> list[RankedCandidate]:
        """Rerank candidates for a scene, return sorted list."""
        ranked = []
        for c in candidates:
            rc = self._score_candidate(c, spec, target_aspect)
            ranked.append(rc)

        ranked.sort(key=lambda x: x.final_score, reverse=True)
        return ranked

    def _score_candidate(self, candidate: dict, spec: SceneSpec, target_aspect: str) -> RankedCandidate:
        """Compute detailed scores for a candidate."""
        rc = RankedCandidate(
            asset_key=candidate.get("asset_key", ""),
            provider=candidate.get("provider", ""),
            source=candidate.get("source", ""),
            local_path=candidate.get("local_path", ""),
            asset_type=candidate.get("asset_type", "image"),
            width=candidate.get("width", 0),
            height=candidate.get("height", 0),
            duration_sec=candidate.get("duration_sec", 0),
            reasons={},
        )

        # 1. Semantic similarity (from retriever)
        rc.semantic_score = min(1.0, candidate.get("similarity", 0))

        # 2. Must-have object coverage
        rc.must_have_score = self._check_must_have(candidate, spec.must_have_objects)

        # 3. Mood/style fit
        rc.mood_style_score = self._check_mood(candidate, spec.mood)

        # 4. Quality score (resolution-based)
        rc.quality_score = self._score_quality(rc.width, rc.height)

        # 5. Aspect ratio fit
        rc.aspect_ratio_fit = self._score_aspect(rc.width, rc.height, target_aspect)

        # 6. Duration fit (for video)
        rc.duration_fit = self._score_duration(rc.duration_sec, spec.duration_sec, rc.asset_type)

        # 7. Negative penalties
        rc.negative_penalty = self._check_negatives(candidate, spec.must_not_show)

        # 8. Duplicate penalty
        if rc.asset_key in self.recent_used:
            rc.duplicate_penalty = 1.0
            rc.reasons["duplicate"] = "Used recently in same channel"

        # Final weighted score
        rc.final_score = (
            rc.semantic_score * 0.45
            + rc.must_have_score * 0.20
            + rc.mood_style_score * 0.10
            + rc.quality_score * 0.10
            + rc.aspect_ratio_fit * 0.05
            + rc.duration_fit * 0.05
            - rc.negative_penalty * 0.03
            - rc.duplicate_penalty * 0.02
        )
        rc.final_score = max(0, min(1, rc.final_score))

        # Confidence label
        if rc.final_score >= 0.82:
            rc.confidence_label = "high"
        elif rc.final_score >= 0.65:
            rc.confidence_label = "medium"
        else:
            rc.confidence_label = "low"

        return rc

    def _check_must_have(self, candidate: dict, must_have: list[str]) -> float:
        if not must_have:
            return 0.7  # neutral
        tags = str(candidate.get("tags_json", "")).lower()
        key = candidate.get("asset_key", "").lower()
        hits = sum(1 for obj in must_have if obj.lower() in tags or obj.lower() in key)
        return min(1.0, hits / len(must_have))

    def _check_mood(self, candidate: dict, mood: str) -> float:
        if mood == "neutral":
            return 0.7
        tags = str(candidate.get("tags_json", "")).lower()
        return 0.9 if mood.lower() in tags else 0.5

    def _score_quality(self, width: int, height: int) -> float:
        if width >= 1920:
            return 1.0
        if width >= 1280:
            return 0.8
        if width >= 640:
            return 0.5
        return 0.3

    def _score_aspect(self, width: int, height: int, target: str) -> float:
        if width == 0 or height == 0:
            return 0.5
        ratio = width / height
        if target == "landscape":
            return 1.0 if ratio >= 1.3 else 0.5 if ratio >= 0.9 else 0.2
        else:  # portrait
            return 1.0 if ratio <= 0.75 else 0.5 if ratio <= 1.1 else 0.2

    def _score_duration(self, asset_dur: float, target_dur: float, asset_type: str) -> float:
        if asset_type == "image":
            return 0.8  # images get motion effects
        if asset_dur <= 0:
            return 0.3
        ratio = asset_dur / target_dur if target_dur > 0 else 1
        if 0.8 <= ratio <= 3.0:
            return 1.0
        if ratio > 3.0:
            return 0.7  # can extract segment
        return 0.4  # too short

    def _check_negatives(self, candidate: dict, must_not: list[str]) -> float:
        if not must_not:
            return 0
        tags = str(candidate.get("tags_json", "")).lower()
        hits = sum(1 for obj in must_not if obj.lower() in tags)
        return min(1.0, hits * 0.5)
