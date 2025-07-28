"""
Performance Optimizer

Advanced performance optimization system for LaxyFile with memory management,
caching strategies, and resource monitoring.
"""

import asyncio
import gc
import psutil
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta
import weakref

from .exceptions import PerformanceError
from ..utils.logger import Logger


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization"""
    max_concurrent_operations: int = 10
    chunk_size: int = 100
    memory_threshold_mb: int = 500
    lazy_loading_threshold: int = 1000
    background_processing: bool = True
    use_threading: bool = True
    max_worker_threads: int = 4
    cache_ttl_seconds: int = 300
    gc_interval_seconds: int = 60
    memory_check_interval: int = 30


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    operation_times: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    memory_usage: List[Tuple[datetime, float]] = field(default_factory=list)
    cache_stats: Dict[str, Any] = field(default_factory=dict)
    thread_pool_stats: Dict[str, Any] = field(default_factory=dict)
    gc_stats: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


class MemoryManager:
    """Advanced memory management system"""

    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.logger = Logger()
        self._memory_threshold = config.memory_threshold_mb * 1024 * 1024  # Convert to bytes
        self._last_gc = time.time()
        self._memory_history = deque(maxlen=100)
        self._weak_refs = weakref.WeakSet()

    def check_memory_usage(self) -> Dict[str, Any]:
        """Check current memory usage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            stats = {
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'percent': memory_percent,
                'available': psutil.virtual_memory().available,
                'threshold_exceeded': memory_info.rss > self._memory_threshold
            }

            # Track memory history
            self._memory_history.append((datetime.now(), memory_info.rss))

            return stats

        except Exception as e:
            self.logger.error(f"Error checking memory usage: {e}")
            return {}

    def optimize_memory(self) -> Dict[str, Any]:
        """Perform memory optimization"""
        start_time = time.time()
        initial_memory = self.check_memory_usage().get('rss', 0)

        try:
            # Force garbage collection
            collected = gc.collect()

            # Clear weak references if needed
            if len(self._weak_refs) > 1000:
                self._weak_refs.clear()

            # Update last GC time
            self._last_gc = time.time()

            final_memory = self.check_memory_usage().get('rss', 0)
            memory_freed = initial_memory - final_memory

            stats = {
                'objects_collected': collected,
                'memory_freed_bytes': memory_freed,
                'memory_freed_mb': memory_freed / (1024 * 1024),
                'optimization_time': time.time() - start_time,
                'gc_counts': gc.get_count()
            }

            if memory_freed > 0:
                self.logger.info(f"Memory optimization freed {memory_freed / (1024 * 1024):.2f} MB")

            return stats

        except Exception as e:
            self.logger.error(f"Error during memory optimization: {e}")
            return {}

    def should_optimize_memory(self) -> bool:
        """Check if memory optimization should be performed"""
        current_time = time.time()
        memory_stats = self.check_memory_usage()

        # Optimize if threshold exceeded or GC interval passed
        return (
            memory_stats.get('threshold_exceeded', False) or
            (current_time - self._last_gc) > self.config.gc_interval_seconds
        )

    def register_weak_ref(self, obj) -> None:
        """Register object for weak reference tracking"""
        try:
            self._weak_refs.add(obj)
        except TypeError:
            # Object doesn't support weak references
            pass

    def get_memory_trend(self) -> Dict[str, Any]:
        """Get memory usage trend analysis"""
        if len(self._memory_history) < 2:
            return {}

        try:
            recent_usage = [usage for _, usage in self._memory_history[-10:]]
            avg_usage = sum(recent_usage) / len(recent_usage)

            # Calculate trend
            if len(recent_usage) >= 2:
                trend = (recent_usage[-1] - recent_usage[0]) / len(recent_usage)
            else:
                trend = 0

            return {
                'average_usage_mb': avg_usage / (1024 * 1024),
                'current_usage_mb': recent_usage[-1] / (1024 * 1024),
                'trend_mb_per_sample': trend / (1024 * 1024),
                'samples_count': len(self._memory_history),
                'is_increasing': trend > 0
            }

        except Exception as e:
            self.logger.error(f"Error calculating memory trend: {e}")
            return {}


