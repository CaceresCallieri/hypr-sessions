#!/usr/bin/env python3
"""
Debug script to see what paths are being checked during session operations
"""

import sys
from pathlib import Path

# Add commands directory to path for imports (go up 2 levels from tests/integration/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "commands"))
from shared.path_cache import path_cache, enable_debug

# Import SessionList with proper module path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from commands.list import SessionList

def debug_path_operations():
    """Debug what path operations are being performed"""
    print("=" * 60)
    print("PATH CACHE DEBUG - WHAT PATHS ARE BEING CHECKED")
    print("=" * 60)
    
    # Enable debug output
    enable_debug()
    path_cache.clear()
    
    print("\nRunning session list with debug enabled...")
    print("-" * 40)
    
    # Create session lister and run it
    lister = SessionList(debug=True)
    result = lister.list_sessions(archived=False, show_all=False)
    
    print("-" * 40)
    print(f"\nOperation completed. Success: {result.success}")
    
    # Show final cache stats
    stats = path_cache.get_stats()
    print(f"Final cache statistics:")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Hit rate: {stats['hit_rate_percent']:.1f}%")
    print(f"  Cache size: {stats['size']}")
    
    print(f"\nSession count found: {len(result.data.get('active_sessions', []))}")
    
    # Run again to see cache effectiveness
    print("\n" + "=" * 60)
    print("SECOND RUN - SHOULD SHOW CACHE HITS")
    print("=" * 60)
    
    print("\nRunning session list again...")
    print("-" * 40)
    
    result2 = lister.list_sessions(archived=False, show_all=False)
    
    print("-" * 40)
    print(f"\nSecond operation completed. Success: {result2.success}")
    
    # Show final cache stats after second run
    final_stats = path_cache.get_stats()
    print(f"Final cache statistics after second run:")
    print(f"  Hits: {final_stats['hits']}")
    print(f"  Misses: {final_stats['misses']}")
    print(f"  Hit rate: {final_stats['hit_rate_percent']:.1f}%")
    print(f"  Cache size: {final_stats['size']}")
    
    cache_hits_increased = final_stats['hits'] > stats['hits']
    print(f"\nCache effectiveness: {'✓' if cache_hits_increased else '✗'} ({final_stats['hits'] - stats['hits']} new hits)")

if __name__ == "__main__":
    debug_path_operations()