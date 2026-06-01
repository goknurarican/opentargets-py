"""Main public client for the Open Targets Platform."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, cast

from ._cache import CacheBackend, TTLCache, _NoCache
from ._graphql import GraphQLClient
from ._queries.disease import DISEASE_QUERY, DISEASE_TARGETS_QUERY
from ._queries.drug import DRUG_CHEMBL_IDS_QUERY, DRUG_INDICATIONS_QUERY, DRUG_QUERY
from ._queries.search import SEARCH_QUERY
from ._queries.target import (
    TARGET_ASSOCIATIONS_QUERY,
    TARGET_CONSTRAINT_QUERY,
    TARGET_DRUGS_QUERY,
    TARGET_EXPRESSION_QUERY,
    TARGET_QUERY,
    TARGET_SAFETY_QUERY,
    TARGET_TRACTABILITY_QUERY,
    TARGETS_BATCH_QUERY,
)
from ._retry import DEFAULT_RETRY_CONFIG, RetryConfig
from .exceptions import NotFoundError
from .models import (
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

if TYPE_CHECKING:
    import pandas as pd

_DEFAULT_URL = "https://api.platform.opentargets.org/api/v4/graphql"


class OpenTargetsClient:
    """Synchronous client for the Open Targets Platform GraphQL API.

    Args:
        base_url: GraphQL endpoint. Override for self-hosted instances.
        timeout: HTTP timeout in seconds.
        cache: Set to ``False`` to disable in-memory caching.
        cache_ttl: Cache entry lifetime in seconds (default 5 min).

    Example::

        from opentargets import OpenTargetsClient

        client = OpenTargetsClient()
        target = client.get_target("EGFR")
        print(target.approved_name)
    """

    def __init__(
        self,
        base_url: str = _DEFAULT_URL,
        timeout: float = 30.0,
        cache: bool | CacheBackend = True,
        cache_ttl: float = 300.0,
        retry_config: Optional[RetryConfig] = None,
    ) -> None:
        self._gql = GraphQLClient(
            base_url=base_url,
            timeout=timeout,
            retry_config=retry_config
            if retry_config is not None
            else DEFAULT_RETRY_CONFIG,
        )
        if isinstance(cache, bool):
            _sym: CacheBackend = TTLCache(ttl=cache_ttl) if cache else _NoCache()
            _res: CacheBackend = TTLCache(ttl=cache_ttl) if cache else _NoCache()
        else:
            _sym = cache
            _res = cache
        self._symbol_cache = _sym
        self._result_cache = _res

    # ------------------------------------------------------------------
    # Target queries
    # ------------------------------------------------------------------

    def get_target(self, target_id: str) -> Target:
        """Return core annotations for a single gene target.

        Retrieves approved name, biotype, and functional descriptions for the
        given target. Accepts either an Ensembl stable ID or an HGNC gene
        symbol; symbols are resolved automatically via a search call.

        Args:
            target_id: Ensembl gene ID like ``'ENSG00000146648'`` or HGNC
                symbol like ``'EGFR'``.

        Returns:
            A :class:`~opentargets.models.Target` instance.

        Raises:
            NotFoundError: If no target matches *target_id*.

        Example::

            client = OpenTargetsClient()
            target = client.get_target("EGFR")
            print(target.approved_name)  # epidermal growth factor receptor
            print(target.id)             # ENSG00000146648
        """
        ensembl_id = self._resolve_target(target_id)
        cache_key = f"target:{ensembl_id}"
        cached = self._result_cache.get(cache_key)
        if cached is not None:
            return cast(Target, cached)

        data = self._gql.execute(TARGET_QUERY, {"ensemblId": ensembl_id})
        raw = data.get("target")
        if not raw:
            raise NotFoundError("target", target_id)
        target = _parse_target(raw)
        self._result_cache.set(cache_key, target)
        return target

    def get_targets(self, target_ids: list[str]) -> list[Target]:
        """Return core annotations for multiple gene targets in one API call.

        More efficient than calling :meth:`get_target` in a loop when you
        already have a list of identifiers.

        Args:
            target_ids: List of Ensembl gene IDs like ``'ENSG00000146648'`` or
                HGNC symbols like ``'EGFR'``. Mixed formats are accepted.

        Returns:
            List of :class:`~opentargets.models.Target` instances in the same
            order as *target_ids* (targets not found are silently omitted).

        Example::

            client = OpenTargetsClient()
            targets = client.get_targets(["EGFR", "BRAF", "TP53"])
            for t in targets:
                print(t.approved_symbol, t.biotype)
        """
        ensembl_ids = [self._resolve_target(t) for t in target_ids]
        data = self._gql.execute(TARGETS_BATCH_QUERY, {"ids": ensembl_ids})
        raws: list[dict[str, Any]] = data.get("targets") or []
        by_id = {r["id"]: _parse_target(r) for r in raws}
        return [by_id[eid] for eid in ensembl_ids if eid in by_id]

    def get_target_associations(
        self,
        target_id: str,
        limit: int = 25,
        as_dataframe: bool = False,
    ) -> list[Association] | pd.DataFrame:
        """Return diseases associated with a target, ranked by association score.

        Each association includes an overall score (0–1) and per-datasource
        scores (genetics, literature, clinical trials, etc.). Results are
        ordered by descending overall score.

        Args:
            target_id: Ensembl gene ID like ``'ENSG00000146648'`` or HGNC
                symbol like ``'EGFR'``.
            limit: Maximum number of associations to return (default ``25``).
            as_dataframe: When ``True``, return a flat ``pandas.DataFrame``
                instead of a list of model objects. Requires ``pandas``.

        Returns:
            List of :class:`~opentargets.models.Association` objects, or a
            ``pandas.DataFrame`` when *as_dataframe* is ``True``.

        Example::

            client = OpenTargetsClient()
            assocs = client.get_target_associations("EGFR", limit=5)
            for a in assocs:
                print(a.disease_name, round(a.score, 3))
        """
        ensembl_id = self._resolve_target(target_id)
        rows = self._gql.paginate(
            TARGET_ASSOCIATIONS_QUERY,
            {"ensemblId": ensembl_id},
            data_path=["target", "associatedDiseases"],
            size=min(limit, 25),
        )
        rows = rows[:limit]

        symbol = ""
        data_raw = self._gql.execute(TARGET_QUERY, {"ensemblId": ensembl_id})
        if data_raw.get("target"):
            symbol = data_raw["target"].get("approvedSymbol", "")

        associations = [_parse_target_association(r, ensembl_id, symbol) for r in rows]

        if as_dataframe:
            return _to_dataframe(associations)
        return associations

    def get_target_drugs(self, target_id: str) -> list[Drug]:
        """Return approved drugs and clinical candidates that interact with a target.

        Includes the drug name, type, mechanism of action, trade names, and
        maximum clinical trial phase reached.

        Args:
            target_id: Ensembl gene ID like ``'ENSG00000146648'`` or HGNC
                symbol like ``'EGFR'``.

        Returns:
            List of :class:`~opentargets.models.Drug` objects.

        Example::

            client = OpenTargetsClient()
            drugs = client.get_target_drugs("EGFR")
            for d in drugs:
                print(d.name, d.maximum_clinical_stage)
        """
        ensembl_id = self._resolve_target(target_id)
        data = self._gql.execute(TARGET_DRUGS_QUERY, {"ensemblId": ensembl_id})
        rows = (data.get("target") or {}).get("drugAndClinicalCandidates", {}).get(
            "rows"
        ) or []
        return [_parse_drug(r["drug"]) for r in rows if "drug" in r]

    def get_target_tractability(self, target_id: str) -> list[Tractability]:
        """Return tractability assessments indicating how druggable a target is.

        Covers small-molecule, antibody, PROTAC, and other modalities, each
        with a label and value indicating the assessment category (e.g.
        ``"Clinical precedence"``, ``"Discovery precedence"``).

        Args:
            target_id: Ensembl gene ID like ``'ENSG00000146648'`` or HGNC
                symbol like ``'EGFR'``.

        Returns:
            List of :class:`~opentargets.models.Tractability` objects, one per
            modality/label combination.

        Example::

            client = OpenTargetsClient()
            tracts = client.get_target_tractability("EGFR")
            for t in tracts:
                print(t.modality, t.label, t.value)
        """
        ensembl_id = self._resolve_target(target_id)
        data = self._gql.execute(TARGET_TRACTABILITY_QUERY, {"ensemblId": ensembl_id})
        rows: list[dict[str, Any]] = (data.get("target") or {}).get(
            "tractability"
        ) or []
        return [Tractability.model_validate(r) for r in rows]

    def get_target_safety(self, target_id: str) -> list[SafetyLiability]:
        """Return known safety liabilities for a target.

        Safety liabilities describe adverse events associated with target
        perturbation, the biosample in which they were observed, the
        directional effect (activation/inhibition), and the source literature.

        Args:
            target_id: Ensembl gene ID like ``'ENSG00000146648'`` or HGNC
                symbol like ``'EGFR'``.

        Returns:
            List of :class:`~opentargets.models.SafetyLiability` objects.

        Example::

            client = OpenTargetsClient()
            liabilities = client.get_target_safety("EGFR")
            for s in liabilities:
                print(s.event, s.datasource)
        """
        ensembl_id = self._resolve_target(target_id)
        data = self._gql.execute(TARGET_SAFETY_QUERY, {"ensemblId": ensembl_id})
        rows: list[dict[str, Any]] = (data.get("target") or {}).get(
            "safetyLiabilities"
        ) or []
        return [_parse_safety_liability(r) for r in rows]

    def get_target_expression(self, target_id: str) -> list[TissueExpression]:
        """Return baseline tissue-level RNA and protein expression for a target.

        Data is sourced from GTEx (RNA) and the Human Protein Atlas (protein).
        Each entry covers one tissue and includes RNA TPM value/z-score and
        protein reliability/level.

        Args:
            target_id: Ensembl gene ID like ``'ENSG00000146648'`` or HGNC
                symbol like ``'EGFR'``.

        Returns:
            List of :class:`~opentargets.models.TissueExpression` objects.

        Example::

            client = OpenTargetsClient()
            expressions = client.get_target_expression("EGFR")
            for e in expressions:
                print(e.tissue.label, e.rna.value, e.protein.level)
        """
        ensembl_id = self._resolve_target(target_id)
        data = self._gql.execute(TARGET_EXPRESSION_QUERY, {"ensemblId": ensembl_id})
        rows: list[dict[str, Any]] = (data.get("target") or {}).get("expressions") or []
        return [_parse_tissue_expression(r) for r in rows]

    def get_target_constraint(self, target_id: str) -> list[GeneticConstraint]:
        """Return gnomAD genetic constraint metrics for a target.

        Constraint metrics quantify intolerance to variation and are useful
        when assessing whether perturbing a target is likely to be tolerated.
        Typical entries cover synonymous (``syn``), missense (``mis``), and
        loss-of-function (``lof``) variant classes with pLI, LOEUF, and Z-score
        values.

        Args:
            target_id: Ensembl gene ID like ``'ENSG00000146648'`` or HGNC
                symbol like ``'EGFR'``.

        Returns:
            List of :class:`~opentargets.models.GeneticConstraint` objects —
            typically one entry each for ``syn``, ``mis``, and ``lof``.

        Example::

            client = OpenTargetsClient()
            constraints = client.get_target_constraint("EGFR")
            for c in constraints:
                print(c.constraintType, c.pLI, c.loeuf)
        """
        ensembl_id = self._resolve_target(target_id)
        data = self._gql.execute(TARGET_CONSTRAINT_QUERY, {"ensemblId": ensembl_id})
        rows: list[dict[str, Any]] = (data.get("target") or {}).get(
            "geneticConstraint"
        ) or []
        return [GeneticConstraint.model_validate(r) for r in rows]

    # ------------------------------------------------------------------
    # Disease queries
    # ------------------------------------------------------------------

    def get_disease(self, disease_id: str) -> Disease:
        """Return core annotations for a single disease or phenotype.

        Retrieves name, description, therapeutic area classification, and
        cross-database references (OMIM, MeSH, MONDO, etc.).

        Args:
            disease_id: EFO ontology identifier like ``'EFO_0000311'``
                (cancer) or ``'EFO_0003060'`` (lung carcinoma). MONDO and
                OMIM IDs are also accepted where Open Targets indexes them.

        Returns:
            A :class:`~opentargets.models.Disease` instance.

        Raises:
            NotFoundError: If no disease matches *disease_id*.

        Example::

            client = OpenTargetsClient()
            disease = client.get_disease("EFO_0000311")
            print(disease.name)         # cancer
            print(disease.description)
        """
        cache_key = f"disease:{disease_id}"
        cached = self._result_cache.get(cache_key)
        if cached is not None:
            return cast(Disease, cached)

        data = self._gql.execute(DISEASE_QUERY, {"efoId": disease_id})
        raw = data.get("disease")
        if not raw:
            raise NotFoundError("disease", disease_id)
        disease = _parse_disease(raw)
        self._result_cache.set(cache_key, disease)
        return disease

    def get_disease_targets(
        self,
        disease_id: str,
        limit: int = 25,
        as_dataframe: bool = False,
    ) -> list[Association] | pd.DataFrame:
        """Return targets associated with a disease, ranked by association score.

        The inverse of :meth:`get_target_associations`. Each association
        includes an overall score and per-datasource scores. Results are
        ordered by descending overall score.

        Args:
            disease_id: EFO ontology identifier like ``'EFO_0000311'``
                (cancer) or ``'EFO_0003060'`` (lung carcinoma).
            limit: Maximum number of associations to return (default ``25``).
            as_dataframe: When ``True``, return a flat ``pandas.DataFrame``
                instead of a list of model objects. Requires ``pandas``.

        Returns:
            List of :class:`~opentargets.models.Association` objects or a
            ``pandas.DataFrame`` when *as_dataframe* is ``True``.

        Example::

            client = OpenTargetsClient()
            assocs = client.get_disease_targets("EFO_0000311", limit=5)
            for a in assocs:
                print(a.target_symbol, round(a.score, 3))
        """
        rows = self._gql.paginate(
            DISEASE_TARGETS_QUERY,
            {"efoId": disease_id},
            data_path=["disease", "associatedTargets"],
            size=min(limit, 25),
        )
        rows = rows[:limit]

        disease_name = ""
        data_raw = self._gql.execute(DISEASE_QUERY, {"efoId": disease_id})
        if data_raw.get("disease"):
            disease_name = data_raw["disease"].get("name", "")

        associations = [
            _parse_disease_association(r, disease_id, disease_name) for r in rows
        ]

        if as_dataframe:
            return _to_dataframe(associations)
        return associations

    # ------------------------------------------------------------------
    # Drug queries
    # ------------------------------------------------------------------

    def get_drug(self, drug_id: str) -> Drug:
        """Return core annotations for a single drug or clinical candidate.

        Retrieves the drug name, type (small molecule, antibody, etc.),
        mechanism of action, synonyms, trade names, and the highest clinical
        trial phase reached.

        Args:
            drug_id: ChEMBL identifier like ``'CHEMBL941'`` (erlotinib) or
                ``'CHEMBL1421'`` (gefitinib).

        Returns:
            A :class:`~opentargets.models.Drug` instance.

        Raises:
            NotFoundError: If no drug matches *drug_id*.

        Example::

            client = OpenTargetsClient()
            drug = client.get_drug("CHEMBL941")
            print(drug.name)                    # ERLOTINIB
            print(drug.maximum_clinical_stage)  # 4
        """
        cache_key = f"drug:{drug_id}"
        cached = self._result_cache.get(cache_key)
        if cached is not None:
            return cast(Drug, cached)

        data = self._gql.execute(DRUG_QUERY, {"chemblId": drug_id})
        raw = data.get("drug")
        if not raw:
            raise NotFoundError("drug", drug_id)
        drug = _parse_drug(raw)
        self._result_cache.set(cache_key, drug)
        return drug

    def get_drug_indications(self, drug_id: str) -> list[DrugIndication]:
        """Return approved and clinical-stage disease indications for a drug.

        Each indication includes the disease name and the maximum clinical
        trial phase associated with the drug–disease pair.

        Args:
            drug_id: ChEMBL identifier like ``'CHEMBL941'`` (erlotinib).

        Returns:
            List of :class:`~opentargets.models.DrugIndication` objects.

        Example::

            client = OpenTargetsClient()
            indications = client.get_drug_indications("CHEMBL941")
            for ind in indications:
                print(ind.disease_name, ind.max_clinical_stage)
        """
        data = self._gql.execute(DRUG_INDICATIONS_QUERY, {"chemblId": drug_id})
        rows = (data.get("drug") or {}).get("indications", {}).get("rows") or []
        return [_parse_drug_indication(r) for r in rows]

    def get_drug_chembl_ids(self, drug_id: str) -> list[str]:
        """Return all ChEMBL IDs linked to a drug via its cross-references.

        The Open Targets ``Drug`` type stores external references in
        ``crossReferences`` (source + ids).  This method returns only those
        ``ids`` belonging to sources that look like a ChEMBL reference — i.e.
        any cross-reference whose ``ids`` list contains strings starting with
        ``CHEMBL``, plus the primary drug ID itself.  Useful when a compound
        has multiple ChEMBL entries (e.g. salt vs. free base).

        Args:
            drug_id: ChEMBL identifier like ``'CHEMBL941'`` (erlotinib) or
                ``'CHEMBL521'``.

        Returns:
            Deduplicated list of ChEMBL identifier strings, primary ID first.

        Raises:
            NotFoundError: If no drug matches *drug_id*.

        Example::

            client = OpenTargetsClient()
            ids = client.get_drug_chembl_ids("CHEMBL941")
            print(ids)  # ['CHEMBL941', ...]
        """
        data = self._gql.execute(DRUG_CHEMBL_IDS_QUERY, {"chemblId": drug_id})
        raw = data.get("drug")
        if not raw:
            raise NotFoundError("drug", drug_id)
        return _extract_chembl_ids(raw)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query_string: str,
        entity_type: str | None = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search the Open Targets Platform for targets, diseases, or drugs.

        Performs a ranked free-text search. Each result carries the entity
        type, stable ID, display name, and a relevance score. Useful for
        resolving human-readable names to stable identifiers.

        Args:
            query_string: Free-text search string, e.g. ``'EGFR'``,
                ``'lung cancer'``, or ``'erlotinib'``.
            entity_type: Restrict results to ``'target'``, ``'disease'``, or
                ``'drug'``. Pass ``None`` (default) to search all types.
            limit: Maximum number of results to return (default ``10``).

        Returns:
            List of :class:`~opentargets.models.SearchResult` objects ordered
            by relevance.

        Example::

            client = OpenTargetsClient()
            results = client.search("lung cancer", entity_type="disease", limit=3)
            for r in results:
                print(r.id, r.name, r.entity)
        """
        entity_names = [entity_type] if entity_type else []
        data = self._gql.execute(
            SEARCH_QUERY,
            {
                "queryString": query_string,
                "entityNames": entity_names,
                "page": {"index": 0, "size": limit},
            },
        )
        hits: list[dict[str, Any]] = (data.get("search") or {}).get("hits") or []
        return [SearchResult.model_validate(h) for h in hits]

    # ------------------------------------------------------------------
    # Association queries
    # ------------------------------------------------------------------

    def get_associations(
        self,
        target_id: str,
        disease_id: str,
    ) -> Association | None:
        """Return the association score between one specific target and disease.

        Looks up the direct target–disease pair and returns its overall
        association score together with per-datasource scores. Returns
        ``None`` if Open Targets does not record an association.

        Args:
            target_id: Ensembl gene ID like ``'ENSG00000146648'`` or HGNC
                symbol like ``'EGFR'``.
            disease_id: EFO ontology identifier like ``'EFO_0000311'``
                (cancer) or ``'EFO_0003060'`` (lung carcinoma).

        Returns:
            An :class:`~opentargets.models.Association` with overall and
            per-datasource scores, or ``None`` if no association exists.

        Example::

            client = OpenTargetsClient()
            assoc = client.get_associations("EGFR", "EFO_0000311")
            if assoc:
                print(assoc.score)  # e.g. 0.853
        """
        ensembl_id = self._resolve_target(target_id)
        rows = self._gql.paginate(
            TARGET_ASSOCIATIONS_QUERY,
            {"ensemblId": ensembl_id},
            data_path=["target", "associatedDiseases"],
            size=25,
        )
        match = next(
            (r for r in rows if (r.get("disease") or {}).get("id") == disease_id),
            None,
        )
        if match is None:
            return None
        symbol = ""
        d = self._gql.execute(TARGET_QUERY, {"ensemblId": ensembl_id})
        if d.get("target"):
            symbol = d["target"].get("approvedSymbol", "")
        return _parse_target_association(match, ensembl_id, symbol)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._gql.close()

    def __enter__(self) -> OpenTargetsClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_target(self, target_id: str) -> str:
        """Return Ensembl ID for *target_id*, resolving gene symbols via search."""
        if target_id.upper().startswith("ENSG"):
            return target_id

        cached = self._symbol_cache.get(target_id.upper())
        if cached is not None:
            return cast(str, cached)

        results = self.search(target_id, entity_type="target", limit=1)
        if not results:
            raise NotFoundError("target", target_id)
        ensembl_id = results[0].id
        self._symbol_cache.set(target_id.upper(), ensembl_id)
        return ensembl_id


