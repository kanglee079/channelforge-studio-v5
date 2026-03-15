"""Media Intelligence Router — V5.7 API endpoints.

9 endpoints: index rebuild/warmup, asset ingest/list, match run/list/detail/pin/retry.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db import get_conn
from ..utils import utc_now_iso
from ..media_intel.scene_spec_builder import SceneSpecBuilder
from ..media_intel.embedder import Embedder
from ..media_intel.index_store import IndexStore
from ..media_intel.retriever import Retriever
from ..media_intel.reranker import Reranker
from ..media_intel.shot_planner import ShotPlanner
from ..media_intel.review_gate import ReviewGate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/media-intel", tags=["media-intel"])

# Singletons
_embedder = Embedder()
_index = IndexStore()
_retriever = Retriever(_embedder, _index)
_reranker = Reranker()
_shot_planner = ShotPlanner()
_scene_builder = SceneSpecBuilder()
_review_gate = ReviewGate()


# ═══════════════════════════════════════════════════════════
# Index management
# ═══════════════════════════════════════════════════════════

@router.post("/index/rebuild")
def rebuild_index():
    """Rebuild local vector index from all stored assets."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM media_assets_v2 ORDER BY created_at DESC").fetchall()

    _index.clear()
    embedded = 0

    for row in rows:
        asset = dict(row)
        # Embed text from tags + key
        text = f"{asset['asset_key']} {asset.get('tags_json', '')}"
        vec = _embedder.embed_text(text)
        _index.add(vec, {"asset_id": asset["id"], "asset_key": asset["asset_key"],
                         "provider": asset["provider"], "asset_type": asset["asset_type"],
                         "local_path": asset.get("local_path", ""), "width": asset.get("width", 0),
                         "height": asset.get("height", 0), "duration_sec": asset.get("duration_sec", 0),
                         "tags_json": asset.get("tags_json", "[]")})
        embedded += 1

    _index.build()
    _index.save("default")

    return {"ok": True, "message": f"Index rebuilt: {embedded} assets indexed", "engine": _index.engine,
            "embedding_model": _embedder.active_model_name}


@router.post("/index/warmup")
def warmup_index():
    """Load existing index from disk."""
    loaded = _index.load("default")
    return {"ok": loaded, "message": "Index loaded" if loaded else "No index found on disk",
            "size": _index.size, "engine": _index.engine}


# ═══════════════════════════════════════════════════════════
# Asset management
# ═══════════════════════════════════════════════════════════

class IngestAssetRequest(BaseModel):
    asset_key: str
    provider: str = "local"
    source_url: str = ""
    local_path: str = ""
    asset_type: str = "image"
    width: int = 0
    height: int = 0
    duration_sec: float = 0
    tags: list[str] = []
    license_notes: str = ""


@router.post("/assets/ingest")
def ingest_asset(req: IngestAssetRequest):
    """Ingest a new asset into the local cache and DB."""
    conn = get_conn()
    now = utc_now_iso()

    try:
        conn.execute(
            """INSERT OR REPLACE INTO media_assets_v2 (asset_key, provider, source_url, local_path, asset_type,
               width, height, duration_sec, tags_json, license_notes, embedding_status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
            (req.asset_key, req.provider, req.source_url, req.local_path, req.asset_type,
             req.width, req.height, req.duration_sec, json.dumps(req.tags), req.license_notes, now, now),
        )
        conn.commit()
        return {"ok": True, "message": f"Asset '{req.asset_key}' ingested"}
    except Exception as e:
        return {"ok": False, "message": f"Ingest failed: {e}"}


@router.get("/assets")
def list_assets(limit: int = 100):
    """List local asset cache."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM media_assets_v2 ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return {"items": [dict(r) for r in rows], "total": len(rows),
            "index_size": _index.size, "embedding_model": _embedder.active_model_name}


# ═══════════════════════════════════════════════════════════
# Match runs
# ═══════════════════════════════════════════════════════════

class MatchRunRequest(BaseModel):
    script_text: str
    channel_name: str = ""
    project_id: int = 0


