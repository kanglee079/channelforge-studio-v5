"""V5 DB helpers — CRUD + query functions for V5 entities.

Separated from main db.py to keep modules clean.
"""

from __future__ import annotations

import json
from typing import Any

from .db import get_conn
from .utils import utc_now_iso


# ═══════════════════════════════════════════════════════════
# Review Items
# ═══════════════════════════════════════════════════════════

def create_review_item(
    review_type: str, object_type: str = "", object_id: int = 0,
    channel_name: str = "", priority: int = 100,
    reason_code: str = "", reason_text: str = "",
    score: float = 0.0, payload: dict | None = None,
) -> int:
    now = utc_now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO review_items
               (review_type, object_type, object_id, channel_name, priority,
                reason_code, reason_text, score, payload_json, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)""",
            (review_type, object_type, object_id, channel_name, priority,
             reason_code, reason_text, score, json.dumps(payload or {}), now),
        )
        return int(cur.lastrowid)


def list_review_items(status: str = "open", channel: str | None = None, limit: int = 50) -> list[dict]:
    q = "SELECT * FROM review_items WHERE status=?"
    params: list[Any] = [status]
    if channel:
        q += " AND channel_name=?"
        params.append(channel)
    q += " ORDER BY priority ASC, created_at DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(q, params).fetchall()]


def resolve_review_item(item_id: int, status: str = "approved", resolved_by: str = "user") -> None:
    now = utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            "UPDATE review_items SET status=?, resolved_by=?, resolved_at=? WHERE id=?",
            (status, resolved_by, now, item_id),
        )


# ═══════════════════════════════════════════════════════════
# Provider Usage
# ═══════════════════════════════════════════════════════════

def log_provider_usage(
    provider: str, model: str = "", task_type: str = "",
    channel_name: str = "", job_id: int = 0,
    tokens: int = 0, duration_sec: float = 0.0,
    cost_estimate: float = 0.0, cache_hit: bool = False,
) -> int:
    now = utc_now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO provider_usage_events
               (provider, model, task_type, channel_name, job_id,
                token_count, duration_sec, cost_estimate, cache_hit, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (provider, model, task_type, channel_name, job_id,
             tokens, duration_sec, cost_estimate, int(cache_hit), now),
        )
        return int(cur.lastrowid)


def get_cost_summary(channel: str | None = None, days: int = 30) -> dict:
    with get_conn() as conn:
        if channel:
            rows = conn.execute(
                """SELECT provider, task_type,
                          COUNT(*) as requests,
                          SUM(token_count) as total_tokens,
                          SUM(cost_estimate) as total_cost,
                          SUM(CASE WHEN cache_hit=1 THEN 1 ELSE 0 END) as cache_hits
                   FROM provider_usage_events
                   WHERE channel_name=? AND created_at >= date('now', ?)
                   GROUP BY provider, task_type""",
                (channel, f"-{days} days"),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT provider, task_type,
                          COUNT(*) as requests,
                          SUM(token_count) as total_tokens,
                          SUM(cost_estimate) as total_cost,
                          SUM(CASE WHEN cache_hit=1 THEN 1 ELSE 0 END) as cache_hits
                   FROM provider_usage_events
                   WHERE created_at >= date('now', ?)
                   GROUP BY provider, task_type""",
                (f"-{days} days",),
            ).fetchall()
        return {"breakdown": [dict(r) for r in rows]}


# ═══════════════════════════════════════════════════════════
# Analytics Daily
# ═══════════════════════════════════════════════════════════

def upsert_analytics_daily(channel_name: str, day: str, **kwargs) -> None:
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM analytics_daily WHERE channel_name=? AND day=?",
            (channel_name, day),
        ).fetchone()
        if existing:
            sets = ", ".join(f"{k}={k}+?" for k in kwargs)
            conn.execute(
                f"UPDATE analytics_daily SET {sets} WHERE channel_name=? AND day=?",
                (*kwargs.values(), channel_name, day),
            )
        else:
            cols = "channel_name, day, " + ", ".join(kwargs.keys())
            placeholders = "?, ?, " + ", ".join("?" for _ in kwargs)
            conn.execute(
                f"INSERT INTO analytics_daily ({cols}) VALUES ({placeholders})",
                (channel_name, day, *kwargs.values()),
            )


def get_analytics_summary(channel: str | None = None, days: int = 30) -> list[dict]:
    with get_conn() as conn:
        if channel:
            rows = conn.execute(
                "SELECT * FROM analytics_daily WHERE channel_name=? AND day >= date('now', ?) ORDER BY day DESC",
                (channel, f"-{days} days"),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM analytics_daily WHERE day >= date('now', ?) ORDER BY day DESC",
                (f"-{days} days",),
            ).fetchall()
        return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════
# Budget Profiles
# ═══════════════════════════════════════════════════════════

def create_budget_profile(name: str, monthly_limit: float = 100.0, quality_mode: str = "budget", rules: dict | None = None) -> int:
    now = utc_now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO budget_profiles (name, monthly_limit, preferred_quality_mode, rules_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (name, monthly_limit, quality_mode, json.dumps(rules or {}), now, now),
        )
        return int(cur.lastrowid)


def list_budget_profiles() -> list[dict]:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM budget_profiles ORDER BY name").fetchall()]


# ═══════════════════════════════════════════════════════════
# Watchlists
# ═══════════════════════════════════════════════════════════

def create_watchlist(channel_name: str, name: str, watch_type: str, query: str) -> int:
    now = utc_now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO watchlists (channel_name, name, watch_type, query, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (channel_name, name, watch_type, query, now, now),
        )
        return int(cur.lastrowid)


def list_watchlists(channel: str | None = None) -> list[dict]:
    with get_conn() as conn:
        if channel:
            rows = conn.execute("SELECT * FROM watchlists WHERE channel_name=? AND active=1 ORDER BY name", (channel,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM watchlists WHERE active=1 ORDER BY channel_name, name").fetchall()
        return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════
# Proxy Profiles
# ═══════════════════════════════════════════════════════════

def create_proxy_profile(name: str, server: str, port: int, protocol: str = "http", username: str = "", password: str = "", notes: str = "") -> int:
    now = utc_now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO proxy_profiles (name, protocol, server, port, username, password_encrypted, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (name, protocol, server, port, username, password, notes, now, now),
        )
        return int(cur.lastrowid)


def list_proxy_profiles() -> list[dict]:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM proxy_profiles ORDER BY name").fetchall()]


# ═══════════════════════════════════════════════════════════
# Trend Items
# ═══════════════════════════════════════════════════════════

def insert_trend_item(source_type: str, title: str, snippet: str = "", url: str = "", region: str = "", raw_json: dict | None = None, normalized_hash: str = "") -> int:
    now = utc_now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO trend_items
               (source_type, title, snippet, url, region, fetched_at, raw_json, normalized_hash, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new')""",
            (source_type, title, snippet, url, region, now, json.dumps(raw_json or {}), normalized_hash),
        )
        return int(cur.lastrowid)


def list_trend_items(source_type: str | None = None, limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        if source_type:
            rows = conn.execute("SELECT * FROM trend_items WHERE source_type=? ORDER BY fetched_at DESC LIMIT ?", (source_type, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM trend_items ORDER BY fetched_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
