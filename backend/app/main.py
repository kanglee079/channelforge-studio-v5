
from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import init_db
from .profiles import sync_profiles
from .routers.api import router as api_router
from .scheduler_ui import start_background_scheduler

app = FastAPI(title="YouTube Auto Studio V4", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
sync_profiles()
start_background_scheduler()

app.include_router(api_router, prefix="/api")

frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


@app.get("/healthz")
def healthz():
    return {"ok": True, "app": "youtube-auto-studio-v4"}
