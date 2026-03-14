"""Workspace management routers V5 — Full lifecycle + proxy + health."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..db import get_conn
from ..db_v5 import create_proxy_profile, list_proxy_profiles
from ..services.workspace_manager import WorkspaceService
from ..utils import utc_now_iso

router = APIRouter(prefix="/api/v2/workspaces", tags=["workspaces"])

ws_service = WorkspaceService()


# ═══════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════

class CreateWorkspaceRequest(BaseModel):
    name: str
    channel_name: str | None = None
    proxy_config: str = ""
    proxy_profile_id: int | None = None
    locale: str = "en-US"
    timezone: str = ""
    notes: str = ""


class ProxyProfileRequest(BaseModel):
    name: str
    server: str
    port: int
    protocol: str = "http"
    username: str = ""
    password: str = ""
    notes: str = ""


# ═══════════════════════════════════════════════════════════
# Workspace CRUD
# ═══════════════════════════════════════════════════════════

@router.get("")
def list_workspaces():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM workspaces ORDER BY created_at DESC").fetchall()
    items = []
    for r in rows:
        item = dict(r)
        # Enrich with health info
        storage = Path(item.get("storage_path", ""))
        item["health"] = {
            "storage_exists": storage.exists(),
            "has_profile": (storage / "Default").exists() if storage.exists() else False,
            "has_downloads": (storage / "downloads").exists() if storage.exists() else False,
        }
        items.append(item)
    return {"items": items}


@router.post("")
def create_workspace(req: CreateWorkspaceRequest):
    conn = get_conn()
    now = utc_now_iso()
    storage = ws_service.create_workspace_dir(req.name)

    # Create sub-directories per V5.2 spec
    for subdir in ["downloads", "screenshots", "storage", "logs", "temp"]:
        (storage / subdir).mkdir(exist_ok=True)

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

    # Log health event
    _log_health_event(conn, req.name, "workspace_created", "info", f"Workspace created for channel {req.channel_name}")

    return {"ok": True, "message": f"Workspace '{req.name}' created", "storage_path": str(storage)}


@router.get("/{ws_id}")
def get_workspace(ws_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Workspace not found")
    item = dict(row)
    storage = Path(item.get("storage_path", ""))
    item["health"] = ws_service.check_health(item.get("storage_path", ""))
    item["disk_info"] = _disk_info(storage) if storage.exists() else {}

    # Get recent health events
    events = conn.execute(
        "SELECT * FROM workspace_health_events WHERE workspace_id=? ORDER BY created_at DESC LIMIT 10",
        (ws_id,),
    ).fetchall()
    item["health_events"] = [dict(e) for e in events]
    return item


@router.delete("/{ws_id}")
def delete_workspace(ws_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Workspace not found")
    conn.execute("DELETE FROM workspaces WHERE id = ?", (ws_id,))
    conn.commit()
    return {"ok": True, "message": f"Workspace '{row['name']}' deleted (storage preserved)"}


# ═══════════════════════════════════════════════════════════
# Browser Launch
# ═══════════════════════════════════════════════════════════

@router.post("/{ws_id}/launch")
async def launch_workspace(ws_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Workspace not found")

    proxy = row.get("proxy_config") or ""

    try:
        await ws_service.launch_browser(row["storage_path"], proxy or None)
        now = utc_now_iso()
        conn.execute("UPDATE workspaces SET session_status = 'active', last_login_at = ?, updated_at = ? WHERE id = ?", (now, now, ws_id))
        conn.commit()
        _log_health_event(conn, ws_id, "browser_launched", "info", f"Browser launched for '{row['name']}'")
        return {"ok": True, "message": f"Browser launched for '{row['name']}'"}
    except Exception as e:
        _log_health_event(conn, ws_id, "browser_launch_failed", "error", str(e))
        return {"ok": False, "message": f"Launch failed: {e}"}


# ═══════════════════════════════════════════════════════════
# Health Check (3 levels per V5.2)
# ═══════════════════════════════════════════════════════════

@router.get("/{ws_id}/status")
def check_status(ws_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Workspace not found")
    storage = Path(row["storage_path"])
    basic_health = ws_service.check_health(row["storage_path"])
    return {
        "id": ws_id,
        "name": row["name"],
        "session_status": row["session_status"],
        **basic_health,
        "last_login_at": row["last_login_at"],
        "last_verified_at": row["last_verified_at"],
    }


@router.post("/{ws_id}/healthcheck")
def run_healthcheck(ws_id: int):
    """Run comprehensive health check (3 levels)."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Workspace not found")

    storage = Path(row["storage_path"])
    results: dict = {"workspace_id": ws_id, "name": row["name"], "checks": []}

    # Level 1: File system
    checks_l1 = [
        ("profile_dir_exists", storage.exists()),
        ("downloads_dir_exists", (storage / "downloads").exists()),
        ("disk_writable", _is_writable(storage)),
    ]
    for name, passed in checks_l1:
        results["checks"].append({"level": 1, "name": name, "passed": passed})

    # Level 2: Session state
    has_cookies = (storage / "Default" / "Cookies").exists() if storage.exists() else False
    has_local_storage = (storage / "Default" / "Local Storage").exists() if storage.exists() else False
    checks_l2 = [
        ("has_cookies", has_cookies),
        ("has_local_storage", has_local_storage),
    ]
    for name, passed in checks_l2:
        results["checks"].append({"level": 2, "name": name, "passed": passed})

    # Level 3: Proxy check (if configured)
    proxy = row.get("proxy_config", "")
    if proxy:
        proxy_ok = _test_proxy(proxy)
        results["checks"].append({"level": 3, "name": "proxy_reachable", "passed": proxy_ok})

    # Determine overall status
    all_passed = all(c["passed"] for c in results["checks"])
    some_failed = any(not c["passed"] for c in results["checks"])
    severity = "info" if all_passed else ("warning" if sum(not c["passed"] for c in results["checks"]) <= 1 else "error")

    results["overall"] = "healthy" if all_passed else ("degraded" if severity == "warning" else "unhealthy")

    # Update workspace status
    now = utc_now_iso()
    new_status = "active" if all_passed else "degraded"
    conn.execute("UPDATE workspaces SET session_status=?, last_verified_at=?, updated_at=? WHERE id=?", (new_status, now, now, ws_id))
    conn.commit()

    _log_health_event(conn, ws_id, "healthcheck_" + results["overall"], severity, f"{len(results['checks'])} checks, {sum(c['passed'] for c in results['checks'])} passed")

    return results


