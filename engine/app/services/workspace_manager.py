"""Workspace Manager — Manages isolated browser profiles per channel.

Uses Playwright for browser automation with persistent contexts.
Each workspace gets its own storage directory for cookies, localStorage, IndexedDB.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

WORKSPACES_ROOT = Path("workspaces")


class WorkspaceService:
    """Manages browser workspace directories and Playwright sessions."""

    def create_workspace_dir(self, name: str) -> Path:
        """Create an isolated workspace storage directory."""
        ws_dir = WORKSPACES_ROOT / name
        ws_dir.mkdir(parents=True, exist_ok=True)
        (ws_dir / "downloads").mkdir(exist_ok=True)
        logger.info("Created workspace directory: %s", ws_dir)
        return ws_dir

    async def launch_browser(self, storage_path: str, proxy_config: str | None = None) -> None:
        """Launch an isolated Playwright browser with persistent context.

        Args:
            storage_path: Path to workspace directory for state persistence
            proxy_config: Optional proxy URL (e.g., 'http://user:pass@host:port')
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError(
                "Playwright is not installed. Run: pip install playwright && python -m playwright install chromium"
            )

        pw = await async_playwright().start()

        launch_opts: dict = {}
        if proxy_config:
            launch_opts["proxy"] = {"server": proxy_config}

        context = await pw.chromium.launch_persistent_context(
            user_data_dir=storage_path,
            headless=False,
            channel="chromium",
            accept_downloads=True,
            viewport={"width": 1280, "height": 800},
            **launch_opts,
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=30000)

        logger.info("Browser launched for workspace: %s", storage_path)

    def check_health(self, storage_path: str) -> dict:
        """Check if workspace storage contains valid session data."""
        ws_path = Path(storage_path)
        return {
            "storage_exists": ws_path.exists(),
            "has_cookies": (ws_path / "Default" / "Cookies").exists() if ws_path.exists() else False,
            "downloads_dir": str(ws_path / "downloads"),
        }
