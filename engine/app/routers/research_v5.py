"""V5 Research/Trend API Router — Trend ingestion, scoring, watchlists, idea generation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db_v5 import (
    list_trend_items, list_watchlists, create_watchlist,
)

router = APIRouter(prefix="/api/v5/research", tags=["research-v5"])


class IngestRequest(BaseModel):
    sources: list[str] = ["google_trends", "newsapi"]
    query: str = ""
    region: str = "US"
    max_per_source: int = 10


class ScoreTrendsRequest(BaseModel):
    channel_name: str


class GenerateIdeasRequest(BaseModel):
    trend_title: str
    channel_name: str
    max_ideas: int = 5


class ResearchPackRequest(BaseModel):
    idea_id: int
    channel_name: str


class WatchlistRequest(BaseModel):
    channel_name: str
    name: str
    watch_type: str = "keyword"
    query: str


# ── Trend Ingestion ──────────────────────────────────────
@router.post("/trends/ingest")
async def ingest_trends(req: IngestRequest):
    from ..research_v5.ingestion import ingest_trends as do_ingest
    items = await do_ingest(
        sources=req.sources, query=req.query,
        region=req.region, max_per_source=req.max_per_source,
    )
    return {"ok": True, "total": len(items), "message": f"Ingested {len(items)} trends"}


# ── List Trends ──────────────────────────────────────────
@router.get("/trends")
def get_trends(source: str | None = None, limit: int = 50):
    items = list_trend_items(source_type=source, limit=limit)
    return {"items": items}


# ── Score Trends for Channel ─────────────────────────────
@router.post("/trends/score")
def score_trends(req: ScoreTrendsRequest):
    from ..research_v5.scoring import score_trends_for_channel
    results = score_trends_for_channel(req.channel_name)
    return {
        "channel": req.channel_name,
        "total": len(results),
        "items": results,
        "produce": sum(1 for r in results if r.get("recommended_action") == "produce"),
        "research": sum(1 for r in results if r.get("recommended_action") == "research"),
    }


# ── Generate Ideas from Trend ────────────────────────────
@router.post("/ideas/generate")
async def generate_ideas(req: GenerateIdeasRequest):
    from ..research_v5.idea_generator import generate_ideas_from_trend
    ideas = await generate_ideas_from_trend(
        trend_title=req.trend_title,
        channel_name=req.channel_name,
        max_ideas=req.max_ideas,
    )
    return {"ok": True, "ideas": ideas, "count": len(ideas)}


# ── Research Pack ────────────────────────────────────────
@router.post("/research-pack/generate")
async def gen_research_pack(req: ResearchPackRequest):
    from ..research_v5.idea_generator import generate_research_pack
    result = await generate_research_pack(req.idea_id, req.channel_name)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


# ── Watchlists ───────────────────────────────────────────
@router.get("/watchlists")
def get_watchlists(channel: str | None = None):
    return {"items": list_watchlists(channel=channel)}


@router.post("/watchlists")
def add_watchlist(req: WatchlistRequest):
    wid = create_watchlist(
        channel_name=req.channel_name,
        name=req.name,
        watch_type=req.watch_type,
        query=req.query,
    )
    return {"ok": True, "id": wid, "message": f"Watchlist '{req.name}' created"}