@router.post("/match/run")
def run_match(req: MatchRunRequest):
    """Run a full media match pipeline for a script."""
    conn = get_conn()
    now = utc_now_iso()

    # 1. Build scene specs
    specs = _scene_builder.build(req.script_text, req.channel_name)
    if not specs:
        return {"ok": False, "message": "Không thể phân tích script thành scenes"}

    # 2. Create match run record
    cur = conn.execute(
        "INSERT INTO scene_match_runs (project_id, channel_name, model_name, total_scenes, status, created_at) VALUES (?, ?, ?, ?, 'running', ?)",
        (req.project_id, req.channel_name, _embedder.active_model_name, len(specs), now),
    )
    conn.commit()
    run_id = cur.lastrowid

    # 3. Match each scene
    matched = 0
    review_count = 0

    for spec in specs:
        # Retrieve candidates
        candidates_raw = _retriever.retrieve_for_scene(spec, top_k=10)

        # Rerank
        ranked = _reranker.rerank(candidates_raw, spec)

        # Select best
        selected = ranked[0] if ranked else None
        shot = None

        if selected:
            shot = _shot_planner.plan_shot(spec, selected)
            matched += 1
        else:
            shot = _shot_planner.plan_fallback(spec, fallback_level=3)

        # Review gate
        review_result = _review_gate.check_and_create(spec, ranked, selected, run_id)
        if review_result["needs_review"]:
            review_count += 1

        # Save match item
        conn.execute(
            """INSERT INTO scene_match_items (run_id, scene_index, spoken_text, visual_goal,
               selected_asset_id, selected_segment_start, selected_segment_end,
               confidence_score, confidence_label, fallback_used, requires_review,
               candidates_json, explain_json, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                run_id, spec.scene_index, spec.spoken_text[:200], spec.visual_goal[:200],
                0,  # asset ID (could be resolved)
                shot.segment_start if shot else 0, shot.segment_end if shot else 0,
                selected.final_score if selected else 0,
                selected.confidence_label if selected else "low",
                shot.asset_type if shot and shot.fallback_level > 0 else "",
                1 if review_result["needs_review"] else 0,
                json.dumps([c.to_dict() for c in ranked[:5]]),
                json.dumps({"shot": shot.to_dict() if shot else {}, "review": review_result}),
                now,
            ),
        )

    # Update run summary
    conn.execute(
        "UPDATE scene_match_runs SET status='completed', matched_scenes=?, review_scenes=?, summary_json=? WHERE id=?",
        (matched, review_count, json.dumps({"total": len(specs), "matched": matched, "review": review_count}), run_id),
    )
    conn.commit()

    return {"ok": True, "run_id": run_id, "total_scenes": len(specs),
            "matched_scenes": matched, "review_scenes": review_count,
            "model": _embedder.active_model_name}


@router.get("/match/runs")
def list_match_runs(limit: int = 20):
    """List all match runs."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM scene_match_runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return {"items": [dict(r) for r in rows]}


@router.get("/match/runs/{run_id}")
def get_match_run(run_id: int):
    """Get match run details with all scene items."""
    conn = get_conn()
    run = conn.execute("SELECT * FROM scene_match_runs WHERE id=?", (run_id,)).fetchone()
    if not run:
        raise HTTPException(404, "Match run not found")

    items = conn.execute(
        "SELECT * FROM scene_match_items WHERE run_id=? ORDER BY scene_index", (run_id,)
    ).fetchall()

    return {"run": dict(run), "items": [dict(i) for i in items]}


class PinRequest(BaseModel):
    scene_index: int
    asset_key: str


@router.post("/match/runs/{run_id}/pin")
def pin_candidate(run_id: int, req: PinRequest):
    """Pin a specific candidate asset for a scene."""
    conn = get_conn()
    now = utc_now_iso()
    conn.execute(
        "UPDATE scene_match_items SET confidence_label='pinned', requires_review=0, explain_json=json_set(explain_json, '$.pinned_asset', ?) WHERE run_id=? AND scene_index=?",
        (req.asset_key, run_id, req.scene_index),
    )
    conn.commit()
    return {"ok": True, "message": f"Scene #{req.scene_index} pinned to asset '{req.asset_key}'"}


class RetrySceneRequest(BaseModel):
    scene_index: int


@router.post("/match/runs/{run_id}/retry-scene")
def retry_scene(run_id: int, req: RetrySceneRequest):
    """Retry matching for a specific scene."""
    conn = get_conn()
    item = conn.execute(
        "SELECT * FROM scene_match_items WHERE run_id=? AND scene_index=?", (run_id, req.scene_index)
    ).fetchone()
    if not item:
        raise HTTPException(404, "Scene item not found")

    # Re-run match for this scene
    spec = _scene_builder.build(item["spoken_text"])[0] if item["spoken_text"] else None
    if not spec:
        return {"ok": False, "message": "Không thể tái tạo scene spec"}

    candidates_raw = _retriever.retrieve_for_scene(spec, top_k=15)  # More candidates on retry
    ranked = _reranker.rerank(candidates_raw, spec)
    selected = ranked[0] if ranked else None

    now = utc_now_iso()
    conn.execute(
        "UPDATE scene_match_items SET confidence_score=?, confidence_label=?, candidates_json=?, requires_review=? WHERE run_id=? AND scene_index=?",
        (selected.final_score if selected else 0, selected.confidence_label if selected else "low",
         json.dumps([c.to_dict() for c in ranked[:5]]),
         1 if (not selected or selected.final_score < 0.65) else 0,
         run_id, req.scene_index),
    )
    conn.commit()

    return {"ok": True, "message": f"Scene #{req.scene_index} re-matched",
            "new_confidence": selected.confidence_label if selected else "low",
            "candidates": len(ranked)}
