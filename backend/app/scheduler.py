from __future__ import annotations

from datetime import datetime, timedelta, timezone

from dateutil.parser import isoparse


def schedule_publish_at(index: int, *, interval_minutes: int, schedule_start_at: str | None = None, now_utc: datetime | None = None) -> str:
    if schedule_start_at:
        start = isoparse(schedule_start_at)
    else:
        start = (now_utc or datetime.now(timezone.utc)) + timedelta(hours=1)
    ts = start + timedelta(minutes=index * interval_minutes)
    return ts.replace(microsecond=0).isoformat().replace("+00:00", "Z")
