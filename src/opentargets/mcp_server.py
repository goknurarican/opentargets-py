"""MCP server exposing the Open Targets SDK as tools for AI assistants.

Run as a standalone server::

    python -m opentargets.mcp_server
    # or, after pip install opentargets-py[mcp]:
    opentargets-mcp

Configure in Claude Desktop::

    {
      "mcpServers": {
        "opentargets": {
          "command": "opentargets-mcp"
        }
      }
    }
"""

from __future__ import annotations

from typing import Any, cast

import fastmcp

from .client import OpenTargetsClient
from .exceptions import NotFoundError

# ---------------------------------------------------------------------------
# Module-level client — long-lived process, one instance is fine.
# Cache is enabled with default 5-minute TTL.
# ---------------------------------------------------------------------------
_client = OpenTargetsClient()

mcp = fastmcp.FastMCP("opentargets")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _dump_model(obj: Any) -> dict[str, Any]:
    """Return a JSON-serialisable dict from a Pydantic model."""
    return cast(dict[str, Any], obj.model_dump(mode="json"))


# ---------------------------------------------------------------------------
# Target tools
# ---------------------------------------------------------------------------


@mcp.tool
def get_target_info(gene_symbol_or_ensembl_id: str) -> dict[str, Any]:
    """Fetch detailed information about a drug target from Open Targets.

    Accepts either a gene symbol or an Ensembl gene ID.  The result includes
    the approved name, biotype, and functional descriptions curated from
    Ensembl and UniProt.

    Args:
        gene_symbol_or_ensembl_id: Gene symbol (e.g. ``EGFR``, ``BRAF``) or
            Ensembl ID (e.g. ``ENSG00000146648``).

    Returns:
        Dictionary with fields ``id``, ``approved_symbol``, ``approved_name``,
        ``biotype``, ``description``, and ``function_descriptions``.

    Raises:
        ValueError: If the target cannot be found.
    """
    try:
        target = _client.get_target(gene_symbol_or_ensembl_id)
    except NotFoundError:
        raise ValueError(f"target not found: {gene_symbol_or_ensembl_id}") from None
    return _dump_model(target)