# ------------------------------------------------------------------
# Parse helpers (keep client.py clean by handling field mapping here)
# ------------------------------------------------------------------


def _parse_target(raw: dict[str, Any]) -> Target:
    descs: list[str] = raw.get("functionDescriptions") or []
    return Target.model_validate(
        {
            "id": raw.get("id", ""),
            "approvedSymbol": raw.get("approvedSymbol", ""),
            "approvedName": raw.get("approvedName", ""),
            "biotype": raw.get("biotype", ""),
            "functionDescriptions": descs,
            "description": descs[0] if descs else "",
        }
    )


def _parse_disease(raw: dict[str, Any]) -> Disease:
    areas_raw: list[Any] = raw.get("therapeuticAreas") or []
    areas = [a["name"] if isinstance(a, dict) else str(a) for a in areas_raw]
    return Disease.model_validate(
        {
            "id": raw.get("id", ""),
            "name": raw.get("name", ""),
            "description": raw.get("description", ""),
            "therapeuticAreas": areas,
            "dbXRefs": raw.get("dbXRefs") or [],
        }
    )


def _parse_drug(raw: dict[str, Any]) -> Drug:
    moa_obj = raw.get("mechanismsOfAction") or {}
    moa_rows: list[dict[str, Any]] = moa_obj.get("rows") or []
    moa_str = moa_rows[0].get("mechanismOfAction", "") if moa_rows else ""
    return Drug.model_validate(
        {
            "id": raw.get("id", ""),
            "name": raw.get("name", ""),
            "drugType": raw.get("drugType", ""),
            "mechanism_of_action": moa_str,
            "synonyms": raw.get("synonyms") or [],
            "tradeNames": raw.get("tradeNames") or [],
            "maximumClinicalStage": raw.get("maximumClinicalStage"),
        }
    )


