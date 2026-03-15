"""Scene Spec Builder — Parse script text into structured SceneSpecs.

Dùng LLM nếu có, fallback sentence splitter + noun extraction.
Mỗi scene có: visual_goal, search_queries, camera_style, fallback_strategy.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SceneSpec:
    """Structured specification for one visual scene."""
    scene_index: int = 0
    spoken_text: str = ""
    visual_goal: str = ""
    must_have_objects: list[str] = field(default_factory=list)
    must_not_show: list[str] = field(default_factory=list)
    mood: str = "neutral"
    location_hint: str = ""
    time_period: str = ""
    camera_style: str = "medium_shot"
    asset_preference: str = "video"  # video | image | any
    fallback_strategy: str = "image_motion"  # image_motion | text_card | template_bg
    duration_sec: float = 5.0
    search_queries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class SceneSpecBuilder:
    """Build SceneSpecs from raw script text."""

    def build(self, script_text: str, channel_niche: str = "", style: str = "") -> list[SceneSpec]:
        """Parse script into SceneSpecs. Uses heuristic sentence splitting."""
        if not script_text.strip():
            return []

        sentences = self._split_sentences(script_text)
        specs = []

        for i, sent in enumerate(sentences):
            sent = sent.strip()
            if not sent or len(sent) < 5:
                continue

            # Extract visual cues
            objects = self._extract_objects(sent)
            queries = self._build_search_queries(sent, channel_niche, objects)
            mood = self._detect_mood(sent)
            duration = max(3.0, min(len(sent.split()) * 0.5, 12.0))  # ~0.5s per word, 3-12s range

            spec = SceneSpec(
                scene_index=i,
                spoken_text=sent,
                visual_goal=self._build_visual_goal(sent, objects),
                must_have_objects=objects[:5],
                mood=mood,
                camera_style=self._suggest_camera(mood, i, len(sentences)),
                duration_sec=round(duration, 1),
                search_queries=queries[:3],
                fallback_strategy="image_motion",
            )
            specs.append(spec)

        logger.info("Built %d SceneSpecs from script (%d chars)", len(specs), len(script_text))
        return specs

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Split on period/exclamation/question + common scene markers
        parts = re.split(r'(?<=[.!?])\s+|\n\n+', text)
        result = []
        for part in parts:
            part = part.strip()
            if len(part) >= 10:
                result.append(part)
            elif result:
                result[-1] += " " + part
        return result if result else [text]

    def _extract_objects(self, text: str) -> list[str]:
        """Extract potential visual objects from text (heuristic)."""
        # Simple: capitalize words likely = proper nouns / objects
        words = text.split()
        objects = []
        for w in words:
            clean = re.sub(r'[^\w]', '', w)
            if clean and len(clean) > 2 and (clean[0].isupper() or clean in ("war", "battle", "city", "river", "mountain", "king", "queen", "castle", "ship", "army", "soldier")):
                objects.append(clean.lower())
        return list(dict.fromkeys(objects))  # dedupe preserving order

    def _build_search_queries(self, text: str, niche: str, objects: list[str]) -> list[str]:
        """Build 3 types of search queries for retrieval."""
        queries = []
        # 1. Exact intent
        short = text[:80] if len(text) > 80 else text
        queries.append(short)
        # 2. Object-focused
        if objects:
            queries.append(" ".join(objects[:3]))
        # 3. Niche + mood
        if niche:
            queries.append(f"{niche} {self._detect_mood(text)}")
        return queries

    def _build_visual_goal(self, text: str, objects: list[str]) -> str:
        """Build a concise visual goal description."""
        if objects:
            return f"Show {', '.join(objects[:3])} related to: {text[:60]}"
        return f"Visual representing: {text[:80]}"

    def _detect_mood(self, text: str) -> str:
        """Simple mood detection."""
        lower = text.lower()
        if any(w in lower for w in ("war", "battle", "fight", "destroy", "attack", "death")):
            return "dramatic"
        if any(w in lower for w in ("beautiful", "peace", "calm", "nature", "garden")):
            return "serene"
        if any(w in lower for w in ("discover", "explore", "adventure", "journey")):
            return "adventurous"
        if any(w in lower for w in ("mystery", "secret", "hidden", "unknown")):
            return "mysterious"
        return "neutral"

    def _suggest_camera(self, mood: str, scene_idx: int, total: int) -> str:
        """Suggest camera style based on mood and position."""
        if scene_idx == 0:
            return "wide_establishing"
        if scene_idx == total - 1:
            return "slow_zoom_out"
        if mood == "dramatic":
            return "close_up"
        if mood == "serene":
            return "slow_pan"
        return "medium_shot"
