
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
from .scheduler_ui import start_background_scheduler

app = FastAPI(title="ChannelForge Studio", version="5.0.0")

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


@app.get("/healthz")
def healthz():
    return {"ok": True, "app": "channelforge-studio-v5"}


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/v2/audit-logs")
def get_audit_logs(limit: int = Query(default=100, ge=1, le=500), action: str | None = None, channel: str | None = None):
    items = list_audit_logs(limit=limit, action=action, channel=channel)
    return {"items": items}
