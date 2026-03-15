"""Diagnostics & Support Bundle — V5.8 system health checks.

Full diagnostics: OS, Python, deps, FFmpeg, Playwright, DB, media cache.
Each check returns structured result: {ok, severity, message, fix, blocks}.
Support bundle export (sanitized — no credentials).
"""

from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..db import get_conn
from ..utils import utc_now_iso

logger = logging.getLogger(__name__)

APP_VERSION = "5.8.0"


# ═══════════════════════════════════════════════════════════
# Structured check result builder
# ═══════════════════════════════════════════════════════════

def _check(ok: bool, message: str, *, severity: str = "info",
           fix: str = "", blocks: str = "none", **extra) -> dict:
    """Build a structured check result.

    severity: critical | warning | info
    blocks:   boot | feature_subset | none
    """
    return {"ok": ok, "severity": severity, "message": message,
            "fix": fix, "blocks": blocks, **extra}


# ═══════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════

def get_full_diagnostics() -> dict:
    """Run comprehensive system diagnostics."""
    checks = {
        "python": _check_python(),
        "database": _check_database(),
        "ffmpeg": _check_ffmpeg(),
        "playwright": _check_playwright(),
        "writable_dirs": _check_writable_dirs(),
        "api_keys": _check_api_keys(),
        "media_cache": _check_media_cache(),
    }

    # Compute overall health from severity
    severities = [c["severity"] for c in checks.values() if not c["ok"]]
    if "critical" in severities:
        overall = "blocked"
    elif "warning" in severities:
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "timestamp": utc_now_iso(),
        "overall_health": overall,
        "app": _app_info(),
        "system": _system_info(),
        "checks": checks,
        "dependencies": _dependency_matrix(),
        "workspace_summary": _workspace_summary(),
        "recent_errors": _recent_errors(),
    }


def get_readiness() -> dict:
    """Get structured readiness report for first-run wizard."""
    checks = {
        "python": _check_python(),
        "database": _check_database(),
        "ffmpeg": _check_ffmpeg(),
        "playwright": _check_playwright(),
        "writable_dirs": _check_writable_dirs(),
        "api_keys": _check_api_keys(),
        "media_cache": _check_media_cache(),
        "migrations": _check_migrations(),
    }

    # Classify
    blockers = [k for k, v in checks.items() if v["blocks"] == "boot" and not v["ok"]]
    warnings = [k for k, v in checks.items() if not v["ok"] and v["blocks"] != "boot"]
    passed = [k for k, v in checks.items() if v["ok"]]

    all_ok = len(blockers) == 0
    status = "ready" if all_ok and len(warnings) == 0 else "degraded" if all_ok else "blocked"

    return {
        "ok": all_ok,
        "status": status,
        "version": APP_VERSION,
        "checks": checks,
        "summary": {
            "passed": len(passed),
            "warnings": len(warnings),
            "blockers": len(blockers),
            "total": len(checks),
        },
        "blocker_names": blockers,
        "warning_names": warnings,
    }


def get_health_quick() -> dict:
    """Fast health check for /api/health endpoint."""
    py = _check_python()
    db = _check_database()
    if not py["ok"] or not db["ok"]:
        status = "blocked"
    else:
        ffmpeg = _check_ffmpeg()
        status = "healthy" if ffmpeg["ok"] else "degraded"

    return {
        "ok": status != "blocked",
        "status": status,
        "version": APP_VERSION,
        "checks": {
            "python": py["ok"],
            "database": db["ok"],
        },
    }


def get_dependency_matrix() -> dict:
    return _dependency_matrix()


