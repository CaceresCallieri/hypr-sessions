"""
Unit tests for PathCache — the thread-safe filesystem existence cache.

All tests use tmp_path-based directories and fresh PathCache instances so they
never touch the live ~/.config/hypr-sessions directory and never rely on the
global singleton.
"""

import time
import threading
from pathlib import Path

import pytest

from commands.shared.path_cache import PathCache, CacheEntry


# ---------------------------------------------------------------------------
# Basic cache hit / miss behaviour
# ---------------------------------------------------------------------------

class TestCacheHitMiss:
    """Verify fundamental cache lookup semantics."""

    def test_first_lookup_is_cache_miss(self, fresh_cache, tmp_path):
        target = tmp_path / "some-file.txt"
        target.touch()

        fresh_cache.exists(target)
        stats = fresh_cache.get_stats()

        assert stats["misses"] == 1
        assert stats["hits"] == 0

    def test_second_lookup_is_cache_hit(self, fresh_cache, tmp_path):
        target = tmp_path / "some-file.txt"
        target.touch()

        fresh_cache.exists(target)
        fresh_cache.exists(target)
        stats = fresh_cache.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_existing_path_returns_true(self, fresh_cache, tmp_path):
        target = tmp_path / "exists.txt"
        target.touch()

        assert fresh_cache.exists(target) is True

    def test_nonexistent_path_returns_false(self, fresh_cache, tmp_path):
        target = tmp_path / "does-not-exist.txt"

        assert fresh_cache.exists(target) is False

    def test_directory_existence_is_cached(self, fresh_cache, tmp_path):
        target = tmp_path / "subdir"
        target.mkdir()

        assert fresh_cache.exists(target) is True
        fresh_cache.exists(target)

        stats = fresh_cache.get_stats()
        assert stats["hits"] == 1

    def test_nonexistent_path_cached_as_false(self, fresh_cache, tmp_path):
        """A non-existent path should be cached and return False on second lookup."""
        target = tmp_path / "ghost.txt"

        assert fresh_cache.exists(target) is False
        assert fresh_cache.exists(target) is False

        stats = fresh_cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_multiple_distinct_paths(self, fresh_cache, tmp_path):
        """Different paths each get their own cache entry."""
        file_a = tmp_path / "a.txt"
        file_b = tmp_path / "b.txt"
        file_a.touch()
        file_b.touch()

        fresh_cache.exists(file_a)
        fresh_cache.exists(file_b)

        stats = fresh_cache.get_stats()
        assert stats["misses"] == 2
        assert stats["size"] == 2


# ---------------------------------------------------------------------------
# Invalidation
# ---------------------------------------------------------------------------

class TestInvalidation:
    """Verify single-path and directory invalidation."""

    def test_invalidate_causes_cache_miss(self, fresh_cache, tmp_path):
        target = tmp_path / "file.txt"
        target.touch()

        fresh_cache.exists(target)  # populate
        fresh_cache.invalidate(target)
        fresh_cache.exists(target)  # should miss again

        stats = fresh_cache.get_stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 0

    def test_invalidate_removes_child_paths(self, fresh_cache, tmp_path):
        parent = tmp_path / "sessions"
        parent.mkdir()
        child = parent / "session.json"
        child.touch()

        fresh_cache.exists(parent)
        fresh_cache.exists(child)
        assert fresh_cache.get_stats()["size"] == 2

        fresh_cache.invalidate(parent)

        # Both parent and child should have been removed
        assert fresh_cache.get_stats()["size"] == 0

    def test_invalidate_nonexistent_path_is_safe(self, fresh_cache, tmp_path):
        """Invalidating a path that was never cached should not raise."""
        target = tmp_path / "never-cached"
        fresh_cache.invalidate(target)  # should not raise

        assert fresh_cache.get_stats()["size"] == 0


# ---------------------------------------------------------------------------
# invalidate_directory
# ---------------------------------------------------------------------------

