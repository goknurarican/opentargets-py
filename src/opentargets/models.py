"""Pydantic v2 response models for the Open Targets Platform API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _OTBaseModel(BaseModel):
    """Base for Open Targets response models.

    Coerces ``None`` to ``""`` for any field annotated as ``str`` with a
    default of ``""``. The GraphQL API explicitly returns ``null`` for some
    description/name-style fields (e.g. ``description`` on ``study`` search
    hits), which would otherwise fail Pydantic's strict string validation.
    Required string fields are left alone — a null there is a real error.
    """

    @model_validator(mode="before")
    @classmethod
    def _none_str_to_empty(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        for name, field in cls.model_fields.items():
            if field.annotation is str and field.default == "":
                for key in (field.alias, name):
                    if key and key in data and data[key] is None:
                        data[key] = ""
        return data


class Target(_OTBaseModel):
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


class Disease(_OTBaseModel):
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


class Drug(_OTBaseModel):
    """A drug or compound from the Open Targets Platform.

    Attributes:
        id: ChEMBL identifier (e.g. "CHEMBL939").
        name: Drug name.
        drug_type: Molecule type (e.g. "Small molecule").
        mechanism_of_action: Pharmacological mechanism string.
        synonyms: Alternative drug names.
        trade_names: Commercial brand names.
        max_clinical_trial_phase: Highest phase reached in clinical trials (0-4).
        chembl_ids: ChEMBL IDs extracted from ``crossReferences``.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str
    name: str
    drug_type: str = Field("", alias="drugType")
    mechanism_of_action: str = ""
    synonyms: list[str] = Field(default_factory=list)
    trade_names: list[str] = Field(default_factory=list, alias="tradeNames")
    max_clinical_trial_phase: Optional[str] = Field(None, alias="maximumClinicalStage")
    chembl_ids: list[str] = Field(default_factory=list)


class DatasourceScore(_OTBaseModel):
    """A per-datasource association score.

    Attributes:
        id: Datasource identifier (e.g. "ot_genetics_portal").
        score: Numeric score between 0 and 1.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    score: float


class Association(_OTBaseModel):
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


class SearchResult(_OTBaseModel):
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


class DrugIndication(_OTBaseModel):
    """A disease indication for a given drug.

    Attributes:
        disease_id: EFO identifier.
        disease_name: Disease name.
        max_phase_for_indication: Highest clinical trial phase for this indication.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    disease_id: str = ""
    disease_name: str = ""
    max_phase_for_indication: Optional[str] = Field(None, alias="maxClinicalStage")


# ---------------------------------------------------------------------------
# New models for the 5 additional endpoints
# ---------------------------------------------------------------------------


class Tractability(_OTBaseModel):
    """A tractability assessment for a target.

    Attributes:
        modality: Modality type (e.g. "SM", "AB", "OC").
        label: Human-readable tractability label.
        value: Whether the target meets this tractability criterion.
    """

    model_config = ConfigDict(frozen=True)

    modality: str
    label: str
    value: bool


class SafetyBiosample(_OTBaseModel):
    """Biosample information from a safety liability entry.

    Attributes:
        tissue_label: Tissue label from the biosample.
        tissue_id: Tissue ontology ID.
        cell_label: Cell type label.
        cell_id: Cell ontology ID.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    tissue_label: Optional[str] = Field(None, alias="tissueLabel")
    tissue_id: Optional[str] = Field(None, alias="tissueId")
    cell_label: Optional[str] = Field(None, alias="cellLabel")
    cell_id: Optional[str] = Field(None, alias="cellId")


class SafetyEffect(_OTBaseModel):
    """An effect associated with a safety liability entry.

    Attributes:
        direction: Direction of effect (e.g. "Activation/Increase/Upregulation").
        dosing: Dosing information if available.
    """

    model_config = ConfigDict(frozen=True)

    direction: Optional[str] = None
    dosing: Optional[str] = None


class SafetyLiability(_OTBaseModel):
    """A safety liability entry for a target.

    Attributes:
        event: Safety event description.
        datasource: Data source name.
        biosamples: List of relevant biosamples.
        effects: List of associated effects.
        literature: PubMed/literature reference.
        url: URL for further information.
        event_id: Optional event identifier.
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    event: Optional[str] = None
    datasource: str
    biosamples: list[SafetyBiosample] = Field(default_factory=list)
    effects: list[SafetyEffect] = Field(default_factory=list)
    literature: Optional[str] = None
    url: Optional[str] = None
    event_id: Optional[str] = Field(None, alias="eventId")


class TissueInfo(_OTBaseModel):
    """Tissue identity from expression data.

    Attributes:
        id: Tissue ontology ID.
        label: Human-readable tissue label.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    label: str


class RnaExpression(_OTBaseModel):
    """RNA expression values for a tissue.

    Attributes:
        value: Expression value (e.g. TPM or RPKM).
        level: Discretised expression level (0–4).
        zscore: Z-score relative to other tissues.
        unit: Unit of expression value.
    """

    model_config = ConfigDict(frozen=True)

    value: float
    level: int
    zscore: int
    unit: str


class ProteinExpression(_OTBaseModel):
    """Protein expression values for a tissue.

    Attributes:
        level: Discretised protein expression level.
        reliability: Whether the antibody used is reliable.
    """

    model_config = ConfigDict(frozen=True)

    level: int
    reliability: bool


class TissueExpression(_OTBaseModel):
    """Baseline tissue expression for a target.

    Attributes:
        tissue: Tissue identity.
        rna: RNA expression data.
        protein: Protein expression data.
    """

    model_config = ConfigDict(frozen=True)

    tissue: TissueInfo
    rna: RnaExpression
    protein: ProteinExpression


class GeneticConstraint(_OTBaseModel):
    """gnomAD genetic constraint metric for a target.

    Attributes:
        constraint_type: Type of constraint (``syn``, ``mis``, ``lof``).
        obs: Observed variant count.
        exp: Expected variant count.
        oe: Observed/expected ratio.
        oe_lower: Lower 95 % CI for oe ratio.
        oe_upper: Upper 95 % CI for oe ratio.
        score: Constraint score (pLI-equivalent for lof).
    """

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    constraint_type: str = Field(alias="constraintType")
    obs: Optional[int] = None
    exp: Optional[float] = None
    oe: Optional[float] = None
    oe_lower: Optional[float] = Field(None, alias="oeLower")
    oe_upper: Optional[float] = Field(None, alias="oeUpper")
    score: Optional[float] = None
