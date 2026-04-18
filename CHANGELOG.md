# Changelog

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
