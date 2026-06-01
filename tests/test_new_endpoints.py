"""Tests for the 5 new endpoint methods added in feat/endpoints."""

from __future__ import annotations

import httpx
import pytest
import respx

from opentargets import (
    GeneticConstraint,
    OpenTargetsClient,
    SafetyLiability,
    TissueExpression,
    Tractability,
)

_GQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"

# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

_TRACTABILITY_ROWS = [
    {"modality": "SM", "label": "Druggable Genome", "value": True},
    {"modality": "AB", "label": "High-Quality Pocket", "value": False},
]

_SAFETY_ROWS = [
    {
        "event": "drug toxicity",
        "eventId": None,
        "datasource": "ClinPGx",
        "literature": None,
        "url": None,
        "effects": [],
        "biosamples": [],
    },
    {
        "event": "hepatotoxicity",
        "eventId": "tox_001",
        "datasource": "ToxCast",
        "literature": "PMID:12345678",
        "url": "https://example.com",
        "effects": [{"direction": "Activation/Increase/Upregulation", "dosing": None}],
        "biosamples": [
            {
                "tissueLabel": "liver",
                "tissueId": "UBERON_0002107",
                "cellLabel": "HepG2",
                "cellId": "CLO_0003703",
            }
        ],
    },
]

_EXPRESSION_ROWS = [
    {
        "tissue": {"id": "UBERON_0000178", "label": "blood"},
        "rna": {"value": 450.5, "level": 3, "zscore": 1, "unit": "TPM"},
        "protein": {"level": 2, "reliability": True},
    },
    {
        "tissue": {"id": "UBERON_0002113", "label": "kidney"},
        "rna": {"value": 120.0, "level": 2, "zscore": -1, "unit": "TPM"},
        "protein": {"level": -1, "reliability": False},
    },
]

_CONSTRAINT_ROWS = [
    {
        "constraintType": "lof",
        "obs": 12,
        "exp": 43.32,
        "oe": 0.277,
        "oeLower": 0.177,
        "oeUpper": 0.449,
        "score": 0.998,
    },
    {
        "constraintType": "mis",
        "obs": 464,
        "exp": 537.24,
        "oe": 0.864,
        "oeLower": 0.8,
        "oeUpper": 0.933,
        "score": 1.154,
    },
]

_DRUG_CROSS_REFS = {
    "id": "CHEMBL521",
    "name": "IBUPROFEN",
    "crossReferences": [
        {"source": "drugbank", "ids": ["DB01050"]},
        {"source": "ChEMBL", "ids": ["CHEMBL521"]},
    ],
}


# Responses that include ensembl target wrapper
def _target_tractability_resp() -> dict:
    return {
        "data": {
            "target": {
                "id": "ENSG00000146648",
                "tractability": _TRACTABILITY_ROWS,
            }
        }
    }


def _target_safety_resp() -> dict:
    return {
        "data": {
            "target": {
                "id": "ENSG00000146648",
                "safetyLiabilities": _SAFETY_ROWS,
            }
        }
    }


def _target_expression_resp() -> dict:
    return {
        "data": {
            "target": {
                "id": "ENSG00000146648",
                "expressions": _EXPRESSION_ROWS,
            }
        }
    }


def _target_constraint_resp() -> dict:
    return {
        "data": {
            "target": {
                "id": "ENSG00000146648",
                "geneticConstraint": _CONSTRAINT_ROWS,
            }
        }
    }


def _drug_chembl_resp() -> dict:
    return {"data": {"drug": _DRUG_CROSS_REFS}}


# ---------------------------------------------------------------------------
# get_target_tractability
# ---------------------------------------------------------------------------


@respx.mock
def test_get_target_tractability_returns_list():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json=_target_tractability_resp())
    )
    client = OpenTargetsClient(cache=False)
    results = client.get_target_tractability("ENSG00000146648")
    assert len(results) == 2
    assert all(isinstance(r, Tractability) for r in results)
    assert results[0].modality == "SM"
    assert results[0].label == "Druggable Genome"
    assert results[0].value is True
    assert results[1].value is False


@respx.mock
def test_get_target_tractability_empty():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(
            200,
            json={"data": {"target": {"id": "ENSG00000146648", "tractability": []}}},
        )
    )
    client = OpenTargetsClient(cache=False)
    results = client.get_target_tractability("ENSG00000146648")
    assert results == []


# ---------------------------------------------------------------------------
# get_target_safety
# ---------------------------------------------------------------------------


@respx.mock
def test_get_target_safety_returns_list():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json=_target_safety_resp())
    )
    client = OpenTargetsClient(cache=False)
    results = client.get_target_safety("ENSG00000146648")
    assert len(results) == 2
    assert all(isinstance(r, SafetyLiability) for r in results)
    first = results[0]
    assert first.event == "drug toxicity"
    assert first.datasource == "ClinPGx"
    assert first.effects == []
    assert first.biosamples == []


@respx.mock
def test_get_target_safety_with_effects_and_biosamples():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json=_target_safety_resp())
    )
    client = OpenTargetsClient(cache=False)
    results = client.get_target_safety("ENSG00000146648")
    second = results[1]
    assert second.event_id == "tox_001"
    assert second.literature == "PMID:12345678"
    assert len(second.effects) == 1
    assert second.effects[0].direction == "Activation/Increase/Upregulation"
    assert len(second.biosamples) == 1
    assert second.biosamples[0].tissue_label == "liver"
    assert second.biosamples[0].cell_label == "HepG2"


# ---------------------------------------------------------------------------
# get_target_expression
# ---------------------------------------------------------------------------


