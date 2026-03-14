from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry_call(fn: Callable[[], T], *, tries: int = 3, base_seconds: float = 2.0, retry_on: tuple[type[Exception], ...] = (Exception,)) -> T:
    last_error: Exception | None = None
    for attempt in range(tries):
        try:
            return fn()
        except retry_on as exc:
            last_error = exc
            if attempt == tries - 1:
                raise
            time.sleep(base_seconds * (2 ** attempt))
    assert last_error is not None
    raise last_error
