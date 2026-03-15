"""Review Gate — Auto-create review items when confidence is low.

Tích hợp với bảng review_items có sẵn từ V5.5.
"""

from __future__ import annotations

import json
import logging

from ..db import get_conn
from ..utils import utc_now_iso
from .scene_spec_builder import SceneSpec
from .reranker import RankedCandidate

logger = logging.getLogger(__name__)

# Confidence threshold for auto-review
REVIEW_THRESHOLD = 0.65


class ReviewGate:
    """Auto-create review items when scene match confidence is low."""

    def check_and_create(self, spec: SceneSpec, candidates: list[RankedCandidate],
                         selected: RankedCandidate | None, run_id: int = 0) -> dict:
        """Check if a scene match needs review and create review item if so.

        Creates review item when:
        - confidence < REVIEW_THRESHOLD
        - must_have coverage < 0.5
        - only fallback assets found
        - multiple candidates have near-identical scores (tie)
        """
        needs_review = False
        reasons = []

        if selected is None:
            needs_review = True
            reasons.append("Không tìm được asset phù hợp")
        else:
            if selected.final_score < REVIEW_THRESHOLD:
                needs_review = True
                reasons.append(f"Confidence thấp: {selected.final_score:.2f}")

            if selected.must_have_score < 0.5 and spec.must_have_objects:
                needs_review = True
                reasons.append(f"Must-have coverage thấp: {selected.must_have_score:.2f}")

            if selected.source == "fallback":
                needs_review = True
                reasons.append("Chỉ tìm được fallback assets")

            # Check for score ties
            if len(candidates) >= 2:
                top_scores = sorted([c.final_score for c in candidates[:5]], reverse=True)
                if len(top_scores) >= 2 and abs(top_scores[0] - top_scores[1]) < 0.05:
                    needs_review = True
                    reasons.append(f"Nhiều candidates có điểm gần nhau: {top_scores[0]:.2f} vs {top_scores[1]:.2f}")

        if needs_review:
            review_id = self._create_review_item(spec, candidates, selected, reasons, run_id)
            return {"needs_review": True, "review_item_id": review_id, "reasons": reasons}

        return {"needs_review": False, "reasons": []}

    def _create_review_item(self, spec: SceneSpec, candidates: list[RankedCandidate],
                            selected: RankedCandidate | None, reasons: list[str], run_id: int) -> int:
        """Create a review_items entry in the database."""
        conn = get_conn()
        now = utc_now_iso()

        payload = {
            "scene_index": spec.scene_index,
            "spoken_text": spec.spoken_text[:200],
            "visual_goal": spec.visual_goal[:200],
            "top_candidates": [c.to_dict() for c in candidates[:5]],
            "selected": selected.to_dict() if selected else None,
            "reasons": reasons,
            "run_id": run_id,
        }

        try:
            cur = conn.execute(
                """INSERT INTO review_items (item_type, source_type, source_id, channel_name, title, details_json, severity, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)""",
                (
                    "scene_match_low_confidence",
                    "scene_match_run",
                    str(run_id),
                    "",
                    f"Scene #{spec.scene_index}: {spec.visual_goal[:80]}",
                    json.dumps(payload, ensure_ascii=False),
                    "medium" if (selected and selected.final_score > 0.4) else "high",
                    now, now,
                ),
            )
            conn.commit()
            review_id = cur.lastrowid
            logger.info("Created review item #%d for scene %d (reasons: %s)", review_id, spec.scene_index, "; ".join(reasons))
            return review_id
        except Exception as e:
            logger.warning("Failed to create review item: %s", e)
            return 0
