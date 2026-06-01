# opentargets-py

Modern Python client for the [Open Targets Platform](https://platform.opentargets.org) GraphQL API — sync and async clients, a `--json` CLI, and an MCP server so AI agents can query it directly.

```{note}
Unofficial, community-maintained. Not affiliated with or endorsed by the Open Targets consortium.
```

## Install

```bash
pip install opentargets-py                 # core SDK (sync + async)
pip install opentargets-py[pandas]         # adds DataFrame output
pip install opentargets-py[cli]            # adds the `opentargets` CLI
pip install opentargets-py[mcp]            # adds the `opentargets-mcp` MCP server
pip install opentargets-py[all]            # everything
```

## At a glance

```python
from opentargets import OpenTargetsClient

with OpenTargetsClient() as client:
    target = client.get_target("EGFR")
    print(target.approved_name)  # epidermal growth factor receptor

    for a in client.get_target_associations("EGFR", limit=5):
        print(a.disease_name, round(a.score, 3))
```

## Contents

```{toctree}
:maxdepth: 2

quickstart
api-reference
api
```

## Links

- Source: <https://github.com/goknurarican/opentargets-py>
- PyPI: <https://pypi.org/project/opentargets-py/>
- Open Targets Platform: <https://platform.opentargets.org>
- `llms.txt` for agent ingestion: <https://github.com/goknurarican/opentargets-py/blob/main/llms.txt>
