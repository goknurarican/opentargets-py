"""Tests for AsyncOpenTargetsClient public methods."""

from __future__ import annotations

import httpx
import pytest
import respx

from opentargets import AsyncOpenTargetsClient, NotFoundError

_GQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"


@pytest.mark.asyncio
@respx.mock
async def test_async_get_target_by_ensembl_id(target_response: dict) -> None:
    respx.post(_GQL_URL).mock(return_value=httpx.Response(200, json=target_response))
    async with AsyncOpenTargetsClient(cache=False) as client:
        target = await client.get_target("ENSG00000146648")
    assert target.id == "ENSG00000146648"
    assert target.approved_symbol == "EGFR"


@pytest.mark.asyncio
@respx.mock
async def test_async_get_target_by_symbol(
    search_response: dict, target_response: dict
) -> None:
    respx.post(_GQL_URL).mock(
        side_effect=[
            httpx.Response(200, json=search_response),
            httpx.Response(200, json=target_response),
            httpx.Response(200, json=target_response),
        ]
    )
    async with AsyncOpenTargetsClient(cache=False) as client:
        target = await client.get_target("EGFR")
    assert target.approved_symbol == "EGFR"


@pytest.mark.asyncio
@respx.mock
async def test_async_get_target_not_found() -> None:
    empty = {"data": {"search": {"total": 0, "hits": []}}}
    respx.post(_GQL_URL).mock(return_value=httpx.Response(200, json=empty))
    async with AsyncOpenTargetsClient(cache=False) as client:
        with pytest.raises(NotFoundError) as exc_info:
            await client.get_target("DOESNOTEXIST")
    assert exc_info.value.entity_type == "target"


@pytest.mark.asyncio
@respx.mock
async def test_async_get_target_api_returns_null() -> None:
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json={"data": {"target": None}})
    )
    async with AsyncOpenTargetsClient(cache=False) as client:
        with pytest.raises(NotFoundError):
            await client.get_target("ENSG00000000000")


@pytest.mark.asyncio
@respx.mock
async def test_async_get_targets(targets_batch_response: dict) -> None:
    # Ensembl IDs bypass symbol resolution — only one HTTP call needed
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json=targets_batch_response)
    )
    async with AsyncOpenTargetsClient(cache=False) as client:
        targets = await client.get_targets(["ENSG00000146648"])
    assert len(targets) == 1
    assert targets[0].id == "ENSG00000146648"


@pytest.mark.asyncio
@respx.mock
async def test_async_get_target_associations(
    search_response: dict,
    associations_response: dict,
    target_response: dict,
) -> None:
    respx.post(_GQL_URL).mock(
        side_effect=[
            httpx.Response(200, json=search_response),
            httpx.Response(200, json=associations_response),
            httpx.Response(200, json=target_response),
        ]
    )
    async with AsyncOpenTargetsClient(cache=False) as client:
        assocs = await client.get_target_associations("EGFR", limit=25)
    assert len(assocs) == 1
    assert assocs[0].disease_name == "lung carcinoma"
    assert assocs[0].score == 0.75


@pytest.mark.asyncio
@respx.mock
async def test_async_get_target_drugs(search_response: dict) -> None:
    drug_resp = {
        "data": {
            "target": {
                "id": "ENSG00000146648",
                "drugAndClinicalCandidates": {
                    "rows": [
                        {
                            "drug": {
                                "id": "CHEMBL939",
                                "name": "ERLOTINIB",
                                "drugType": "Small molecule",
                                "mechanismsOfAction": {
                                    "rows": [{"mechanismOfAction": "EGFR inhibitor"}]
                                },
                                "synonyms": [],
                                "tradeNames": [],
                                "maximumClinicalStage": "APPROVAL",
                            }
                        }
                    ]
                },
            }
        }
    }
    respx.post(_GQL_URL).mock(
        side_effect=[
            httpx.Response(200, json=search_response),
            httpx.Response(200, json=drug_resp),
        ]
    )
    async with AsyncOpenTargetsClient(cache=False) as client:
        drugs = await client.get_target_drugs("EGFR")
    assert len(drugs) == 1
    assert drugs[0].name == "ERLOTINIB"


@pytest.mark.asyncio
@respx.mock
async def test_async_get_disease(disease_response: dict) -> None:
    respx.post(_GQL_URL).mock(return_value=httpx.Response(200, json=disease_response))
    async with AsyncOpenTargetsClient(cache=False) as client:
        disease = await client.get_disease("EFO_0003060")
    assert disease.id == "EFO_0003060"
    assert disease.name == "lung carcinoma"


@pytest.mark.asyncio
@respx.mock
async def test_async_get_disease_not_found() -> None:
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json={"data": {"disease": None}})
    )
    async with AsyncOpenTargetsClient(cache=False) as client:
        with pytest.raises(NotFoundError) as exc_info:
            await client.get_disease("EFO_9999999")
    assert exc_info.value.entity_type == "disease"


