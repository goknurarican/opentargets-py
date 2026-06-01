"""Tests for the MCP server tool registrations.

These tests verify that each tool is registered and callable as a plain Python
function — no MCP transport is started.  The SDK client is monkeypatched so
that no real network calls are made.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest

pytest.importorskip("fastmcp", reason="fastmcp requires Python >=3.10")

from opentargets import mcp_server as _mod
from opentargets.exceptions import NotFoundError
from opentargets.models import (
    Association,
    DatasourceScore,
    Disease,
    Drug,
    DrugIndication,
    GeneticConstraint,
    ProteinExpression,
    RnaExpression,
    SafetyBiosample,
    SafetyEffect,
    SafetyLiability,
    SearchResult,
    Target,
    TissueExpression,
    TissueInfo,
    Tractability,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ASSOCIATION = Association(
    target_id="ENSG00000146648",
    target_symbol="EGFR",
    disease_id="EFO_0003060",
    disease_name="lung carcinoma",
    score=0.75,
    datasource_scores=[DatasourceScore(id="ot_genetics_portal", score=0.6)],
)

_TARGET = Target(
    id="ENSG00000146648",
    approvedSymbol="EGFR",
    approvedName="epidermal growth factor receptor",
    biotype="protein_coding",
    functionDescriptions=["Receptor tyrosine kinase"],
)

_DISEASE = Disease(
    id="EFO_0003060",
    name="lung carcinoma",
    description="A lung cancer.",
    therapeuticAreas=["oncology"],
    dbXRefs=["OMIM:211980"],
)

_DRUG = Drug(
    id="CHEMBL939",
    name="ERLOTINIB",
    drugType="Small molecule",
    mechanism_of_action="EGFR inhibitor",
    synonyms=["Tarceva"],
    tradeNames=["Tarceva"],
    maximumClinicalStage="APPROVAL",
)

_TRACTABILITY = [
    Tractability(modality="SM", label="Phase 4", value=True),
]

_SAFETY = [
    SafetyLiability(
        event="cardiac failure",
        datasource="toxcast",
        biosamples=[
            SafetyBiosample(
                tissueLabel="heart",
                tissueId="UBERON_0000948",
                cellLabel=None,
                cellId=None,
            )
        ],
        effects=[
            SafetyEffect(direction="Activation/Increase/Upregulation", dosing=None)
        ],
    ),
]

_EXPRESSION = [
    TissueExpression(
        tissue=TissueInfo(id="UBERON_0000948", label="heart"),
        rna=RnaExpression(value=12.5, level=2, zscore=1, unit="TPM"),
        protein=ProteinExpression(level=1, reliability=True),
    ),
]

_CONSTRAINT = [
    GeneticConstraint(
        constraintType="lof",
        obs=5,
        exp=20.0,
        oe=0.25,
        oeLower=0.1,
        oeUpper=0.5,
        score=0.9,
    ),
]

_INDICATIONS = [
    DrugIndication(
        disease_id="EFO_0003060",
        disease_name="lung carcinoma",
        maxClinicalStage="APPROVAL",
    ),
]

_SEARCH = [
    SearchResult(id="ENSG00000146648", name="EGFR", entity="target", score=10.0),
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace the module-level _client with a MagicMock for every test."""
    mock = MagicMock()
    # Set return values for all SDK methods used by MCP tools
    mock.get_target.return_value = _TARGET
    mock.get_target_associations.return_value = [_ASSOCIATION]
    mock.get_target_drugs.return_value = [_DRUG]
    mock.get_target_tractability.return_value = _TRACTABILITY
    mock.get_target_safety.return_value = _SAFETY
    mock.get_target_expression.return_value = _EXPRESSION
    mock.get_target_constraint.return_value = _CONSTRAINT
    mock.get_disease.return_value = _DISEASE
    mock.get_disease_targets.return_value = [_ASSOCIATION]
    mock.get_drug.return_value = _DRUG
    mock.get_drug_indications.return_value = _INDICATIONS
    mock.search.return_value = _SEARCH

    monkeypatch.setattr(_mod, "_client", mock)
    return mock


# ---------------------------------------------------------------------------
# Registration checks — every named tool must be registered
# ---------------------------------------------------------------------------

_EXPECTED_TOOL_NAMES = {
    "get_target_info",
    "find_target_associations",
    "get_target_drugs",
    "get_target_tractability",
    "get_target_safety",
    "get_target_expression",
    "get_target_constraint",
    "get_disease_info",
    "find_disease_targets",
    "get_drug_info",
    "get_drug_indications",
    "search_open_targets",
}


def test_all_tools_registered() -> None:
    """Every expected tool name must appear in mcp.list_tools()."""

    async def _list() -> list[str]:
        tools = await _mod.mcp.list_tools()
        return [t.name for t in tools]

    registered = asyncio.run(_list())
    missing = _EXPECTED_TOOL_NAMES - set(registered)
    assert not missing, f"Tools not registered: {missing}"


# ---------------------------------------------------------------------------
# Individual tool call tests
# ---------------------------------------------------------------------------


def _is_json_serializable(obj: Any) -> bool:
    import json

    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False


def test_get_target_info_returns_dict(mock_client: MagicMock) -> None:
    result = _mod.get_target_info("EGFR")
    assert isinstance(result, dict)
    assert result["id"] == "ENSG00000146648"
    assert result["approved_symbol"] == "EGFR"
    assert _is_json_serializable(result)
    mock_client.get_target.assert_called_once_with("EGFR")


