"""Core GraphQL executor: sends queries, handles pagination and errors."""

from __future__ import annotations

from typing import Any

import httpx

from ._retry import with_retry
from .exceptions import APIError, QueryError, RateLimitError

_DEFAULT_URL = "https://api.platform.opentargets.org/api/v4/graphql"
_DEFAULT_TIMEOUT = 30.0


class GraphQLClient:
    """Low-level GraphQL client wrapping ``httpx``.

    Args:
        base_url: GraphQL endpoint URL.
        timeout: Request timeout in seconds.
        http_client: Optional pre-configured :class:`httpx.Client` to reuse.
    """

    def __init__(
        self,
        base_url: str = _DEFAULT_URL,
        timeout: float = _DEFAULT_TIMEOUT,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._client = http_client or httpx.Client(timeout=timeout)
        self._owns_client = http_client is None

    def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query and return the ``data`` field.

        Args:
            query: GraphQL query string.
            variables: Optional variable bindings.

        Returns:
            The ``data`` portion of the GraphQL response.

        Raises:
            RateLimitError: On HTTP 429.
            APIError: On other non-2xx HTTP responses.
            QueryError: When the response body contains ``errors``.
        """
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        def _do_request() -> dict[str, Any]:
            response = self._client.post(self._base_url, json=payload)
            _raise_for_status(response)
            body: dict[str, Any] = response.json()
            if "errors" in body and body["errors"]:
                raise QueryError(body["errors"])
            return body.get("data") or {}

        return with_retry(_do_request)

    def paginate(
        self,
        query: str,
        variables: dict[str, Any],
        data_path: list[str],
        rows_key: str = "rows",
        size: int = 25,
    ) -> list[Any]:
        """Fetch all pages for a paginated query.

        Injects ``index`` and ``size`` into *variables* automatically and
        follows pages until the ``count`` is exhausted.

        Args:
            query: Paginated GraphQL query string
                   (must accept ``$index`` and ``$size``).
            variables: Base variables (without ``index`` / ``size``).
            data_path: Keys to traverse in the response to reach the paginated object
                       (e.g. ``["target", "associatedDiseases"]``).
            rows_key: Key name of the rows list inside the paginated object.
            size: Page size.

        Returns:
            Flat list of all row objects across pages.
        """
        rows: list[Any] = []
        index = 0

        while True:
            page_vars = {**variables, "index": index, "size": size}
            data = self.execute(query, page_vars)

            node: Any = data
            for key in data_path:
                node = node.get(key, {}) if isinstance(node, dict) else {}

            page_rows: list[Any] = (
                node.get(rows_key, []) if isinstance(node, dict) else []
            )
            count: int = node.get("count", 0) if isinstance(node, dict) else 0
            rows.extend(page_rows)

            if len(rows) >= count or not page_rows:
                break
            index += 1

        return rows

    def close(self) -> None:
        """Close the underlying HTTP client if owned by this instance."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> GraphQLClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _raise_for_status(response: httpx.Response) -> None:
    """Raise an appropriate exception for non-2xx responses."""
    if response.status_code == 429:
        retry_after_raw = response.headers.get("Retry-After")
        retry_after = float(retry_after_raw) if retry_after_raw else None
        raise RateLimitError(retry_after=retry_after)
    if response.is_error:
        raise APIError(
            status_code=response.status_code,
            message=response.text[:500],
        )
