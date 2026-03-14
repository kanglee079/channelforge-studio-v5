
from __future__ import annotations

import os
from apscheduler.schedulers.background import BackgroundScheduler

from .services.trend_assistant import refresh_trends_cache

_scheduler: BackgroundScheduler | None = None


def start_background_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    enabled = os.getenv("ENABLE_BACKGROUND_SCANNER", "true").lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return
    interval = int(os.getenv("TREND_SCAN_MINUTES", "60"))
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(refresh_trends_cache, "interval", minutes=interval, id="trend-refresh", replace_existing=True)
    _scheduler.start()