def test_get_target_info_not_found(mock_client: MagicMock) -> None:
    mock_client.get_target.side_effect = NotFoundError("target", "DOESNOTEXIST")
    with pytest.raises(ValueError, match="target not found"):
        _mod.get_target_info("DOESNOTEXIST")


def test_find_target_associations_returns_list(mock_client: MagicMock) -> None:
    result = _mod.find_target_associations("EGFR")
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["score"] == 0.75
    assert _is_json_serializable(result)
    mock_client.get_target_associations.assert_called_once_with("EGFR", limit=25)


def test_find_target_associations_not_found(mock_client: MagicMock) -> None:
    mock_client.get_target_associations.side_effect = NotFoundError("target", "BAD")
    with pytest.raises(ValueError, match="target not found"):
        _mod.find_target_associations("BAD")


def test_get_target_drugs_returns_list(mock_client: MagicMock) -> None:
    result = _mod.get_target_drugs("EGFR")
    assert isinstance(result, list)
    assert result[0]["name"] == "ERLOTINIB"
    assert _is_json_serializable(result)


def test_get_target_drugs_not_found(mock_client: MagicMock) -> None:
    mock_client.get_target_drugs.side_effect = NotFoundError("target", "BAD")
    with pytest.raises(ValueError, match="target not found"):
        _mod.get_target_drugs("BAD")


def test_get_target_tractability_returns_list(mock_client: MagicMock) -> None:
    result = _mod.get_target_tractability("EGFR")
    assert isinstance(result, list)
    assert result[0]["modality"] == "SM"
    assert _is_json_serializable(result)


def test_get_target_safety_returns_list(mock_client: MagicMock) -> None:
    result = _mod.get_target_safety("EGFR")
    assert isinstance(result, list)
    assert result[0]["event"] == "cardiac failure"
    assert _is_json_serializable(result)


def test_get_target_expression_returns_list(mock_client: MagicMock) -> None:
    result = _mod.get_target_expression("EGFR")
    assert isinstance(result, list)
    assert result[0]["tissue"]["label"] == "heart"
    assert _is_json_serializable(result)


def test_get_target_constraint_returns_list(mock_client: MagicMock) -> None:
    result = _mod.get_target_constraint("EGFR")
    assert isinstance(result, list)
    assert result[0]["constraint_type"] == "lof"
    assert _is_json_serializable(result)


def test_get_disease_info_returns_dict(mock_client: MagicMock) -> None:
    result = _mod.get_disease_info("EFO_0003060")
    assert isinstance(result, dict)
    assert result["id"] == "EFO_0003060"
    assert result["name"] == "lung carcinoma"
    assert _is_json_serializable(result)
    mock_client.get_disease.assert_called_once_with("EFO_0003060")


def test_get_disease_info_not_found(mock_client: MagicMock) -> None:
    mock_client.get_disease.side_effect = NotFoundError("disease", "EFO_9999999")
    with pytest.raises(ValueError, match="disease not found"):
        _mod.get_disease_info("EFO_9999999")


def test_find_disease_targets_returns_list(mock_client: MagicMock) -> None:
    result = _mod.find_disease_targets("EFO_0003060")
    assert isinstance(result, list)
    assert result[0]["target_symbol"] == "EGFR"
    assert _is_json_serializable(result)


def test_find_disease_targets_min_score_filter(mock_client: MagicMock) -> None:
    """Associations below min_score must be filtered out client-side."""
    result = _mod.find_disease_targets("EFO_0003060", min_score=0.9)
    # _ASSOCIATION has score 0.75, which is below 0.9
    assert result == []


def test_find_disease_targets_not_found(mock_client: MagicMock) -> None:
    mock_client.get_disease_targets.side_effect = NotFoundError("disease", "BAD")
    with pytest.raises(ValueError, match="disease not found"):
        _mod.find_disease_targets("BAD")


def test_get_drug_info_returns_dict(mock_client: MagicMock) -> None:
    result = _mod.get_drug_info("CHEMBL939")
    assert isinstance(result, dict)
    assert result["id"] == "CHEMBL939"
    assert result["name"] == "ERLOTINIB"
    assert _is_json_serializable(result)
    mock_client.get_drug.assert_called_once_with("CHEMBL939")


def test_get_drug_info_not_found(mock_client: MagicMock) -> None:
    mock_client.get_drug.side_effect = NotFoundError("drug", "CHEMBL0000000")
    with pytest.raises(ValueError, match="drug not found"):
        _mod.get_drug_info("CHEMBL0000000")


def test_get_drug_indications_returns_list(mock_client: MagicMock) -> None:
    result = _mod.get_drug_indications("CHEMBL939")
    assert isinstance(result, list)
    assert result[0]["disease_name"] == "lung carcinoma"
    assert _is_json_serializable(result)


def test_get_drug_indications_not_found(mock_client: MagicMock) -> None:
    mock_client.get_drug_indications.side_effect = NotFoundError("drug", "BAD")
    with pytest.raises(ValueError, match="drug not found"):
        _mod.get_drug_indications("BAD")


def test_search_open_targets_returns_list(mock_client: MagicMock) -> None:
    result = _mod.search_open_targets("EGFR")
    assert isinstance(result, list)
    assert result[0]["name"] == "EGFR"
    assert result[0]["entity_type"] == "target"
    assert _is_json_serializable(result)
    mock_client.search.assert_called_once_with("EGFR")
