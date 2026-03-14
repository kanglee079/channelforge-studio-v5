"""Workspace management routers — Browser profile isolation per channel."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db import get_conn
from ..services.workspace_manager import WorkspaceService
from ..utils import utc_now_iso

router = APIRouter(prefix="/api/v2/workspaces", tags=["workspaces"])

ws_service = WorkspaceService()


class CreateWorkspaceRequest(BaseModel):
    name: str
    channel_name: str | None = None
    proxy_config: str = ""
    notes: str = ""


# ── List workspaces ───────────────────────────────────────
@router.get("")
def list_workspaces():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM workspaces ORDER BY created_at DESC").fetchall()
    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "name": r["name"],
            "channel_name": r["channel_name"],
            "storage_path": r["storage_path"],
            "session_status": r["session_status"],
            "last_login_at": r["last_login_at"],
            "last_verified_at": r["last_verified_at"],
            "proxy_config": r["proxy_config"],
            "notes": r["notes"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        })
    return {"items": items}


# ── Create workspace ──────────────────────────────────────
@router.post("")
def create_workspace(req: CreateWorkspaceRequest):
    conn = get_conn()
    now = utc_now_iso()
    storage = ws_service.create_workspace_dir(req.name)
    try:
        conn.execute(
            """INSERT INTO workspaces (name, channel_name, storage_path, session_status, proxy_config, notes, created_at, updated_at)
               VALUES (?, ?, ?, 'new', ?, ?, ?, ?)""",
            (req.name, req.channel_name, str(storage), req.proxy_config, req.notes, now, now),
        )
        conn.commit()
    except Exception as e:
        if "UNIQUE" in str(e):
            raise HTTPException(400, f"Workspace '{req.name}' already exists")
        raise
    return {"ok": True, "message": f"Workspace '{req.name}' created"}


# ── Get workspace ─────────────────────────────────────────
@router.get("/{ws_id}")
def get_workspace(ws_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Workspace not found")
    return dict(row)


# ── Launch browser ────────────────────────────────────────
@router.post("/{ws_id}/launch")
async def launch_workspace(ws_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Workspace not found")

    try:
        await ws_service.launch_browser(row["storage_path"], row.get("proxy_config"))
        now = utc_now_iso()
        conn.execute("UPDATE workspaces SET session_status = 'active', last_login_at = ?, updated_at = ? WHERE id = ?", (now, now, ws_id))
        conn.commit()
        return {"ok": True, "message": f"Browser launched for '{row['name']}'"}
    except Exception as e:
        return {"ok": False, "message": f"Launch failed: {e}"}


# ── Check status ──────────────────────────────────────────
@router.get("/{ws_id}/status")
def check_status(ws_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Workspace not found")
    storage = Path(row["storage_path"])
    return {
        "id": ws_id,
        "name": row["name"],
        "session_status": row["session_status"],
        "storage_exists": storage.exists(),
        "last_login_at": row["last_login_at"],
        "last_verified_at": row["last_verified_at"],
    }


# ── Delete workspace ─────────────────────────────────────
@router.delete("/{ws_id}")
def delete_workspace(ws_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Workspace not found")
    conn.execute("DELETE FROM workspaces WHERE id = ?", (ws_id,))
    conn.commit()
    return {"ok": True, "message": f"Workspace '{row['name']}' deleted (storage preserved)"}
