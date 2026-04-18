# Quick Start

## Installation

```bash
pip install opentargets-py
# with pandas
pip install opentargets-py[pandas]
```

## Basic usage

```python
from opentargets import OpenTargetsClient

client = OpenTargetsClient()

target = client.get_target("EGFR")
print(target.id)             # ENSG00000146648
print(target.approved_name)  # epidermal growth factor receptor

assocs = client.get_target_associations("EGFR", limit=25)
df = client.get_target_associations("EGFR", limit=100, as_dataframe=True)
```

## Configuration

```python
client = OpenTargetsClient(
    base_url="https://api.platform.opentargets.org/api/v4/graphql",
    timeout=60.0,
    cache=True,
    cache_ttl=600.0,   # 10 minutes
)
```

## Context manager

```python
with OpenTargetsClient() as client:
    drug = client.get_drug("CHEMBL939")
```
