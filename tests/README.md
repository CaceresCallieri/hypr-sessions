# Hypr Sessions Test Suite

This directory contains tests for various components of the hypr-sessions system, organized by test type and purpose.

## Directory Structure

### `unit/` - Unit Tests
Direct testing of individual components in isolation.

- **`test_cache_direct.py`** - Direct unit tests for path cache functionality
  - Tests basic cache hit/miss behavior
  - Tests cache invalidation
  - Verifies thread-safe operations
  - **Usage**: `python tests/unit/test_cache_direct.py`

### `performance/` - Performance Tests
Benchmarking and performance measurement tools.

- **`test_path_cache_performance.py`** - In-process performance testing
  - Measures cache effectiveness within single Python process
  - Tests session list operations with cache statistics
  - **Usage**: `python tests/performance/test_path_cache_performance.py`

- **`benchmark_path_cache.py`** - Cross-process benchmark suite
  - Measures performance across subprocess calls
  - Compares cached vs uncached operation timing
  - **Usage**: `python tests/performance/benchmark_path_cache.py`

### `integration/` - Integration Tests
End-to-end testing of components working together.

- **`test_recovery_cache.py`** - Recovery operation cache integration
  - Tests cache effectiveness during session recovery
  - Tests real archive/recovery workflows
  - **Usage**: `python tests/integration/test_recovery_cache.py`

- **`debug_path_cache.py`** - Debug and troubleshooting tool
  - Enables debug output to analyze cache behavior
  - Useful for investigating cache issues
  - **Usage**: `python tests/integration/debug_path_cache.py`

## Test Categories

### Path Cache Testing
All tests related to the path caching system implemented in `commands/shared/path_cache.py`.

**Key Test Scenarios**:
- Basic cache functionality (hit/miss patterns)
- Cache invalidation after filesystem modifications
- Performance improvements in repeated operations
- Thread safety for UI usage
- TTL (time-to-live) expiration behavior
- Cache size management and eviction

### Performance Validation
Tests that verify the path cache system meets performance criteria:
- ✅ Reduce filesystem calls by 60%+ (measured via hit rate)
- ✅ Improve operation performance by 20%+ (timed measurements)
- ✅ Cache invalidation correctness
- ✅ Thread-safe operations

## Running Tests

### Quick Validation
To quickly verify path cache functionality:
```bash
python tests/unit/test_cache_direct.py
```

### Performance Analysis
To analyze cache performance impact:
```bash
python tests/performance/test_path_cache_performance.py
```

### Debug Cache Issues
To troubleshoot cache behavior:
```bash
python tests/integration/debug_path_cache.py
```

### Full Integration Test
To test cache in real recovery scenarios:
```bash
# First create an archived session
./hypr-sessions.py delete "some-session-name"

# Then test recovery cache effectiveness
python tests/integration/test_recovery_cache.py
```

## Test Dependencies

All tests require:
- Python 3.7+
- Access to hypr-sessions project commands
- Proper session directory structure (`~/.config/hypr-sessions/`)

Integration tests may require:
- Existing session data
- Archive/recovery test scenarios

## Maintenance

These tests should be run:
- **After path cache modifications** - Verify functionality
- **During performance optimization** - Measure improvements
- **When debugging cache issues** - Analyze behavior
- **Before releases** - Ensure cache system stability

## Future Test Additions

Consider adding tests for:
- UI cache integration (fabric-ui components)
- Cache behavior under high concurrency
- Cache performance with large session counts
- Memory usage profiling for cache size tuning