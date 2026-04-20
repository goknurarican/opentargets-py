"""Tests for OpenTargetsClient public methods."""

from __future__ import annotations

import httpx
import pytest
import respx

from opentargets import NotFoundError, OpenTargetsClient

_GQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"


def _post(response_json: dict) -> respx.MockRouter:
    return respx.mock(assert_all_called=False)


@respx.mock
def test_get_target_by_ensembl_id(target_response):
    respx.post(_GQL_URL).mock(return_value=httpx.Response(200, json=target_response))
    client = OpenTargetsClient(cache=False)
    target = client.get_target("ENSG00000146648")
    assert target.id == "ENSG00000146648"
    assert target.approved_symbol == "EGFR"


@respx.mock
def test_get_target_by_symbol(search_response, target_response):
    # First call resolves symbol → Ensembl ID via search
    # Second call fetches target info
    respx.post(_GQL_URL).mock(
        side_effect=[
            httpx.Response(200, json=search_response),
            httpx.Response(200, json=target_response),
            httpx.Response(200, json=target_response),
        ]
    )
    client = OpenTargetsClient(cache=False)
    target = client.get_target("EGFR")
    assert target.approved_symbol == "EGFR"


@respx.mock
def test_get_target_not_found(search_response):
    empty = {"data": {"search": {"total": 0, "hits": []}}}
    respx.post(_GQL_URL).mock(return_value=httpx.Response(200, json=empty))
    client = OpenTargetsClient(cache=False)
    with pytest.raises(NotFoundError) as exc_info:
        client.get_target("DOESNOTEXIST")
    assert exc_info.value.entity_type == "target"


@respx.mock
def test_get_target_api_returns_null():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json={"data": {"target": None}})
    )
    client = OpenTargetsClient(cache=False)
    with pytest.raises(NotFoundError):
        client.get_target("ENSG00000000000")


@respx.mock
def test_get_disease(disease_response):
    respx.post(_GQL_URL).mock(return_value=httpx.Response(200, json=disease_response))
    client = OpenTargetsClient(cache=False)
    disease = client.get_disease("EFO_0003060")
    assert disease.id == "EFO_0003060"
    assert disease.name == "lung carcinoma"


@respx.mock
def test_get_disease_not_found():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json={"data": {"disease": None}})
    )
    client = OpenTargetsClient(cache=False)
    with pytest.raises(NotFoundError) as exc_info:
        client.get_disease("EFO_9999999")
    assert exc_info.value.entity_type == "disease"


@respx.mock
def test_get_drug(drug_response):
    respx.post(_GQL_URL).mock(return_value=httpx.Response(200, json=drug_response))
    client = OpenTargetsClient(cache=False)
    drug = client.get_drug("CHEMBL939")
    assert drug.id == "CHEMBL939"
    assert drug.name == "ERLOTINIB"
    assert drug.max_clinical_trial_phase == "APPROVAL"


@respx.mock
def test_get_drug_not_found():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json={"data": {"drug": None}})
    )
    client = OpenTargetsClient(cache=False)
    with pytest.raises(NotFoundError):
        client.get_drug("CHEMBL0000000")


@respx.mock
def test_search_returns_results(search_response):
    respx.post(_GQL_URL).mock(return_value=httpx.Response(200, json=search_response))
    client = OpenTargetsClient(cache=False)
    results = client.search("EGFR", entity_type="target", limit=1)
    assert len(results) == 1
    assert results[0].id == "ENSG00000146648"
    assert results[0].entity_type == "target"


@respx.mock
def test_search_empty_results():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(
            200, json={"data": {"search": {"total": 0, "hits": []}}}
        )
    )
    client = OpenTargetsClient(cache=False)
    results = client.search("xyznotexist")
    assert results == []


@respx.mock
def test_get_target_associations(
    search_response, target_response, associations_response
):
    respx.post(_GQL_URL).mock(
        side_effect=[
            httpx.Response(200, json=search_response),
            httpx.Response(200, json=associations_response),
            httpx.Response(200, json=target_response),
        ]
    )
    client = OpenTargetsClient(cache=False)
    assocs = client.get_target_associations("EGFR", limit=25)
    assert len(assocs) == 1
    assert assocs[0].disease_name == "lung carcinoma"
    assert assocs[0].score == 0.75


@respx.mock
def test_get_drug_indications(drug_indications_response):
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json=drug_indications_response)
    )
    client = OpenTargetsClient(cache=False)
    indications = client.get_drug_indications("CHEMBL939")
    assert len(indications) == 1
    assert indications[0].disease_name == "lung carcinoma"
    assert indications[0].max_phase_for_indication == "APPROVAL"


def test_client_context_manager():
    with OpenTargetsClient(cache=False) as client:
        assert client is not None
