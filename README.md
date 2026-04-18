# opentargets-py

[![PyPI version](https://badge.fury.io/py/opentargets-py.svg)](https://pypi.org/project/opentargets-py/)
[![Python versions](https://img.shields.io/pypi/pyversions/opentargets-py)](https://pypi.org/project/opentargets-py/)
[![CI](https://github.com/goknurarican/opentargets-py/actions/workflows/ci.yml/badge.svg)](https://github.com/goknurarican/opentargets-py/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Modern Python client for the [Open Targets Platform](https://platform.opentargets.org) GraphQL API.

> **Disclaimer:** This is an **unofficial, community-maintained** client and is not affiliated with, endorsed by, or supported by the Open Targets consortium. For the official platform, visit [platform.opentargets.org](https://platform.opentargets.org).

The official `opentargets` package was deprecated when Open Targets migrated to GraphQL in 2021 and has since been removed from PyPI. This library fills that gap — it is the only Python SDK targeting the current GraphQL API.

## Installation

```bash
pip install opentargets-py
```

With pandas support:

```bash
pip install opentargets-py[pandas]
```

## Quick Start

```python
from opentargets import OpenTargetsClient

client = OpenTargetsClient()

# Look up a target by gene symbol
target = client.get_target("EGFR")
print(target.approved_name)  # epidermal growth factor receptor

# Get associated diseases
associations = client.get_target_associations("EGFR", limit=10)
for a in associations:
    print(a.disease_name, a.score)

# Get drugs for a target
drugs = client.get_target_drugs("EGFR")

# Look up a disease
disease = client.get_disease("EFO_0003060")

# Search across the platform
results = client.search("lung cancer", entity_type="disease", limit=5)
```

## Features

- **Type-safe** — full Pydantic v2 models, `py.typed` marker, `mypy --strict` compliant
- **Symbol resolution** — pass `"EGFR"` instead of `"ENSG00000146648"`
- **Auto-pagination** — fetches all pages transparently
- **In-memory cache** — LRU cache with TTL, reduces redundant API calls
- **Retry with backoff** — automatic retries on 429/5xx with exponential backoff
- **Pandas integration** — `as_dataframe=True` on any list method
- **Minimal dependencies** — only `httpx` and `pydantic`

## More Examples

See the [`examples/`](examples/) directory:

- [`basic_usage.py`](examples/basic_usage.py) — targets, diseases, drugs, search
- [`batch_query.py`](examples/batch_query.py) — batch fetch + DataFrame output
- [`network_analysis.py`](examples/network_analysis.py) — build a target–disease network

## API Reference

See [`docs/api-reference.md`](docs/api-reference.md).

## Contributing

1. Fork the repo and create a feature branch.
2. Install dev dependencies: `pip install -e ".[dev,pandas]"`
3. Run tests: `pytest`
4. Run linting: `ruff check src tests && ruff format src tests`
5. Open a pull request.

## License

Apache 2.0 — see [LICENSE](LICENSE).
