"""
Model and Vectorization Cache Manager for Advanced AI Analyzer

Handles lazy loading of ML models and caching of expensive computations
to keep classification latency under 200ms during 15-second automation cycles.
"""

import logging
import time
from typing import Any, Dict, Optional
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelCacheManager:
    """
    Intelligent caching system for ML models with LRU eviction and performance tracking.

    Features:
    - Lazy loading of models (only load when first needed)
    - LRU cache eviction (keeps memory bounded)
    - Access time tracking (performance monitoring)
    - Cache statistics (hit rate, eviction tracking)
    """

    def __init__(self, max_cache_size_mb: int = 500):
        """
        Initialize cache manager.

        Args:
            max_cache_size_mb: Maximum cache size in MB (default 500MB)
        """
        self.models = {}
        self.vectorizations = {}
        self.cache_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "evictions": 0,
            "models_loaded": 0,
            "models_failed": 0,
        }
        self.last_access = {}
        self.max_cache_size_mb = max_cache_size_mb
        self.current_size_mb = 0
        self.load_times = {}

    def get_model(self, model_name: str, loader_func=None) -> Optional[Any]:
        """
        Get model from cache or load it lazily.

        Args:
            model_name: Name/key of the model
            loader_func: Function to load model if not cached (async or sync)

        Returns:
            Model object or None if loading fails
        """
        self.cache_stats["total_requests"] += 1
        current_time = time.time()

        # Check if in cache
        if model_name in self.models:
            self.cache_stats["cache_hits"] += 1
            self.last_access[model_name] = current_time
            logger.debug(f"Cache hit for model: {model_name}")
            return self.models[model_name]

        # Not in cache - load it
        self.cache_stats["cache_misses"] += 1
        if loader_func is None:
            logger.warning(f"No loader function provided for model: {model_name}")
            return None

        try:
            logger.info(f"Loading model: {model_name}")
            start_time = time.time()
            model = loader_func()
            load_time = time.time() - start_time
            self.load_times[model_name] = load_time

            if model is None:
                self.cache_stats["models_failed"] += 1
                logger.error(f"Failed to load model: {model_name}")
                return None

            # Store in cache
            self.models[model_name] = model
            self.last_access[model_name] = current_time
            self.cache_stats["models_loaded"] += 1

            logger.info(f"Model loaded successfully: {model_name} (took {load_time:.2f}s)")

            # Check if we need to evict
            self._check_and_evict()

            return model

        except Exception as e:
            logger.error(f"Error loading model {model_name}: {str(e)}")
            self.cache_stats["models_failed"] += 1
            return None

    def get_cached_vectorization(self, text_hash: str) -> Optional[Any]:
        """
        Get cached text vectorization by hash.

        Args:
            text_hash: Hash of the text (use hashlib.md5 for generation)

        Returns:
            Cached vector or None
        """
        if text_hash in self.vectorizations:
            self.cache_stats["cache_hits"] += 1
            self.last_access[text_hash] = time.time()
            logger.debug(f"Vectorization cache hit: {text_hash[:8]}")
            return self.vectorizations[text_hash]

        self.cache_stats["cache_misses"] += 1
        return None

    def cache_vectorization(self, text_hash: str, vector: Any) -> None:
        """
        Cache a text vectorization.

        Args:
            text_hash: Hash of the text
            vector: The vectorized representation
        """
        self.vectorizations[text_hash] = vector
        self.last_access[text_hash] = time.time()
        logger.debug(f"Vectorization cached: {text_hash[:8]}")

    def clear_cache(self) -> None:
        """Clear all cached models and vectorizations."""
        self.models.clear()
        self.vectorizations.clear()
        self.last_access.clear()
        logger.info("Cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics and performance metrics.

        Returns:
            Dictionary with cache stats and performance data
        """
        total = self.cache_stats["total_requests"]
        hits = self.cache_stats["cache_hits"]
        hit_rate = (hits / total * 100) if total > 0 else 0

        return {
            "total_requests": total,
            "cache_hits": hits,
            "cache_misses": self.cache_stats["cache_misses"],
            "cache_hit_rate": f"{hit_rate:.1f}%",
            "models_loaded": self.cache_stats["models_loaded"],
            "models_failed": self.cache_stats["models_failed"],
            "evictions": self.cache_stats["evictions"],
            "cached_models": len(self.models),
            "cached_vectors": len(self.vectorizations),
            "load_times": self.load_times,
        }

    def _check_and_evict(self) -> None:
        """
        Check cache size and evict least recently used models if needed.
        Uses simple heuristic: if more than 10 models, evict oldest unused.
        """
        # Simple LRU eviction: if too many models, remove least recently accessed
        if len(self.models) > 10:
            # Find least recently accessed model
            if self.last_access:
                lru_key = min(
                    self.last_access.keys(),
                    key=lambda k: self.last_access[k]
                )
                if lru_key in self.models:
                    del self.models[lru_key]
                    del self.last_access[lru_key]
                    self.cache_stats["evictions"] += 1
                    logger.info(f"Evicted model (LRU): {lru_key}")


# Global singleton instance
_cache_manager = None


def get_cache_manager(max_cache_size_mb: int = 500) -> ModelCacheManager:
    """
    Get or create the global cache manager instance.

    Args:
        max_cache_size_mb: Max cache size in MB (only used on first call)

    Returns:
        Singleton ModelCacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = ModelCacheManager(max_cache_size_mb=max_cache_size_mb)
        logger.info(f"Cache manager initialized (max: {max_cache_size_mb}MB)")
    return _cache_manager


def reset_cache_manager() -> None:
    """Reset the global cache manager (mainly for testing)."""
    global _cache_manager
    if _cache_manager:
        _cache_manager.clear_cache()
    _cache_manager = None
