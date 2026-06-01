"""opentargets-py — Modern Python client for the Open Targets Platform GraphQL API."""

from ._async_client import AsyncOpenTargetsClient
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
    SearchResult,
    Target,
)

__version__ = "0.1.0"
__all__ = [
    "AsyncOpenTargetsClient",
    "OpenTargetsClient",
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
]
