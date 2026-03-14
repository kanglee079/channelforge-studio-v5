
from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from ..config import settings
from ..db import get_conn
from ..profiles import list_profiles, load_profile


def dashboard_summary() -> dict[str, Any]:
    with get_conn() as conn:
        job_counts = {row["state"]: row["c"] for row in conn.execute("SELECT state, COUNT(*) as c FROM jobs GROUP BY state")}
        total_jobs = sum(job_counts.values())
        recent = [dict(row) for row in conn.execute("SELECT id, channel, title_seed, state, retries, error, created_at, updated_at FROM jobs ORDER BY id DESC LIMIT 10").fetchall()]
    channels = []
    for name in list_profiles():
        profile = load_profile(name)
        channels.append(profile.to_dict())
    return {
        "job_counts": job_counts,
        "total_jobs": total_jobs,
        "channels_count": len(channels),
        "channels": channels,
        "recent_jobs": recent,
        "db_path": str(settings.db_path),
        "output_root": str(settings.output_root),
        "cache_root": str(settings.cache_root),
    }


def list_jobs(state: str | None = None, channel: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    query = "SELECT id, channel, title_seed, state, retries, priority, next_attempt_at, error, created_at, updated_at, result_json FROM jobs WHERE 1=1"
    params: list[Any] = []
    if state:
        query += " AND state=?"
        params.append(state)
    if channel:
        query += " AND channel=?"
        params.append(channel)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        if item.get("result_json"):
            try:
                item["result"] = json.loads(item["result_json"])
            except Exception:
                item["result"] = None
        out.append(item)
    return out


def scan_content_library(limit: int = 100) -> list[dict[str, Any]]:
    items = []
    if not settings.output_root.exists():
        return items
    for channel_dir in sorted(settings.output_root.glob("*")):
        if not channel_dir.is_dir():
            continue
        for job_dir in sorted(channel_dir.glob("*"), reverse=True):
            if not job_dir.is_dir():
                continue
            script_json = job_dir / "script.json"
            upload_json = job_dir / "upload.json"
            item = {
                "channel": channel_dir.name,
                "job_dir": str(job_dir),
                "title": job_dir.name,
                "thumbnail": str(job_dir / "thumbnail.jpg"),
                "video": str(job_dir / "final.mp4"),
            }
            if script_json.exists():
                try:
                    script = json.loads(script_json.read_text(encoding="utf-8"))
                    item["title"] = script.get("title") or item["title"]
                    item["description"] = script.get("description", "")
                    item["tags"] = script.get("tags", [])
                except Exception:
                    pass
            if upload_json.exists():
                try:
                    item["upload"] = json.loads(upload_json.read_text(encoding="utf-8"))
                except Exception:
                    item["upload"] = None
            items.append(item)
            if len(items) >= limit:
                return items
    return items
