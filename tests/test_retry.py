"""Tests for retry / backoff logic."""

from __future__ import annotations

import pytest

from opentargets._retry import DEFAULT_RETRY_CONFIG, RetryConfig, _backoff, with_retry
from opentargets.exceptions import APIError, RateLimitError


def test_backoff_values():
    assert _backoff(0) == 1.0
    assert _backoff(1) == 2.0
    assert _backoff(2) == 4.0
    assert _backoff(10) == 60.0  # capped at MAX_DELAY


def test_no_retry_on_success():
    calls = []

    def fn() -> str:
        calls.append(1)
        return "ok"

    result = with_retry(fn)
    assert result == "ok"
    assert len(calls) == 1


def test_retry_on_rate_limit(monkeypatch):
    monkeypatch.setattr("opentargets._retry._sleep", lambda _: None)
    attempts = []

    def fn() -> str:
        attempts.append(1)
        if len(attempts) < 3:
            raise RateLimitError()
        return "ok"

    result = with_retry(fn)
    assert result == "ok"
    assert len(attempts) == 3


def test_no_retry_on_4xx(monkeypatch):
    monkeypatch.setattr("opentargets._retry._sleep", lambda _: None)

    def fn() -> str:
        raise APIError(status_code=400, message="Bad request")

    with pytest.raises(APIError) as exc_info:
        with_retry(fn)
    assert exc_info.value.status_code == 400


def test_exhausts_retries(monkeypatch):
    monkeypatch.setattr("opentargets._retry._sleep", lambda _: None)

    def fn() -> str:
        raise APIError(status_code=503, message="unavailable")

    with pytest.raises(APIError) as exc_info:
        with_retry(fn)
    assert exc_info.value.status_code == 503


# ---------------------------------------------------------------------------
# New configurable-retry tests
# ---------------------------------------------------------------------------


def test_retry_max_retries_zero_disables_retries(monkeypatch):
    """max_retries=0 means fn is called exactly once and any error propagates."""
    monkeypatch.setattr("opentargets._retry._sleep", lambda _: None)
    config = RetryConfig(max_retries=0)
    calls = []

    def fn() -> str:
        calls.append(1)
        raise APIError(status_code=503, message="unavailable")

    with pytest.raises(APIError):
        with_retry(fn, config)

    assert len(calls) == 1


def test_retry_custom_retryable_statuses(monkeypatch):
    """Status 418 (not in defaults) triggers retry when added to config."""
    monkeypatch.setattr("opentargets._retry._sleep", lambda _: None)
    config = RetryConfig(
        max_retries=3,
        retryable_statuses=frozenset({418, 429, 500, 502, 503, 504}),
    )
    attempts = []

    def fn() -> str:
        attempts.append(1)
        if len(attempts) < 3:
            raise APIError(status_code=418, message="I'm a teapot")
        return "ok"

    result = with_retry(fn, config)
    assert result == "ok"
    assert len(attempts) == 3


def test_retry_respect_retry_after_false(monkeypatch):
    """When respect_retry_after=False the Retry-After header value is ignored
    and exponential backoff is used instead."""
    monkeypatch.setattr("opentargets._retry._sleep", lambda _: None)
    config = RetryConfig(respect_retry_after=False)
    slept: list[float] = []
    monkeypatch.setattr("opentargets._retry._sleep", lambda s: slept.append(s))

    attempts = []

    def fn() -> str:
        attempts.append(1)
        if len(attempts) < 2:
            # Provide a large retry_after value that should NOT be used
            raise RateLimitError(retry_after=9999.0)
        return "ok"

    result = with_retry(fn, config)
    assert result == "ok"
    # The delay recorded must be a backoff value (1.0 for attempt 0),
    # NOT the 9999.0 from the Retry-After header.
    assert slept == [1.0]


def test_retry_config_default_unchanged(monkeypatch):
    """Default RetryConfig produces behaviour identical to the old constants."""
    monkeypatch.setattr("opentargets._retry._sleep", lambda _: None)
    attempts = []

    def fn() -> str:
        attempts.append(1)
        raise APIError(status_code=503, message="unavailable")

    # Default config: max_retries=3 → 4 total calls (1 initial + 3 retries)
    # All raise → error propagated after exhausting retries
    with pytest.raises(APIError) as exc_info:
        with_retry(fn, DEFAULT_RETRY_CONFIG)

    assert exc_info.value.status_code == 503
    assert len(attempts) == 4  # 1 initial + 3 retries

    # Also confirm default field values match old constants
    assert DEFAULT_RETRY_CONFIG.max_retries == 3
    assert DEFAULT_RETRY_CONFIG.base_delay == 1.0
    assert DEFAULT_RETRY_CONFIG.max_delay == 60.0
    assert DEFAULT_RETRY_CONFIG.retryable_statuses == frozenset(
        {429, 500, 502, 503, 504}
    )
    assert DEFAULT_RETRY_CONFIG.respect_retry_after is True
