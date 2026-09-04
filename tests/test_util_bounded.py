import time
import pytest
from openfactory.util.bounded import BoundedDict, LRUCache, TokenBucket

def test_bounded_dict_fifo_eviction():
    d = BoundedDict(3)
    d["a"] = 1
    d["b"] = 2
    d["c"] = 3
    assert len(d) == 3
    assert d.evicted == 0

    d["d"] = 4
    assert len(d) == 3
    assert d.evicted == 1
    assert "a" not in d
    assert d["b"] == 2
    assert d["c"] == 3
    assert d["d"] == 4

def test_bounded_dict_reassignment_no_eviction():
    d = BoundedDict(3)
    d["a"] = 1
    d["b"] = 2
    d["c"] = 3
    d["a"] = 10
    assert len(d) == 3
    assert d.evicted == 0
    assert d["a"] == 10

def test_lru_cache_eviction():
    c = LRUCache(3)
    c["a"] = 1
    c["b"] = 2
    c["c"] = 3

    # Access "a" to make it most recently used
    _ = c["a"]

    # Add "d", should evict "b" (least recently used)
    c["d"] = 4
    assert len(c) == 3
    assert c.evicted == 1
    assert "b" not in c
    assert "a" in c
    assert "c" in c
    assert "d" in c

def test_lru_cache_get_updates_recency():
    c = LRUCache(3)
    c["a"] = 1
    c["b"] = 2
    c["c"] = 3

    # Access "a" via get to make it most recently used
    _ = c.get("a")

    # Add "d", should evict "b"
    c["d"] = 4
    assert "b" not in c
    assert "a" in c

def test_token_bucket_initial_state():
    tb = TokenBucket(10, 1)
    assert tb.available == 10
    assert tb.capacity == 10
    assert tb.refill_rate_per_sec == 1

def test_token_bucket_consumption(monkeypatch):
    class FakeTime:
        def __init__(self):
            self.t = 1000.0
        def time(self):
            return self.t

    clock = FakeTime()
    monkeypatch.setattr(time, "time", clock.time)

    tb = TokenBucket(10, 1)
    assert tb.consume(5) is True
    assert tb.available == 5

    assert tb.consume(6) is False  # Not enough tokens
    assert tb.consume(5) is True
    assert tb.available == 0

def test_token_bucket_refill(monkeypatch):
    class FakeTime:
        def __init__(self):
            self.t = 1000.0
        def time(self):
            return self.t

    clock = FakeTime()
    monkeypatch.setattr(time, "time", clock.time)

    tb = TokenBucket(10, 2) # capacity 10, 2 tokens per sec
    assert tb.consume(10) is True
    assert tb.available == 0

    # advance 2 seconds -> should refill 4 tokens
    clock.t += 2.0
    assert tb.available == 4
    assert tb.consume(4) is True
    assert tb.consume(1) is False

    # advance 10 seconds -> should refill to capacity (10)
    clock.t += 10.0
    assert tb.available == 10
    assert tb.consume(10) is True
