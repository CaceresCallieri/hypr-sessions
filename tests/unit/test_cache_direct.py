#!/usr/bin/env python3
"""
Direct test of path cache to verify it's working
"""

import sys
from pathlib import Path

# Add commands directory to path for imports (go up 2 levels from tests/unit/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "commands"))
from shared.path_cache import path_cache, enable_debug

def test_path_cache_directly():
    """Test path cache directly to ensure it's working"""
    print("=" * 60)
    print("DIRECT PATH CACHE TEST")
    print("=" * 60)
    
    # Enable debug
    enable_debug()
    path_cache.clear()
    
    print("\nTesting with real session paths...")
    
    # Test with actual session paths
    session_dir = Path.home() / ".config" / "hypr-sessions" / "sessions" / "test-session-2"
    session_file = session_dir / "session.json"
    
    print(f"Testing path: {session_dir}")
    
    # First check (should be cache miss)
    print("\n1. First exists() call (cache miss expected):")
    result1 = path_cache.exists(session_dir)
    stats1 = path_cache.get_stats()
    print(f"Result: {result1}")
    print(f"Stats: Hits={stats1['hits']}, Misses={stats1['misses']}")
    
    # Second check (should be cache hit)
    print("\n2. Second exists() call (cache hit expected):")
    result2 = path_cache.exists(session_dir)
    stats2 = path_cache.get_stats()
    print(f"Result: {result2}")
    print(f"Stats: Hits={stats2['hits']}, Misses={stats2['misses']}")
    
    # Check session file too
    print(f"\n3. Check session file: {session_file}")
    result3 = path_cache.exists(session_file)
    stats3 = path_cache.get_stats()
    print(f"Result: {result3}")
    print(f"Stats: Hits={stats3['hits']}, Misses={stats3['misses']}")
    
    # Check session file again (should be cache hit)
    print(f"\n4. Check session file again (cache hit expected):")
    result4 = path_cache.exists(session_file)
    stats4 = path_cache.get_stats()
    print(f"Result: {result4}")
    print(f"Stats: Hits={stats4['hits']}, Misses={stats4['misses']}")
    
    print(f"\nFINAL ANALYSIS:")
    print(f"Cache working: {stats4['hits'] > 0} (Expected: hits > 0)")
    print(f"Total hits: {stats4['hits']}")
    print(f"Total misses: {stats4['misses']}")
    print(f"Hit rate: {stats4['hit_rate_percent']:.1f}%")
    
    # Test invalidation
    print(f"\n5. Testing invalidation:")
    path_cache.invalidate(session_dir)
    stats5 = path_cache.get_stats()
    print(f"After invalidation - Stats: Hits={stats5['hits']}, Misses={stats5['misses']}, Size={stats5['size']}")
    
    # Check again after invalidation (should be cache miss)
    print(f"\n6. Check after invalidation (cache miss expected):")
    result6 = path_cache.exists(session_dir)
    stats6 = path_cache.get_stats()
    print(f"Result: {result6}")
    print(f"Stats: Hits={stats6['hits']}, Misses={stats6['misses']}")
    
    cache_worked = stats2['hits'] > stats1['hits']
    invalidation_worked = stats6['misses'] > stats5['misses']
    
    return cache_worked, invalidation_worked

if __name__ == "__main__":
    cache_worked, invalidation_worked = test_path_cache_directly()
    
    print(f"\n" + "=" * 60)
    print("RESULTS:")
    print(f"✓ Cache working: {cache_worked}")
    print(f"✓ Invalidation working: {invalidation_worked}")
    
    if cache_worked and invalidation_worked:
        print("🎉 PATH CACHE IS WORKING CORRECTLY!")
    else:
        print("❌ PATH CACHE HAS ISSUES!")