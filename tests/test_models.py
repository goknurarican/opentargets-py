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


def test_search_result_null_description_coerced():
    # API returns null description for some hit types (e.g. study).
    sr = SearchResult.model_validate(
        {"id": "GCST1", "name": "study", "entity": "study", "description": None}
    )
    assert sr.description == ""


def test_target_null_description_coerced():
    t = Target.model_validate(
        {
            "id": "ENSG1",
            "approvedSymbol": "X",
            "approvedName": "x",
            "biotype": None,
            "description": None,
        }
    )
    assert t.biotype == ""
    assert t.description == ""


def test_disease_null_description_coerced():
    d = Disease.model_validate({"id": "EFO1", "name": "d", "description": None})
    assert d.description == ""


def test_drug_null_string_fields_coerced():
    dr = Drug.model_validate(
        {"id": "C1", "name": "x", "drugType": None, "mechanism_of_action": None}
    )
    assert dr.drug_type == ""
    assert dr.mechanism_of_action == ""
