"""Shared pytest fixtures and mock response data."""

from __future__ import annotations

import pytest

TARGET_RAW = {
    "id": "ENSG00000146648",
    "approvedSymbol": "EGFR",
    "approvedName": "epidermal growth factor receptor",
    "biotype": "protein_coding",
    "functionDescriptions": ["Receptor tyrosine kinase"],
}

DISEASE_RAW = {
    "id": "EFO_0003060",
    "name": "lung carcinoma",
    "description": "A lung cancer.",
    "therapeuticAreas": [{"name": "oncology"}],
    "dbXRefs": ["OMIM:211980"],
}

DRUG_RAW = {
    "id": "CHEMBL939",
    "name": "ERLOTINIB",
    "drugType": "Small molecule",
    "mechanismOfAction": "EGFR inhibitor",
    "synonyms": ["Tarceva"],
    "tradeNames": ["Tarceva"],
    "maximumClinicalTrialPhase": 4.0,
}

ASSOCIATION_ROW = {
    "disease": {"id": "EFO_0003060", "name": "lung carcinoma"},
    "score": 0.75,
    "datasourceScores": [{"id": "ot_genetics_portal", "score": 0.6}],
}

SEARCH_HIT = {
    "id": "ENSG00000146648",
    "entity": "target",
    "name": "EGFR",
    "description": "epidermal growth factor receptor",
    "score": 10.0,
}


@pytest.fixture()
def target_response() -> dict:
    return {"data": {"target": TARGET_RAW}}


@pytest.fixture()
def targets_batch_response() -> dict:
    return {"data": {"targets": [TARGET_RAW]}}


@pytest.fixture()
def disease_response() -> dict:
    return {"data": {"disease": DISEASE_RAW}}


@pytest.fixture()
def drug_response() -> dict:
    return {"data": {"drug": DRUG_RAW}}


@pytest.fixture()
def search_response() -> dict:
    return {"data": {"search": {"total": 1, "hits": [SEARCH_HIT]}}}


@pytest.fixture()
def associations_response() -> dict:
    return {
        "data": {
            "target": {
                "id": "ENSG00000146648",
                "approvedSymbol": "EGFR",
                "associatedDiseases": {
                    "count": 1,
                    "rows": [ASSOCIATION_ROW],
                },
            }
        }
    }


@pytest.fixture()
def drug_indications_response() -> dict:
    return {
        "data": {
            "drug": {
                "id": "CHEMBL939",
                "name": "ERLOTINIB",
                "indications": {
                    "count": 1,
                    "rows": [
                        {
                            "maxPhaseForIndication": 4.0,
                            "disease": {"id": "EFO_0003060", "name": "lung carcinoma"},
                        }
                    ],
                },
            }
        }
    }