# ═══════════════════════════════════════════════════════════
# Archive / Restore
# ═══════════════════════════════════════════════════════════

@router.post("/{ws_id}/archive")
def archive_workspace(ws_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Workspace not found")
    now = utc_now_iso()
    conn.execute("UPDATE workspaces SET session_status='archived', updated_at=? WHERE id=?", (now, ws_id))
    conn.commit()
    _log_health_event(conn, ws_id, "workspace_archived", "info", "Workspace archived by user")
    return {"ok": True, "message": f"Workspace '{row['name']}' archived"}


@router.post("/{ws_id}/restore")
def restore_workspace(ws_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Workspace not found")
    now = utc_now_iso()
    conn.execute("UPDATE workspaces SET session_status='new', updated_at=? WHERE id=?", (now, ws_id))
    conn.commit()
    _log_health_event(conn, ws_id, "workspace_restored", "info", "Workspace restored by user")
    return {"ok": True, "message": f"Workspace '{row['name']}' restored"}


@router.post("/{ws_id}/clear-temp")
def clear_temp(ws_id: int):
    """Clear temporary files from workspace."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Workspace not found")

    storage = Path(row["storage_path"])
    temp_dir = storage / "temp"
    cleared = 0
    if temp_dir.exists():
        import shutil
        for item in temp_dir.iterdir():
            if item.is_file():
                item.unlink()
                cleared += 1
            elif item.is_dir():
                shutil.rmtree(item)
                cleared += 1
    return {"ok": True, "message": f"Cleared {cleared} items from temp", "cleared": cleared}


# ═══════════════════════════════════════════════════════════
# Health Events Log
# ═══════════════════════════════════════════════════════════

@router.get("/{ws_id}/health-events")
def get_health_events(ws_id: int, limit: int = Query(default=50, ge=1, le=200)):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM workspace_health_events WHERE workspace_id=? ORDER BY created_at DESC LIMIT ?",
        (ws_id, limit),
    ).fetchall()
    return {"items": [dict(r) for r in rows]}


# ═══════════════════════════════════════════════════════════
# Proxy Profiles
# ═══════════════════════════════════════════════════════════

@router.get("/proxy-profiles", tags=["proxy"])
def get_proxy_profiles():
    return {"items": list_proxy_profiles()}


@router.post("/proxy-profiles", tags=["proxy"])
def add_proxy_profile(req: ProxyProfileRequest):
    pid = create_proxy_profile(
        name=req.name, server=req.server, port=req.port,
        protocol=req.protocol, username=req.username,
        password=req.password, notes=req.notes,
    )
    return {"ok": True, "id": pid, "message": f"Proxy profile '{req.name}' created"}


@router.post("/proxy-profiles/{profile_id}/test", tags=["proxy"])
def test_proxy_profile(profile_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM proxy_profiles WHERE id=?", (profile_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Proxy profile not found")

    proxy_url = f"{row['protocol']}://{row['server']}:{row['port']}"
    ok = _test_proxy(proxy_url)
    now = utc_now_iso()
    status = "active" if ok else "failed"
    conn.execute("UPDATE proxy_profiles SET last_tested_at=?, last_test_status=?, status=?, updated_at=? WHERE id=?",
                 (now, "ok" if ok else "unreachable", status, now, profile_id))
    conn.commit()
    return {"ok": ok, "message": f"Proxy {'reachable' if ok else 'unreachable'}", "status": status}


@router.post("/{ws_id}/bind-proxy")
def bind_proxy(ws_id: int, profile_id: int = 0):
    """Bind or unbind a proxy profile to a workspace."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM workspaces WHERE id=?", (ws_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Workspace not found")

    if profile_id > 0:
        proxy = conn.execute("SELECT * FROM proxy_profiles WHERE id=?", (profile_id,)).fetchone()
        if not proxy:
            raise HTTPException(404, "Proxy profile not found")
        proxy_config = f"{proxy['protocol']}://{proxy['server']}:{proxy['port']}"
        if proxy["username"]:
            proxy_config = f"{proxy['protocol']}://{proxy['username']}:{proxy['password_encrypted']}@{proxy['server']}:{proxy['port']}"
    else:
        proxy_config = ""

    now = utc_now_iso()
    conn.execute("UPDATE workspaces SET proxy_config=?, updated_at=? WHERE id=?", (proxy_config, now, ws_id))
    conn.commit()
    return {"ok": True, "message": f"Proxy {'bound' if profile_id > 0 else 'unbound'} for workspace"}


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def _log_health_event(conn, workspace_id_or_name, event_type: str, severity: str, message: str):
    now = utc_now_iso()
    ws_id = workspace_id_or_name if isinstance(workspace_id_or_name, int) else 0
    try:
        conn.execute(
            "INSERT INTO workspace_health_events (workspace_id, event_type, severity, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (ws_id, event_type, severity, message, now),
        )
        conn.commit()
    except Exception:
        pass


def _is_writable(path: Path) -> bool:
    try:
        test_file = path / ".write_test"
        test_file.write_text("ok")
        test_file.unlink()
        return True
    except Exception:
        return False


def _disk_info(path: Path) -> dict:
    try:
        import shutil
        total, used, free = shutil.disk_usage(str(path))
        size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        return {"workspace_size_mb": round(size / 1024 / 1024, 1), "disk_free_gb": round(free / 1024**3, 1)}
    except Exception:
        return {}


def _test_proxy(proxy_url: str) -> bool:
    try:
        import urllib.request
        proxy_handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
        opener = urllib.request.build_opener(proxy_handler)
        opener.open("http://httpbin.org/ip", timeout=10)
        return True
    except Exception:
        return False
