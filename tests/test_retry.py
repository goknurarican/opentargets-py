"""Tests for retry / backoff logic."""

from __future__ import annotations

import pytest

from opentargets._retry import _backoff, with_retry
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
