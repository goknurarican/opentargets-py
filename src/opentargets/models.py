"""Pydantic v2 response models for the Open Targets Platform API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Target(BaseModel):
    """A drug target (gene/protein) from the Open Targets Platform.

    Attributes:
        id: Ensembl gene ID (e.g. "ENSG00000146648").
        approved_symbol: HGNC-approved gene symbol (e.g. "EGFR").
        approved_name: Full gene name.
        biotype: Ensembl biotype (e.g. "protein_coding").
        description: Short description from Ensembl.
        function_descriptions: List of functional annotation strings.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    approved_symbol: str = Field(alias="approvedSymbol")
    approved_name: str = Field(alias="approvedName")
    biotype: str = ""
    description: str = ""
    function_descriptions: list[str] = Field(
        default_factory=list, alias="functionDescriptions"
    )

    model_config = ConfigDict(frozen=True, populate_by_name=True)


class Disease(BaseModel):
    """A disease or phenotype from the Open Targets Platform.

    Attributes:
        id: EFO identifier (e.g. "EFO_0003060").
        name: Disease name.
        description: Plain-text description.
        therapeutic_areas: List of broad therapeutic area names.
        db_x_refs: Cross-references to external databases.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str
    name: str
    description: str = ""
    therapeutic_areas: list[str] = Field(default_factory=list, alias="therapeuticAreas")
    db_x_refs: list[str] = Field(default_factory=list, alias="dbXRefs")


class Drug(BaseModel):
    """A drug or compound from the Open Targets Platform.

    Attributes:
        id: ChEMBL identifier (e.g. "CHEMBL939").
        name: Drug name.
        drug_type: Molecule type (e.g. "Small molecule").
        mechanism_of_action: Pharmacological mechanism string.
        synonyms: Alternative drug names.
        trade_names: Commercial brand names.
        max_clinical_trial_phase: Highest phase reached in clinical trials (0-4).
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str
    name: str
    drug_type: str = Field("", alias="drugType")
    mechanism_of_action: str = Field("", alias="mechanismOfAction")
    synonyms: list[str] = Field(default_factory=list)
    trade_names: list[str] = Field(default_factory=list, alias="tradeNames")
    max_clinical_trial_phase: Optional[float] = Field(
        None, alias="maximumClinicalTrialPhase"
    )


class DatasourceScore(BaseModel):
    """A per-datasource association score.

    Attributes:
        id: Datasource identifier (e.g. "ot_genetics_portal").
        score: Numeric score between 0 and 1.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    score: float


class Association(BaseModel):
    """A target–disease association with evidence scores.

    Attributes:
        target_id: Ensembl gene ID of the associated target.
        target_symbol: Gene symbol of the associated target.
        disease_id: EFO identifier of the associated disease.
        disease_name: Name of the associated disease.
        score: Overall association score (0–1).
        datasource_scores: Per-datasource evidence scores.
        evidence_count: Total number of supporting evidence items.
    """

    model_config = ConfigDict(frozen=True)

    target_id: str = ""
    target_symbol: str = ""
    disease_id: str = ""
    disease_name: str = ""
    score: float = 0.0
    datasource_scores: list[DatasourceScore] = Field(default_factory=list)
    evidence_count: int = 0


class SearchResult(BaseModel):
    """A single result from the platform-wide search endpoint.

    Attributes:
        id: Entity identifier.
        name: Display name.
        entity_type: One of "target", "disease", "drug".
        description: Short description.
        score: Search relevance score.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str
    name: str
    entity_type: str = Field("", alias="entity")
    description: str = ""
    score: float = 0.0


class DrugIndication(BaseModel):
    """A disease indication for a given drug.

    Attributes:
        disease_id: EFO identifier.
        disease_name: Disease name.
        max_phase_for_indication: Highest clinical trial phase for this indication.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    disease_id: str = ""
    disease_name: str = ""
    max_phase_for_indication: Optional[float] = Field(
        None, alias="maxPhaseForIndication"
    )
