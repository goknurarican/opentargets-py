"""Tests for GraphQLClient: pagination, error handling, lifecycle."""

from __future__ import annotations

import httpx
import pytest
import respx

from opentargets._graphql import GraphQLClient
from opentargets.exceptions import APIError, QueryError, RateLimitError

_GQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"


@respx.mock
def test_execute_graphql_errors_raises_query_error():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(
            200,
            json={"errors": [{"message": "Field not found"}]},
        )
    )
    client = GraphQLClient()
    with pytest.raises(QueryError) as exc_info:
        client.execute("query { bad }")
    assert "Field not found" in str(exc_info.value)


@respx.mock
def test_execute_http_error_raises_api_error():
    respx.post(_GQL_URL).mock(return_value=httpx.Response(400, text="Bad Request"))
    client = GraphQLClient()
    with pytest.raises(APIError) as exc_info:
        client.execute("query { test }")
    assert exc_info.value.status_code == 400


@respx.mock
def test_execute_rate_limit_with_retry_after(monkeypatch):
    monkeypatch.setattr("opentargets._retry._sleep", lambda _: None)
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(429, headers={"Retry-After": "5"})
    )
    client = GraphQLClient()
    with pytest.raises(RateLimitError) as exc_info:
        client.execute("query { test }")
    assert exc_info.value.retry_after == 5.0


def test_close_owned_client():
    client = GraphQLClient()
    client.close()


def test_close_external_client_not_closed():
    http = httpx.Client()
    client = GraphQLClient(http_client=http)
    client.close()
    assert not http.is_closed
    http.close()


def test_context_manager():
    with GraphQLClient() as client:
        assert client is not None


@respx.mock
def test_paginate_multi_page():
    page1 = {
        "data": {
            "target": {
                "associatedDiseases": {
                    "count": 2,
                    "rows": [
                        {"disease": {"id": "EFO_A", "name": "Disease A"}, "score": 0.9}
                    ],
                }
            }
        }
    }
    page2 = {
        "data": {
            "target": {
                "associatedDiseases": {
                    "count": 2,
                    "rows": [
                        {"disease": {"id": "EFO_B", "name": "Disease B"}, "score": 0.5}
                    ],
                }
            }
        }
    }
    respx.post(_GQL_URL).mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
    )
    client = GraphQLClient()
    _Q = (
        "query Q($index: Int!, $size: Int!) { target { "
        "associatedDiseases(page: {index: $index, size: $size}) "
        "{ count rows { disease { id } score } } } }"
    )
    rows = client.paginate(
        _Q,
        variables={"ensemblId": "ENSG00000146648"},
        data_path=["target", "associatedDiseases"],
        size=1,
    )
    assert len(rows) == 2
    assert rows[0]["disease"]["id"] == "EFO_A"
    assert rows[1]["disease"]["id"] == "EFO_B"


@respx.mock
def test_paginate_missing_data_path_returns_empty():
    respx.post(_GQL_URL).mock(return_value=httpx.Response(200, json={"data": {}}))
    client = GraphQLClient()
    rows = client.paginate("query", {}, data_path=["nonexistent", "path"])
    assert rows == []
