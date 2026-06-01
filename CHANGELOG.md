# Changelog

## [0.2.0] - 2026-06-02

### Added
- `AsyncOpenTargetsClient` — full async parity with `OpenTargetsClient` so you can fan out hundreds of queries with `asyncio.gather`
- 5 new target endpoints: `get_target_tractability`, `get_target_safety`, `get_target_expression`, `get_target_constraint`, `get_drug_chembl_ids`
- New models: `Tractability`, `SafetyLiability`, `SafetyBiosample`, `SafetyEffect`, `TissueExpression`, `TissueInfo`, `RnaExpression`, `ProteinExpression`, `GeneticConstraint`
- `RetryConfig` dataclass — tune `max_retries`, `base_delay`, `max_delay`, `retryable_statuses`, `respect_retry_after`
- `DiskCache` — SQLite-backed cache that survives process restarts; opt in via `OpenTargetsClient(cache=DiskCache(path=...))`
- `CacheBackend` Protocol so you can drop in your own cache
- `opentargets` CLI (extras: `[cli]`) — six subcommands (`target`, `targets`, `disease`, `drug`, `search`, `associations`), each supports `--json` for clean machine-parseable output, rich tables for humans
- `opentargets-mcp` MCP server (extras: `[mcp]`, requires Python ≥3.10) — exposes 12 tools so AI assistants like Claude Desktop and Cursor can query Open Targets directly
- `[all]` extra bundling pandas + cli + mcp
- `llms.txt` for LLM discoverability + comprehensive Pydantic v2 docstrings on every public method

### Changed
- `OpenTargetsClient.__init__` now accepts `cache: bool | CacheBackend` (widened from `bool`) and `retry_config: Optional[RetryConfig]`
- Schema fixes against the live Open Targets v4 API: `Constraint` (not `GeneticConstraint`) for the genetic constraint type; ChEMBL IDs surfaced via `crossReferences` since `Drug.chemblIds` does not exist as a direct field
- Default retry behaviour is byte-identical to 0.1.0 — `RetryConfig()` mirrors the old hardcoded values
- README rewritten to cover sync + async + CLI + MCP usage end-to-end

## [0.1.0] - 2026-04-19

### Added
- Initial release
- `OpenTargetsClient` with sync support
- Target, disease, drug, association, and search queries
- Auto-pagination for association endpoints
- Symbol-to-Ensembl ID resolution with caching
- In-memory LRU cache with TTL
- Exponential backoff retry (no third-party dependencies)
- Pydantic v2 response models (frozen, fully typed)
- Optional pandas DataFrame output
- GitHub Actions CI (Python 3.9, 3.11, 3.13) and PyPI publish workflow
