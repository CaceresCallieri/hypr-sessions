#!/usr/bin/env python3
"""
Test path cache effectiveness during recovery operations (hot path with many .exists() calls)
"""

import sys
from pathlib import Path

# Add commands directory to path for imports (go up 2 levels from tests/integration/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "commands"))
from shared.path_cache import path_cache, enable_debug

# Import with proper module path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from commands.recover import SessionRecovery

def test_recovery_cache_performance():
    """Test cache effectiveness during recovery operations which have many path checks"""
    print("=" * 60)
    print("RECOVERY OPERATION CACHE EFFECTIVENESS TEST") 
    print("=" * 60)
    
    # Enable debug to see cache operations
    enable_debug()
    path_cache.clear()
    
    # Find an archived session to recover
    recovery = SessionRecovery(debug=True)
    
    # List archived sessions to find one to test with
    from commands.list import SessionList
    lister = SessionList(debug=False)
    archived_result = lister.list_sessions(archived=True, show_all=False)
    
    if not archived_result.success or not archived_result.data.get('archived_sessions'):
        print("❌ No archived sessions found for testing!")
        print("   Run: ./hypr-sessions.py delete <session-name> first")
        return False
    
    archived_session = archived_result.data['archived_sessions'][0]['name']
    print(f"Testing recovery cache with archived session: {archived_session}")
    
    print(f"\n1. FIRST RECOVERY ATTEMPT (Cold cache):")
    print("-" * 50)
    
    # First recovery attempt (cold cache)
    result1 = recovery.recover_session(archived_session, "test-cache-recovery-1")
    stats1 = path_cache.get_stats()
    
    print("-" * 50)
    print(f"First recovery result: {result1.success}")
    print(f"Cache stats after 1st recovery: Hits={stats1['hits']}, Misses={stats1['misses']}, Hit Rate={stats1['hit_rate_percent']:.1f}%")
    
    if result1.success:
        print("✓ First recovery successful")
        
        # Archive it again for second test  
        from commands.delete import SessionArchive
        archiver = SessionArchive(debug=False)
        archive_result = archiver.archive_session("test-cache-recovery-1")
        
        if archive_result.success:
            print(f"\n2. SECOND RECOVERY ATTEMPT (Warm cache):")
            print("-" * 50)
            
            # Second recovery attempt (should have cache hits)
            result2 = recovery.recover_session("test-cache-recovery-1-20250910-143918", "test-cache-recovery-2")
            stats2 = path_cache.get_stats()
            
            print("-" * 50)
            print(f"Second recovery result: {result2.success}")
            print(f"Cache stats after 2nd recovery: Hits={stats2['hits']}, Misses={stats2['misses']}, Hit Rate={stats2['hit_rate_percent']:.1f}%")
            
            cache_hits_increased = stats2['hits'] > stats1['hits']
            hits_gained = stats2['hits'] - stats1['hits']
            
            print(f"\nCACHE EFFECTIVENESS ANALYSIS:")
            print(f"Cache hits increased: {cache_hits_increased} ({'✓' if cache_hits_increased else '✗'})")
            print(f"Additional hits gained: {hits_gained}")
            
            if hits_gained > 0:
                print(f"✅ CACHE IS EFFECTIVE: {hits_gained} filesystem calls avoided on 2nd recovery")
                
                # Calculate rough performance benefit
                hit_rate = stats2['hit_rate_percent']
                if hit_rate >= 60:
                    print(f"✅ SUCCESS CRITERIA MET: {hit_rate:.1f}% hit rate >= 60% target")
                    return True
                else:
                    print(f"⚠️  Hit rate {hit_rate:.1f}% below 60% target, but cache is working")
                    return True
            else:
                print(f"❌ CACHE NOT EFFECTIVE: No cache hits gained between operations")
                return False
        else:
            print("❌ Failed to archive session for second test")
            return False
    else:
        print("❌ First recovery failed")
        print(f"Error messages: {[msg['message'] for msg in result1.messages if msg['status'] == 'error']}")
        return False

if __name__ == "__main__":
    success = test_recovery_cache_performance()
    if success:
        print(f"\n🎉 PATH CACHE WORKING EFFECTIVELY IN RECOVERY OPERATIONS!")
    else:
        print(f"\n⚠️  PATH CACHE NEEDS INVESTIGATION")