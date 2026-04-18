"""In-memory LRU cache with TTL support."""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Generic, TypeVar

_K = TypeVar("_K")
_V = TypeVar("_V")

DEFAULT_TTL = 300.0  # 5 minutes
DEFAULT_MAXSIZE = 256


class TTLCache(Generic[_K, _V]):
    """Thread-unsafe LRU cache with per-entry time-to-live.

    Args:
        maxsize: Maximum number of entries to keep in cache.
        ttl: Seconds before a cached entry is considered stale.
    """

    def __init__(
        self, maxsize: int = DEFAULT_MAXSIZE, ttl: float = DEFAULT_TTL
    ) -> None:
        self._maxsize = maxsize
        self._ttl = ttl
        self._store: OrderedDict[_K, tuple[_V, float]] = OrderedDict()

    def get(self, key: _K) -> _V | None:
        """Return cached value or *None* if missing / expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return value

    def set(self, key: _K, value: _V) -> None:
        """Insert or update *key* with *value*."""
        expires_at = time.monotonic() + self._ttl
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = (value, expires_at)
        if len(self._store) > self._maxsize:
            self._store.popitem(last=False)

    def clear(self) -> None:
        """Remove all entries from the cache."""
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)
