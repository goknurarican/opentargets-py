"""Exponential backoff retry logic (no third-party dependencies)."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any, TypeVar

from .exceptions import RateLimitError

_T = TypeVar("_T")

# ---------------------------------------------------------------------------
# Legacy module-level constants — kept for backwards-compat; config is
# now the canonical source of truth.
# ---------------------------------------------------------------------------
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
_MAX_RETRIES = 3
_BASE_DELAY = 1.0
_MAX_DELAY = 60.0


@dataclass(frozen=True)
class RetryConfig:
    """Immutable configuration for retry behavior.

    Args:
        max_retries: Maximum number of retry attempts (0 = no retries).
        base_delay: Initial backoff delay in seconds.
        max_delay: Maximum backoff delay in seconds.
        retryable_statuses: Set of HTTP status codes that trigger a retry.
        respect_retry_after: When ``True`` (default) honour the ``Retry-After``
            response header value for 429 responses.  When ``False`` use
            exponential back-off instead.
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    retryable_statuses: frozenset = field(  # type: ignore[type-arg]
        default_factory=lambda: frozenset({429, 500, 502, 503, 504})
    )
    respect_retry_after: bool = True


DEFAULT_RETRY_CONFIG = RetryConfig()


def with_retry(
    fn: Callable[[], _T],
    config: RetryConfig = DEFAULT_RETRY_CONFIG,
) -> _T:
    """Execute *fn* with exponential backoff on retryable HTTP errors.

    Retries on :class:`~opentargets.exceptions.RateLimitError` and
    :class:`~opentargets.exceptions.APIError` whose ``status_code`` is in
    ``config.retryable_statuses``.

    Args:
        fn: Zero-argument callable that performs the HTTP request.
        config: Retry configuration; defaults to :data:`DEFAULT_RETRY_CONFIG`.

    Returns:
        The return value of *fn* on success.

    Raises:
        The last exception raised by *fn* after all retries are exhausted.
    """
    from .exceptions import APIError

    last_exc: Exception | None = None
    for attempt in range(config.max_retries + 1):
        try:
            return fn()
        except RateLimitError as exc:
            last_exc = exc
            if config.respect_retry_after and exc.retry_after is not None:
                delay = exc.retry_after
            else:
                delay = _backoff(attempt, config)
            _sleep(delay)
        except APIError as exc:
            if exc.status_code not in config.retryable_statuses:
                raise
            last_exc = exc
            _sleep(_backoff(attempt, config))

    assert last_exc is not None
    raise last_exc


async def with_retry_async(
    fn: Callable[[], Coroutine[Any, Any, _T]],
    config: RetryConfig = DEFAULT_RETRY_CONFIG,
) -> _T:
    """Async version of :func:`with_retry`.

    Args:
        fn: Zero-argument async callable that performs the HTTP request.
        config: Retry configuration; defaults to :data:`DEFAULT_RETRY_CONFIG`.

    Returns:
        The return value of *fn* on success.

    Raises:
        The last exception raised by *fn* after all retries are exhausted.
    """
    from .exceptions import APIError

    last_exc: Exception | None = None
    for attempt in range(config.max_retries + 1):
        try:
            return await fn()
        except RateLimitError as exc:
            last_exc = exc
            if config.respect_retry_after and exc.retry_after is not None:
                delay = exc.retry_after
            else:
                delay = _backoff(attempt, config)
            await asyncio.sleep(delay)
        except APIError as exc:
            if exc.status_code not in config.retryable_statuses:
                raise
            last_exc = exc
            await asyncio.sleep(_backoff(attempt, config))

    assert last_exc is not None
    raise last_exc


def _backoff(attempt: int, config: RetryConfig = DEFAULT_RETRY_CONFIG) -> float:
    """Return delay in seconds for the given attempt index (0-based)."""
    delay = config.base_delay * (2.0**attempt)
    return delay if delay < config.max_delay else config.max_delay


def _sleep(seconds: float) -> None:
    time.sleep(seconds)
