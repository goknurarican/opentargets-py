# API Reference

## OpenTargetsClient

```python
OpenTargetsClient(
    base_url: str = "https://api.platform.opentargets.org/api/v4/graphql",
    timeout: float = 30.0,
    cache: bool = True,
    cache_ttl: float = 300.0,
)
```

### Target methods

| Method | Returns |
|---|---|
| `get_target(target_id)` | `Target` |
| `get_targets(target_ids)` | `list[Target]` |
| `get_target_associations(target_id, limit, as_dataframe)` | `list[Association]` or `DataFrame` |
| `get_target_drugs(target_id)` | `list[Drug]` |

### Disease methods

| Method | Returns |
|---|---|
| `get_disease(disease_id)` | `Disease` |
| `get_disease_targets(disease_id, limit, as_dataframe)` | `list[Association]` or `DataFrame` |

### Drug methods

| Method | Returns |
|---|---|
| `get_drug(drug_id)` | `Drug` |
| `get_drug_indications(drug_id)` | `list[DrugIndication]` |

### Search

| Method | Returns |
|---|---|
| `search(query_string, entity_type, limit)` | `list[SearchResult]` |

### Associations

| Method | Returns |
|---|---|
| `get_associations(target_id, disease_id)` | `Association \| None` |

## Models

### Target
`id`, `approved_symbol`, `approved_name`, `biotype`, `description`, `function_descriptions`

### Disease
`id`, `name`, `description`, `therapeutic_areas`, `db_x_refs`

### Drug
`id`, `name`, `drug_type`, `mechanism_of_action`, `synonyms`, `trade_names`, `max_clinical_trial_phase`

### Association
`target_id`, `target_symbol`, `disease_id`, `disease_name`, `score`, `datasource_scores`, `evidence_count`

### SearchResult
`id`, `name`, `entity_type`, `description`, `score`

### DrugIndication
`disease_id`, `disease_name`, `max_phase_for_indication`

## Exceptions

| Exception | When |
|---|---|
| `OpenTargetsError` | Base class |
| `APIError` | HTTP error (non-2xx) |
| `QueryError` | GraphQL `errors` in response |
| `NotFoundError` | Entity not found |
| `RateLimitError` | HTTP 429 |
