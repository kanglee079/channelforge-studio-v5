"""Workspace Verifier — YouTube Studio session verification.

Xác minh session thật sự usable, login state, upload entrypoint.
Chụp screenshot khi verify fail. Ghi vào workspace_session_checks.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from ..db import get_conn
from ..utils import utc_now_iso

logger = logging.getLogger(__name__)


class WorkspaceVerifier:
    """Verify YouTube Studio sessions for workspaces."""

    async def verify_youtube_studio(self, context, workspace_id: int) -> dict:
        """Verify that the workspace browser is logged into YouTube Studio.

        Checks:
        - page title/URL contains studio.youtube.com
        - login redirect detection
        - studio shell / upload button availability
        """
        conn = get_conn()
        ws_row = conn.execute("SELECT storage_path FROM workspaces WHERE id=?", (workspace_id,)).fetchone()
        storage_path = ws_row["storage_path"] if ws_row else ""

        result = {
            "workspace_id": workspace_id,
            "status": "unknown",
            "checks": [],
            "screenshot_path": "",
        }

        try:
            page = context.pages[0] if context.pages else await context.new_page()

            # Navigate to YouTube Studio
            await page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            current_url = page.url
            title = await page.title()

            # Check 1: URL contains studio.youtube.com
            is_studio = "studio.youtube.com" in current_url
            result["checks"].append({"name": "studio_url", "passed": is_studio, "value": current_url})

            # Check 2: Not redirected to login
            is_login_redirect = "accounts.google.com" in current_url or "signin" in current_url.lower()
            result["checks"].append({"name": "not_login_redirect", "passed": not is_login_redirect, "value": "" if not is_login_redirect else "Login redirect detected"})

            # Check 3: Studio dashboard loaded (look for channel content area)
            has_dashboard = False
            try:
                # Look for common Studio elements
                dashboard_selectors = [
                    "ytcp-entity-page-header",  # Channel header
                    "#create-icon",  # Create/Upload button
                    "ytcp-uploads-dialog",
                    ".dashboard-header",
                ]
                for sel in dashboard_selectors:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            has_dashboard = True
                            break
                    except Exception:
                        continue
            except Exception:
                pass
            result["checks"].append({"name": "studio_dashboard", "passed": has_dashboard or is_studio, "value": ""})

            # Check 4: Upload button reachable
            upload_reachable = False
            try:
                upload_btn = await page.query_selector("#create-icon, #upload-icon, button[aria-label*='Upload'], button[aria-label*='Tải lên']")
                upload_reachable = upload_btn is not None
            except Exception:
                pass
            result["checks"].append({"name": "upload_reachable", "passed": upload_reachable, "value": ""})

            # Determine overall status
            all_passed = all(c["passed"] for c in result["checks"])
            if is_login_redirect:
                result["status"] = "login_required"
            elif all_passed:
                result["status"] = "upload_ready"
            elif is_studio:
                result["status"] = "degraded"
            else:
                result["status"] = "blocked"

        except Exception as e:
            result["status"] = "error"
            result["checks"].append({"name": "page_load", "passed": False, "value": str(e)[:300]})

        # Screenshot on failure
        if result["status"] not in ("upload_ready",):
            ss_path = await self.capture_failure_artifacts(context, workspace_id, storage_path)
            result["screenshot_path"] = ss_path

        # Save to workspace_session_checks
        self._save_check(workspace_id, result)

        # Update workspace runtime state
        if result["status"] in ("upload_ready", "login_required", "degraded", "blocked"):
            conn = get_conn()
            now = utc_now_iso()
            try:
                conn.execute(
                    "UPDATE workspace_runtime_state SET runtime_status=?, updated_at=? WHERE workspace_id=?",
                    (result["status"], now, workspace_id),
                )
                conn.execute(
                    "UPDATE workspaces SET session_status=?, last_verified_at=?, updated_at=? WHERE id=?",
                    (result["status"], now, now, workspace_id),
                )
                conn.commit()
            except Exception:
                pass

        return result

    async def capture_failure_artifacts(self, context, workspace_id: int, storage_path: str = "") -> str:
        """Capture screenshot when verification fails."""
        if not storage_path:
            return ""

        screenshots_dir = Path(storage_path) / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = screenshots_dir / f"verify_fail_{ts}.png"

        try:
            page = context.pages[0] if context.pages else None
            if page:
                await page.screenshot(path=str(path))
                return str(path)
        except Exception as e:
            logger.warning("Failed to capture failure screenshot: %s", e)
        return ""

    def get_session_checks(self, workspace_id: int, limit: int = 20) -> list[dict]:
        """Get session check history."""
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM workspace_session_checks WHERE workspace_id=? ORDER BY created_at DESC LIMIT ?",
            (workspace_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def _save_check(self, workspace_id: int, result: dict):
        """Save session check to database."""
        import json
        now = utc_now_iso()
        conn = get_conn()
        try:
            conn.execute(
                "INSERT INTO workspace_session_checks (workspace_id, check_type, status, details_json, screenshot_path, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (workspace_id, "youtube_studio", result["status"],
                 json.dumps(result["checks"]), result.get("screenshot_path", ""), now),
            )
            conn.commit()
        except Exception as e:
            logger.warning("Failed to save session check: %s", e)


# Module-level singleton
verifier = WorkspaceVerifier()
