# Hypr Sessions Test Suite

pytest-based test suite for hypr-sessions core components.

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run only path cache tests
python -m pytest tests/unit/test_path_cache.py -v

# Run a specific test class
python -m pytest tests/unit/test_path_cache.py::TestTTLExpiration -v
```

## Directory Structure

```
tests/
  conftest.py             # Shared fixtures (tmp_path session dirs, fresh caches)
  unit/
    test_path_cache.py    # PathCache unit tests
```

## Fixtures (conftest.py)

| Fixture                | Description                                              |
|------------------------|----------------------------------------------------------|
| `session_dir`          | Empty session directory layout (sessions/ + archived/)   |
| `populated_session_dir`| Pre-populated with sample session folders and JSON files |
| `fresh_cache`          | New PathCache(ttl=5s, max=1000) — not the global singleton |
| `small_cache`          | PathCache(max=5) for eviction testing                    |
| `short_ttl_cache`      | PathCache(ttl=0.1s) for expiration testing               |

## Test Coverage

### PathCache (`commands/shared/path_cache.py`)

- **Hit / miss**: First lookup misses, second hits, correct boolean results
- **Invalidation**: Single-path, child-path, and directory-level invalidation
- **TTL expiration**: Entries expire and re-check filesystem after TTL elapses
- **Eviction**: Oldest entries removed when max_size exceeded
- **Thread safety**: Concurrent reads, mixed read/invalidate, size bounds under contention
- **Statistics**: Hit rate calculation, counter tracking, initial state
- **Configuration**: Custom TTL, max_size, debug flag

## Debug / Benchmark Scripts

The `debug_path_cache.py` script (formerly in tests/integration/) has been moved to
`scripts/` as it is a debugging tool, not a test.
