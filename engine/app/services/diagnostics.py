"""Diagnostics & Support Bundle — V5.8 system health checks.

Full diagnostics: OS, Python, deps, FFmpeg, Playwright, DB, media cache.
Support bundle export (sanitized — no credentials).
"""

from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from ..db import get_conn
from ..utils import utc_now_iso

logger = logging.getLogger(__name__)


def get_full_diagnostics() -> dict:
    """Run comprehensive system diagnostics."""
    diag = {
        "timestamp": utc_now_iso(),
        "app": _app_info(),
        "system": _system_info(),
        "python": _python_info(),
        "dependencies": _dependency_matrix(),
        "ffmpeg": _check_ffmpeg(),
        "playwright": _check_playwright(),
        "database": _check_database(),
        "media_cache": _check_media_cache(),
        "workspace_summary": _workspace_summary(),
        "recent_errors": _recent_errors(),
    }

    # Overall health
    critical_checks = [
        diag["python"]["ok"],
        diag["database"]["ok"],
    ]
    diag["overall_health"] = "healthy" if all(critical_checks) else "degraded"
    return diag


def get_dependency_matrix() -> dict:
    """Get installed optional dependencies."""
    return _dependency_matrix()


def generate_support_bundle(output_dir: str = "engine/data") -> str:
    """Generate a sanitized support bundle ZIP file."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bundle_name = f"channelforge_support_{ts}"
    output_path = Path(output_dir) / f"{bundle_name}.zip"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    diag = get_full_diagnostics()

    with zipfile.ZipFile(str(output_path), 'w', zipfile.ZIP_DEFLATED) as zf:
        # Diagnostics JSON
        zf.writestr(f"{bundle_name}/diagnostics.json", json.dumps(diag, indent=2, ensure_ascii=False))

        # Migration status
        migration_status = get_migration_status()
        zf.writestr(f"{bundle_name}/migrations.json", json.dumps(migration_status, indent=2))

        # Recent crash logs
        conn = get_conn()
        try:
            crashes = conn.execute("SELECT * FROM crash_logs ORDER BY created_at DESC LIMIT 50").fetchall()
            zf.writestr(f"{bundle_name}/crash_logs.json", json.dumps([dict(r) for r in crashes], indent=2, ensure_ascii=False))
        except Exception:
            pass

        # Recent health events
        try:
            events = conn.execute("SELECT * FROM workspace_health_events ORDER BY created_at DESC LIMIT 100").fetchall()
            zf.writestr(f"{bundle_name}/health_events.json", json.dumps([dict(r) for r in events], indent=2, ensure_ascii=False))
        except Exception:
            pass

        # Masked config
        try:
            configs = conn.execute("SELECT * FROM app_config").fetchall()
            masked = []
            for c in configs:
                d = dict(c)
                key_lower = d["key"].lower()
                if any(s in key_lower for s in ("key", "secret", "password", "token", "credential")):
                    d["value"] = "***MASKED***"
                masked.append(d)
            zf.writestr(f"{bundle_name}/app_config_masked.json", json.dumps(masked, indent=2, ensure_ascii=False))
        except Exception:
            pass

    logger.info("Support bundle generated: %s", output_path)
    return str(output_path)


def get_migration_status() -> dict:
    """Get migration version status."""
    conn = get_conn()
    try:
        rows = conn.execute("SELECT version, applied_at FROM schema_version ORDER BY version").fetchall()
        applied = [{"version": r["version"], "applied_at": r["applied_at"]} for r in rows]
    except Exception:
        applied = []

    # List migration files
    migrations_dir = Path(__file__).parent.parent / "migrations"
    available = []
    if migrations_dir.exists():
        for f in sorted(migrations_dir.glob("*.sql")):
            ver = int(f.stem.split("_")[0])
            available.append({"version": ver, "filename": f.name})

    applied_versions = {m["version"] for m in applied}
    pending = [m for m in available if m["version"] not in applied_versions]

    return {
        "applied": applied,
        "available": available,
        "pending": pending,
        "current_version": max(applied_versions) if applied_versions else 0,
    }


def run_pending_migrations() -> dict:
    """Run all pending migrations."""
    from ..db import _run_migrations
    try:
        _run_migrations()
        status = get_migration_status()
        return {"ok": True, "message": f"Migrations completed. Current version: {status['current_version']}", **status}
    except Exception as e:
        return {"ok": False, "message": f"Migration failed: {e}"}


def log_crash(error_type: str, error_message: str, traceback_str: str = "", context: dict | None = None):
    """Log a crash/error to the database."""
    conn = get_conn()
    now = utc_now_iso()
    try:
        conn.execute(
            "INSERT INTO crash_logs (error_type, error_message, traceback, context_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (error_type, error_message[:1000], traceback_str[:5000], json.dumps(context or {}), now),
        )
        conn.commit()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# Internal checkers
# ═══════════════════════════════════════════════════════════

def _app_info() -> dict:
    return {
        "name": "ChannelForge Studio",
        "version": "5.8.0",
        "build_type": "dev" if (Path("engine") / ".venv").exists() else "packaged",
    }


def _system_info() -> dict:
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "arch": platform.machine(),
        "hostname": platform.node(),
        "cpu_count": os.cpu_count(),
        "disk_free_gb": round(shutil.disk_usage(".").free / 1024**3, 1),
    }


def _python_info() -> dict:
    return {
        "ok": True,
        "version": sys.version,
        "executable": sys.executable,
        "prefix": sys.prefix,
    }


def _dependency_matrix() -> dict:
    """Check optional dependencies."""
    deps = {}
    for name in ["numpy", "sentence_transformers", "faiss", "open_clip",
                  "cv2", "moviepy", "PIL", "playwright", "httpx", "pydantic"]:
        try:
            mod = __import__(name)
            version = getattr(mod, "__version__", "installed")
            deps[name] = {"installed": True, "version": str(version)}
        except ImportError:
            deps[name] = {"installed": False, "version": ""}

    return deps


def _check_ffmpeg() -> dict:
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        version_line = result.stdout.split("\n")[0] if result.stdout else ""
        return {"ok": result.returncode == 0, "version": version_line, "path": shutil.which("ffmpeg") or ""}
    except Exception:
        return {"ok": False, "version": "", "path": ""}


def _check_playwright() -> dict:
    try:
        from playwright.sync_api import sync_playwright
        return {"ok": True, "installed": True}
    except ImportError:
        return {"ok": False, "installed": False}


def _check_database() -> dict:
    try:
        conn = get_conn()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t["name"] for t in tables]
        row_count = conn.execute("SELECT COUNT(*) FROM workspaces").fetchone()[0]
        return {"ok": True, "tables": len(table_names), "workspace_count": row_count}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _check_media_cache() -> dict:
    cache_dir = Path("engine/data/media_cache")
    if not cache_dir.exists():
        return {"ok": True, "exists": False, "size_mb": 0}
    size = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
    return {"ok": True, "exists": True, "size_mb": round(size / 1024 / 1024, 1)}


def _workspace_summary() -> dict:
    try:
        conn = get_conn()
        total = conn.execute("SELECT COUNT(*) FROM workspaces").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM workspaces WHERE session_status='active'").fetchone()[0]
        return {"total": total, "active": active}
    except Exception:
        return {"total": 0, "active": 0}


def _recent_errors() -> list[dict]:
    try:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM crash_logs ORDER BY created_at DESC LIMIT 5").fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