class CacheOptimizer:
    """Advanced caching optimization system"""

    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.logger = Logger()
        self._cache_stats = defaultdict(lambda: {
            'hits': 0,
            'misses': 0,
            'size': 0,
            'last_cleanup': time.time()
        })

    def optimize_cache(self, cache_name: str, cache_dict: Dict) -> Dict[str, Any]:
        """Optimize a specific cache"""
        start_time = time.time()
        initial_size = len(cache_dict)

        try:
            # Remove expired entries
            current_time = time.time()
            expired_keys = []

            for key, value in cache_dict.items():
                if isinstance(value, tuple) and len(value) >= 2:
                    # Assume (data, timestamp) format
                    _, timestamp = value[:2]
                    if isinstance(timestamp, datetime):
                        age = (datetime.now() - timestamp).total_seconds()
                        if age > self.config.cache_ttl_seconds:
                            expired_keys.append(key)

            # Remove expired keys
            for key in expired_keys:
                del cache_dict[key]

            # Update stats
            stats = self._cache_stats[cache_name]
            stats['size'] = len(cache_dict)
            stats['last_cleanup'] = current_time

            optimization_stats = {
                'cache_name': cache_name,
                'initial_size': initial_size,
                'final_size': len(cache_dict),
                'expired_entries': len(expired_keys),
                'optimization_time': time.time() - start_time,
                'hit_rate': self._calculate_hit_rate(cache_name)
            }

            if expired_keys:
                self.logger.debug(f"Cache {cache_name}: removed {len(expired_keys)} expired entries")

            return optimization_stats

        except Exception as e:
            self.logger.error(f"Error optimizing cache {cache_name}: {e}")
            return {}

    def record_cache_hit(self, cache_name: str) -> None:
        """Record a cache hit"""
        self._cache_stats[cache_name]['hits'] += 1

    def record_cache_miss(self, cache_name: str) -> None:
        """Record a cache miss"""
        self._cache_stats[cache_name]['misses'] += 1

    def _calculate_hit_rate(self, cache_name: str) -> float:
        """Calculate cache hit rate"""
        stats = self._cache_stats[cache_name]
        total = stats['hits'] + stats['misses']
        return stats['hits'] / total if total > 0 else 0.0

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return dict(self._cache_stats)


