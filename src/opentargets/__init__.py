"""opentargets-py — Modern Python client for the Open Targets Platform GraphQL API."""

from ._cache import CacheBackend, DiskCache
from ._retry import DEFAULT_RETRY_CONFIG, RetryConfig
from .client import OpenTargetsClient
from .exceptions import (
    APIError,
    NotFoundError,
    OpenTargetsError,
    QueryError,
    RateLimitError,
)
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

__version__ = "0.1.0"
__all__ = [
    "OpenTargetsClient",
    # Retry config
    "RetryConfig",
    "DEFAULT_RETRY_CONFIG",
    # Cache
    "CacheBackend",
    "DiskCache",
    # Exceptions
    "OpenTargetsError",
    "APIError",
    "QueryError",
    "NotFoundError",
    "RateLimitError",
    # Models
    "Target",
    "Disease",
    "Drug",
    "Association",
    "DatasourceScore",
    "SearchResult",
    "DrugIndication",
    # New models
    "Tractability",
    "SafetyLiability",
    "SafetyBiosample",
    "SafetyEffect",
    "TissueExpression",
    "TissueInfo",
    "RnaExpression",
    "ProteinExpression",
    "GeneticConstraint",
]
