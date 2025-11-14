"""
Result Cache - Cache quantum calculations to avoid expensive recomputation
"""
import json
import hashlib
import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import threading


class ResultCache:
    """Thread-safe caching system for quantum calculation results"""
    
    def __init__(self, cache_dir: str = 'cache', ttl_hours: int = 24):
        """
        Initialize cache
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        self.lock = threading.Lock()
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_key(self, elements: list, geometry: Optional[Dict] = None) -> str:
        """
        Generate unique cache key for molecule
        
        Args:
            elements: List of element symbols
            geometry: Molecular geometry
            
        Returns:
            Cache key (hash)
        """
        # Sort elements to make key order-independent for same molecule
        sorted_elements = sorted(elements)
        
        # Create unique identifier
        identifier = {
            'elements': sorted_elements,
            'geometry': geometry if geometry else None
        }
        
        # Hash to create key
        key_str = json.dumps(identifier, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> str:
        """Get file path for cache key"""
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def get(self, elements: list, geometry: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached result
        
        Args:
            elements: List of element symbols
            geometry: Molecular geometry
            
        Returns:
            Cached result or None if not found/expired
        """
        key = self._get_cache_key(elements, geometry)
        cache_path = self._get_cache_path(key)
        
        with self.lock:
            if not os.path.exists(cache_path):
                return None
            
            try:
                with open(cache_path, 'r') as f:
                    cached = json.load(f)
                
                # Check expiration
                cached_time = datetime.fromisoformat(cached['timestamp'])
                if datetime.now() - cached_time > self.ttl:
                    # Expired, remove
                    os.remove(cache_path)
                    return None
                
                return cached['data']
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # Corrupted cache, remove
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                return None
    
    def set(self, elements: list, data: Dict[str, Any], geometry: Optional[Dict] = None):
        """
        Store result in cache
        
        Args:
            elements: List of element symbols
            data: Result data to cache
            geometry: Molecular geometry
        """
        key = self._get_cache_key(elements, geometry)
        cache_path = self._get_cache_path(key)
        
        cache_entry = {
            'timestamp': datetime.now().isoformat(),
            'elements': elements,
            'data': data
        }
        
        with self.lock:
            with open(cache_path, 'w') as f:
                json.dump(cache_entry, f, indent=2)
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, filename))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
            total_entries = len(cache_files)
            
            total_size = sum(
                os.path.getsize(os.path.join(self.cache_dir, f)) 
                for f in cache_files
            )
            
            return {
                'total_entries': total_entries,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'cache_dir': self.cache_dir
            }


class SmartCache:
    """
    Enhanced cache with frequency tracking and automatic optimization
    """
    
    def __init__(self, cache_dir: str = 'cache', max_entries: int = 1000):
        self.base_cache = ResultCache(cache_dir)
        self.max_entries = max_entries
        self.access_counts = {}  # Track access frequency
        self.lock = threading.Lock()
    
    def get(self, elements: list, geometry: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Get with frequency tracking"""
        key = self.base_cache._get_cache_key(elements, geometry)
        
        result = self.base_cache.get(elements, geometry)
        
        if result:
            with self.lock:
                self.access_counts[key] = self.access_counts.get(key, 0) + 1
        
        return result
    
    def set(self, elements: list, data: Dict[str, Any], geometry: Optional[Dict] = None):
        """Set with automatic cleanup if needed"""
        # Check if we need to cleanup
        stats = self.base_cache.get_stats()
        
        if stats['total_entries'] >= self.max_entries:
            self._cleanup_least_used()
        
        self.base_cache.set(elements, data, geometry)
    
    def _cleanup_least_used(self):
        """Remove least frequently accessed entries"""
        with self.lock:
            if not self.access_counts:
                return
            
            # Sort by access count
            sorted_keys = sorted(self.access_counts.items(), key=lambda x: x[1])
            
            # Remove bottom 20%
            num_to_remove = len(sorted_keys) // 5
            for key, _ in sorted_keys[:num_to_remove]:
                cache_path = self.base_cache._get_cache_path(key)
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                del self.access_counts[key]