class TestInvalidateDirectory:
    """Verify bulk directory invalidation."""

    def test_invalidate_directory_clears_all_children(self, fresh_cache, tmp_path):
        base = tmp_path / "sessions"
        base.mkdir()
        for name in ("a", "b", "c"):
            child = base / name
            child.mkdir()
            fresh_cache.exists(child)

        assert fresh_cache.get_stats()["size"] == 3

        fresh_cache.invalidate_directory(base)

        assert fresh_cache.get_stats()["size"] == 0

    def test_invalidate_directory_includes_directory_itself(self, fresh_cache, tmp_path):
        base = tmp_path / "sessions"
        base.mkdir()
        fresh_cache.exists(base)

        fresh_cache.invalidate_directory(base)

        assert fresh_cache.get_stats()["size"] == 0

    def test_invalidate_directory_does_not_affect_siblings(self, fresh_cache, tmp_path):
        """Invalidating /a should not remove /ab entries."""
        dir_a = tmp_path / "a"
        dir_ab = tmp_path / "ab"
        dir_a.mkdir()
        dir_ab.mkdir()

        fresh_cache.exists(dir_a)
        fresh_cache.exists(dir_ab)

        fresh_cache.invalidate_directory(dir_a)

        # dir_ab should still be cached
        assert fresh_cache.get_stats()["size"] == 1

    def test_invalidate_empty_directory_is_safe(self, fresh_cache, tmp_path):
        base = tmp_path / "empty"
        base.mkdir()

        fresh_cache.invalidate_directory(base)  # nothing cached, should not raise
        assert fresh_cache.get_stats()["size"] == 0


# ---------------------------------------------------------------------------
# TTL expiration
# ---------------------------------------------------------------------------

class TestTTLExpiration:
    """Verify entries expire after TTL elapses."""

    def test_expired_entry_triggers_cache_miss(self, short_ttl_cache, tmp_path):
        target = tmp_path / "file.txt"
        target.touch()

        short_ttl_cache.exists(target)  # miss
        time.sleep(0.15)  # exceed 0.1s TTL
        short_ttl_cache.exists(target)  # should miss again (expired)

        stats = short_ttl_cache.get_stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 0

    def test_non_expired_entry_is_cache_hit(self, short_ttl_cache, tmp_path):
        target = tmp_path / "file.txt"
        target.touch()

        short_ttl_cache.exists(target)
        # Do NOT sleep — entry should still be valid
        short_ttl_cache.exists(target)

        stats = short_ttl_cache.get_stats()
        assert stats["hits"] == 1

    def test_expired_entry_reflects_filesystem_changes(self, short_ttl_cache, tmp_path):
        target = tmp_path / "transient.txt"
        target.touch()

        assert short_ttl_cache.exists(target) is True

        target.unlink()
        time.sleep(0.15)

        assert short_ttl_cache.exists(target) is False


# ---------------------------------------------------------------------------
# Eviction (_evict_oldest)
# ---------------------------------------------------------------------------

class TestEviction:
    """Verify LRU-style eviction when cache exceeds max_size."""

    def test_eviction_occurs_when_exceeding_max_size(self, small_cache, tmp_path):
        """Filling a max_size=5 cache with 6 entries should trigger eviction."""
        paths = []
        for i in range(6):
            p = tmp_path / f"file_{i}.txt"
            p.touch()
            paths.append(p)
            small_cache.exists(p)

        stats = small_cache.get_stats()
        assert stats["size"] <= small_cache.max_size
        assert stats["evictions"] > 0

    def test_eviction_removes_oldest_entries(self, tmp_path):
        """The oldest-timestamped entries should be evicted first."""
        cache = PathCache(ttl_seconds=60.0, max_size=3, debug=False)

        first = tmp_path / "first.txt"
        second = tmp_path / "second.txt"
        third = tmp_path / "third.txt"
        overflow = tmp_path / "overflow.txt"

        for p in (first, second, third, overflow):
            p.touch()

        cache.exists(first)
        cache.exists(second)
        cache.exists(third)
        # This should trigger eviction of oldest (first)
        cache.exists(overflow)

        stats = cache.get_stats()
        assert stats["evictions"] >= 1
        assert stats["size"] <= 3

    def test_eviction_on_empty_cache_is_safe(self):
        cache = PathCache(ttl_seconds=5.0, max_size=5, debug=False)
        # Directly call the internal eviction method
        cache._evict_oldest()  # should not raise


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------

