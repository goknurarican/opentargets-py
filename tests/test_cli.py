"""Tests for the opentargets CLI."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from opentargets.cli import app
from opentargets.models import (
    Association,
    DatasourceScore,
    Disease,
    Drug,
    DrugIndication,
    GeneticConstraint,
    SearchResult,
    Target,
    Tractability,
)

runner = CliRunner()

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

MOCK_TARGET = Target.model_validate(
    {
        "id": "ENSG00000146648",
        "approvedSymbol": "EGFR",
        "approvedName": "epidermal growth factor receptor",
        "biotype": "protein_coding",
        "description": "Receptor tyrosine kinase.",
        "functionDescriptions": ["Receptor tyrosine kinase"],
    }
)

MOCK_DISEASE = Disease.model_validate(
    {
        "id": "EFO_0003060",
        "name": "lung carcinoma",
        "description": "A type of lung cancer.",
        "therapeuticAreas": ["oncology"],
        "dbXRefs": ["OMIM:211980"],
    }
)

MOCK_DRUG = Drug.model_validate(
    {
        "id": "CHEMBL939",
        "name": "ERLOTINIB",
        "drugType": "Small molecule",
        "mechanism_of_action": "EGFR inhibitor",
        "synonyms": ["Tarceva"],
        "tradeNames": ["Tarceva"],
        "maximumClinicalStage": "APPROVAL",
    }
)

MOCK_ASSOCIATION = Association(
    target_id="ENSG00000146648",
    target_symbol="EGFR",
    disease_id="EFO_0003060",
    disease_name="lung carcinoma",
    score=0.75,
    datasource_scores=[DatasourceScore(id="ot_genetics_portal", score=0.6)],
)

MOCK_SEARCH = SearchResult.model_validate(
    {
        "id": "ENSG00000146648",
        "entity": "target",
        "name": "EGFR",
        "description": "epidermal growth factor receptor",
        "score": 10.0,
    }
)

MOCK_TRACTABILITY = Tractability(modality="SM", label="High Quality Ligand", value=True)

MOCK_CONSTRAINT = GeneticConstraint.model_validate(
    {
        "constraintType": "lof",
        "obs": 5,
        "exp": 45.2,
        "oe": 0.11,
        "oeLower": 0.04,
        "oeUpper": 0.27,
        "score": 0.99,
    }
)

MOCK_DRUG_INDICATION = DrugIndication.model_validate(
    {
        "disease_id": "EFO_0003060",
        "disease_name": "lung carcinoma",
        "maxClinicalStage": "APPROVAL",
    }
)


def _mock_client(**overrides: Any) -> MagicMock:
    """Return a MagicMock that stands in for OpenTargetsClient."""
    m = MagicMock()
    m.get_target.return_value = MOCK_TARGET
    m.get_targets.return_value = [MOCK_TARGET]
    m.get_target_associations.return_value = [MOCK_ASSOCIATION]
    m.get_target_drugs.return_value = [MOCK_DRUG]
    m.get_target_tractability.return_value = [MOCK_TRACTABILITY]
    m.get_target_safety.return_value = []
    m.get_target_expression.return_value = []
    m.get_target_constraint.return_value = [MOCK_CONSTRAINT]
    m.get_disease.return_value = MOCK_DISEASE
    m.get_disease_targets.return_value = [MOCK_ASSOCIATION]
    m.get_drug.return_value = MOCK_DRUG
    m.get_drug_indications.return_value = [MOCK_DRUG_INDICATION]
    m.get_drug_chembl_ids.return_value = ["CHEMBL939"]
    m.search.return_value = [MOCK_SEARCH]
    for attr, val in overrides.items():
        setattr(m, attr, val)
    return m


# ---------------------------------------------------------------------------
# target
# ---------------------------------------------------------------------------


class TestTargetCommand:
    def test_json_output(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["target", "EGFR", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["approved_symbol"] == "EGFR"
        assert data["id"] == "ENSG00000146648"

    def test_human_output(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["target", "EGFR"])
        assert result.exit_code == 0, result.output
        assert "EGFR" in result.output
        assert "epidermal growth factor receptor" in result.output

    def test_with_associations_json(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["target", "EGFR", "--associations", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "associations" in data
        assert data["associations"][0]["disease_name"] == "lung carcinoma"

    def test_with_associations_human(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["target", "EGFR", "--associations"])
        assert result.exit_code == 0, result.output
        assert "lung carcinoma" in result.output

    def test_with_drugs_json(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["target", "EGFR", "--drugs", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "drugs" in data
        assert data["drugs"][0]["name"] == "ERLOTINIB"

    def test_with_tractability_json(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["target", "EGFR", "--tractability", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "tractability" in data
        assert data["tractability"][0]["modality"] == "SM"

    def test_with_constraint_human(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["target", "EGFR", "--constraint"])
        assert result.exit_code == 0, result.output
        assert "lof" in result.output

    def test_not_found_error(self) -> None:
        from opentargets.exceptions import NotFoundError

        mock = _mock_client()
        mock.get_target.side_effect = NotFoundError("target", "NOSUCHGENE")
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["target", "NOSUCHGENE"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# targets
# ---------------------------------------------------------------------------


class TestTargetsCommand:
    def test_json_output(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["targets", "EGFR", "BRAF", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["approved_symbol"] == "EGFR"

    def test_human_output(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["targets", "EGFR", "BRAF"])
        assert result.exit_code == 0, result.output
        assert "EGFR" in result.output
        assert "ENSG00000146648" in result.output


# ---------------------------------------------------------------------------
# disease
# ---------------------------------------------------------------------------


class TestDiseaseCommand:
    def test_json_output(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["disease", "EFO_0003060", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["id"] == "EFO_0003060"
        assert data["name"] == "lung carcinoma"

    def test_human_output(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["disease", "EFO_0003060"])
        assert result.exit_code == 0, result.output
        assert "lung carcinoma" in result.output

    def test_with_targets_json(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(
                app, ["disease", "EFO_0003060", "--targets", "--json"]
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "targets" in data
        assert data["targets"][0]["target_symbol"] == "EGFR"

    def test_with_targets_human(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["disease", "EFO_0003060", "--targets"])
        assert result.exit_code == 0, result.output
        assert "EGFR" in result.output

    def test_not_found_error(self) -> None:
        from opentargets.exceptions import NotFoundError

        mock = _mock_client()
        mock.get_disease.side_effect = NotFoundError("disease", "EFO_INVALID")
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["disease", "EFO_INVALID"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# drug
# ---------------------------------------------------------------------------


class TestDrugCommand:
    def test_json_output(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["drug", "CHEMBL939", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["id"] == "CHEMBL939"
        assert data["name"] == "ERLOTINIB"

    def test_human_output(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["drug", "CHEMBL939"])
        assert result.exit_code == 0, result.output
        assert "ERLOTINIB" in result.output

    def test_with_indications_json(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(
                app, ["drug", "CHEMBL939", "--indications", "--json"]
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "indications" in data
        assert data["indications"][0]["disease_name"] == "lung carcinoma"

    def test_with_indications_human(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["drug", "CHEMBL939", "--indications"])
        assert result.exit_code == 0, result.output
        assert "lung carcinoma" in result.output

    def test_with_chembl_ids_json(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["drug", "CHEMBL939", "--chembl-ids", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "chembl_ids" in data
        assert "CHEMBL939" in data["chembl_ids"]

    def test_not_found_error(self) -> None:
        from opentargets.exceptions import NotFoundError

        mock = _mock_client()
        mock.get_drug.side_effect = NotFoundError("drug", "CHEMBL000")
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["drug", "CHEMBL000"])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


class TestSearchCommand:
    def test_json_output(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["search", "lung cancer", "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["name"] == "EGFR"

    def test_human_output(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["search", "lung cancer"])
        assert result.exit_code == 0, result.output
        assert "EGFR" in result.output

    def test_with_entity_filter(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(
                app, ["search", "EGFR", "--entity", "target", "--json"]
            )
        assert result.exit_code == 0, result.output
        mock.search.assert_called_once_with("EGFR", entity_type="target", limit=10)


# ---------------------------------------------------------------------------
# associations
# ---------------------------------------------------------------------------


class TestAssociationsCommand:
    def test_json_output(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(
                app, ["associations", "EGFR", "--limit", "5", "--json"]
            )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["disease_name"] == "lung carcinoma"
        mock.get_target_associations.assert_called_once_with("EGFR", limit=5)

    def test_human_output(self) -> None:
        mock = _mock_client()
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["associations", "EGFR"])
        assert result.exit_code == 0, result.output
        assert "lung carcinoma" in result.output
        assert "EFO_0003060" in result.output

    def test_not_found_error(self) -> None:
        from opentargets.exceptions import NotFoundError

        mock = _mock_client()
        mock.get_target_associations.side_effect = NotFoundError("target", "NOSUCH")
        with patch("opentargets.cli.OpenTargetsClient", return_value=mock):
            result = runner.invoke(app, ["associations", "NOSUCH"])
        assert result.exit_code == 1
