"""Shot Planner — Plan video segments and image motion effects.

Video: chọn segment tốt nhất theo scene duration.
Image: chọn motion effect (pan, zoom, parallax) theo mood.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from .scene_spec_builder import SceneSpec
from .reranker import RankedCandidate

logger = logging.getLogger(__name__)


@dataclass
class ShotPlan:
    """Planned shot for a scene."""
    scene_index: int = 0
    asset_key: str = ""
    asset_type: str = ""
    segment_start: float = 0
    segment_end: float = 0
    motion_effect: str = ""  # pan_left, pan_right, zoom_in, zoom_out, parallax_light
    duration_sec: float = 0
    confidence: str = "low"
    fallback_level: int = 0  # 0=primary match, 1=fallback image, 2=template_bg, 3=text_card

    def to_dict(self) -> dict:
        return asdict(self)


MOTION_EFFECTS = {
    "dramatic": "zoom_in",
    "serene": "slow_pan",
    "adventurous": "pan_right",
    "mysterious": "zoom_in",
    "neutral": "parallax_light",
}


class ShotPlanner:
    """Plan shots for scenes based on matched candidates."""

    def plan_shot(self, spec: SceneSpec, candidate: RankedCandidate) -> ShotPlan:
        """Plan a shot for a scene using the top candidate."""
        plan = ShotPlan(
            scene_index=spec.scene_index,
            asset_key=candidate.asset_key,
            asset_type=candidate.asset_type,
            duration_sec=spec.duration_sec,
            confidence=candidate.confidence_label,
        )

        if candidate.asset_type == "video":
            plan = self._plan_video_shot(plan, candidate, spec)
        else:
            plan = self._plan_image_shot(plan, spec)

        return plan

    def plan_fallback(self, spec: SceneSpec, fallback_level: int = 1) -> ShotPlan:
        """Plan a fallback shot when no good candidate found."""
        plan = ShotPlan(
            scene_index=spec.scene_index,
            duration_sec=spec.duration_sec,
            confidence="low",
            fallback_level=fallback_level,
        )

        if fallback_level == 1:
            plan.motion_effect = MOTION_EFFECTS.get(spec.mood, "parallax_light")
            plan.asset_type = "image"
        elif fallback_level == 2:
            plan.motion_effect = "static"
            plan.asset_type = "template_bg"
        elif fallback_level >= 3:
            plan.motion_effect = "none"
            plan.asset_type = "text_card"

        return plan

    def _plan_video_shot(self, plan: ShotPlan, candidate: RankedCandidate, spec: SceneSpec) -> ShotPlan:
        """Plan segment extraction from a video candidate."""
        video_dur = candidate.duration_sec

        if video_dur <= 0:
            # Unknown duration — use from start
            plan.segment_start = 0
            plan.segment_end = spec.duration_sec
            return plan

        if video_dur <= spec.duration_sec * 1.2:
            # Video roughly matches scene — use full
            plan.segment_start = 0
            plan.segment_end = min(video_dur, spec.duration_sec)
        elif video_dur > spec.duration_sec:
            # Video is longer — pick middle segment (most interesting content)
            mid = video_dur / 2
            half_scene = spec.duration_sec / 2
            plan.segment_start = max(0, mid - half_scene)
            plan.segment_end = min(video_dur, mid + half_scene)

        plan.motion_effect = "none"  # Video plays as-is
        return plan

    def _plan_image_shot(self, plan: ShotPlan, spec: SceneSpec) -> ShotPlan:
        """Plan motion effect for an image candidate."""
        plan.segment_start = 0
        plan.segment_end = spec.duration_sec

        # Choose motion effect based on mood and duration
        plan.motion_effect = MOTION_EFFECTS.get(spec.mood, "parallax_light")

        # Shorter scenes get simpler effects
        if spec.duration_sec < 4:
            plan.motion_effect = "zoom_in"

        return plan

    def get_fallback_ladder(self) -> list[str]:
        """Return the fallback strategy ladder."""
        return [
            "1. Video semantic match",
            "2. Image semantic match + motion effect",
            "3. Local template background",
            "4. Text/emphasis card",
            "5. Manual review required",
        ]