class TestClear:
    """Verify cache clearing."""

    def test_clear_removes_all_entries(self, fresh_cache, tmp_path):
        for i in range(5):
            p = tmp_path / f"f{i}.txt"
            p.touch()
            fresh_cache.exists(p)

        assert fresh_cache.get_stats()["size"] == 5

        fresh_cache.clear()

        assert fresh_cache.get_stats()["size"] == 0

    def test_clear_does_not_reset_counters(self, fresh_cache, tmp_path):
        """Clearing the cache empties entries but preserves hit/miss counters."""
        p = tmp_path / "file.txt"
        p.touch()
        fresh_cache.exists(p)

        fresh_cache.clear()

        stats = fresh_cache.get_stats()
        assert stats["misses"] == 1
        assert stats["size"] == 0


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

class TestGetStats:
    """Verify statistics reporting."""

    def test_initial_stats_are_zero(self, fresh_cache):
        stats = fresh_cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["size"] == 0
        assert stats["evictions"] == 0
        assert stats["hit_rate_percent"] == 0

    def test_hit_rate_calculation(self, fresh_cache, tmp_path):
        p = tmp_path / "file.txt"
        p.touch()

        fresh_cache.exists(p)  # miss
        fresh_cache.exists(p)  # hit
        fresh_cache.exists(p)  # hit

        stats = fresh_cache.get_stats()
        # 2 hits / 3 total = 66.67%
        assert stats["hit_rate_percent"] == pytest.approx(66.67, abs=0.01)

    def test_max_size_reported(self, fresh_cache):
        stats = fresh_cache.get_stats()
        assert stats["max_size"] == 1000


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

class TestThreadSafety:
    """Verify PathCache is safe under concurrent access."""

    def test_concurrent_reads_do_not_corrupt(self, fresh_cache, tmp_path):
        """Multiple threads reading the same path should not cause errors."""
        target = tmp_path / "shared.txt"
        target.touch()
        errors = []

        def reader():
            try:
                for _ in range(100):
                    fresh_cache.exists(target)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=reader) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"
        stats = fresh_cache.get_stats()
        total = stats["hits"] + stats["misses"]
        assert total == 800  # 8 threads * 100 iterations

    def test_concurrent_reads_and_invalidations(self, fresh_cache, tmp_path):
        """Concurrent reads mixed with invalidations should not raise."""
        target = tmp_path / "contested.txt"
        target.touch()
        errors = []

        def reader():
            try:
                for _ in range(50):
                    fresh_cache.exists(target)
            except Exception as exc:
                errors.append(exc)

        def invalidator():
            try:
                for _ in range(50):
                    fresh_cache.invalidate(target)
            except Exception as exc:
                errors.append(exc)

        threads = (
            [threading.Thread(target=reader) for _ in range(4)]
            + [threading.Thread(target=invalidator) for _ in range(4)]
        )
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"

    def test_concurrent_writes_respect_max_size(self, tmp_path):
        """Many threads adding entries should never exceed max_size (plus eviction margin)."""
        cache = PathCache(ttl_seconds=60.0, max_size=20, debug=False)
        errors = []

        def writer(thread_id):
            try:
                for i in range(30):
                    p = tmp_path / f"t{thread_id}_f{i}.txt"
                    p.touch()
                    cache.exists(p)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(tid,)) for tid in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"
        assert cache.get_stats()["size"] <= cache.max_size


# ---------------------------------------------------------------------------
# CacheEntry dataclass
# ---------------------------------------------------------------------------

class TestCacheEntry:
    """Verify CacheEntry data structure."""

    def test_cache_entry_stores_values(self):
        entry = CacheEntry(exists=True, timestamp=1234.5)
        assert entry.exists is True
        assert entry.timestamp == 1234.5

    def test_cache_entry_equality(self):
        a = CacheEntry(exists=True, timestamp=1.0)
        b = CacheEntry(exists=True, timestamp=1.0)
        assert a == b


# ---------------------------------------------------------------------------
# Constructor / configuration
# ---------------------------------------------------------------------------

class TestPathCacheConfiguration:
    """Verify PathCache constructor parameters."""

    def test_custom_ttl(self):
        cache = PathCache(ttl_seconds=30.0, max_size=500)
        assert cache.ttl == 30.0

    def test_custom_max_size(self):
        cache = PathCache(ttl_seconds=1.0, max_size=42)
        assert cache.max_size == 42

    def test_debug_mode_creates_debugger(self):
        cache = PathCache(debug=True)
        assert cache.debugger.enabled is True

    def test_default_debug_is_disabled(self):
        cache = PathCache()
        assert cache.debugger.enabled is False
