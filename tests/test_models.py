"""Tests for Pydantic response models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from opentargets.models import (
    Association,
    DatasourceScore,
    Disease,
    Drug,
    SearchResult,
    Target,
)


def test_target_model_aliases():
    t = Target.model_validate(
        {
            "id": "ENSG00000146648",
            "approvedSymbol": "EGFR",
            "approvedName": "epidermal growth factor receptor",
            "biotype": "protein_coding",
            "functionDescriptions": ["Receptor TK"],
        }
    )
    assert t.approved_symbol == "EGFR"
    assert t.function_descriptions == ["Receptor TK"]


def test_target_is_frozen():
    t = Target.model_validate({"id": "X", "approvedSymbol": "X", "approvedName": "X"})
    with pytest.raises(ValidationError):
        t.id = "Y"  # type: ignore[misc]


def test_disease_therapeutic_areas_list():
    d = Disease.model_validate(
        {
            "id": "EFO_0003060",
            "name": "lung carcinoma",
            "therapeuticAreas": ["oncology"],
        }
    )
    assert d.therapeutic_areas == ["oncology"]


def test_drug_optional_fields_default():
    drug = Drug.model_validate({"id": "CHEMBL1", "name": "TestDrug"})
    assert drug.drug_type == ""
    assert drug.synonyms == []
    assert drug.max_clinical_trial_phase is None


def test_association_defaults():
    a = Association()
    assert a.score == 0.0
    assert a.datasource_scores == []


def test_datasource_score():
    ds = DatasourceScore(id="genetics_portal", score=0.9)
    assert ds.score == 0.9


def test_search_result_entity_alias():
    sr = SearchResult.model_validate(
        {
            "id": "ENSG1",
            "name": "EGFR",
            "entity": "target",
            "score": 5.0,
        }
    )
    assert sr.entity_type == "target"
