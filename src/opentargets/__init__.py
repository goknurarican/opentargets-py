"""opentargets-py — Modern Python client for the Open Targets Platform GraphQL API."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from ._async_client import AsyncOpenTargetsClient
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

try:
    __version__ = _pkg_version("opentargets-py")
except PackageNotFoundError:  # editable install without installed metadata
    __version__ = "0.0.0+unknown"

__all__ = [
    "AsyncOpenTargetsClient",
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
