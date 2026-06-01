"""Async public client for the Open Targets Platform."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, cast

from ._async_graphql import AsyncGraphQLClient
from ._cache import TTLCache
from ._queries.disease import DISEASE_QUERY, DISEASE_TARGETS_QUERY
from ._queries.drug import DRUG_INDICATIONS_QUERY, DRUG_QUERY
from ._queries.search import SEARCH_QUERY
from ._queries.target import (
    TARGET_ASSOCIATIONS_QUERY,
    TARGET_DRUGS_QUERY,
    TARGET_QUERY,
    TARGETS_BATCH_QUERY,
)
from .client import (
    _NoCache,
    _parse_disease,
    _parse_disease_association,
    _parse_drug,
    _parse_drug_indication,
    _parse_target,
    _parse_target_association,
    _to_dataframe,
)
from .exceptions import NotFoundError
from .models import (
    Association,
    Disease,
    Drug,
    DrugIndication,
    SearchResult,
    Target,
)

if TYPE_CHECKING:
    import pandas as pd

_DEFAULT_URL = "https://api.platform.opentargets.org/api/v4/graphql"


class AsyncOpenTargetsClient:
    """Asynchronous client for the Open Targets Platform GraphQL API.

    Mirrors :class:`~opentargets.OpenTargetsClient` with ``async``/``await``
    semantics. Use with ``asyncio.gather`` to query hundreds of targets
    concurrently.

    Args:
        base_url: GraphQL endpoint. Override for self-hosted instances.
        timeout: HTTP timeout in seconds.
        cache: Set to ``False`` to disable in-memory caching.
        cache_ttl: Cache entry lifetime in seconds (default 5 min).

    Example::

        import asyncio
        from opentargets import AsyncOpenTargetsClient

        async def main():
            async with AsyncOpenTargetsClient() as client:
                target = await client.get_target("EGFR")
                print(target.approved_name)

        asyncio.run(main())
    """

    def __init__(
        self,
        base_url: str = _DEFAULT_URL,
        timeout: float = 30.0,
        cache: bool = True,
        cache_ttl: float = 300.0,
    ) -> None:
        self._gql = AsyncGraphQLClient(base_url=base_url, timeout=timeout)
        _sym: TTLCache[str, str] = TTLCache(ttl=cache_ttl) if cache else _NoCache()
        _res: TTLCache[str, Any] = TTLCache(ttl=cache_ttl) if cache else _NoCache()
        self._symbol_cache = _sym
        self._result_cache = _res

    # ------------------------------------------------------------------
    # Target queries
    # ------------------------------------------------------------------

    async def get_target(self, target_id: str) -> Target:
        """Fetch a single target by Ensembl ID or gene symbol.

        Args:
            target_id: Ensembl gene ID (``ENSG…``) or HGNC symbol (``EGFR``).

        Returns:
            A :class:`~opentargets.models.Target` instance.

        Raises:
            NotFoundError: If no target matches *target_id*.
        """
        ensembl_id = await self._resolve_target(target_id)
        cache_key = f"target:{ensembl_id}"
        cached = self._result_cache.get(cache_key)
        if cached is not None:
            return cast(Target, cached)

        data = await self._gql.execute(TARGET_QUERY, {"ensemblId": ensembl_id})
        raw = data.get("target")
        if not raw:
            raise NotFoundError("target", target_id)
        target = _parse_target(raw)
        self._result_cache.set(cache_key, target)
        return target

    async def get_targets(self, target_ids: list[str]) -> list[Target]:
        """Fetch multiple targets in a single API request.

        Args:
            target_ids: List of Ensembl IDs or gene symbols.

        Returns:
            List of :class:`~opentargets.models.Target` instances (same order as input).
        """
        ensembl_ids = [await self._resolve_target(t) for t in target_ids]
        data = await self._gql.execute(TARGETS_BATCH_QUERY, {"ids": ensembl_ids})
        raws: list[dict[str, Any]] = data.get("targets") or []
        by_id = {r["id"]: _parse_target(r) for r in raws}
        return [by_id[eid] for eid in ensembl_ids if eid in by_id]

    async def get_target_associations(
        self,
        target_id: str,
        limit: int = 25,
        as_dataframe: bool = False,
    ) -> list[Association] | pd.DataFrame:
        """Fetch diseases associated with a target.

        Args:
            target_id: Ensembl ID or gene symbol.
            limit: Maximum number of associations to return.
            as_dataframe: Return a ``pandas.DataFrame`` instead of a list.

        Returns:
            List of :class:`~opentargets.models.Association` objects, or a
            ``DataFrame`` when *as_dataframe* is ``True``.
        """
        ensembl_id = await self._resolve_target(target_id)
        rows = await self._gql.paginate(
            TARGET_ASSOCIATIONS_QUERY,
            {"ensemblId": ensembl_id},
            data_path=["target", "associatedDiseases"],
            size=min(limit, 25),
        )
        rows = rows[:limit]

        symbol = ""
        data_raw = await self._gql.execute(TARGET_QUERY, {"ensemblId": ensembl_id})
        if data_raw.get("target"):
            symbol = data_raw["target"].get("approvedSymbol", "")

        associations = [_parse_target_association(r, ensembl_id, symbol) for r in rows]

        if as_dataframe:
            return _to_dataframe(associations)
        return associations

    async def get_target_drugs(self, target_id: str) -> list[Drug]:
        """Fetch drugs known to interact with a target.

        Args:
            target_id: Ensembl ID or gene symbol.

        Returns:
            List of :class:`~opentargets.models.Drug` objects.
        """
        ensembl_id = await self._resolve_target(target_id)
        data = await self._gql.execute(TARGET_DRUGS_QUERY, {"ensemblId": ensembl_id})
        rows = (data.get("target") or {}).get("drugAndClinicalCandidates", {}).get(
            "rows"
        ) or []
        return [_parse_drug(r["drug"]) for r in rows if "drug" in r]

    # ------------------------------------------------------------------
    # Disease queries
    # ------------------------------------------------------------------

    async def get_disease(self, disease_id: str) -> Disease:
        """Fetch a single disease by EFO identifier.

        Args:
            disease_id: EFO identifier (e.g. ``EFO_0003060``).

        Returns:
            A :class:`~opentargets.models.Disease` instance.

        Raises:
            NotFoundError: If no disease matches *disease_id*.
        """
        cache_key = f"disease:{disease_id}"
        cached = self._result_cache.get(cache_key)
        if cached is not None:
            return cast(Disease, cached)

        data = await self._gql.execute(DISEASE_QUERY, {"efoId": disease_id})
        raw = data.get("disease")
        if not raw:
            raise NotFoundError("disease", disease_id)
        disease = _parse_disease(raw)
        self._result_cache.set(cache_key, disease)
        return disease

    async def get_disease_targets(
        self,
        disease_id: str,
        limit: int = 25,
        as_dataframe: bool = False,
    ) -> list[Association] | pd.DataFrame:
        """Fetch targets associated with a disease.

        Args:
            disease_id: EFO identifier.
            limit: Maximum number of associations to return.
            as_dataframe: Return a ``pandas.DataFrame`` instead of a list.

        Returns:
            List of :class:`~opentargets.models.Association` objects or a DataFrame.
        """
        rows = await self._gql.paginate(
            DISEASE_TARGETS_QUERY,
            {"efoId": disease_id},
            data_path=["disease", "associatedTargets"],
            size=min(limit, 25),
        )
        rows = rows[:limit]

        disease_name = ""
        data_raw = await self._gql.execute(DISEASE_QUERY, {"efoId": disease_id})
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

    async def get_drug(self, drug_id: str) -> Drug:
        """Fetch a single drug by ChEMBL identifier.

        Args:
            drug_id: ChEMBL ID (e.g. ``CHEMBL939``).

        Returns:
            A :class:`~opentargets.models.Drug` instance.

        Raises:
            NotFoundError: If no drug matches *drug_id*.
        """
        cache_key = f"drug:{drug_id}"
        cached = self._result_cache.get(cache_key)
        if cached is not None:
            return cast(Drug, cached)

        data = await self._gql.execute(DRUG_QUERY, {"chemblId": drug_id})
        raw = data.get("drug")
        if not raw:
            raise NotFoundError("drug", drug_id)
        drug = _parse_drug(raw)
        self._result_cache.set(cache_key, drug)
        return drug

    async def get_drug_indications(self, drug_id: str) -> list[DrugIndication]:
        """Fetch disease indications for a drug.

        Args:
            drug_id: ChEMBL ID.

        Returns:
            List of :class:`~opentargets.models.DrugIndication` objects.
        """
        data = await self._gql.execute(DRUG_INDICATIONS_QUERY, {"chemblId": drug_id})
        rows = (data.get("drug") or {}).get("indications", {}).get("rows") or []
        return [_parse_drug_indication(r) for r in rows]

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        query_string: str,
        entity_type: Optional[str] = None,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Search the platform for targets, diseases, or drugs.

        Args:
            query_string: Free-text search string.
            entity_type: Filter by ``"target"``, ``"disease"``, or ``"drug"``.
                         Pass ``None`` to search all entity types.
            limit: Maximum number of results.

        Returns:
            List of :class:`~opentargets.models.SearchResult` objects.
        """
        entity_names = [entity_type] if entity_type else []
        data = await self._gql.execute(
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

    async def get_associations(
        self,
        target_id: str,
        disease_id: str,
    ) -> Optional[Association]:
        """Fetch the association between a specific target and disease.

        Args:
            target_id: Ensembl ID or gene symbol.
            disease_id: EFO identifier.

        Returns:
            An :class:`~opentargets.models.Association` or ``None`` if no
            association exists.
        """
        ensembl_id = await self._resolve_target(target_id)
        rows = await self._gql.paginate(
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
        d = await self._gql.execute(TARGET_QUERY, {"ensemblId": ensembl_id})
        if d.get("target"):
            symbol = d["target"].get("approvedSymbol", "")
        return _parse_target_association(match, ensembl_id, symbol)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._gql.close()

    async def __aenter__(self) -> AsyncOpenTargetsClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _resolve_target(self, target_id: str) -> str:
        """Return Ensembl ID for *target_id*, resolving gene symbols via search."""
        if target_id.upper().startswith("ENSG"):
            return target_id

        cached = self._symbol_cache.get(target_id.upper())
        if cached is not None:
            return cached

        results = await self.search(target_id, entity_type="target", limit=1)
        if not results:
            raise NotFoundError("target", target_id)
        ensembl_id = results[0].id
        self._symbol_cache.set(target_id.upper(), ensembl_id)
        return ensembl_id