def generate_support_bundle(output_dir: str = "engine/data") -> str:
    """Generate a sanitized support bundle ZIP file."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bundle_name = f"channelforge_support_{ts}"
    output_path = Path(output_dir) / f"{bundle_name}.zip"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    diag = get_full_diagnostics()

    with zipfile.ZipFile(str(output_path), 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{bundle_name}/diagnostics.json", json.dumps(diag, indent=2, ensure_ascii=False))

        migration_status = get_migration_status()
        zf.writestr(f"{bundle_name}/migrations.json", json.dumps(migration_status, indent=2))

        conn = get_conn()
        try:
            crashes = conn.execute("SELECT * FROM crash_logs ORDER BY created_at DESC LIMIT 50").fetchall()
            zf.writestr(f"{bundle_name}/crash_logs.json", json.dumps([dict(r) for r in crashes], indent=2, ensure_ascii=False))
        except Exception:
            pass

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
    conn = get_conn()
    try:
        rows = conn.execute("SELECT version, applied_at FROM schema_version ORDER BY version").fetchall()
        applied = [{"version": r["version"], "applied_at": r["applied_at"]} for r in rows]
    except Exception:
        applied = []

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
    from ..db import _run_migrations
    try:
        _run_migrations()
        status = get_migration_status()
        return {"ok": True, "message": f"Migrations completed. Current version: {status['current_version']}", **status}
    except Exception as e:
        return {"ok": False, "message": f"Migration failed: {e}"}


def log_crash(error_type: str, error_message: str, traceback_str: str = "", context: dict | None = None):
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
# Internal structured checks
# ═══════════════════════════════════════════════════════════

def _app_info() -> dict:
    return {
        "name": "ChannelForge Studio",
        "version": APP_VERSION,
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


def _check_python() -> dict:
    v = sys.version.split(" ")[0]
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 11):
        return _check(False, f"Python {v} — cần >= 3.11",
                       severity="critical", blocks="boot",
                       fix="Cài Python 3.11+ từ python.org",
                       version=v, executable=sys.executable)
    return _check(True, f"Python {v}",
                   version=v, executable=sys.executable)


def _check_database() -> dict:
    try:
        conn = get_conn()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        count = conn.execute("SELECT COUNT(*) FROM workspaces").fetchone()[0]
        return _check(True, f"{len(tables)} bảng, {count} workspaces",
                       tables=len(tables), workspace_count=count)
    except Exception as e:
        return _check(False, f"Database lỗi: {e}",
                       severity="critical", blocks="boot",
                       fix="Kiểm tra quyền ghi file DB trong engine/data/")


def _check_ffmpeg() -> dict:
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            ver = result.stdout.split("\n")[0] if result.stdout else ""
            return _check(True, ver[:60], path=shutil.which("ffmpeg") or "")
        return _check(False, "FFmpeg không hoạt động",
                       severity="warning", blocks="feature_subset",
                       fix="Cài FFmpeg: https://ffmpeg.org/download.html và thêm vào PATH")
    except FileNotFoundError:
        return _check(False, "FFmpeg chưa cài",
                       severity="warning", blocks="feature_subset",
                       fix="Cài FFmpeg: https://ffmpeg.org/download.html và thêm vào PATH")
    except Exception:
        return _check(False, "FFmpeg check timeout",
                       severity="warning", blocks="feature_subset",
                       fix="Kiểm tra FFmpeg hoạt động: ffmpeg -version")


def _check_playwright() -> dict:
    try:
        import playwright  # noqa: F401
        return _check(True, "Playwright đã cài",
                       severity="info", installed=True)
    except ImportError:
        return _check(False, "Playwright chưa cài",
                       severity="warning", blocks="feature_subset",
                       fix="pip install playwright && python -m playwright install chromium",
                       installed=False)


def _check_writable_dirs() -> dict:
    dirs_to_check = [
        Path("engine/data"),
        Path("engine/data/media_cache"),
    ]
    issues = []
    for d in dirs_to_check:
        d.mkdir(parents=True, exist_ok=True)
        test_file = d / ".write_test"
        try:
            test_file.write_text("ok")
            test_file.unlink()
        except Exception:
            issues.append(str(d))

    if issues:
        return _check(False, f"Không ghi được: {', '.join(issues)}",
                       severity="critical", blocks="boot",
                       fix=f"Cấp quyền ghi cho: {', '.join(issues)}",
                       failed_dirs=issues)
    return _check(True, "Tất cả thư mục ghi được")


def _check_api_keys() -> dict:
    from ..config import settings
    keys = {
        "OPENAI_API_KEY": len(settings.openai_api_keys) > 0,
        "PEXELS_API_KEY": bool(settings.pexels_api_key),
        "PIXABAY_API_KEY": bool(settings.pixabay_api_key),
        "ELEVENLABS_API_KEY": len(settings.elevenlabs_api_keys) > 0,
    }
    configured = sum(1 for v in keys.values() if v)
    total = len(keys)

    if configured == 0:
        return _check(False, f"Chưa cấu hình API key nào (0/{total})",
                       severity="warning", blocks="feature_subset",
                       fix="Tạo file engine/.env và thêm API keys (xem docs/API_KEYS_VI.md)",
                       keys=keys)
    if configured < total:
        missing = [k for k, v in keys.items() if not v]
        return _check(True, f"{configured}/{total} keys đã cấu hình",
                       severity="info",
                       fix=f"Thiếu: {', '.join(missing)}",
                       keys=keys)
    return _check(True, f"Tất cả {total} API keys đã cấu hình", keys=keys)


def _check_media_cache() -> dict:
    cache_dir = Path("engine/data/media_cache")
    if not cache_dir.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
        return _check(True, "Media cache vừa tạo (trống)", exists=False, size_mb=0)
    size = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
    size_mb = round(size / 1024 / 1024, 1)
    return _check(True, f"Media cache: {size_mb} MB", exists=True, size_mb=size_mb)


def _check_migrations() -> dict:
    status = get_migration_status()
    pending = len(status["pending"])
    if pending > 0:
        return _check(False, f"{pending} migration(s) chưa chạy",
                       severity="warning", blocks="feature_subset",
                       fix="Chạy migrations từ trang Chẩn đoán hoặc restart backend",
                       current_version=status["current_version"], pending=pending)
    return _check(True, f"DB migration v{status['current_version']} — tất cả đã chạy",
                   current_version=status["current_version"], pending=0)


def _dependency_matrix() -> dict:
    deps = {}
    check_list = [
        ("numpy", "Vector operations, embeddings", "pip install numpy"),
        ("sentence_transformers", "CLIP/semantic embeddings", "pip install sentence-transformers"),
        ("faiss", "Fast vector search", "pip install faiss-cpu"),
        ("open_clip", "Multilingual CLIP", "pip install open-clip-torch"),
        ("cv2", "Frame extraction from video", "pip install opencv-python-headless"),
        ("moviepy", "Video editing fallback", "pip install moviepy"),
        ("PIL", "Image processing", "pip install Pillow"),
        ("playwright", "Browser automation", "pip install playwright"),
        ("httpx", "HTTP client", "pip install httpx"),
        ("pydantic", "Data validation (required)", "pip install pydantic"),
        ("scrapling", "Web scraping", "pip install scrapling"),
        ("faster_whisper", "Local transcription", "pip install faster-whisper"),
        ("kokoro", "Local TTS", "pip install kokoro"),
    ]
    for name, purpose, install_cmd in check_list:
        try:
            mod = __import__(name)
            version = getattr(mod, "__version__", "installed")
            deps[name] = {"installed": True, "version": str(version), "purpose": purpose}
        except ImportError:
            deps[name] = {"installed": False, "version": "", "purpose": purpose, "install": install_cmd}
    return deps


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
