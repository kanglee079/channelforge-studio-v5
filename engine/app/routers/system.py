"""Diagnostics & Setup Wizard API — System health, environment checks, first-run wizard."""

from __future__ import annotations

import os
import sys
import shutil
import platform
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v5/system", tags=["system"])


# ═══════════════════════════════════════════════════════════
# Diagnostics Center
# ═══════════════════════════════════════════════════════════

@router.get("/diagnostics")
def get_diagnostics():
    """Full system diagnostics report."""
    engine_dir = Path(__file__).resolve().parent.parent
    data_dir = engine_dir / "data"
    db_path = data_dir / "channelforge.db"
    env_path = engine_dir / ".env"
    ws_dir = data_dir / "workspaces"

    # Check Python packages
    packages = _check_packages()

    # Check disk usage
    disk = shutil.disk_usage(str(engine_dir))

    # Check API keys
    from ..config import settings
    api_keys = {
        "OPENAI_API_KEY": len(settings.openai_api_keys) > 0,
        "PEXELS_KEY": bool(settings.pexels_api_key),
        "PIXABAY_KEY": bool(settings.pixabay_api_key),
        "ELEVENLABS_KEY": bool(settings.elevenlabs_api_keys),
    }

    # DB stats
    db_stats = _get_db_stats()

    return {
        "environment": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "arch": platform.machine(),
            "engine_dir": str(engine_dir),
            "data_dir": str(data_dir),
        },
        "files": {
            "db_exists": db_path.exists(),
            "db_size_mb": round(db_path.stat().st_size / 1024 / 1024, 2) if db_path.exists() else 0,
            "env_exists": env_path.exists(),
            "workspaces_dir": ws_dir.exists(),
            "workspace_count": len(list(ws_dir.iterdir())) if ws_dir.exists() else 0,
        },
        "disk": {
            "total_gb": round(disk.total / 1024**3, 1),
            "used_gb": round(disk.used / 1024**3, 1),
            "free_gb": round(disk.free / 1024**3, 1),
            "usage_percent": round(disk.used / disk.total * 100, 1),
        },
        "packages": packages,
        "api_keys": api_keys,
        "db_stats": db_stats,
    }


@router.get("/diagnostics/quick")
def quick_health():
    """Quick health check — lightweight."""
    engine_dir = Path(__file__).resolve().parent.parent
    db_path = engine_dir / "data" / "channelforge.db"
    return {
        "ok": True,
        "db_exists": db_path.exists(),
        "python": sys.version.split()[0],
        "platform": platform.system(),
    }


# ═══════════════════════════════════════════════════════════
# Setup Wizard
# ═══════════════════════════════════════════════════════════

class SetupStep(BaseModel):
    step: str  # check_env | check_deps | check_keys | init_db | ready


@router.get("/setup/status")
def setup_status():
    """Check which setup steps are complete."""
    engine_dir = Path(__file__).resolve().parent.parent
    data_dir = engine_dir / "data"
    env_path = engine_dir / ".env"
    db_path = data_dir / "channelforge.db"

    from ..config import settings

    steps = {
        "env_file": env_path.exists(),
        "database": db_path.exists(),
        "api_keys": len(settings.openai_api_keys) > 0,
        "data_dir": data_dir.exists(),
        "channels": False,
    }

    # Check if any channels exist
    try:
        from ..db import get_conn
        conn = get_conn()
        count = conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
        steps["channels"] = count > 0
    except Exception:
        pass

    all_done = all(steps.values())
    return {"steps": steps, "complete": all_done, "progress": sum(steps.values()), "total": len(steps)}


@router.post("/setup/init-dirs")
def init_directories():
    """Create required directories."""
    engine_dir = Path(__file__).resolve().parent.parent
    dirs = [
        engine_dir / "data",
        engine_dir / "data" / "workspaces",
        engine_dir / "data" / "media",
        engine_dir / "data" / "exports",
        engine_dir / "data" / "temp",
    ]
    created = []
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d))
    return {"ok": True, "created": created, "message": f"Created {len(created)} directories"}