class ThreadPoolOptimizer:
    """Thread pool optimization and management"""

    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.logger = Logger()
        self._thread_pools = {}
        self._pool_stats = defaultdict(lambda: {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'active_threads': 0,
            'queue_size': 0
        })

    def get_optimized_thread_pool(self, pool_name: str, max_workers: Optional[int] = None):
        """Get or create an optimized thread pool"""
        if pool_name not in self._thread_pools:
            from concurrent.futures import ThreadPoolExecutor

            workers = max_workers or self.config.max_worker_threads
            self._thread_pools[pool_name] = ThreadPoolExecutor(
                max_workers=workers,
                thread_name_prefix=f"laxyfile-{pool_name}"
            )

        return self._thread_pools[pool_name]

    def submit_task(self, pool_name: str, func: Callable, *args, **kwargs):
        """Submit task to optimized thread pool"""
        pool = self.get_optimized_thread_pool(pool_name)
        self._pool_stats[pool_name]['tasks_submitted'] += 1

        future = pool.submit(func, *args, **kwargs)

        # Add completion callback
        def on_complete(fut):
            self._pool_stats[pool_name]['tasks_completed'] += 1

        future.add_done_callback(on_complete)
        return future

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get thread pool statistics"""
        stats = {}
        for pool_name, pool in self._thread_pools.items():
            pool_stats = self._pool_stats[pool_name].copy()

            # Add runtime stats if available
            if hasattr(pool, '_threads'):
                pool_stats['active_threads'] = len(pool._threads)
            if hasattr(pool, '_work_queue'):
                pool_stats['queue_size'] = pool._work_queue.qsize()

            stats[pool_name] = pool_stats

        return stats

    def shutdown_pools(self, wait: bool = True) -> None:
        """Shutdown all thread pools"""
        for pool_name, pool in self._thread_pools.items():
            try:
                pool.shutdown(wait=wait)
                self.logger.debug(f"Shutdown thread pool: {pool_name}")
            except Exception as e:
                self.logger.error(f"Error shutting down pool {pool_name}: {e}")

        self._thread_pools.clear()


class PerformanceOptimizer:
    """Main performance optimization coordinator"""

    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.logger = Logger()

        # Initialize sub-optimizers
        self.memory_manager = MemoryManager(config)
        self.cache_optimizer = CacheOptimizer(config)
        self.thread_optimizer = ThreadPoolOptimizer(config)

        # Performance metrics
        self.metrics = PerformanceMetrics()

        # Background optimization
        self._optimization_task = None
        self._running = False

    async def initialize(self) -> None:
        """Initialize the performance optimizer"""
        try:
            self.logger.info("Initializing PerformanceOptimizer")

            if self.config.background_processing:
                await self.start_background_optimization()

            self.logger.info("PerformanceOptimizer initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize PerformanceOptimizer: {e}")
            raise

    async def start_background_optimization(self) -> None:
        """Start background optimization task"""
        if self._optimization_task is None or self._optimization_task.done():
            self._running = True
            self._optimization_task = asyncio.create_task(self._background_optimization_loop())
            self.logger.info("Started background optimization")

    async def stop_background_optimization(self) -> None:
        """Stop background optimization task"""
        self._running = False
        if self._optimization_task and not self._optimization_task.done():
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass
            self.logger.info("Stopped background optimization")

    async def _background_optimization_loop(self) -> None:
        """Background optimization loop"""
        while self._running:
            try:
                # Memory optimization
                if self.memory_manager.should_optimize_memory():
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.memory_manager.optimize_memory
                    )

                # Update metrics
                await self._update_metrics()

                # Sleep before next optimization cycle
                await asyncio.sleep(self.config.memory_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in background optimization: {e}")
                await asyncio.sleep(5)  # Brief pause on error

    async def _update_metrics(self) -> None:
        """Update performance metrics"""
        try:
            # Memory metrics
            memory_stats = self.memory_manager.check_memory_usage()
            if memory_stats:
                self.metrics.memory_usage.append((
                    datetime.now(),
                    memory_stats.get('rss', 0) / (1024 * 1024)  # Convert to MB
                ))

            # Cache metrics
            self.metrics.cache_stats = self.cache_optimizer.get_cache_stats()

            # Thread pool metrics
            self.metrics.thread_pool_stats = self.thread_optimizer.get_pool_stats()

            # Memory trend
            memory_trend = self.memory_manager.get_memory_trend()
            if memory_trend:
                self.metrics.cache_stats['memory_trend'] = memory_trend

            self.metrics.last_updated = datetime.now()

        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")

    def record_operation_time(self, operation: str, duration: float) -> None:
        """Record operation timing"""
        self.metrics.operation_times[operation].append(duration)

        # Keep only recent measurements
        if len(self.metrics.operation_times[operation]) > 100:
            self.metrics.operation_times[operation] = self.metrics.operation_times[operation][-50:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        try:
            stats = {
                'memory': self.memory_manager.check_memory_usage(),
                'memory_trend': self.memory_manager.get_memory_trend(),
                'cache': self.cache_optimizer.get_cache_stats(),
                'thread_pools': self.thread_optimizer.get_pool_stats(),
                'operation_times': self._calculate_operation_stats(),
                'last_updated': self.metrics.last_updated.isoformat()
            }

            return stats

        except Exception as e:
            self.logger.error(f"Error getting performance stats: {e}")
            return {}

    def _calculate_operation_stats(self) -> Dict[str, Any]:
        """Calculate operation timing statistics"""
        stats = {}

        for operation, times in self.metrics.operation_times.items():
            if times:
                stats[operation] = {
                    'count': len(times),
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'total_time': sum(times),
                    'recent_avg': sum(times[-10:]) / min(len(times), 10)
                }

        return stats

    async def optimize_for_large_directory(self, file_count: int) -> Dict[str, Any]:
        """Optimize performance for large directory operations"""
        try:
            optimizations = []

            # Adjust chunk size based on file count
            if file_count > 10000:
                chunk_size = min(50, self.config.chunk_size)
                optimizations.append(f"Reduced chunk size to {chunk_size}")
            elif file_count > 1000:
                chunk_size = min(100, self.config.chunk_size)
                optimizations.append(f"Adjusted chunk size to {chunk_size}")

            # Trigger memory optimization
            if file_count > 5000:
                memory_stats = await asyncio.get_event_loop().run_in_executor(
                    None, self.memory_manager.optimize_memory
                )
                optimizations.append("Performed memory optimization")

            # Suggest UI optimizations
            ui_optimizations = []
            if file_count > 1000:
                ui_optimizations.append("Enable lazy loading")
            if file_count > 5000:
                ui_optimizations.append("Reduce preview updates")
            if file_count > 10000:
                ui_optimizations.append("Disable animations")

            return {
                'file_count': file_count,
                'optimizations_applied': optimizations,
                'ui_suggestions': ui_optimizations,
                'recommended_chunk_size': chunk_size if 'chunk_size' in locals() else self.config.chunk_size
            }

        except Exception as e:
            self.logger.error(f"Error optimizing for large directory: {e}")
            return {}

    def optimize_cache(self, cache_name: str, cache_dict: Dict) -> Dict[str, Any]:
        """Optimize a specific cache"""
        return self.cache_optimizer.optimize_cache(cache_name, cache_dict)

    def submit_background_task(self, pool_name: str, func: Callable, *args, **kwargs):
        """Submit task to background thread pool"""
        return self.thread_optimizer.submit_task(pool_name, func, *args, **kwargs)

    async def shutdown(self) -> None:
        """Shutdown the performance optimizer"""
        try:
            await self.stop_background_optimization()
            self.thread_optimizer.shutdown_pools()
            self.logger.info("PerformanceOptimizer shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    def __del__(self):
        """Cleanup on deletion"""
        try:
            if hasattr(self, 'thread_optimizer'):
                self.thread_optimizer.shutdown_pools(wait=False)
        except:
            pass