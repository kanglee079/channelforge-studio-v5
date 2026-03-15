
from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db, list_audit_logs
from .profiles import sync_profiles
from .routers.api import router as api_router
from .routers.workspaces import router as workspaces_router
from .routers.research import router as research_router
from .routers.content import router as content_router
from .routers.templates import router as templates_router, seed_default_templates
from .routers.visual_match import router as visual_match_router
from .routers.research_v5 import router as research_v5_router
from .routers.review_analytics_cost import router as rac_router
from .routers.system import router as system_router
from .routers.media_intel import router as media_intel_router
from .scheduler_ui import start_background_scheduler

app = FastAPI(title="ChannelForge Studio", version="5.8.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
sync_profiles()
seed_default_templates()
start_background_scheduler()

# V1 API (backward compatible)
app.include_router(api_router, prefix="/api")

# V2 API (Phase 1 + Phase 2)
app.include_router(workspaces_router)
app.include_router(research_router)
app.include_router(content_router)
app.include_router(templates_router)

# V5 API (Phase 3+)
app.include_router(visual_match_router)
app.include_router(research_v5_router)
app.include_router(rac_router)
app.include_router(system_router)
app.include_router(media_intel_router)


@app.get("/healthz")
def healthz():
    return {"ok": True, "app": "channelforge-studio-v5"}


@app.get("/api/health")
def health():
    from .services.diagnostics import get_health_quick
    return get_health_quick()


@app.get("/api/v2/audit-logs")
def get_audit_logs(limit: int = Query(default=100, ge=1, le=500), action: str | None = None, channel: str | None = None):
    items = list_audit_logs(limit=limit, action=action, channel=channel)
    return {"items": items}