def _parse_target_association(
    row: dict[str, Any],
    target_id: str,
    target_symbol: str,
) -> Association:
    disease = row.get("disease") or {}
    ds_scores = [
        DatasourceScore(id=s["id"], score=s["score"])
        for s in (row.get("datasourceScores") or [])
    ]
    return Association(
        target_id=target_id,
        target_symbol=target_symbol,
        disease_id=disease.get("id", ""),
        disease_name=disease.get("name", ""),
        score=row.get("score", 0.0),
        datasource_scores=ds_scores,
    )


def _parse_disease_association(
    row: dict[str, Any],
    disease_id: str,
    disease_name: str,
) -> Association:
    target = row.get("target") or {}
    ds_scores = [
        DatasourceScore(id=s["id"], score=s["score"])
        for s in (row.get("datasourceScores") or [])
    ]
    return Association(
        target_id=target.get("id", ""),
        target_symbol=target.get("approvedSymbol", ""),
        disease_id=disease_id,
        disease_name=disease_name,
        score=row.get("score", 0.0),
        datasource_scores=ds_scores,
    )


def _parse_association_raw(raw: dict[str, Any]) -> Association:
    target = raw.get("target") or {}
    disease = raw.get("disease") or {}
    ds_scores = [
        DatasourceScore(id=s["id"], score=s["score"])
        for s in (raw.get("datasourceScores") or [])
    ]
    return Association(
        target_id=target.get("id", ""),
        target_symbol=target.get("approvedSymbol", ""),
        disease_id=disease.get("id", ""),
        disease_name=disease.get("name", ""),
        score=raw.get("score", 0.0),
        datasource_scores=ds_scores,
    )


