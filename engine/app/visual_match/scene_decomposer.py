"""Scene Decomposer — Tách script thành scenes với visual intent.

Dùng LLM (OpenAI) để phân tích script text và sinh ra scene objects
có chứa visual_intent, must_have_objects, mood, location_hint.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .schema import SceneIntent

logger = logging.getLogger(__name__)


def decompose_script(script_text: str, channel_niche: str = "", target_format: str = "shorts") -> list[SceneIntent]:
    """Decompose script text into scenes with visual intents using AI."""
    if not script_text.strip():
        return []

    prompt = f"""Analyze this video narration script and break it into visual scenes.
For each scene, provide: spoken_text, visual_intent, must_have_objects, must_not_show, mood, location_hint, asset_preference, duration_sec.

Channel niche: {channel_niche or 'general'}
Format: {target_format}

Script:
{script_text[:3000]}

Return ONLY a JSON array of scene objects. Each scene:
{{
  "spoken_text": "the narration for this scene",
  "visual_intent": "brief description of what should be shown visually",
  "must_have_objects": ["object1", "object2"],
  "must_not_show": [],
  "mood": "dramatic|calm|exciting|mysterious|informative",
  "location_hint": "where this takes place",
  "asset_preference": "video|image|both",
  "duration_sec": 5.0
}}"""

    try:
        from ..openai_api import chat
        raw = chat(prompt, model=None)
        result = raw if isinstance(raw, str) else str(raw)

        # Parse JSON from response
        scenes_data = _extract_json_array(result)
        scenes = []
        for i, s in enumerate(scenes_data):
            scenes.append(SceneIntent(
                scene_index=i,
                spoken_text=s.get("spoken_text", ""),
                visual_intent=s.get("visual_intent", ""),
                must_have_objects=s.get("must_have_objects", []),
                must_not_show=s.get("must_not_show", []),
                mood=s.get("mood", "neutral"),
                location_hint=s.get("location_hint", ""),
                asset_preference=s.get("asset_preference", "video"),
                duration_sec=float(s.get("duration_sec", 5.0)),
            ))
        logger.info("Decomposed script into %d scenes", len(scenes))
        return scenes
    except Exception as e:
        logger.error("Scene decomposition failed: %s", e)
        # Fallback: simple sentence-based decomposition
        return _fallback_decompose(script_text)


def _fallback_decompose(script_text: str) -> list[SceneIntent]:
    """Fallback decomposition — split by sentences/paragraphs."""
    import re
    sentences = re.split(r'[.!?]+', script_text)
    scenes = []
    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if len(sent) < 10:
            continue
        # Extract simple keywords as must_have_objects
        words = [w.lower() for w in sent.split() if len(w) > 4]
        key_objects = words[:3] if words else []
        scenes.append(SceneIntent(
            scene_index=i,
            spoken_text=sent,
            visual_intent=sent[:100],
            must_have_objects=key_objects,
            mood="informative",
            asset_preference="video",
            duration_sec=max(3.0, len(sent.split()) / 2.5),
        ))
    return scenes


def _extract_json_array(text: str) -> list[dict]:
    """Extract JSON array from LLM response (handles markdown code blocks)."""
    import re
    # Try to find JSON array in code blocks
    match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # Try direct JSON
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return []
