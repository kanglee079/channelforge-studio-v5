from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .config import settings
from .utils import utc_now_iso


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS profiles (
                name TEXT PRIMARY KEY,
                json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL,
                title_seed TEXT NOT NULL,
                state TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                result_json TEXT,
                retries INTEGER NOT NULL DEFAULT 0,
                priority INTEGER NOT NULL DEFAULT 100,
                next_attempt_at TEXT NOT NULL,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_jobs_state_next ON jobs(state, next_attempt_at, priority, created_at);
            CREATE INDEX IF NOT EXISTS idx_jobs_channel_state ON jobs(channel, state, created_at);
            CREATE TABLE IF NOT EXISTS title_index (
                channel TEXT NOT NULL,
                normalized_title TEXT NOT NULL,
                raw_title TEXT NOT NULL,
                job_id INTEGER,
                created_at TEXT NOT NULL,
                UNIQUE(channel, normalized_title)
            );
            CREATE TABLE IF NOT EXISTS upload_log (
                day_utc TEXT NOT NULL,
                channel TEXT NOT NULL,
                count INTEGER NOT NULL,
                PRIMARY KEY(day_utc, channel)
            );
            """
        )


def save_profile_json(name: str, profile_json: dict[str, Any]) -> None:
    now = utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO profiles(name, json, updated_at) VALUES (?, ?, ?) ON CONFLICT(name) DO UPDATE SET json=excluded.json, updated_at=excluded.updated_at",
            (name, json.dumps(profile_json, ensure_ascii=False), now),
        )


def enqueue_job(channel: str, title_seed: str, payload_json: dict[str, Any], priority: int = 100) -> int:
    now = utc_now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO jobs(channel, title_seed, state, payload_json, retries, priority, next_attempt_at, created_at, updated_at) VALUES (?, ?, 'queued', ?, 0, ?, ?, ?, ?)",
            (channel, title_seed, json.dumps(payload_json, ensure_ascii=False), priority, now, now, now),
        )
        return int(cur.lastrowid)


def claim_jobs(limit: int = 1, channel: str | None = None) -> list[sqlite3.Row]:
    now = utc_now_iso()
    with get_conn() as conn:
        if channel:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE channel=? AND state IN ('queued','retry') AND next_attempt_at <= ? ORDER BY priority ASC, created_at ASC LIMIT ?",
                (channel, now, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE state IN ('queued','retry') AND next_attempt_at <= ? ORDER BY priority ASC, created_at ASC LIMIT ?",
                (now, limit),
            ).fetchall()
        ids = [row['id'] for row in rows]
        if ids:
            conn.executemany(
                "UPDATE jobs SET state='processing', updated_at=? WHERE id=?",
                [(now, _id) for _id in ids],
            )
        return rows


def mark_done(job_id: int, result_json: dict[str, Any], final_state: str = 'done') -> None:
    now = utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            "UPDATE jobs SET state=?, result_json=?, updated_at=?, error=NULL WHERE id=?",
            (final_state, json.dumps(result_json, ensure_ascii=False), now, job_id),
        )


def mark_retry(job_id: int, error: str, retries: int, next_attempt_at: str) -> None:
    now = utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            "UPDATE jobs SET state='retry', error=?, retries=?, next_attempt_at=?, updated_at=? WHERE id=?",
            (error[:4000], retries, next_attempt_at, now, job_id),
        )


def mark_failed(job_id: int, error: str, final_state: str = 'failed') -> None:
    now = utc_now_iso()
    with get_conn() as conn:
        conn.execute(
            "UPDATE jobs SET state=?, error=?, updated_at=? WHERE id=?",
            (final_state, error[:4000], now, job_id),
        )


def add_title_index(channel: str, normalized_title: str, raw_title: str, job_id: int | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO title_index(channel, normalized_title, raw_title, job_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (channel, normalized_title, raw_title, job_id, utc_now_iso()),
        )


def get_indexed_titles(channel: str) -> list[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT raw_title FROM title_index WHERE channel=? ORDER BY created_at DESC", (channel,)).fetchall()
    return [r[0] for r in rows]


def increment_upload_count(channel: str) -> None:
    day = utc_now_iso()[:10]
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO upload_log(day_utc, channel, count) VALUES (?, ?, 1) ON CONFLICT(day_utc, channel) DO UPDATE SET count=count+1",
            (day, channel),
        )


def get_upload_count_today(channel: str) -> int:
    day = utc_now_iso()[:10]
    with get_conn() as conn:
        row = conn.execute("SELECT count FROM upload_log WHERE day_utc=? AND channel=?", (day, channel)).fetchone()
    return int(row[0]) if row else 0


def stats() -> dict[str, Any]:
    with get_conn() as conn:
        rows = conn.execute("SELECT state, COUNT(*) AS c FROM jobs GROUP BY state").fetchall()
    return {row['state']: row['c'] for row in rows}