def _parse_drug_indication(row: dict[str, Any]) -> DrugIndication:
    disease = row.get("disease") or {}
    return DrugIndication.model_validate(
        {
            "disease_id": disease.get("id", ""),
            "disease_name": disease.get("name", ""),
            "maxClinicalStage": row.get("maxClinicalStage"),
        }
    )


def _parse_safety_liability(raw: dict[str, Any]) -> SafetyLiability:
    biosamples = [
        SafetyBiosample.model_validate(b) for b in (raw.get("biosamples") or [])
    ]
    effects = [SafetyEffect.model_validate(e) for e in (raw.get("effects") or [])]
    return SafetyLiability.model_validate(
        {
            "event": raw.get("event"),
            "datasource": raw.get("datasource", ""),
            "biosamples": biosamples,
            "effects": effects,
            "literature": raw.get("literature"),
            "url": raw.get("url"),
            "eventId": raw.get("eventId"),
        }
    )


def _parse_tissue_expression(raw: dict[str, Any]) -> TissueExpression:
    tissue_raw = raw.get("tissue") or {}
    rna_raw = raw.get("rna") or {}
    protein_raw = raw.get("protein") or {}
    return TissueExpression(
        tissue=TissueInfo(
            id=tissue_raw.get("id", ""),
            label=tissue_raw.get("label", ""),
        ),
        rna=RnaExpression(
            value=rna_raw.get("value", 0.0),
            level=rna_raw.get("level", 0),
            zscore=rna_raw.get("zscore", 0),
            unit=rna_raw.get("unit", ""),
        ),
        protein=ProteinExpression(
            level=protein_raw.get("level", -1),
            reliability=protein_raw.get("reliability", False),
        ),
    )


def _extract_chembl_ids(raw: dict[str, Any]) -> list[str]:
    """Return deduplicated ChEMBL IDs from a drug's crossReferences."""
    seen: set[str] = set()
    result: list[str] = []
    primary_id = raw.get("id", "")
    if primary_id:
        seen.add(primary_id)
        result.append(primary_id)
    for ref in raw.get("crossReferences") or []:
        for ref_id in ref.get("ids") or []:
            if (
                isinstance(ref_id, str)
                and ref_id.upper().startswith("CHEMBL")
                and ref_id not in seen
            ):
                seen.add(ref_id)
                result.append(ref_id)
    return result


def _to_dataframe(associations: list[Association]) -> pd.DataFrame:
    try:
        import pandas as pd
    except ImportError as exc:
        raise ImportError(
            "pandas is required for DataFrame output. "
            "Install it with: pip install opentargets-py[pandas]"
        ) from exc

    return pd.DataFrame([a.model_dump() for a in associations])
