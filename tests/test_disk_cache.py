"""Tests for DiskCache and client integration with disk-backed cache."""

from __future__ import annotations

import time

import httpx
import respx

from opentargets import DiskCache, OpenTargetsClient

_GQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"


# ---------------------------------------------------------------------------
# DiskCache unit tests
# ---------------------------------------------------------------------------


def test_disk_cache_set_get_basic(tmp_path):
    """A value stored via set() is returned by get()."""
    cache = DiskCache(tmp_path / "cache.db")
    cache.set("hello", "world")
    assert cache.get("hello") == "world"
    cache.close()


def test_disk_cache_miss_returns_none(tmp_path):
    """get() on a missing key returns None."""
    cache = DiskCache(tmp_path / "cache.db")
    assert cache.get("nonexistent") is None
    cache.close()


def test_disk_cache_ttl_expiry(tmp_path, monkeypatch):
    """An entry whose TTL has elapsed is not returned."""
    cache = DiskCache(tmp_path / "cache.db", ttl=1.0)
    cache.set("key", "value")
    # Advance monotonic clock by more than 1 s
    _real_monotonic = time.monotonic
    monkeypatch.setattr(time, "monotonic", lambda: _real_monotonic() + 2.0)
    assert cache.get("key") is None
    cache.close()


def test_disk_cache_persists_across_instances(tmp_path):
    """Values survive closing and re-opening the database file."""
    db_path = tmp_path / "cache.db"

    cache1 = DiskCache(db_path, ttl=3600.0)
    cache1.set("persistent_key", {"data": 42})
    cache1.close()

    cache2 = DiskCache(db_path, ttl=3600.0)
    result = cache2.get("persistent_key")
    assert result == {"data": 42}
    cache2.close()


def test_disk_cache_clear(tmp_path):
    """clear() removes all entries and len() returns 0."""
    cache = DiskCache(tmp_path / "cache.db")
    cache.set("a", 1)
    cache.set("b", 2)
    assert len(cache) == 2
    cache.clear()
    assert len(cache) == 0
    assert cache.get("a") is None
    cache.close()


def test_disk_cache_maxsize_prunes(tmp_path):
    """When maxsize is set, inserting beyond it prunes the oldest entries."""
    cache = DiskCache(tmp_path / "cache.db", ttl=3600.0, maxsize=3)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    cache.set("d", 4)  # should prune "a"
    # At most 3 entries should remain
    assert len(cache) <= 3
    # Newest entry must still be present
    assert cache.get("d") == 4
    cache.close()


def test_disk_cache_auto_creates_parent_dir(tmp_path):
    """DiskCache auto-creates missing parent directories."""
    nested = tmp_path / "a" / "b" / "c" / "cache.db"
    cache = DiskCache(nested)
    cache.set("x", 99)
    assert cache.get("x") == 99
    cache.close()


def test_disk_cache_len_excludes_expired(tmp_path, monkeypatch):
    """len() does not count expired entries."""
    cache = DiskCache(tmp_path / "cache.db", ttl=1.0)
    cache.set("alive", "yes")
    cache.set("dying", "no")

    _real_monotonic = time.monotonic
    monkeypatch.setattr(time, "monotonic", lambda: _real_monotonic() + 2.0)

    assert len(cache) == 0
    cache.close()


# ---------------------------------------------------------------------------
# Integration: client uses DiskCache, second call skips network
# ---------------------------------------------------------------------------


@respx.mock
def test_client_with_disk_cache(tmp_path, target_response):
    """A second identical query is served from DiskCache without a network call."""
    db_path = tmp_path / "client_cache.db"
    disk_cache = DiskCache(db_path, ttl=3600.0)

    route = respx.post(_GQL_URL).mock(
        return_value=httpx.Response(200, json=target_response)
    )

    client = OpenTargetsClient(cache=disk_cache)

    # First call — hits the network once (TARGET_QUERY)
    target1 = client.get_target("ENSG00000146648")
    assert target1.approved_symbol == "EGFR"
    first_call_count = route.call_count

    # Second call — should be served from cache, no additional network hit
    target2 = client.get_target("ENSG00000146648")
    assert target2.approved_symbol == "EGFR"
    assert route.call_count == first_call_count, (
        "Expected no additional network requests on cache hit"
    )

    disk_cache.close()