@respx.mock
def test_get_target_expression_returns_list():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json=_target_expression_resp())
    )
    client = OpenTargetsClient(cache=False)
    results = client.get_target_expression("ENSG00000146648")
    assert len(results) == 2
    assert all(isinstance(r, TissueExpression) for r in results)
    first = results[0]
    assert first.tissue.label == "blood"
    assert first.tissue.id == "UBERON_0000178"
    assert first.rna.value == pytest.approx(450.5)
    assert first.rna.level == 3
    assert first.protein.level == 2
    assert first.protein.reliability is True


@respx.mock
def test_get_target_expression_protein_unreliable():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json=_target_expression_resp())
    )
    client = OpenTargetsClient(cache=False)
    results = client.get_target_expression("ENSG00000146648")
    second = results[1]
    assert second.protein.reliability is False
    assert second.protein.level == -1


# ---------------------------------------------------------------------------
# get_target_constraint
# ---------------------------------------------------------------------------


@respx.mock
def test_get_target_constraint_returns_list():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json=_target_constraint_resp())
    )
    client = OpenTargetsClient(cache=False)
    results = client.get_target_constraint("ENSG00000146648")
    assert len(results) == 2
    assert all(isinstance(r, GeneticConstraint) for r in results)
    lof = results[0]
    assert lof.constraint_type == "lof"
    assert lof.obs == 12
    assert lof.oe == pytest.approx(0.277)
    assert lof.score == pytest.approx(0.998)


@respx.mock
def test_get_target_constraint_mis_entry():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json=_target_constraint_resp())
    )
    client = OpenTargetsClient(cache=False)
    results = client.get_target_constraint("ENSG00000146648")
    mis = results[1]
    assert mis.constraint_type == "mis"
    assert mis.oe_lower == pytest.approx(0.8)
    assert mis.oe_upper == pytest.approx(0.933)


# ---------------------------------------------------------------------------
# get_drug_chembl_ids
# ---------------------------------------------------------------------------


@respx.mock
def test_get_drug_chembl_ids_returns_primary_id():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json=_drug_chembl_resp())
    )
    client = OpenTargetsClient(cache=False)
    ids = client.get_drug_chembl_ids("CHEMBL521")
    # Primary ID should always be first
    assert ids[0] == "CHEMBL521"


@respx.mock
def test_get_drug_chembl_ids_includes_crossref_chembl():
    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json=_drug_chembl_resp())
    )
    client = OpenTargetsClient(cache=False)
    ids = client.get_drug_chembl_ids("CHEMBL521")
    # Should contain the crossRef CHEMBL id (deduplicated — same as primary here)
    assert "CHEMBL521" in ids


@respx.mock
def test_get_drug_chembl_ids_not_found():
    from opentargets import NotFoundError

    respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json={"data": {"drug": None}})
    )
    client = OpenTargetsClient(cache=False)
    with pytest.raises(NotFoundError):
        client.get_drug_chembl_ids("CHEMBL9999999")


@respx.mock
def test_get_drug_chembl_ids_skips_non_chembl_refs():
    # crossReferences that don't start with CHEMBL should not be included
    resp = {
        "data": {
            "drug": {
                "id": "CHEMBL521",
                "name": "IBUPROFEN",
                "crossReferences": [
                    {"source": "drugbank", "ids": ["DB01050"]},
                    {"source": "DailyMed", "ids": ["ibuprofen"]},
                ],
            }
        }
    }
    respx.post(_GQL_URL).mock(return_value=httpx.Response(200, json=resp))
    client = OpenTargetsClient(cache=False)
    ids = client.get_drug_chembl_ids("CHEMBL521")
    # Only the primary ChEMBL id should be returned (no drugbank or DailyMed)
    assert ids == ["CHEMBL521"]


# ---------------------------------------------------------------------------
# Integration tests (skipped by default — hit real API)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_integration_get_target_tractability():
    client = OpenTargetsClient()
    results = client.get_target_tractability("ENSG00000141510")  # TP53
    assert len(results) > 0
    assert all(isinstance(r, Tractability) for r in results)
    modalities = {r.modality for r in results}
    assert modalities  # should have at least one modality


@pytest.mark.integration
def test_integration_get_target_safety():
    client = OpenTargetsClient()
    results = client.get_target_safety("ENSG00000141510")  # TP53
    assert len(results) > 0
    assert all(isinstance(r, SafetyLiability) for r in results)
    assert all(r.datasource for r in results)


@pytest.mark.integration
def test_integration_get_target_expression():
    client = OpenTargetsClient()
    results = client.get_target_expression("ENSG00000141510")  # TP53
    assert len(results) > 0
    assert all(isinstance(r, TissueExpression) for r in results)
    # RNA values should be non-negative
    assert all(r.rna.value >= 0 for r in results)


@pytest.mark.integration
def test_integration_get_target_constraint():
    client = OpenTargetsClient()
    results = client.get_target_constraint("ENSG00000141510")  # TP53
    constraint_types = {r.constraint_type for r in results}
    # TP53 should have lof, mis, syn constraint types
    assert "lof" in constraint_types
    lof = next(r for r in results if r.constraint_type == "lof")
    assert lof.score is not None
    assert lof.oe is not None


@pytest.mark.integration
def test_integration_get_drug_chembl_ids():
    client = OpenTargetsClient()
    ids = client.get_drug_chembl_ids("CHEMBL521")  # ibuprofen
    assert "CHEMBL521" in ids
    assert all(isinstance(i, str) for i in ids)