@router.post("/setup/init-env")
def init_env_file():
    """Create a template .env file if it doesn't exist."""
    engine_dir = Path(__file__).resolve().parent.parent
    env_path = engine_dir / ".env"
    if env_path.exists():
        return {"ok": True, "message": "File .env đã tồn tại"}

    template = """# ChannelForge Studio V5 — Environment Configuration
# Uncomment and fill in your API keys

OPENAI_API_KEY=
PEXELS_KEY=
PIXABAY_KEY=
ELEVENLABS_KEY=

# Optional
# NEWSAPI_KEY=
# OLLAMA_HOST=http://localhost:11434
"""
    env_path.write_text(template, encoding="utf-8")
    return {"ok": True, "message": "Đã tạo file .env mẫu — hãy điền API keys"}


# ═══════════════════════════════════════════════════════════
# V4 → V5 Migration
# ═══════════════════════════════════════════════════════════

@router.get("/migration/check")
def check_migration():
    """Check if V4 data exists and needs migration."""
    engine_dir = Path(__file__).resolve().parent.parent
    db_path = engine_dir / "data" / "channelforge.db"

    if not db_path.exists():
        return {"needs_migration": False, "reason": "No database found"}

    from ..db import get_conn
    conn = get_conn()

    # Check which tables exist
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    v5_tables = ["proxy_profiles", "workspace_health_events", "media_assets",
                 "scene_match_results", "trend_items", "review_items",
                 "analytics_daily", "provider_usage_events", "budget_profiles"]

    missing_v5 = [t for t in v5_tables if t not in tables]

    return {
        "needs_migration": len(missing_v5) > 0,
        "existing_tables": len(tables),
        "missing_v5_tables": missing_v5,
        "v5_ready": len(missing_v5) == 0,
    }


@router.post("/migration/apply")
def apply_migration():
    """Apply V5 migration if needed."""
    from ..db import get_conn, init_db
    init_db()  # re-run init_db which applies all migrations
    return {"ok": True, "message": "V5 migration applied successfully"}


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def _check_packages() -> dict[str, dict]:
    """Check if required Python packages are installed."""
    required = {
        "fastapi": "Web framework",
        "uvicorn": "ASGI server",
        "openai": "OpenAI API",
        "aiohttp": "Async HTTP",
        "playwright": "Browser automation",
        "pydantic": "Data validation",
    }
    optional = {
        "pytrends": "Google Trends",
        "feedparser": "RSS parsing",
        "moviepy": "Video editing",
        "elevenlabs": "ElevenLabs TTS",
    }

    result = {}
    for pkg, desc in {**required, **optional}.items():
        try:
            __import__(pkg)
            result[pkg] = {"installed": True, "description": desc, "required": pkg in required}
        except ImportError:
            result[pkg] = {"installed": False, "description": desc, "required": pkg in required}
    return result


def _get_db_stats() -> dict:
    """Get database statistics."""
    try:
        from ..db import get_conn
        conn = get_conn()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        stats = {"table_count": len(tables)}
        for table in tables:
            name = table[0]
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
                stats[name] = count
            except Exception:
                pass
        return stats
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════
# V5.8 — Enhanced Diagnostics & Support Bundle
# ═══════════════════════════════════════════════════════════

from ..services.diagnostics import (
    get_full_diagnostics, get_dependency_matrix,
    generate_support_bundle, get_migration_status,
    run_pending_migrations, log_crash,
)


@router.get("/diagnostics/full")
def diagnostics_full():
    """V5.8 comprehensive diagnostics — OS, Python, deps, FFmpeg, DB, media cache."""
    return get_full_diagnostics()


@router.get("/diagnostics/dependencies")
def diagnostics_dependencies():
    """Optional dependency matrix."""
    return {"dependencies": get_dependency_matrix()}


@router.post("/diagnostics/support-bundle")
def create_support_bundle():
    """Generate sanitized support bundle ZIP (no credentials)."""
    path = generate_support_bundle()
    return {"ok": True, "path": path, "message": f"Support bundle generated: {path}"}


@router.get("/migrations/status")
def migrations_status():
    """Get migration version status."""
    return get_migration_status()


@router.post("/migrations/run")
def run_migrations():
    """Run pending DB migrations."""
    return run_pending_migrations()
