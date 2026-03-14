
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from ..config import settings
from ..db import init_db, save_profile_json
from ..pipeline import enqueue_batch, run_workers
from ..profiles import list_profiles, load_profile, sync_profiles
from ..services.catalog import dashboard_summary, list_jobs, scan_content_library
from ..services.trend_assistant import load_trends_cache, refresh_trends_cache, scan_trends
from .schemas import ChannelUpsertRequest, EnqueueRequest, GenericMessage, RunWorkerRequest, TrendScanRequest

router = APIRouter()


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/dashboard")
def get_dashboard():
    init_db()
    sync_profiles()
    return dashboard_summary()


@router.get("/channels")
def get_channels():
    sync_profiles()
    return {"items": [load_profile(name).to_dict() for name in list_profiles()]}


@router.post("/channels", response_model=GenericMessage)
def upsert_channel(payload: ChannelUpsertRequest):
    save_profile_json(payload.name, payload.model_dump())
    return GenericMessage(message="Channel profile saved", data={"name": payload.name})


@router.get("/jobs")
def get_jobs(state: str | None = None, channel: str | None = None, limit: int = Query(default=100, ge=1, le=500)):
    init_db()
    return {"items": list_jobs(state=state, channel=channel, limit=limit)}


@router.post("/jobs/enqueue", response_model=GenericMessage)
def enqueue_jobs(payload: EnqueueRequest):
    init_db()
    sync_profiles()
    try:
        profile = load_profile(payload.profile)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Profile not found: {payload.profile}") from exc

    topic_file = Path(payload.topic_file) if payload.topic_file else None
    seed_url_file = Path(payload.seed_url_file) if payload.seed_url_file else None
    youtube_url_file = Path(payload.youtube_url_file) if payload.youtube_url_file else None
    job_ids = enqueue_batch(
        profile=profile,
        count=payload.count,
        niche=payload.niche,
        topic_file=topic_file,
        video_format=payload.format,
        seed_url_file=seed_url_file,
        youtube_url_file=youtube_url_file,
    )
    return GenericMessage(message=f"Enqueued {len(job_ids)} jobs", data={"job_ids": job_ids})


@router.post("/workers/run", response_model=GenericMessage)
def run_worker(payload: RunWorkerRequest):
    init_db()
    results = run_workers(channel=payload.profile, limit=payload.limit)
    return GenericMessage(message=f"Processed {len(results)} jobs", data={"items": [r.__dict__ | {"root": str(r.root), "video_path": str(r.video_path), "thumbnail_path": str(r.thumbnail_path)} for r in results]})


@router.get("/content")
def get_content(limit: int = Query(default=100, ge=1, le=500)):
    return {"items": scan_content_library(limit=limit)}


@router.get("/trends")
def get_trends():
    return load_trends_cache()


@router.post("/trends/scan")
def post_trends(payload: TrendScanRequest):
    return scan_trends(niche=payload.niche, geo=payload.geo, max_items=payload.max_items)


@router.post("/trends/refresh")
def refresh():
    return refresh_trends_cache()


@router.get("/settings/keys")
def get_key_status():
    return {
        "openai_keys": len(settings.openai_api_keys),
        "elevenlabs_keys": len(settings.elevenlabs_api_keys),
        "pexels": bool(settings.pexels_api_key),
        "pixabay": bool(settings.pixabay_api_key),
        "newsapi": bool(os.getenv("NEWSAPI_KEY", "").strip()),
        "serpapi": bool(os.getenv("SERPAPI_KEY", "").strip()),
        "youtube_upload_enabled": settings.upload_to_youtube,
        "upload_thumbnail": settings.upload_thumbnail,
        "upload_captions": settings.upload_captions,
    }


@router.get("/sources")
def get_sources():
    return {
        "research_providers": settings.research_provider_order,
        "footage_providers": settings.footage_provider_order,
        "voice_providers": settings.voice_provider_order,
        "transcribe_providers": settings.transcribe_provider_order,
        "trend_sources": [
            "Google Trends Trending Now page / RSS",
            "GDELT",
            "NewsAPI (optional)",
            "SerpApi Google Trends (optional)",
            "Trafilatura / Scrapling hooks for article fetch",
        ],
    }
