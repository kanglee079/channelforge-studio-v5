"""Pipeline Controller Router — End-to-end content production API.

11 endpoints: create/advance/fail/pause/resume/list/detail/summary + policy CRUD + cost.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.pipeline_controller import controller

router = APIRouter(prefix="/api/v2/pipeline", tags=["pipeline"])


# ═══════════════════════════════════════════════════════════
# Job management
# ═══════════════════════════════════════════════════════════

class CreateJobRequest(BaseModel):
    workspace_id: int
    channel_name: str = ""
    idea_id: int = 0
    priority: int = 50


@router.post("/jobs")
def create_job(req: CreateJobRequest):
    """Create a new pipeline job."""
    return controller.create_job(req.workspace_id, req.channel_name, req.idea_id, req.priority)


@router.post("/jobs/{job_id}/advance")
def advance_job(job_id: int, force_stage: str = ""):
    """Advance a job to its next stage."""
    return controller.advance_stage(job_id, force_next=force_stage)


@router.post("/jobs/{job_id}/fail")
def fail_job(job_id: int, error: str = "Unknown error"):
    """Mark job as failed, trigger retry or permanent failure."""
    return controller.fail_job(job_id, error)


@router.post("/jobs/{job_id}/pause")
def pause_job(job_id: int):
    return controller.pause_job(job_id)


@router.post("/jobs/{job_id}/resume")
def resume_job(job_id: int):
    return controller.resume_job(job_id)


@router.get("/jobs")
def list_jobs(workspace_id: int = 0, status: str = "", limit: int = 50):
    return {"items": controller.list_jobs(workspace_id, status, limit)}


@router.get("/jobs/{job_id}")
def get_job(job_id: int):
    job = controller.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/queue/summary")
def queue_summary():
    """Get queue state summary."""
    return controller.get_queue_summary()


# ═══════════════════════════════════════════════════════════
# Channel automation policy
# ═══════════════════════════════════════════════════════════

class PolicyRequest(BaseModel):
    workspace_id: int
    channel_name: str = ""
    content_niche: str = ""
    preferred_language: str = "en"
    review_strictness: str = "medium"
    max_daily_videos: int = 3
    quality_threshold: float = 0.65
    auto_publish: bool = False
    thumbnail_enabled: bool = True
    preferred_providers: str = "local,pexels,pixabay"
    cost_limit_daily_usd: float = 5.0


@router.get("/policy/{workspace_id}")
def get_policy(workspace_id: int):
    policy = controller.get_policy(workspace_id)
    return policy or {"message": "No policy configured", "workspace_id": workspace_id}


@router.post("/policy")
def upsert_policy(req: PolicyRequest):
    return controller.upsert_policy(
        req.workspace_id,
        channel_name=req.channel_name,
        content_niche=req.content_niche,
        preferred_language=req.preferred_language,
        review_strictness=req.review_strictness,
        max_daily_videos=req.max_daily_videos,
        quality_threshold=req.quality_threshold,
        auto_publish=int(req.auto_publish),
        thumbnail_enabled=int(req.thumbnail_enabled),
        preferred_providers=req.preferred_providers,
        cost_limit_daily_usd=req.cost_limit_daily_usd,
    )


# ═══════════════════════════════════════════════════════════
# Cost tracking
# ═══════════════════════════════════════════════════════════

class AddCostRequest(BaseModel):
    provider: str
    amount_usd: float
    description: str = ""


@router.post("/jobs/{job_id}/cost")
def add_cost(job_id: int, req: AddCostRequest):
    controller.add_cost(job_id, req.provider, req.amount_usd, req.description)
    return {"ok": True, "message": f"${req.amount_usd:.4f} added for {req.provider}"}
