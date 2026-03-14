"""Scorer — Multi-layer scoring for scene-candidate matching.

Score formula:
  final = 0.40*semantic + 0.20*object_match + 0.10*quality + 0.10*style_match
        + 0.10*novelty_bonus + 0.10*provider_trust - negative_penalty - duplicate_penalty
"""

from __future__ import annotations

import logging
from typing import Any

from .schema import SceneIntent, CandidateAsset

logger = logging.getLogger(__name__)

# Provider trust scores
PROVIDER_TRUST: dict[str, float] = {
    "pexels": 0.90,
    "pixabay": 0.85,
    "local_cache": 0.70,
    "manual": 1.0,
}

# Min resolution for quality
MIN_WIDTH = 640
MIN_HEIGHT = 360


def score_candidates(scene: SceneIntent, candidates: list[CandidateAsset]) -> list[CandidateAsset]:
    """Score all candidates for a scene, return sorted by final_score descending."""
    for c in candidates:
        c.semantic_score = _compute_semantic_score(scene, c)
        c.object_match_score = _compute_object_match(scene, c)
        c.quality_score = _compute_quality(c)
        c.style_match_score = _compute_style_match(scene, c)
        c.negative_penalty = _compute_negative_penalty(scene, c)
        c.duplicate_penalty = _compute_duplicate_penalty(c)

        novelty_bonus = max(0.0, 1.0 - (c.duplicate_penalty * 2))
        trust = PROVIDER_TRUST.get(c.source_provider, 0.5)

        c.final_score = (
            0.40 * c.semantic_score +
            0.20 * c.object_match_score +
            0.10 * c.quality_score +
            0.10 * c.style_match_score +
            0.10 * novelty_bonus +
            0.10 * trust -
            c.negative_penalty -
            c.duplicate_penalty
        )
        c.final_score = round(max(0.0, min(1.0, c.final_score)), 3)

        c.explain = {
            "semantic": round(c.semantic_score, 3),
            "object_match": round(c.object_match_score, 3),
            "quality": round(c.quality_score, 3),
            "style": round(c.style_match_score, 3),
            "novelty": round(novelty_bonus, 3),
            "trust": round(trust, 3),
            "neg_penalty": round(c.negative_penalty, 3),
            "dup_penalty": round(c.duplicate_penalty, 3),
        }

    candidates.sort(key=lambda c: c.final_score, reverse=True)
    return candidates


def _compute_semantic_score(scene: SceneIntent, candidate: CandidateAsset) -> float:
    """Compute semantic similarity between scene intent and candidate."""
    intent_words = set(scene.visual_intent.lower().split())
    tag_words = set(w.lower() for t in candidate.tags for w in t.split())
    all_candidate_text = tag_words | set(candidate.source_url.lower().split("/"))

    if not intent_words:
        return 0.3

    overlap = intent_words & all_candidate_text
    score = len(overlap) / max(len(intent_words), 1)
    return min(1.0, score * 1.5)  # Boost slightly


def _compute_object_match(scene: SceneIntent, candidate: CandidateAsset) -> float:
    """Check if required objects are present in candidate."""
    if not scene.must_have_objects:
        return 0.7  # Neutral if no requirements

    tag_str = " ".join(candidate.tags).lower()
    url_str = candidate.source_url.lower()
    combined = tag_str + " " + url_str

    matched = sum(1 for obj in scene.must_have_objects if obj.lower() in combined)
    return matched / max(len(scene.must_have_objects), 1)


def _compute_quality(candidate: CandidateAsset) -> float:
    """Score based on resolution and duration."""
    score = 0.5
    if candidate.width >= 1920:
        score += 0.3
    elif candidate.width >= 1280:
        score += 0.2
    elif candidate.width >= MIN_WIDTH:
        score += 0.1

    if candidate.asset_type == "video" and candidate.duration_sec >= 3.0:
        score += 0.2

    return min(1.0, score)


def _compute_style_match(scene: SceneIntent, candidate: CandidateAsset) -> float:
    """Check if asset style/mood matches scene mood."""
    # Simple heuristic based on tags
    mood_keywords: dict[str, list[str]] = {
        "dramatic": ["dramatic", "intense", "dark", "epic", "cinematic"],
        "calm": ["calm", "peaceful", "serene", "gentle", "soft"],
        "exciting": ["exciting", "action", "fast", "energetic", "dynamic"],
        "mysterious": ["mysterious", "foggy", "dark", "shadow", "abstract"],
        "informative": ["education", "science", "technology", "nature", "documentary"],
    }
    expected = mood_keywords.get(scene.mood, [])
    if not expected:
        return 0.5

    tag_str = " ".join(candidate.tags).lower()
    if any(kw in tag_str for kw in expected):
        return 0.8
    return 0.4


def _compute_negative_penalty(scene: SceneIntent, candidate: CandidateAsset) -> float:
    """Penalty for must_not_show violations."""
    if not scene.must_not_show:
        return 0.0

    tag_str = " ".join(candidate.tags).lower()
    violations = sum(1 for item in scene.must_not_show if item.lower() in tag_str)
    return min(0.5, violations * 0.25)


def _compute_duplicate_penalty(candidate: CandidateAsset) -> float:
    """Penalty for overused assets."""
    try:
        from ..db import get_conn
        conn = get_conn()
        if candidate.asset_id:
            row = conn.execute("SELECT usage_count FROM media_assets WHERE id=?", (candidate.asset_id,)).fetchone()
            if row and row["usage_count"] > 3:
                return min(0.3, (row["usage_count"] - 3) * 0.05)
    except Exception:
        pass
    return 0.0
