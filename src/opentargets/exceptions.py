"""Custom exceptions for the opentargets-py SDK."""

from __future__ import annotations


class OpenTargetsError(Exception):
    """Base exception for all opentargets-py errors."""


class APIError(OpenTargetsError):
    """Raised when the API returns an HTTP error response.

    Args:
        status_code: HTTP status code returned by the API.
        message: Human-readable error message.
    """

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"API error {status_code}: {message}")


class QueryError(OpenTargetsError):
    """Raised when the GraphQL API returns errors in the response body.

    Args:
        errors: List of GraphQL error objects from the response.
    """

    def __init__(self, errors: list[dict[str, object]]) -> None:
        self.errors = errors
        messages = "; ".join(str(e.get("message", e)) for e in errors)
        super().__init__(f"GraphQL query error: {messages}")


class NotFoundError(OpenTargetsError):
    """Raised when a requested entity does not exist in the platform.

    Args:
        entity_type: Type of entity that was not found (e.g. "target", "disease").
        entity_id: Identifier that was searched for.
    """

    def __init__(self, entity_type: str, entity_id: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} not found: {entity_id!r}")


class RateLimitError(APIError):
    """Raised when the API responds with 429 Too Many Requests.

    Args:
        retry_after: Seconds to wait before retrying, if provided by the API.
    """

    def __init__(self, retry_after: float | None = None) -> None:
        self.retry_after = retry_after
        msg = "Rate limit exceeded"
        if retry_after is not None:
            msg += f"; retry after {retry_after}s"
        super().__init__(status_code=429, message=msg)
