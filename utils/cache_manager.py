import hashlib
import json
import pickle
from pathlib import Path
from typing import Optional, Any, Callable
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Simple file-based cache for LLM responses.

    Usage:
        cache = CacheManager(cache_dir="./cache")

        # Cache decorator
        @cache.cached(ttl_days=30)
        def expensive_llm_call(text):
            return llm.generate(text)

        # Manual caching
        result = cache.get(key)
        if not result:
            result = expensive_operation()
            cache.set(key, result)
    """

    def __init__(self, cache_dir: str = "./cache", format: str = "json"):
        """
        Args:
            cache_dir: Directory to store cache files
            format: "json" or "pickle" - json is human-readable, pickle handles complex objects
        """
        self.cache_dir = Path(cache_dir)
        # Create directory and all parent directories if they don't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.format = format
        logger.info(f"Cache initialized at {self.cache_dir}")

    def _get_cache_key(self, key: str) -> str:
        """Generate MD5 hash for cache key"""
        if isinstance(key, str):
            return hashlib.md5(key.encode()).hexdigest()
        else:
            # Handle non-string keys
            return hashlib.md5(str(key).encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        """Get full path to cache file"""
        cache_key = self._get_cache_key(key)
        extension = "json" if self.format == "json" else "pkl"
        return self.cache_dir / f"{cache_key}.{extension}"

    def get(self, key: str, max_age_days: Optional[int] = None) -> Optional[Any]:
        """
        Retrieve cached value by key.

        Args:
            key: Cache key (will be hashed)
            max_age_days: If set, only return cache if younger than this many days

        Returns:
            Cached value or None if not found/expired
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            logger.debug(f"Cache miss: {key[:50]}...")
            return None

        # Check age if specified
        if max_age_days is not None:
            file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
            if file_age > timedelta(days=max_age_days):
                logger.info(f"Cache expired: {key[:50]}... (age: {file_age.days} days)")
                return None

        try:
            if self.format == "json":
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)

            logger.debug(f"Cache hit: {key[:50]}...")
            return data

        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None

    def set(self, key: str, value: Any) -> bool:
        """
        Store value in cache.

        Args:
            key: Cache key (will be hashed)
            value: Value to cache (must be JSON-serializable if format=json)

        Returns:
            True if successful, False otherwise
        """
        cache_path = self._get_cache_path(key)

        try:
            if self.format == "json":
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(value, f, indent=2)
            else:
                with open(cache_path, 'wb') as f:
                    pickle.dump(value, f)

            logger.debug(f"Cached: {key[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Error writing cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete cached value by key"""
        cache_path = self._get_cache_path(key)

        if cache_path.exists():
            cache_path.unlink()
            logger.debug(f"Cache deleted: {key[:50]}...")
            return True
        return False

    def clear_all(self) -> int:
        """
        Clear all cached files.

        Returns:
            Number of files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*"):
            if cache_file.is_file():
                cache_file.unlink()
                count += 1

        logger.info(f"Cleared {count} cache files")
        return count

    def get_stats(self) -> dict:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*"))
        total_size = sum(f.stat().st_size for f in cache_files if f.is_file())

        return {
            "total_files": len(cache_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir)
        }

    def cached(self, ttl_days: int = 30):
        """
        Decorator to automatically cache function results.

        Usage:
            cache = CacheManager()

            @cache.cached(ttl_days=30)
            def expensive_function(text):
                return process(text)

        Args:
            ttl_days: Time-to-live in days
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # Create cache key from function name and arguments
                cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"

                # Try to get from cache
                cached_result = self.get(cache_key, max_age_days=ttl_days)
                if cached_result is not None:
                    logger.info(f"✅ Cache hit for {func.__name__}")
                    return cached_result

                # Call function and cache result
                logger.info(f"❌ Cache miss for {func.__name__}, calling function...")
                result = func(*args, **kwargs)
                self.set(cache_key, result)

                return result

            return wrapper
        return decorator


# Convenience functions for common use cases
def create_text_cache(cache_dir: str = "./cache/llm_responses") -> CacheManager:
    """Create cache manager optimized for text/JSON responses"""
    return CacheManager(cache_dir=cache_dir, format="json")


def create_object_cache(cache_dir: str = "./cache/objects") -> CacheManager:
    """Create cache manager for Python objects using pickle"""
    return CacheManager(cache_dir=cache_dir, format="pickle")
