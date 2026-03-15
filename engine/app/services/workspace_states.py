"""Workspace State Machine — formal lifecycle states and validated transitions.

States: new → initialized → launching → opened → login_required → verifying
        → verified → upload_ready → degraded → stopped → archived → failed

Every transition is validated and logged to workspace_health_events.
"""

from __future__ import annotations

import logging
from enum import Enum

from ..db import get_conn
from ..utils import utc_now_iso

logger = logging.getLogger(__name__)


class WorkspaceState(str, Enum):
    """Valid workspace lifecycle states."""
    NEW = "new"
    INITIALIZED = "initialized"
    LAUNCHING = "launching"
    OPENED = "opened"
    LOGIN_REQUIRED = "login_required"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    UPLOAD_READY = "upload_ready"
    DEGRADED = "degraded"
    STOPPED = "stopped"
    ARCHIVED = "archived"
    FAILED = "failed"


# Explicit valid transitions: from_state → set of allowed to_states
VALID_TRANSITIONS: dict[WorkspaceState, set[WorkspaceState]] = {
    WorkspaceState.NEW: {WorkspaceState.INITIALIZED, WorkspaceState.ARCHIVED},
    WorkspaceState.INITIALIZED: {WorkspaceState.LAUNCHING, WorkspaceState.ARCHIVED},
    WorkspaceState.LAUNCHING: {WorkspaceState.OPENED, WorkspaceState.FAILED, WorkspaceState.STOPPED},
    WorkspaceState.OPENED: {
        WorkspaceState.LOGIN_REQUIRED, WorkspaceState.VERIFYING,
        WorkspaceState.DEGRADED, WorkspaceState.STOPPED, WorkspaceState.FAILED,
    },
    WorkspaceState.LOGIN_REQUIRED: {
        WorkspaceState.VERIFYING, WorkspaceState.STOPPED, WorkspaceState.FAILED,
    },
    WorkspaceState.VERIFYING: {
        WorkspaceState.VERIFIED, WorkspaceState.LOGIN_REQUIRED,
        WorkspaceState.DEGRADED, WorkspaceState.FAILED, WorkspaceState.STOPPED,
    },
    WorkspaceState.VERIFIED: {
        WorkspaceState.UPLOAD_READY, WorkspaceState.DEGRADED,
        WorkspaceState.STOPPED, WorkspaceState.VERIFYING,
    },
    WorkspaceState.UPLOAD_READY: {
        WorkspaceState.DEGRADED, WorkspaceState.STOPPED,
        WorkspaceState.VERIFYING,
    },
    WorkspaceState.DEGRADED: {
        WorkspaceState.LAUNCHING, WorkspaceState.STOPPED, WorkspaceState.FAILED,
    },
    WorkspaceState.STOPPED: {
        WorkspaceState.LAUNCHING, WorkspaceState.ARCHIVED, WorkspaceState.INITIALIZED,
    },
    WorkspaceState.ARCHIVED: {WorkspaceState.INITIALIZED, WorkspaceState.STOPPED},
    WorkspaceState.FAILED: {WorkspaceState.LAUNCHING, WorkspaceState.STOPPED, WorkspaceState.ARCHIVED},
}


def can_transition(from_state: str, to_state: str) -> bool:
    """Check if a state transition is valid."""
    try:
        fr = WorkspaceState(from_state)
        to = WorkspaceState(to_state)
        return to in VALID_TRANSITIONS.get(fr, set())
    except ValueError:
        return False


def transition(workspace_id: int, from_state: str, to_state: str,
               reason: str = "", force: bool = False) -> dict:
    """Perform a validated state transition for a workspace.

    Args:
        workspace_id: Target workspace
        from_state: Expected current state
        to_state: Desired new state
        reason: Human-readable reason
        force: If True, skip validation (for reconciliation)

    Returns:
        dict with ok, from_state, to_state, message
    """
    try:
        to_enum = WorkspaceState(to_state)
    except ValueError:
        return {"ok": False, "message": f"Invalid target state: {to_state}"}

    if not force and not can_transition(from_state, to_state):
        logger.warning("Invalid transition %s → %s for workspace #%d", from_state, to_state, workspace_id)
        return {
            "ok": False,
            "from_state": from_state,
            "to_state": to_state,
            "message": f"Transition {from_state} → {to_state} is not allowed",
        }

    now = utc_now_iso()
    conn = get_conn()

    # Update runtime state table
    existing = conn.execute(
        "SELECT workspace_id FROM workspace_runtime_state WHERE workspace_id=?",
        (workspace_id,)
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE workspace_runtime_state SET runtime_status=?, updated_at=? WHERE workspace_id=?",
            (to_state, now, workspace_id),
        )
    else:
        conn.execute(
            "INSERT INTO workspace_runtime_state (workspace_id, runtime_status, updated_at) VALUES (?, ?, ?)",
            (workspace_id, to_state, now),
        )

    # Update workspaces table session_status
    session_map = {
        "opened": "active", "verified": "active", "upload_ready": "active",
        "launching": "active", "verifying": "active",
        "stopped": "inactive", "archived": "archived",
        "failed": "inactive", "degraded": "active",
    }
    session_status = session_map.get(to_state, "inactive")
    conn.execute(
        "UPDATE workspaces SET session_status=?, updated_at=? WHERE id=?",
        (session_status, now, workspace_id),
    )

    # Log transition event
    try:
        conn.execute(
            "INSERT INTO workspace_health_events (workspace_id, event_type, severity, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (workspace_id, "state_transition", "info",
             f"{from_state} → {to_state}" + (f" ({reason})" if reason else ""), now),
        )
    except Exception:
        pass

    conn.commit()

    logger.info("Workspace #%d: %s → %s%s", workspace_id, from_state, to_state,
                f" ({reason})" if reason else "")

    return {
        "ok": True,
        "from_state": from_state,
        "to_state": to_state,
        "message": f"Transitioned to {to_state}",
    }


def get_current_state(workspace_id: int) -> str:
    """Get current runtime state of a workspace."""
    conn = get_conn()
    row = conn.execute(
        "SELECT runtime_status FROM workspace_runtime_state WHERE workspace_id=?",
        (workspace_id,)
    ).fetchone()
    return row["runtime_status"] if row else WorkspaceState.NEW.value