@mcp.tool
def find_target_associations(
    target_id: str,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Find diseases associated with a gene target in Open Targets.

    Returns the top associations ranked by overall association score.  Each
    entry contains the disease name, EFO ID, overall score, and per-datasource
    scores (genetics, CRISPR screens, literature, etc.).

    Args:
        target_id: Ensembl ID or gene symbol, e.g. ``EGFR`` or
            ``ENSG00000146648``.
        limit: Maximum number of associations to return (default 25).

    Returns:
        List of association dicts, each with ``target_id``, ``target_symbol``,
        ``disease_id``, ``disease_name``, ``score``, and ``datasource_scores``.

    Raises:
        ValueError: If the target cannot be found.
    """
    try:
        assocs = _client.get_target_associations(target_id, limit=limit)
    except NotFoundError:
        raise ValueError(f"target not found: {target_id}") from None
    return [_dump_model(a) for a in assocs]


@mcp.tool
def get_target_drugs(target_id: str) -> list[dict[str, Any]]:
    """List drugs that interact with a gene target in Open Targets.

    Returns all approved drugs and clinical candidates with their mechanism of
    action, drug type, synonyms, trade names, and maximum clinical trial phase.

    Args:
        target_id: Ensembl ID or gene symbol, e.g. ``EGFR`` or
            ``ENSG00000146648``.

    Returns:
        List of drug dicts, each with ``id`` (ChEMBL ID), ``name``,
        ``drug_type``, ``mechanism_of_action``, ``synonyms``, ``trade_names``,
        and ``max_clinical_trial_phase``.

    Raises:
        ValueError: If the target cannot be found.
    """
    try:
        drugs = _client.get_target_drugs(target_id)
    except NotFoundError:
        raise ValueError(f"target not found: {target_id}") from None
    return [_dump_model(d) for d in drugs]


@mcp.tool
def get_target_tractability(target_id: str) -> list[dict[str, Any]]:
    """Return tractability assessments for a gene target from Open Targets.

    Tractability data indicates how "druggable" a target is across different
    modalities (small molecules, antibodies, other clinical modalities).

    Args:
        target_id: Ensembl ID or gene symbol, e.g. ``EGFR`` or
            ``ENSG00000146648``.

    Returns:
        List of tractability dicts, each with ``modality`` (e.g. ``SM``,
        ``AB``, ``OC``), ``label``, and ``value`` (bool).

    Raises:
        ValueError: If the target cannot be found.
    """
    try:
        items = _client.get_target_tractability(target_id)
    except NotFoundError:
        raise ValueError(f"target not found: {target_id}") from None
    return [_dump_model(t) for t in items]


@mcp.tool
def get_target_safety(target_id: str) -> list[dict[str, Any]]:
    """Return safety liability information for a gene target from Open Targets.

    Aggregates safety-relevant observations (adverse events, toxicology studies,
    etc.) across multiple datasources.

    Args:
        target_id: Ensembl ID or gene symbol, e.g. ``EGFR`` or
            ``ENSG00000146648``.

    Returns:
        List of safety liability dicts, each with ``event``, ``datasource``,
        ``biosamples``, ``effects``, ``literature``, ``url``, and ``event_id``.

    Raises:
        ValueError: If the target cannot be found.
    """
    try:
        items = _client.get_target_safety(target_id)
    except NotFoundError:
        raise ValueError(f"target not found: {target_id}") from None
    return [_dump_model(s) for s in items]


@mcp.tool
def get_target_expression(target_id: str) -> list[dict[str, Any]]:
    """Return baseline tissue expression data for a gene target from Open Targets.

    Provides RNA and protein expression levels across hundreds of tissues and
    cell types, sourced from GTEx, HPA, and RNA-seq baselines.

    Args:
        target_id: Ensembl ID or gene symbol, e.g. ``EGFR`` or
            ``ENSG00000146648``.

    Returns:
        List of tissue expression dicts, each with ``tissue`` (id + label),
        ``rna`` (value, level, zscore, unit), and ``protein`` (level,
        reliability).

    Raises:
        ValueError: If the target cannot be found.
    """
    try:
        items = _client.get_target_expression(target_id)
    except NotFoundError:
        raise ValueError(f"target not found: {target_id}") from None
    return [_dump_model(e) for e in items]


@mcp.tool
def get_target_constraint(target_id: str) -> list[dict[str, Any]]:
    """Return gnomAD genetic constraint metrics for a gene target from Open Targets.

    Constraint scores (pLI, Z-scores) indicate how much a gene tolerates
    functional variation in the human population.  A high pLI score (close to 1)
    suggests the gene is intolerant of loss-of-function variants.

    Args:
        target_id: Ensembl ID or gene symbol, e.g. ``EGFR`` or
            ``ENSG00000146648``.

    Returns:
        List of constraint dicts — typically one each for ``syn``
        (synonymous), ``mis`` (missense), and ``lof`` (loss-of-function) —
        with fields ``constraint_type``, ``obs``, ``exp``, ``oe``,
        ``oe_lower``, ``oe_upper``, and ``score``.

    Raises:
        ValueError: If the target cannot be found.
    """
    try:
        items = _client.get_target_constraint(target_id)
    except NotFoundError:
        raise ValueError(f"target not found: {target_id}") from None
    return [_dump_model(c) for c in items]


# ---------------------------------------------------------------------------
# Disease tools
# ---------------------------------------------------------------------------


@mcp.tool
def get_disease_info(disease_id: str) -> dict[str, Any]:
    """Fetch detailed information about a disease from Open Targets.

    Args:
        disease_id: EFO identifier, e.g. ``EFO_0000311`` (cancer),
            ``EFO_0003060`` (lung carcinoma), or ``EFO_0000270`` (asthma).

    Returns:
        Dictionary with ``id``, ``name``, ``description``,
        ``therapeutic_areas``, and ``db_x_refs``.

    Raises:
        ValueError: If the disease cannot be found.
    """
    try:
        disease = _client.get_disease(disease_id)
    except NotFoundError:
        raise ValueError(f"disease not found: {disease_id}") from None
    return _dump_model(disease)


@mcp.tool
def find_disease_targets(
    disease_id: str,
    min_score: float = 0.0,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Find gene targets associated with a disease in Open Targets.

    Returns associations ranked by overall evidence score, optionally filtered
    to a minimum score threshold.  Useful for identifying which genes are most
    strongly linked to a given condition.

    Args:
        disease_id: EFO identifier, e.g. ``EFO_0000311`` (cancer),
            ``EFO_0003060`` (lung carcinoma).
        min_score: Minimum overall association score (0.0-1.0).  Filters out
            low-confidence associations.  Default is ``0.0`` (no filter).
        limit: Maximum number of associations to return (default 25).

    Returns:
        List of association dicts with ``target_id``, ``target_symbol``,
        ``disease_id``, ``disease_name``, ``score``, and ``datasource_scores``.

    Raises:
        ValueError: If the disease cannot be found.
    """
    try:
        assocs = _client.get_disease_targets(disease_id, limit=limit)
    except NotFoundError:
        raise ValueError(f"disease not found: {disease_id}") from None
    filtered = [a for a in assocs if a.score >= min_score]
    return [_dump_model(a) for a in filtered]


# ---------------------------------------------------------------------------
# Drug tools
# ---------------------------------------------------------------------------


@mcp.tool
def get_drug_info(drug_id: str) -> dict[str, Any]:
    """Fetch detailed information about a drug from Open Targets.

    Args:
        drug_id: ChEMBL identifier, e.g. ``CHEMBL941`` (imatinib),
            ``CHEMBL939`` (erlotinib), ``CHEMBL1201567`` (trastuzumab).

    Returns:
        Dictionary with ``id``, ``name``, ``drug_type``,
        ``mechanism_of_action``, ``synonyms``, ``trade_names``,
        and ``max_clinical_trial_phase``.

    Raises:
        ValueError: If the drug cannot be found.
    """
    try:
        drug = _client.get_drug(drug_id)
    except NotFoundError:
        raise ValueError(f"drug not found: {drug_id}") from None
    return _dump_model(drug)


@mcp.tool
def get_drug_indications(drug_id: str) -> list[dict[str, Any]]:
    """Return disease indications for a drug from Open Targets.

    Lists all diseases for which the drug has been investigated in clinical
    trials, along with the maximum phase reached per indication.

    Args:
        drug_id: ChEMBL identifier, e.g. ``CHEMBL941`` (imatinib),
            ``CHEMBL939`` (erlotinib).

    Returns:
        List of indication dicts, each with ``disease_id``, ``disease_name``,
        and ``max_phase_for_indication``.

    Raises:
        ValueError: If the drug cannot be found.
    """
    try:
        indications = _client.get_drug_indications(drug_id)
    except NotFoundError:
        raise ValueError(f"drug not found: {drug_id}") from None
    return [_dump_model(i) for i in indications]


# ---------------------------------------------------------------------------
# Search tool
# ---------------------------------------------------------------------------


@mcp.tool
def search_open_targets(query: str) -> list[dict[str, Any]]:
    """Search the Open Targets Platform for targets, diseases, or drugs.

    Performs a free-text search across all entity types.  Useful when you
    know a name but not the exact identifier (Ensembl ID, EFO ID, ChEMBL ID).

    Args:
        query: Free-text search string, e.g. ``"EGFR"``, ``"lung cancer"``,
            ``"imatinib"``, ``"BRCA1 breast"``.

    Returns:
        List of search result dicts, each with ``id`` (the entity identifier),
        ``name``, ``entity_type`` (``target``, ``disease``, or ``drug``),
        ``description``, and ``score`` (relevance score).
    """
    results = _client.search(query)
    return [_dump_model(r) for r in results]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the MCP server (stdio transport by default)."""
    mcp.run()


if __name__ == "__main__":
    main()
