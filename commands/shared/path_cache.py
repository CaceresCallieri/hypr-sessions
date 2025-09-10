"""
Path existence caching system for improved filesystem operation performance
"""

import time
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Set
from .debug import CommandDebugger


@dataclass
class CacheEntry:
    """Cache entry storing existence status and timestamp"""
    exists: bool
    timestamp: float


class PathCache:
    """Thread-safe path existence cache with TTL and size management"""
    
    def __init__(self, ttl_seconds: float = 5.0, max_size: int = 1000, debug: bool = False):
        """Initialize path cache with configurable TTL and size limits
        
        Args:
            ttl_seconds: Time to live for cache entries (default: 5.0 seconds)
            max_size: Maximum number of cached paths (default: 1000)
            debug: Enable debug logging (default: False)
        """
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self.debugger = CommandDebugger("PathCache", debug)
        
        # Performance tracking
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
    def exists(self, path: Path) -> bool:
        """Check if path exists, using cache when possible
        
        Args:
            path: Path to check for existence
            
        Returns:
            bool: True if path exists, False otherwise
        """
        path_str = str(path.absolute())
        current_time = time.time()
        
        with self._lock:
            # Check cache first
            entry = self._cache.get(path_str)
            if entry and (current_time - entry.timestamp) < self.ttl:
                self._hits += 1
                self.debugger.debug(f"Cache HIT: {path_str} -> {entry.exists}")
                return entry.exists
            
            # Cache miss or expired - check filesystem
            self._misses += 1
            exists_result = path.exists()
            self.debugger.debug(f"Cache MISS: {path_str} -> {exists_result} (filesystem check)")
            
            # Update cache
            self._cache[path_str] = CacheEntry(exists_result, current_time)
            
            # Manage cache size
            if len(self._cache) > self.max_size:
                self._evict_oldest()
                
            return exists_result
    
    def invalidate(self, path: Path):
        """Invalidate cache entry for path and potentially affected child paths
        
        Args:
            path: Path to invalidate (removes exact match and child paths)
        """
        path_str = str(path.absolute())
        
        with self._lock:
            removed_count = 0
            
            # Remove exact match
            if path_str in self._cache:
                del self._cache[path_str]
                removed_count += 1
                
            # Remove child paths that might be affected
            # If we delete a directory, any cached children are potentially stale
            if path.is_dir() or not path.exists():
                path_prefix = path_str + "/"
                to_remove = [k for k in self._cache.keys() if k.startswith(path_prefix)]
                for key in to_remove:
                    del self._cache[key]
                    removed_count += 1
                    
            self.debugger.debug(f"Invalidated {removed_count} cache entries for {path_str}")
    
    def invalidate_directory(self, directory: Path):
        """Invalidate all cache entries within a directory
        
        Args:
            directory: Directory path to invalidate (removes all children)
        """
        dir_str = str(directory.absolute())
        
        with self._lock:
            # Remove all paths within this directory
            to_remove = [k for k in self._cache.keys() 
                        if k.startswith(dir_str + "/") or k == dir_str]
            removed_count = len(to_remove)
            
            for key in to_remove:
                del self._cache[key]
                
            self.debugger.debug(f"Invalidated directory {dir_str}: removed {removed_count} entries")
    
    def clear(self):
        """Clear entire cache"""
        with self._lock:
            cache_size = len(self._cache)
            self._cache.clear()
            self.debugger.debug(f"Cleared entire cache: removed {cache_size} entries")
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache performance statistics
        
        Returns:
            dict: Statistics including hits, misses, size, evictions
        """
        with self._lock:
            hit_rate = self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._cache),
                "max_size": self.max_size,
                "evictions": self._evictions,
                "hit_rate_percent": round(hit_rate * 100, 2)
            }
    
    def _evict_oldest(self):
        """Remove oldest cache entries when size limit is exceeded"""
        if not self._cache:
            return
            
        # Find oldest entries by timestamp
        entries_by_age = sorted(
            self._cache.items(), 
            key=lambda item: item[1].timestamp
        )
        
        # Remove oldest 10% when cache is full
        evict_count = max(1, len(self._cache) // 10)
        evicted = 0
        
        for key, _ in entries_by_age[:evict_count]:
            if key in self._cache:  # Still exists (thread safety)
                del self._cache[key]
                evicted += 1
                
        self._evictions += evicted
        self.debugger.debug(f"Evicted {evicted} oldest cache entries")


# Global cache instance for shared usage across the application
# Using conservative defaults suitable for session management operations
path_cache = PathCache(ttl_seconds=5.0, max_size=1000, debug=False)


def enable_debug():
    """Enable debug logging for the global path cache"""
    path_cache.debugger.enabled = True


def get_cache_stats() -> Dict[str, int]:
    """Get performance statistics for the global path cache
    
    Returns:
        dict: Cache performance metrics
    """
    return path_cache.get_stats()