@pytest.mark.asyncio
@respx.mock
async def test_async_get_disease_targets(disease_response: dict) -> None:
    disease_targets_resp = {
        "data": {
            "disease": {
                "id": "EFO_0003060",
                "name": "lung carcinoma",
                "associatedTargets": {
                    "count": 1,
                    "rows": [
                        {
                            "target": {
                                "id": "ENSG00000146648",
                                "approvedSymbol": "EGFR",
                            },
                            "score": 0.8,
                            "datasourceScores": [],
                        }
                    ],
                },
            }
        }
    }
    respx.post(_GQL_URL).mock(
        side_effect=[
            httpx.Response(200, json=disease_targets_resp),
            httpx.Response(200, json=disease_response),
        ]
    )
    async with AsyncOpenTargetsClient(cache=False) as client:
        assocs = await client.get_disease_targets("EFO_0003060", limit=25)
    assert len(assocs) == 1
    assert assocs[0].target_symbol == "EGFR"
    assert assocs[0].score == 0.8


@pytest.mark.asyncio
@respx.mock
async def test_async_get_drug(drug_response: dict) -> None:
    respx.post(_GQL_URL).mock(return_value=httpx.Response(200, json=drug_response))
    async with AsyncOpenTargetsClient(cache=False) as client:
        drug = await client.get_drug("CHEMBL939")
    assert drug.id == "CHEMBL939"
    assert drug.name == "ERLOTINIB"
    assert drug.max_clinical_trial_phase == "APPROVAL"


@pytest.mark.asyncio
@respx.mock
async def test_async_get_drug_not_found() -> None:
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json={"data": {"drug": None}})
    )
    async with AsyncOpenTargetsClient(cache=False) as client:
        with pytest.raises(NotFoundError):
            await client.get_drug("CHEMBL0000000")


@pytest.mark.asyncio
@respx.mock
async def test_async_get_drug_indications(drug_indications_response: dict) -> None:
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json=drug_indications_response)
    )
    async with AsyncOpenTargetsClient(cache=False) as client:
        indications = await client.get_drug_indications("CHEMBL939")
    assert len(indications) == 1
    assert indications[0].disease_name == "lung carcinoma"
    assert indications[0].max_phase_for_indication == "APPROVAL"


@pytest.mark.asyncio
@respx.mock
async def test_async_search_returns_results(search_response: dict) -> None:
    respx.post(_GQL_URL).mock(return_value=httpx.Response(200, json=search_response))
    async with AsyncOpenTargetsClient(cache=False) as client:
        results = await client.search("EGFR", entity_type="target", limit=1)
    assert len(results) == 1
    assert results[0].id == "ENSG00000146648"
    assert results[0].entity_type == "target"


@pytest.mark.asyncio
@respx.mock
async def test_async_search_empty_results() -> None:
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(
            200, json={"data": {"search": {"total": 0, "hits": []}}}
        )
    )
    async with AsyncOpenTargetsClient(cache=False) as client:
        results = await client.search("xyznotexist")
    assert results == []


@pytest.mark.asyncio
@respx.mock
async def test_async_get_associations_found(
    search_response: dict,
    associations_response: dict,
    target_response: dict,
) -> None:
    respx.post(_GQL_URL).mock(
        side_effect=[
            httpx.Response(200, json=search_response),
            httpx.Response(200, json=associations_response),
            httpx.Response(200, json=target_response),
        ]
    )
    async with AsyncOpenTargetsClient(cache=False) as client:
        assoc = await client.get_associations("EGFR", "EFO_0003060")
    assert assoc is not None
    assert assoc.disease_id == "EFO_0003060"
    assert assoc.target_symbol == "EGFR"


@pytest.mark.asyncio
@respx.mock
async def test_async_get_associations_not_found(
    search_response: dict,
    associations_response: dict,
) -> None:
    respx.post(_GQL_URL).mock(
        side_effect=[
            httpx.Response(200, json=search_response),
            httpx.Response(200, json=associations_response),
        ]
    )
    async with AsyncOpenTargetsClient(cache=False) as client:
        assoc = await client.get_associations("EGFR", "EFO_9999999")
    assert assoc is None


@pytest.mark.asyncio
async def test_async_client_context_manager() -> None:
    async with AsyncOpenTargetsClient(cache=False) as client:
        assert client is not None


@pytest.mark.asyncio
@respx.mock
async def test_async_gather_concurrent(target_response: dict) -> None:
    """Verify asyncio.gather works across multiple concurrent calls."""
    import asyncio

    respx.post(_GQL_URL).mock(return_value=httpx.Response(200, json=target_response))
    async with AsyncOpenTargetsClient(cache=False) as client:
        targets = await asyncio.gather(
            client.get_target("ENSG00000146648"),
            client.get_target("ENSG00000146648"),
            client.get_target("ENSG00000146648"),
        )
    assert all(t.approved_symbol == "EGFR" for t in targets)
