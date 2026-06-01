# opentargets-py

[![PyPI version](https://img.shields.io/pypi/v/opentargets-py?cache=refresh)](https://pypi.org/project/opentargets-py/)
[![Python versions](https://img.shields.io/pypi/pyversions/opentargets-py?cache=refresh)](https://pypi.org/project/opentargets-py/)
[![CI](https://github.com/goknurarican/opentargets-py/actions/workflows/ci.yml/badge.svg)](https://github.com/goknurarican/opentargets-py/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Modern Python client for the [Open Targets Platform](https://platform.opentargets.org) GraphQL API — with sync and async clients, a `--json` CLI, and an MCP server so AI agents can query it directly.

> **Disclaimer:** Unofficial, community-maintained. Not affiliated with or endorsed by the Open Targets consortium. For the official platform, visit [platform.opentargets.org](https://platform.opentargets.org).

The official `opentargets` package was deprecated when Open Targets migrated to GraphQL in 2021 and has since been removed from PyPI. This library fills that gap — it is the only Python SDK targeting the current GraphQL API.

## Installation

```bash
pip install opentargets-py                 # core SDK (sync + async)
pip install opentargets-py[pandas]         # adds DataFrame output
pip install opentargets-py[cli]            # adds the `opentargets` CLI
pip install opentargets-py[mcp]            # adds the `opentargets-mcp` MCP server
pip install opentargets-py[all]            # everything
```

## Quick start

### Sync

```python
from opentargets import OpenTargetsClient

with OpenTargetsClient() as client:
    target = client.get_target("EGFR")
    print(target.approved_name)  # epidermal growth factor receptor

    associations = client.get_target_associations("EGFR", limit=10)
    for a in associations:
        print(a.disease_name, round(a.score, 3))
```

### Async (concurrent fan-out)

```python
import asyncio
from opentargets import AsyncOpenTargetsClient

async def main():
    async with AsyncOpenTargetsClient() as client:
        targets = await asyncio.gather(
            client.get_target("EGFR"),
            client.get_target("BRAF"),
            client.get_target("KRAS"),
        )
        for t in targets:
            print(t.approved_symbol, t.biotype)

asyncio.run(main())
```

### CLI

```bash
opentargets target EGFR                          # rich table
opentargets target EGFR --json                   # machine-parseable
opentargets targets EGFR BRAF KRAS --json        # batch
opentargets disease EFO_0000311 --targets --json | jq '.targets[0]'
opentargets search "lung cancer" --json
```

Every subcommand supports `--json`, so the CLI is usable from shell scripts, agents, and notebooks alike.

### MCP server (Claude Desktop, Cursor, etc.)

```bash
pip install opentargets-py[mcp]
```

Then add to your `claude_desktop_config.json` (macOS path:
`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "opentargets": {
      "command": "opentargets-mcp"
    }
  }
}
```

Now you can ask Claude things like *"What diseases is EGFR associated with?"* and it will call the SDK directly. Exposed tools: `get_target_info`, `find_target_associations`, `get_target_drugs`, `get_target_tractability`, `get_target_safety`, `get_target_expression`, `get_target_constraint`, `get_disease_info`, `find_disease_targets`, `get_drug_info`, `get_drug_indications`, `search_open_targets`.

## Features

- **Sync + async clients** — `OpenTargetsClient` and `AsyncOpenTargetsClient` with full feature parity
- **15 endpoint methods** — targets, diseases, drugs, associations, tractability, safety liabilities, baseline expression, genetic constraint, ChEMBL crosslinks, search
- **Symbol resolution** — pass `"EGFR"` instead of `"ENSG00000146648"`
- **Auto-pagination** — fetches all pages transparently
- **Caching** — in-memory `TTLCache` by default; opt into `DiskCache` (SQLite, survives process restarts) for repeated runs
- **Configurable retries** — `RetryConfig(max_retries=..., base_delay=..., retryable_statuses=..., respect_retry_after=...)`
- **Pandas integration** — `as_dataframe=True` on list-returning methods
- **Typed** — full Pydantic v2 models, `py.typed` marker, `mypy --strict` compliant
- **CLI** — `opentargets` with `--json` on every command, rich tables for humans
- **MCP server** — `opentargets-mcp`, drop-in for Claude Desktop / Cursor / any MCP host
- **Minimal core** — just `httpx` + `pydantic`; everything else is an opt-in extra

## Configuration

### Disk cache (persist across runs)

```python
from opentargets import OpenTargetsClient, DiskCache

cache = DiskCache(path="~/.cache/opentargets.db", ttl=86400)  # 1 day
with OpenTargetsClient(cache=cache) as client:
    target = client.get_target("EGFR")  # first run: API
    target = client.get_target("EGFR")  # second run (even new process): cache hit
```

### Custom retry policy

```python
from opentargets import OpenTargetsClient, RetryConfig

retry = RetryConfig(max_retries=5, base_delay=2.0, max_delay=120.0)
client = OpenTargetsClient(retry_config=retry)
```

## For AI agents

This package was designed to be usable by both humans and LLM-based agents. Three deliberate affordances:

1. **MCP server** (`opentargets-mcp`) — wraps every public method as an MCP tool with LLM-friendly docstrings. Configure once and the model calls Open Targets directly. See [MCP setup above](#mcp-server-claude-desktop-cursor-etc).
2. **CLI with `--json`** — every subcommand emits clean JSON, so agents can shell out and parse the result with `jq` or `json.loads`.
3. **Typed Pydantic responses** — every method returns a model with `.model_dump()` / `.model_dump_json()`, so programmatic agents get structured data without parsing.

See [`llms.txt`](llms.txt) for a skimmable one-page overview of the full API surface, optimized for LLM ingestion.

## More examples

See the [`examples/`](examples/) directory:

- [`basic_usage.py`](examples/basic_usage.py) — targets, diseases, drugs, search
- [`batch_query.py`](examples/batch_query.py) — batch fetch + DataFrame output
- [`network_analysis.py`](examples/network_analysis.py) — build a target–disease network

## API reference

See [`docs/api-reference.md`](docs/api-reference.md). All public methods on `OpenTargetsClient` (and the matching `AsyncOpenTargetsClient`) have docstrings with `Args`, `Returns`, and `Example` blocks.

## Contributing

1. Fork the repo and create a feature branch.
2. Install dev dependencies: `pip install -e ".[dev,all]"`
3. Run tests: `pytest`
4. Run linting + formatting: `ruff check src tests && ruff format src tests`
5. Type check: `mypy src/opentargets`
6. Open a pull request.

## License

Apache 2.0 — see [LICENSE](LICENSE).
