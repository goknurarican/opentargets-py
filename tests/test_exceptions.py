"""Tests for custom exception classes."""

from __future__ import annotations

from opentargets.exceptions import APIError, NotFoundError, QueryError, RateLimitError


def test_api_error_str():
    err = APIError(status_code=500, message="Internal server error")
    assert "500" in str(err)
    assert err.status_code == 500


def test_query_error_messages():
    errors = [{"message": "Field not found"}, {"message": "Bad syntax"}]
    err = QueryError(errors)
    assert "Field not found" in str(err)
    assert err.errors == errors


def test_not_found_error():
    err = NotFoundError("target", "EGFR")
    assert err.entity_type == "target"
    assert err.entity_id == "EGFR"
    assert "EGFR" in str(err)


def test_rate_limit_error_with_retry_after():
    err = RateLimitError(retry_after=30.0)
    assert err.status_code == 429
    assert err.retry_after == 30.0
    assert "30" in str(err)


def test_rate_limit_error_without_retry_after():
    err = RateLimitError()
    assert err.retry_after is None


def test_exception_hierarchy():
    from opentargets.exceptions import OpenTargetsError
    assert isinstance(APIError(404, "not found"), OpenTargetsError)
    assert isinstance(RateLimitError(), APIError)
    assert isinstance(QueryError([]), OpenTargetsError)
    assert isinstance(NotFoundError("x", "y"), OpenTargetsError)
