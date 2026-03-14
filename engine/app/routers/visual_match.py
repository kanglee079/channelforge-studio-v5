"""Visual Match API Router — V5 scene matching endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v5/visual-match", tags=["visual-match"])


class RunMatchRequest(BaseModel):
    channel_name: str = ""
    providers: list[str] | None = None
    min_score_threshold: float = 0.40
    allow_fallback_to_images: bool = True


class SelectCandidateRequest(BaseModel):
    asset_id: int


# ── Run visual matching ──────────────────────────────────
@router.post("/projects/{script_project_id}/run")
async def run_match(script_project_id: int, req: RunMatchRequest):
    from ..visual_match.service import run_visual_match
    try:
        results = await run_visual_match(
            script_project_id=script_project_id,
            channel_name=req.channel_name,
            providers=req.providers,
            min_score_threshold=req.min_score_threshold,
            allow_fallback_images=req.allow_fallback_to_images,
        )
        return {
            "ok": True,
            "total_scenes": len(results),
            "high_confidence": sum(1 for r in results if r.confidence_label == "high"),
            "medium_confidence": sum(1 for r in results if r.confidence_label == "medium"),
            "low_confidence": sum(1 for r in results if r.confidence_label == "low"),
            "message": f"Matched {len(results)} scenes",
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Visual match failed: {e}")


# ── Get match results ────────────────────────────────────
@router.get("/projects/{script_project_id}")
def get_matches(script_project_id: int):
    from ..visual_match.service import get_match_results
    results = get_match_results(script_project_id)
    return {"items": results, "total": len(results)}


# ── Select/replace candidate ─────────────────────────────
@router.post("/scene/{scene_match_id}/select")
def select_candidate(scene_match_id: int, req: SelectCandidateRequest):
    from ..visual_match.service import select_candidate as do_select
    return do_select(scene_match_id, req.asset_id)


# ── Build timeline ───────────────────────────────────────
@router.get("/projects/{script_project_id}/timeline")
def get_timeline(script_project_id: int):
    from ..visual_match.service import build_timeline
    timeline = build_timeline(script_project_id)
    return {"project_id": script_project_id, "timeline": timeline}


# ── Re-run low confidence only ───────────────────────────
@router.post("/projects/{script_project_id}/rerun-low-confidence")
async def rerun_low_confidence(script_project_id: int, req: RunMatchRequest):
    from ..db import get_conn
    conn = get_conn()

    # Get existing low-confidence scene indices
    low_scenes = conn.execute(
        "SELECT scene_index FROM scene_match_results WHERE script_project_id=? AND confidence_label='low'",
        (script_project_id,),
    ).fetchall()

    if not low_scenes:
        return {"ok": True, "message": "No low confidence scenes to rerun", "rerun_count": 0}

    # Delete old low-confidence results
    for row in low_scenes:
        conn.execute(
            "DELETE FROM scene_match_candidates WHERE scene_match_result_id IN (SELECT id FROM scene_match_results WHERE script_project_id=? AND scene_index=?)",
            (script_project_id, row["scene_index"]),
        )
        conn.execute(
            "DELETE FROM scene_match_results WHERE script_project_id=? AND scene_index=? AND confidence_label='low'",
            (script_project_id, row["scene_index"]),
        )
    conn.commit()

    # Re-run full match (will only process missing scenes)
    from ..visual_match.service import run_visual_match
    results = await run_visual_match(
        script_project_id=script_project_id,
        channel_name=req.channel_name,
        providers=req.providers or ["pexels", "pixabay"],
        min_score_threshold=req.min_score_threshold,
    )

    return {
        "ok": True,
        "rerun_count": len(low_scenes),
        "new_results": len(results),
        "message": f"Re-ran {len(low_scenes)} low-confidence scenes",
    }
