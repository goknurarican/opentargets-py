# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install all dependencies (from repo root)
pip install -e ".[dev,pandas]"

# Run tests (no real API calls)
pytest

# Run a single test file
pytest tests/test_client.py -v

# Run a single test
pytest tests/test_client.py::test_get_target_by_ensembl_id -v

# Run integration tests (hits the real API)
pytest -m integration

# Lint + format check
ruff check src tests
ruff format --check src tests

# Type check
mypy src/opentargets
```

## Architecture

The package lives under `src/opentargets/` (PEP 517 src layout).

**Request flow:**  
`OpenTargetsClient` (public API) → `GraphQLClient` (`_graphql.py`) → `with_retry()` → `httpx`

**Key design decisions:**

- `client.py` contains all public methods and delegates to `_graphql.py` for HTTP. Parse helpers (`_parse_target`, `_parse_disease`, etc.) live at the bottom of `client.py` to keep method bodies short.
- `_graphql.py` has two entry points: `execute()` for single queries and `paginate()` for cursor-based pagination. Pagination injects `index`/`size` variables and walks pages until `count` is exhausted.
- `_queries/` holds only GraphQL string constants — no logic. One module per entity type.
- `_retry.py` implements backoff without `tenacity`. It wraps a zero-argument callable, so it's usable with any function via a lambda.
- `_cache.py` is a standalone LRU+TTL cache. `OpenTargetsClient` uses two instances: one for symbol→Ensembl ID mapping (`_symbol_cache`) and one for full entity responses (`_result_cache`). Passing `cache=False` swaps both for `_NoCache` (same interface, no-ops).
- Symbol resolution: if `target_id` starts with `ENSG`, it's used directly. Otherwise the search endpoint is called and the result cached.
- Models in `models.py` use Pydantic v2 `model_validate()` with `populate_by_name=True` so both camelCase API fields and snake_case aliases work.

## Testing

Tests use `respx` to mock `httpx` — no real API calls unless `@pytest.mark.integration`. Fixtures in `conftest.py` provide raw API response dicts that mirror the actual GraphQL schema shape.
