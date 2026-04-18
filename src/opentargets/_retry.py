"""Exponential backoff retry logic (no third-party dependencies)."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from .exceptions import RateLimitError

_T = TypeVar("_T")

_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
_MAX_RETRIES = 3
_BASE_DELAY = 1.0
_MAX_DELAY = 60.0


def with_retry(fn: Callable[[], _T]) -> _T:
    """Execute *fn* with exponential backoff on retryable HTTP errors.

    Retries on :class:`~opentargets.exceptions.RateLimitError` and
    :class:`~opentargets.exceptions.APIError` whose ``status_code`` is in
    ``{429, 500, 502, 503, 504}``.

    Args:
        fn: Zero-argument callable that performs the HTTP request.

    Returns:
        The return value of *fn* on success.

    Raises:
        The last exception raised by *fn* after all retries are exhausted.
    """
    from .exceptions import APIError

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            return fn()
        except RateLimitError as exc:
            last_exc = exc
            delay = (
                exc.retry_after if exc.retry_after is not None else _backoff(attempt)
            )
            _sleep(delay)
        except APIError as exc:
            if exc.status_code not in _RETRYABLE_STATUS:
                raise
            last_exc = exc
            _sleep(_backoff(attempt))

    assert last_exc is not None
    raise last_exc


def _backoff(attempt: int) -> float:
    """Return delay in seconds for the given attempt index (0-based)."""
    delay = _BASE_DELAY * (2.0**attempt)
    return delay if delay < _MAX_DELAY else _MAX_DELAY


def _sleep(seconds: float) -> None:
    time.sleep(seconds)
