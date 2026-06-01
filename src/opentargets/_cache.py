"""In-memory LRU cache with TTL support, plus disk-backed SQLite cache."""

from __future__ import annotations

import pickle
import sqlite3
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Generic, Optional, Protocol, TypeVar, runtime_checkable

_K = TypeVar("_K")
_V = TypeVar("_V")

DEFAULT_TTL = 300.0  # 5 minutes
DEFAULT_MAXSIZE = 256


@runtime_checkable
class CacheBackend(Protocol):
    """Minimal protocol that every cache backend must satisfy."""

    def get(self, key: str) -> Any:
        """Return the cached value for *key*, or ``None`` if missing / expired."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Store *value* under *key*."""
        ...

    def clear(self) -> None:
        """Remove all entries."""
        ...

    def __len__(self) -> int:
        """Return the number of live (non-expired) entries."""
        ...


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

    def get(self, key: _K) -> Optional[_V]:
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


class DiskCache:
    """Disk-backed cache using SQLite, safe for concurrent use within a process.

    Values are serialised with :mod:`pickle`.  The database is created lazily
    on first use, and the parent directory is auto-created if it does not exist.

    Args:
        path: File system path for the SQLite database file.
        ttl: Seconds before a cached entry is considered stale.  Defaults to
             24 hours.
        maxsize: When set, the cache is pruned to at most *maxsize* entries
                 (oldest first) whenever a new entry is inserted.
    """

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS cache(
          key TEXT PRIMARY KEY,
          value BLOB NOT NULL,
          expires_at REAL NOT NULL
        );
    """
    _CREATE_INDEX = "CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at);"

    def __init__(
        self,
        path: str | Path,
        ttl: float = 86400.0,
        maxsize: Optional[int] = None,
    ) -> None:
        self._path = Path(path)
        self._ttl = ttl
        self._maxsize = maxsize
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Return (and lazily create) the SQLite connection."""
        if self._conn is not None:
            return self._conn
        self._path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._path), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(self._CREATE_TABLE)
        conn.execute(self._CREATE_INDEX)
        conn.commit()
        self._conn = conn
        return conn

    def _prune_expired(self, conn: sqlite3.Connection) -> None:
        conn.execute("DELETE FROM cache WHERE expires_at <= ?;", (time.monotonic(),))

    def _prune_maxsize(self, conn: sqlite3.Connection) -> None:
        if self._maxsize is None:
            return
        conn.execute(
            """
            DELETE FROM cache WHERE key IN (
                SELECT key FROM cache
                ORDER BY expires_at ASC
                LIMIT MAX(0, (SELECT COUNT(*) FROM cache) - ?)
            );
            """,
            (self._maxsize,),
        )

    # ------------------------------------------------------------------
    # Public interface (satisfies CacheBackend protocol)
    # ------------------------------------------------------------------

    def get(self, key: str) -> Any:
        """Return the cached value for *key*, or ``None`` if missing / expired."""
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?;", (key,)
            ).fetchone()
            if row is None:
                return None
            blob, expires_at = row
            if time.monotonic() > expires_at:
                conn.execute("DELETE FROM cache WHERE key = ?;", (key,))
                conn.commit()
                return None
            return pickle.loads(blob)  # noqa: S301

    def set(self, key: str, value: Any) -> None:
        """Store *value* under *key*."""
        blob = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        expires_at = time.monotonic() + self._ttl
        with self._lock:
            conn = self._connect()
            sql = (
                "INSERT OR REPLACE INTO cache(key, value, expires_at) VALUES (?, ?, ?);"
            )
            conn.execute(sql, (key, blob, expires_at))
            self._prune_maxsize(conn)
            conn.commit()

    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._lock:
            conn = self._connect()
            conn.execute("DELETE FROM cache;")
            conn.commit()

    def __len__(self) -> int:
        with self._lock:
            conn = self._connect()
            self._prune_expired(conn)
            conn.commit()
            row = conn.execute("SELECT COUNT(*) FROM cache;").fetchone()
            return int(row[0]) if row else 0

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None


class _NoCache(TTLCache[Any, Any]):
    """Drop-in TTLCache replacement that never stores anything."""

    def get(self, key: Any) -> None:
        return None

    def set(self, key: Any, value: Any) -> None:
        pass
