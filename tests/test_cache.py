"""Tests for TTLCache."""

from __future__ import annotations

import time

from opentargets._cache import TTLCache


def test_basic_set_get():
    cache: TTLCache[str, int] = TTLCache()
    cache.set("a", 1)
    assert cache.get("a") == 1


def test_miss_returns_none():
    cache: TTLCache[str, int] = TTLCache()
    assert cache.get("missing") is None


def test_expired_returns_none():
    cache: TTLCache[str, int] = TTLCache(ttl=0.01)
    cache.set("x", 42)
    time.sleep(0.05)
    assert cache.get("x") is None


def test_lru_eviction():
    cache: TTLCache[str, int] = TTLCache(maxsize=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)  # evicts "a"
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_len():
    cache: TTLCache[str, int] = TTLCache()
    cache.set("a", 1)
    cache.set("b", 2)
    assert len(cache) == 2


def test_clear():
    cache: TTLCache[str, int] = TTLCache()
    cache.set("a", 1)
    cache.clear()
    assert len(cache) == 0
    assert cache.get("a") is None
