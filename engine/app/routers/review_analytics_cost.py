"""V5 Review + Analytics + Cost Router API — Review queue, analytics, cost routing."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..db_v5 import (
    list_review_items, resolve_review_item, create_review_item,
    get_analytics_summary, get_cost_summary,
    list_budget_profiles, create_budget_profile,
    log_provider_usage,
)

router = APIRouter(prefix="/api/v5", tags=["review-analytics-cost"])


# ═══════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════

class ResolveRequest(BaseModel):
    status: str = "approved"   # approved, rejected, escalated
    resolved_by: str = "user"


class BudgetProfileRequest(BaseModel):
    name: str
    monthly_limit: float = 100.0
    quality_mode: str = "budget"
    rules: dict | None = None


# ═══════════════════════════════════════════════════════════
# Review Center
# ═══════════════════════════════════════════════════════════

@router.get("/review")
def get_review_items(
    status: str = Query(default="open"),
    channel: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    items = list_review_items(status=status, channel=channel, limit=limit)
    return {
        "items": items,
        "total": len(items),
        "by_type": _group_by(items, "review_type"),
    }


@router.post("/review/{item_id}/resolve")
def resolve_item(item_id: int, req: ResolveRequest):
    resolve_review_item(item_id, status=req.status, resolved_by=req.resolved_by)
    return {"ok": True, "message": f"Review item #{item_id} → {req.status}"}


@router.get("/review/summary")
def review_summary():
    from ..db import get_conn
    conn = get_conn()
    open_count = conn.execute("SELECT COUNT(*) FROM review_items WHERE status='open'").fetchone()[0]
    resolved_today = conn.execute(
        "SELECT COUNT(*) FROM review_items WHERE status IN ('approved','rejected') AND resolved_at >= date('now')"
    ).fetchone()[0]
    by_type = {}
    for row in conn.execute("SELECT review_type, COUNT(*) as cnt FROM review_items WHERE status='open' GROUP BY review_type").fetchall():
        by_type[row[0]] = row[1]
    return {"open": open_count, "resolved_today": resolved_today, "by_type": by_type}


# ═══════════════════════════════════════════════════════════
# Analytics
# ═══════════════════════════════════════════════════════════

@router.get("/analytics")
def get_analytics(channel: str | None = None, days: int = Query(default=30, ge=1, le=365)):
    daily = get_analytics_summary(channel=channel, days=days)
    # Aggregate totals
    totals = {
        "jobs_created": sum(d.get("jobs_created", 0) for d in daily),
        "jobs_completed": sum(d.get("jobs_completed", 0) for d in daily),
        "jobs_failed": sum(d.get("jobs_failed", 0) for d in daily),
        "videos_rendered": sum(d.get("videos_rendered", 0) for d in daily),
        "uploads_completed": sum(d.get("uploads_completed", 0) for d in daily),
        "total_cost": round(sum(d.get("total_cost_estimate", 0) for d in daily), 2),
        "avg_confidence": round(
            sum(d.get("avg_scene_confidence", 0) for d in daily) / max(len(daily), 1), 3
        ) if daily else 0,
    }
    return {"daily": daily, "totals": totals, "days": days}


@router.get("/analytics/providers")
def provider_analytics(channel: str | None = None, days: int = 30):
    cost_data = get_cost_summary(channel=channel, days=days)
    return cost_data


# ═══════════════════════════════════════════════════════════
# Cost Router
# ═══════════════════════════════════════════════════════════

@router.get("/cost/summary")
def cost_summary(channel: str | None = None, days: int = 30):
    data = get_cost_summary(channel=channel, days=days)
    total_cost = sum(b.get("total_cost", 0) or 0 for b in data.get("breakdown", []))
    total_requests = sum(b.get("requests", 0) or 0 for b in data.get("breakdown", []))
    total_tokens = sum(b.get("total_tokens", 0) or 0 for b in data.get("breakdown", []))
    cache_hits = sum(b.get("cache_hits", 0) or 0 for b in data.get("breakdown", []))
    return {
        **data,
        "total_cost": round(total_cost, 4),
        "total_requests": total_requests,
        "total_tokens": total_tokens,
        "cache_hits": cache_hits,
        "cache_hit_rate": round(cache_hits / max(total_requests, 1) * 100, 1),
    }


@router.get("/cost/budgets")
def get_budgets():
    return {"items": list_budget_profiles()}


@router.post("/cost/budgets")
def add_budget(req: BudgetProfileRequest):
    bid = create_budget_profile(
        name=req.name, monthly_limit=req.monthly_limit,
        quality_mode=req.quality_mode, rules=req.rules,
    )
    return {"ok": True, "id": bid, "message": f"Budget profile '{req.name}' created"}


@router.get("/cost/simulate")
def simulate_cost(task_type: str = "script", quality: str = "balanced"):
    """Simulate cost for a task type given quality mode."""
    cost_estimates = {
        "script": {"budget": 0.002, "balanced": 0.01, "premium": 0.03},
        "tts": {"budget": 0.0, "balanced": 0.005, "premium": 0.02},
        "footage": {"budget": 0.0, "balanced": 0.0, "premium": 0.0},
        "image": {"budget": 0.0, "balanced": 0.01, "premium": 0.04},
        "research": {"budget": 0.001, "balanced": 0.005, "premium": 0.02},
    }
    estimates = cost_estimates.get(task_type, {"budget": 0, "balanced": 0, "premium": 0})
    return {
        "task_type": task_type,
        "quality": quality,
        "estimated_cost": estimates.get(quality, 0),
        "all_modes": estimates,
    }


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def _group_by(items: list[dict], key: str) -> dict[str, int]:
    groups: dict[str, int] = {}
    for item in items:
        val = item.get(key, "unknown")
        groups[val] = groups.get(val, 0) + 1
    return groups
