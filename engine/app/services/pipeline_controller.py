"""Pipeline Controller — End-to-end orchestration for content production.

Sequences: idea → research → script → media_match → voice → subtitle → render → qc → review → publish_queue.
Respects review gates, workspace state, network policy, and channel automation policy.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from typing import Any

from ..db import get_conn
from ..utils import utc_now_iso

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Pipeline stages (ordered)
# ═══════════════════════════════════════════════════════════

PIPELINE_STAGES = [
    "idea_pending",
    "research_pending",
    "script_pending",
    "media_match_pending",
    "voice_pending",
    "subtitle_pending",
    "render_pending",
    "qc_pending",
    "review_pending",
    "publish_queue_pending",
    "ready_to_publish",
    "published",
]

TERMINAL_STATES = {"published", "failed", "cancelled"}
PAUSABLE_STATES = {"paused"}


def next_stage(current: str) -> str | None:
    """Return the next stage in the pipeline, or None if terminal."""
    try:
        idx = PIPELINE_STAGES.index(current)
        return PIPELINE_STAGES[idx + 1] if idx + 1 < len(PIPELINE_STAGES) else None
    except ValueError:
        return None


# ═══════════════════════════════════════════════════════════
# Pipeline Controller
# ═══════════════════════════════════════════════════════════

class PipelineController:
    """Orchestrates content production pipeline for workspaces."""

    # ── Job creation ──────────────────────

    def create_job(self, workspace_id: int, channel_name: str = "",
                   idea_id: int = 0, priority: int = 50) -> dict:
        """Create a new pipeline job."""
        conn = get_conn()
        now = utc_now_iso()

        # Check automation policy
        policy = self.get_policy(workspace_id)

        # Check daily limit
        if policy:
            today_count = self._count_today_jobs(workspace_id)
            max_daily = policy.get("max_daily_videos", 3)
            if today_count >= max_daily:
                return {"ok": False, "message": f"Daily limit reached ({today_count}/{max_daily})"}

        history = [{"stage": "idea_pending", "at": now, "from": "created"}]
        cur = conn.execute(
            """INSERT INTO pipeline_jobs
               (workspace_id, channel_name, idea_id, stage, status, stage_history_json,
                current_stage_started_at, priority, created_at, updated_at)
               VALUES (?, ?, ?, 'idea_pending', 'queued', ?, ?, ?, ?, ?)""",
            (workspace_id, channel_name, idea_id, json.dumps(history), now, priority, now, now),
        )
        conn.commit()
        job_id = cur.lastrowid
        logger.info("Created pipeline job #%d for workspace #%d", job_id, workspace_id)
        return {"ok": True, "job_id": job_id, "stage": "idea_pending"}

    # ── Stage advancement ─────────────────

    def advance_stage(self, job_id: int, force_next: str = "") -> dict:
        """Advance a job to its next pipeline stage.

        Checks review gates before advancing.
        Returns ok + new stage, or stops at checkpoint with reason.
        """
        conn = get_conn()
        job = conn.execute("SELECT * FROM pipeline_jobs WHERE id=?", (job_id,)).fetchone()
        if not job:
            return {"ok": False, "message": "Job not found"}

        job = dict(job)
        current = job["stage"]
        status = job["status"]

        if current in TERMINAL_STATES:
            return {"ok": False, "message": f"Job already in terminal state: {current}"}
        if status == "paused":
            return {"ok": False, "message": "Job is paused — resume first"}

        target = force_next or next_stage(current)
        if not target:
            return {"ok": False, "message": f"No next stage from '{current}'"}

        # ── Review gates ──────────────────
        gate = self._check_review_gate(job, current, target)
        if gate["blocked"]:
            self._update_job(job_id, status="review", last_error=gate["reason"])
            return {"ok": False, "blocked": True, "reason": gate["reason"], "stage": current}

        # ── Advance ──────────────────────
        now = utc_now_iso()
        history = json.loads(job.get("stage_history_json", "[]"))
        history.append({"stage": target, "at": now, "from": current})

        conn.execute(
            """UPDATE pipeline_jobs
               SET stage=?, status='queued', stage_history_json=?,
                   current_stage_started_at=?, updated_at=?
               WHERE id=?""",
            (target, json.dumps(history), now, now, job_id),
        )
        conn.commit()

        logger.info("Job #%d: %s → %s", job_id, current, target)
        return {"ok": True, "job_id": job_id, "from_stage": current, "to_stage": target}

    # ── Failure / retry ──────────────────

    def fail_job(self, job_id: int, error: str, stage: str = "") -> dict:
        """Mark a job as failed at its current stage."""
        conn = get_conn()
        job = conn.execute("SELECT * FROM pipeline_jobs WHERE id=?", (job_id,)).fetchone()
        if not job:
            return {"ok": False, "message": "Job not found"}

        job = dict(job)
        retry_count = job["retry_count"] + 1
        max_retries = job["max_retries"]

        if retry_count < max_retries:
            # Retry: keep same stage, increment counter
            self._update_job(job_id, status="queued", retry_count=retry_count,
                            last_error=error[:500], last_error_stage=stage or job["stage"])
            return {"ok": True, "action": "retry", "retry_count": retry_count, "max_retries": max_retries}
        else:
            # Permanent failure
            self._update_job(job_id, status="failed", stage="failed",
                            retry_count=retry_count, last_error=error[:500],
                            last_error_stage=stage or job["stage"])
            return {"ok": True, "action": "failed_permanent", "retry_count": retry_count}

    # ── Pause / resume ───────────────────

    def pause_job(self, job_id: int) -> dict:
        self._update_job(job_id, status="paused")
        return {"ok": True, "message": "Job paused"}

    def resume_job(self, job_id: int) -> dict:
        self._update_job(job_id, status="queued")
        return {"ok": True, "message": "Job resumed"}

    # ── Query ────────────────────────────

    def list_jobs(self, workspace_id: int = 0, status: str = "", limit: int = 50) -> list[dict]:
        conn = get_conn()
        query = "SELECT * FROM pipeline_jobs WHERE 1=1"
        params: list = []
        if workspace_id > 0:
            query += " AND workspace_id=?"
            params.append(workspace_id)
        if status:
            query += " AND status=?"
            params.append(status)
        query += " ORDER BY priority ASC, created_at DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in conn.execute(query, params).fetchall()]

    def get_job(self, job_id: int) -> dict | None:
        conn = get_conn()
        row = conn.execute("SELECT * FROM pipeline_jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None

    def get_queue_summary(self) -> dict:
        """Get summary of queue state across all workspaces."""
        conn = get_conn()
        rows = conn.execute(
            "SELECT stage, status, COUNT(*) as count FROM pipeline_jobs GROUP BY stage, status"
        ).fetchall()
        return {
            "breakdown": [dict(r) for r in rows],
            "total_queued": sum(1 for r in rows if dict(r)["status"] == "queued"),
            "total_running": sum(1 for r in rows if dict(r)["status"] == "running"),
            "total_review": sum(1 for r in rows if dict(r)["status"] == "review"),
            "total_failed": sum(1 for r in rows if dict(r)["status"] == "failed"),
        }

    # ── Channel automation policy ─────────

    def get_policy(self, workspace_id: int) -> dict | None:
        conn = get_conn()
        row = conn.execute(
            "SELECT * FROM channel_automation_policy WHERE workspace_id=?", (workspace_id,)
        ).fetchone()
        return dict(row) if row else None

    def upsert_policy(self, workspace_id: int, **kwargs) -> dict:
        conn = get_conn()
        now = utc_now_iso()
        existing = conn.execute(
            "SELECT id FROM channel_automation_policy WHERE workspace_id=?", (workspace_id,)
        ).fetchone()

        if existing:
            sets = ", ".join(f"{k}=?" for k in kwargs)
            vals = list(kwargs.values()) + [now, workspace_id]
            conn.execute(
                f"UPDATE channel_automation_policy SET {sets}, updated_at=? WHERE workspace_id=?", vals
            )
        else:
            kwargs["workspace_id"] = workspace_id
            kwargs["created_at"] = now
            kwargs["updated_at"] = now
            cols = ", ".join(kwargs.keys())
            placeholders = ", ".join("?" for _ in kwargs)
            conn.execute(
                f"INSERT INTO channel_automation_policy ({cols}) VALUES ({placeholders})",
                list(kwargs.values()),
            )
        conn.commit()
        return {"ok": True, "message": "Policy updated"}

    # ── Cost tracking ────────────────────

    def add_cost(self, job_id: int, provider: str, amount_usd: float, description: str = "") -> None:
        conn = get_conn()
        job = conn.execute("SELECT estimated_cost_usd, provider_usage_json FROM pipeline_jobs WHERE id=?", (job_id,)).fetchone()
        if not job:
            return

        current_cost = (job["estimated_cost_usd"] or 0) + amount_usd
        usage = json.loads(job["provider_usage_json"] or "{}")
        if provider not in usage:
            usage[provider] = {"count": 0, "total_usd": 0}
        usage[provider]["count"] += 1
        usage[provider]["total_usd"] = round(usage[provider]["total_usd"] + amount_usd, 4)

        conn.execute(
            "UPDATE pipeline_jobs SET estimated_cost_usd=?, provider_usage_json=?, updated_at=? WHERE id=?",
            (round(current_cost, 4), json.dumps(usage), utc_now_iso(), job_id),
        )
        conn.commit()

    # ── Internal ─────────────────────────

    def _check_review_gate(self, job: dict, current: str, target: str) -> dict:
        """Check review gates before allowing stage advancement."""
        # Gate 1: media match → voice requires review check
        if current == "media_match_pending" and target == "voice_pending":
            if job.get("match_run_id"):
                conn = get_conn()
                run = conn.execute(
                    "SELECT review_scenes FROM scene_match_runs WHERE id=?", (job["match_run_id"],)
                ).fetchone()
                if run and run["review_scenes"] > 0:
                    return {"blocked": True, "reason": f"Media match has {run['review_scenes']} scenes requiring review"}

        # Gate 2: publish requires workspace verification
        if target in ("ready_to_publish", "published"):
            ws_id = job.get("workspace_id", 0)
            if ws_id > 0:
                conn = get_conn()
                rt = conn.execute(
                    "SELECT runtime_status FROM workspace_runtime_state WHERE workspace_id=?", (ws_id,)
                ).fetchone()
                if not rt or rt["runtime_status"] not in ("verified", "upload_ready"):
                    return {"blocked": True, "reason": "Workspace not verified for publishing"}

        # Gate 3: publish requires auto_publish policy or manual approval
        if target == "published":
            policy = self.get_policy(job.get("workspace_id", 0))
            if policy and not policy.get("auto_publish"):
                return {"blocked": True, "reason": "Auto-publish disabled — manual approval required"}

        return {"blocked": False, "reason": ""}

    def _update_job(self, job_id: int, **kwargs):
        conn = get_conn()
        kwargs["updated_at"] = utc_now_iso()
        sets = ", ".join(f"{k}=?" for k in kwargs)
        conn.execute(f"UPDATE pipeline_jobs SET {sets} WHERE id=?", list(kwargs.values()) + [job_id])
        conn.commit()

    def _count_today_jobs(self, workspace_id: int) -> int:
        conn = get_conn()
        from datetime import date
        today = date.today().isoformat()
        row = conn.execute(
            "SELECT COUNT(*) as c FROM pipeline_jobs WHERE workspace_id=? AND created_at >= ?",
            (workspace_id, today),
        ).fetchone()
        return row["c"] if row else 0


# Module-level singleton
controller = PipelineController()
