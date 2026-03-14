"""Visual Match Service — Main orchestration layer.

Pipeline: decompose → retrieve → score → select → save to DB → timeline output
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .schema import SceneIntent, CandidateAsset, SceneMatchResult, TimelineEntry
from .scene_decomposer import decompose_script
from .candidate_retriever import retrieve_candidates
from .scorer import score_candidates

logger = logging.getLogger(__name__)

# Confidence thresholds
HIGH_CONF = 0.70
MED_CONF = 0.45


async def run_visual_match(
    script_project_id: int,
    channel_name: str = "",
    providers: list[str] | None = None,
    min_score_threshold: float = 0.40,
    allow_fallback_images: bool = True,
) -> list[SceneMatchResult]:
    """Run the full visual matching pipeline for a script project."""
    from ..db import get_conn
    from ..utils import utc_now_iso

    conn = get_conn()

    # 1. Get script text
    script_row = conn.execute("SELECT * FROM script_drafts WHERE id=?", (script_project_id,)).fetchone()
    if not script_row:
        raise ValueError(f"Script project {script_project_id} not found")

    script_text = script_row["script_text"] or ""
    ch = channel_name or script_row.get("channel_name", "")

    # Get channel niche
    niche = ""
    profile = conn.execute("SELECT json FROM profiles WHERE name=?", (ch,)).fetchone()
    if profile:
        pdata = json.loads(profile["json"])
        niche = pdata.get("niche", "")

    # 2. Decompose script into scenes
    logger.info("Decomposing script %d into scenes...", script_project_id)
    scenes = decompose_script(script_text, channel_niche=niche)
    if not scenes:
        logger.warning("No scenes generated for script %d", script_project_id)
        return []

    logger.info("Generated %d scenes", len(scenes))

    # 3. For each scene: retrieve → score → select
    results: list[SceneMatchResult] = []
    now = utc_now_iso()

    for scene in scenes:
        # Retrieve candidates
        candidates = await retrieve_candidates(scene, providers=providers)

        # If no video candidates and fallback allowed, try images
        if not candidates and allow_fallback_images and scene.asset_preference == "video":
            scene.asset_preference = "image"
            candidates = await retrieve_candidates(scene, providers=providers)

        # Score candidates
        scored = score_candidates(scene, candidates)

        # Select best candidate
        selected = scored[0] if scored and scored[0].final_score >= min_score_threshold else None

        # Determine confidence
        conf = "low"
        if selected:
            if selected.final_score >= HIGH_CONF:
                conf = "high"
            elif selected.final_score >= MED_CONF:
                conf = "medium"

        status = "matched" if selected else "review"

        result = SceneMatchResult(
            scene_index=scene.scene_index,
            scene=scene,
            candidates=scored[:5],  # Keep top 5
            selected=selected,
            selected_clip_start=0.0,
            selected_clip_end=min(scene.duration_sec, selected.duration_sec) if selected and selected.duration_sec > 0 else scene.duration_sec,
            confidence_label=conf,
            status=status,
        )
        results.append(result)

        # 4. Save to DB
        try:
            cur = conn.execute(
                """INSERT INTO scene_match_results
                   (script_project_id, channel_name, scene_index, scene_json,
                    selected_asset_id, selected_clip_start_sec, selected_clip_end_sec,
                    final_score, confidence_label, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (script_project_id, ch, scene.scene_index, json.dumps(scene.to_dict()),
                 selected.asset_id if selected else None,
                 result.selected_clip_start, result.selected_clip_end,
                 selected.final_score if selected else 0.0,
                 conf, status, now, now),
            )
            scene_match_id = cur.lastrowid

            # Save top candidates
            for rank, c in enumerate(scored[:5]):
                conn.execute(
                    """INSERT INTO scene_match_candidates
                       (scene_match_result_id, asset_id, semantic_score, object_match_score,
                        style_match_score, quality_score, negative_penalty, duplicate_penalty,
                        final_score, explain_json, rank, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (scene_match_id, c.asset_id, c.semantic_score, c.object_match_score,
                     c.style_match_score, c.quality_score, c.negative_penalty, c.duplicate_penalty,
                     c.final_score, json.dumps(c.explain), rank, now),
                )
            conn.commit()
        except Exception as e:
            logger.error("Failed to save scene match result: %s", e)

    # Create review items for low confidence scenes
    low_conf = [r for r in results if r.confidence_label == "low"]
    if low_conf:
        try:
            from ..db_v5 import create_review_item
            for r in low_conf:
                create_review_item(
                    review_type="scene_low_conf",
                    object_type="scene",
                    object_id=r.scene_index,
                    channel_name=ch,
                    reason_code="low_confidence",
                    reason_text=f"Scene {r.scene_index}: visual match score below threshold",
                    score=r.selected.final_score if r.selected else 0.0,
                    payload={"script_project_id": script_project_id, "visual_intent": r.scene.visual_intent},
                )
        except Exception as e:
            logger.warning("Failed to create review items: %s", e)

    logger.info("Visual match complete: %d scenes, %d high, %d medium, %d low",
                len(results),
                sum(1 for r in results if r.confidence_label == "high"),
                sum(1 for r in results if r.confidence_label == "medium"),
                sum(1 for r in results if r.confidence_label == "low"))

    return results


def get_match_results(script_project_id: int) -> list[dict]:
    """Get saved match results for a script project."""
    from ..db import get_conn
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM scene_match_results WHERE script_project_id=? ORDER BY scene_index",
        (script_project_id,),
    ).fetchall()

    results = []
    for r in rows:
        item = dict(r)
        # Get candidates
        candidates = conn.execute(
            "SELECT * FROM scene_match_candidates WHERE scene_match_result_id=? ORDER BY rank",
            (r["id"],),
        ).fetchall()
        item["candidates"] = [dict(c) for c in candidates]
        results.append(item)
    return results


def select_candidate(scene_match_id: int, asset_id: int) -> dict:
    """Manual select/replace a candidate for a scene."""
    from ..db import get_conn
    from ..utils import utc_now_iso
    conn = get_conn()
    now = utc_now_iso()

    # Find the candidate's score
    candidate = conn.execute(
        "SELECT * FROM scene_match_candidates WHERE scene_match_result_id=? AND asset_id=?",
        (scene_match_id, asset_id),
    ).fetchone()

    score = candidate["final_score"] if candidate else 0.0
    conf = "high" if score >= HIGH_CONF else ("medium" if score >= MED_CONF else "low")

    conn.execute(
        "UPDATE scene_match_results SET selected_asset_id=?, final_score=?, confidence_label=?, status='pinned', updated_at=? WHERE id=?",
        (asset_id, score, conf, now, scene_match_id),
    )
    conn.commit()
    return {"ok": True, "message": f"Selected asset {asset_id} for scene match {scene_match_id}"}


def build_timeline(script_project_id: int) -> list[dict]:
    """Build render timeline from match results."""
    from ..db import get_conn
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM scene_match_results WHERE script_project_id=? AND selected_asset_id IS NOT NULL ORDER BY scene_index",
        (script_project_id,),
    ).fetchall()

    timeline = []
    for r in rows:
        asset = conn.execute("SELECT * FROM media_assets WHERE id=?", (r["selected_asset_id"],)).fetchone()
        timeline.append({
            "scene_index": r["scene_index"],
            "asset_id": r["selected_asset_id"],
            "asset_type": asset["asset_type"] if asset else "video",
            "src_path": asset["local_path"] if asset else "",
            "trim_start": r["selected_clip_start_sec"],
            "trim_end": r["selected_clip_end_sec"],
            "motion_effect": "none",
            "transition": "cut",
        })
    return timeline
