"""Workspace Supervisor — Runtime lifecycle manager for channel workspaces.

Registry tất cả workspace runtime đang sống, quản lý open/close/relaunch/force-kill,
asyncio locks per workspace, heartbeat updates, graceful cleanup.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..db import get_conn
from ..utils import utc_now_iso

logger = logging.getLogger(__name__)


@dataclass
class RuntimeHandle:
    """In-memory handle for a running workspace browser."""
    workspace_id: int
    playwright: Any = None
    context: Any = None
    page: Any = None
    browser_pid: int = 0
    launched_at: str = ""
    last_alive_at: str = ""


class WorkspaceSupervisor:
    """Singleton supervisor managing all workspace browser runtimes."""

    def __init__(self):
        self._registry: dict[int, RuntimeHandle] = {}
        self._locks: dict[int, asyncio.Lock] = {}

    def _get_lock(self, workspace_id: int) -> asyncio.Lock:
        if workspace_id not in self._locks:
            self._locks[workspace_id] = asyncio.Lock()
        return self._locks[workspace_id]

    # ── Reconcile stale runtimes on startup ─────────────────────

    def reconcile_stale_runtimes(self):
        """Reset stale 'running/launching' states after backend restart.

        Called once on startup. Since in-memory registry is empty,
        any DB record showing 'running' or 'launching' is stale.
        """
        from .workspace_states import transition
        conn = get_conn()
        stale_states = ('running', 'launching', 'opened', 'verifying', 'closing')
        rows = conn.execute(
            f"SELECT workspace_id, runtime_status FROM workspace_runtime_state WHERE runtime_status IN ({','.join('?' for _ in stale_states)})",
            stale_states,
        ).fetchall()

        count = 0
        for row in rows:
            ws_id = row['workspace_id']
            old = row['runtime_status']
            transition(ws_id, old, 'stopped', reason='Backend restarted — reconciled stale runtime', force=True)
            count += 1

        if count > 0:
            logger.info('Reconciled %d stale workspace runtime(s) to stopped', count)
        return count

    # ── State persistence ──────────────────────────────────────

    def _save_runtime_state(self, ws_id: int, status: str, **kwargs):
        """Persist runtime state snapshot to DB."""
        now = utc_now_iso()
        conn = get_conn()

        # Check if record exists
        existing = conn.execute("SELECT workspace_id FROM workspace_runtime_state WHERE workspace_id=?", (ws_id,)).fetchone()

        fields = {"runtime_status": status, "updated_at": now}
        fields.update(kwargs)

        if existing:
            sets = ", ".join(f"{k}=?" for k in fields)
            vals = list(fields.values()) + [ws_id]
            conn.execute(f"UPDATE workspace_runtime_state SET {sets} WHERE workspace_id=?", vals)
        else:
            fields["workspace_id"] = ws_id
            cols = ", ".join(fields.keys())
            placeholders = ", ".join("?" for _ in fields)
            conn.execute(f"INSERT INTO workspace_runtime_state ({cols}) VALUES ({placeholders})", list(fields.values()))
        conn.commit()

    def _log_health_event(self, ws_id: int, event_type: str, severity: str, message: str):
        now = utc_now_iso()
        conn = get_conn()
        try:
            conn.execute(
                "INSERT INTO workspace_health_events (workspace_id, event_type, severity, message, created_at) VALUES (?, ?, ?, ?, ?)",
                (ws_id, event_type, severity, message, now),
            )
            conn.commit()
        except Exception:
            pass

    # ── Open workspace ─────────────────────────────────────────

    async def open_workspace(self, workspace_id: int) -> dict:
        """Open a workspace browser with isolated persistent context."""
        lock = self._get_lock(workspace_id)
        async with lock:
            # Check if already running
            if workspace_id in self._registry:
                handle = self._registry[workspace_id]
                if handle.context:
                    return {"ok": True, "message": "Workspace đã đang chạy", "status": "running", "pid": handle.browser_pid}

            # Get workspace info from DB
            conn = get_conn()
            row = conn.execute("SELECT * FROM workspaces WHERE id=?", (workspace_id,)).fetchone()
            if not row:
                return {"ok": False, "message": "Workspace không tồn tại"}

            from .workspace_states import transition, get_current_state
            current = get_current_state(workspace_id)
            transition(workspace_id, current, "launching", reason="Browser opening")

            try:
                from playwright.async_api import async_playwright
            except ImportError:
                self._save_runtime_state(workspace_id, "crashed", last_error_code="MISSING_PLAYWRIGHT", last_error_message="Playwright chưa cài")
                return {"ok": False, "message": "Playwright chưa cài. Chạy: pip install playwright && python -m playwright install chromium"}

            storage_path = row["storage_path"]
            proxy_config = row.get("proxy_config", "") or ""

            try:
                pw = await async_playwright().start()
                launch_opts: dict = {"headless": False, "channel": "chromium"}
                if proxy_config:
                    launch_opts["proxy"] = {"server": proxy_config}

                context = await pw.chromium.launch_persistent_context(
                    user_data_dir=storage_path,
                    accept_downloads=True,
                    viewport={"width": 1280, "height": 800},
                    **launch_opts,
                )

                page = context.pages[0] if context.pages else await context.new_page()
                now = utc_now_iso()

                # Try to get browser PID
                browser_pid = 0
                try:
                    browser_pid = context.browser.process.pid if hasattr(context, 'browser') and context.browser else 0
                except Exception:
                    pass

                handle = RuntimeHandle(
                    workspace_id=workspace_id,
                    playwright=pw,
                    context=context,
                    page=page,
                    browser_pid=browser_pid,
                    launched_at=now,
                    last_alive_at=now,
                )
                self._registry[workspace_id] = handle

                route_mode = "WORKSPACE_ROUTE" if proxy_config else "DIRECT"
                self._save_runtime_state(
                    workspace_id, "running",
                    browser_pid=browser_pid,
                    context_attached=1,
                    last_launch_at=now,
                    last_seen_alive_at=now,
                    current_route_mode=route_mode,
                )

                # Update workspace table
                conn.execute("UPDATE workspaces SET session_status='active', last_login_at=?, updated_at=? WHERE id=?", (now, now, workspace_id))
                conn.commit()

                self._log_health_event(workspace_id, "browser_launched", "info", f"Browser khởi động thành công (PID: {browser_pid})")
                return {"ok": True, "message": "Browser đã khởi động", "status": "running", "pid": browser_pid}

            except Exception as e:
                err_msg = str(e)[:500]
                self._save_runtime_state(workspace_id, "failed", last_error_code="LAUNCH_FAILED", last_error_message=err_msg)
                transition(workspace_id, "launching", "failed", reason=f"Launch failed: {err_msg}", force=True)
                return {"ok": False, "message": f"Khởi động thất bại: {err_msg}"}

    # ── Close workspace ────────────────────────────────────────

    async def close_workspace(self, workspace_id: int) -> dict:
        """Gracefully close workspace browser."""
        lock = self._get_lock(workspace_id)
        async with lock:
            handle = self._registry.get(workspace_id)
            if not handle or not handle.context:
                self._save_runtime_state(workspace_id, "stopped", context_attached=0, last_close_at=utc_now_iso())
                return {"ok": True, "message": "Workspace đã dừng (không có browser đang chạy)"}

            self._save_runtime_state(workspace_id, "closing")

            try:
                await handle.context.close()
            except Exception:
                pass
            try:
                if handle.playwright:
                    await handle.playwright.stop()
            except Exception:
                pass

            now = utc_now_iso()
            self._registry.pop(workspace_id, None)
            self._save_runtime_state(workspace_id, "stopped", context_attached=0, browser_pid=0, last_close_at=now)

            conn = get_conn()
            conn.execute("UPDATE workspaces SET session_status='inactive', updated_at=? WHERE id=?", (now, workspace_id))
            conn.commit()

            self._log_health_event(workspace_id, "workspace_closed", "info", "Browser đã đóng thành công")
            return {"ok": True, "message": "Browser đã đóng"}

    # ── Force kill ─────────────────────────────────────────────

    async def force_kill_workspace(self, workspace_id: int) -> dict:
        """Force kill a workspace browser process."""
        handle = self._registry.get(workspace_id)
        if handle and handle.browser_pid > 0:
            try:
                os.kill(handle.browser_pid, signal.SIGTERM)
            except Exception:
                pass

        # Clean up regardless
        try:
            if handle and handle.context:
                await handle.context.close()
        except Exception:
            pass
        try:
            if handle and handle.playwright:
                await handle.playwright.stop()
        except Exception:
            pass

        self._registry.pop(workspace_id, None)
        now = utc_now_iso()
        self._save_runtime_state(workspace_id, "stopped", context_attached=0, browser_pid=0, last_close_at=now)
        self._log_health_event(workspace_id, "workspace_force_killed", "warning", "Browser bị buộc dừng")
        return {"ok": True, "message": "Browser đã bị buộc dừng"}

    # ── Relaunch ───────────────────────────────────────────────

    async def relaunch_workspace(self, workspace_id: int) -> dict:
        """Close then reopen workspace browser."""
        await self.close_workspace(workspace_id)
        await asyncio.sleep(1)
        return await self.open_workspace(workspace_id)

    # ── Runtime state queries ──────────────────────────────────

    def get_runtime_state(self, workspace_id: int) -> dict:
        """Get runtime state for a workspace."""
        conn = get_conn()
        row = conn.execute("SELECT * FROM workspace_runtime_state WHERE workspace_id=?", (workspace_id,)).fetchone()
        if not row:
            return {"workspace_id": workspace_id, "runtime_status": "stopped", "in_registry": workspace_id in self._registry}

        result = dict(row)
        result["in_registry"] = workspace_id in self._registry
        return result

    def list_runtime_states(self) -> list[dict]:
        """List all workspace runtime states."""
        conn = get_conn()
        rows = conn.execute("SELECT * FROM workspace_runtime_state ORDER BY updated_at DESC").fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["in_registry"] = item["workspace_id"] in self._registry
            result.append(item)
        return result

    # ── Heartbeat ──────────────────────────────────────────────

    def update_heartbeat(self, workspace_id: int):
        """Update last_seen_alive_at for a running workspace."""
        if workspace_id in self._registry:
            now = utc_now_iso()
            self._registry[workspace_id].last_alive_at = now
            self._save_runtime_state(workspace_id, "running", last_seen_alive_at=now)

    # ── Capture artifacts ──────────────────────────────────────

    async def capture_screenshot(self, workspace_id: int) -> dict:
        """Capture a screenshot of the current workspace page."""
        handle = self._registry.get(workspace_id)
        if not handle or not handle.page:
            return {"ok": False, "message": "Workspace không có browser đang chạy"}

        conn = get_conn()
        row = conn.execute("SELECT storage_path FROM workspaces WHERE id=?", (workspace_id,)).fetchone()
        if not row:
            return {"ok": False, "message": "Workspace không tồn tại"}

        screenshots_dir = Path(row["storage_path"]) / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = screenshots_dir / f"capture_{ts}.png"

        try:
            await handle.page.screenshot(path=str(path), full_page=True)
            return {"ok": True, "path": str(path), "message": "Đã chụp screenshot"}
        except Exception as e:
            return {"ok": False, "message": f"Lỗi chụp screenshot: {e}"}

    def get_artifacts(self, workspace_id: int) -> dict:
        """List workspace artifacts (screenshots, logs)."""
        conn = get_conn()
        row = conn.execute("SELECT storage_path FROM workspaces WHERE id=?", (workspace_id,)).fetchone()
        if not row:
            return {"screenshots": [], "logs": []}

        storage = Path(row["storage_path"])
        screenshots = []
        logs = []

        ss_dir = storage / "screenshots"
        if ss_dir.exists():
            screenshots = [{"name": f.name, "path": str(f), "size": f.stat().st_size, "modified": f.stat().st_mtime}
                          for f in sorted(ss_dir.iterdir(), reverse=True) if f.is_file()][:20]

        log_dir = storage / "logs"
        if log_dir.exists():
            logs = [{"name": f.name, "path": str(f), "size": f.stat().st_size}
                   for f in sorted(log_dir.iterdir(), reverse=True) if f.is_file()][:20]

        return {"screenshots": screenshots, "logs": logs}

    # ── Shutdown cleanup ───────────────────────────────────────

    async def shutdown_all(self):
        """Gracefully close all running workspaces. Called on app shutdown."""
        ws_ids = list(self._registry.keys())
        for ws_id in ws_ids:
            try:
                await self.close_workspace(ws_id)
            except Exception as e:
                logger.warning("Error closing workspace %d on shutdown: %s", ws_id, e)
        logger.info("All workspaces cleaned up")


# Module-level singleton
supervisor = WorkspaceSupervisor()
