"""
Performance Optimization System

This module provides performance optimizations for handling large directories,
memory management, and efficient file operations.
"""

import asyncio
import gc
import psutil
import time
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, AsyncIterator
from dataclasses import dataclass
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

from .types import FileInfo, PerformanceMetric
from ..utils.logger import Logger


@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    max_concurrent_operations: int = 10
    chunk_size: int = 100
    memory_threshold_mb: int = 500
    cache_cleanup_interval: int = 300  # seconds
    lazy_loading_threshold: int = 1000  # files
    background_processing: bool = True
    use_threading: bool = True
    max_worker_threads: int = 4


class MemoryMonitor:
    """Memory usage monitoring and management"""

    def __init__(self, threshold_mb: int = 500):
        self.threshold_mb = threshold_mb
        self.logger = Logger()
        self._monitoring = False
        self._monitor_task = None

    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': process.memory_percent(),
                'available_mb': psutil.virtual_memory().available / 1024 / 1024
            }
        except Exception as e:
            self.logger.error(f"Error getting memory usage: {e}")
            return {}

    def is_memory_pressure(self) -> bool:
        """Check if system is under memory pressure"""
        try:
            memory_usage = self.get_memory_usage()
            return memory_usage.get('rss_mb', 0) > self.threshold_mb
        except Exception:
            return False

    def force_garbage_collection(self) -> int:
        """Force garbage collection and return collected objects"""
        try:
            collected = gc.collect()
            self.logger.debug(f"Garbage collection freed {collected} objects")
            return collected
        except Exception as e:
            self.logger.error(f"Error during garbage collection: {e}")
            return 0

    async def start_monitoring(self, callback: Optional[Callable] = None):
        """Start memory monitoring in background"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(callback))

    async def stop_monitoring(self):
        """Stop memory monitoring"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self, callback: Optional[Callable] = None):
        """Memory monitoring loop"""
        while self._monitoring:
            try:
                if self.is_memory_pressure():
                    self.logger.warning("Memory pressure detected, triggering cleanup")
                    self.force_garbage_collection()

                    if callback:
                        await callback()

                await asyncio.sleep(10)  # Check every 10 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in memory monitoring loop: {e}")
                await asyncio.sleep(10)


class LazyLoader:
    """Lazy loading system for large directories"""

    def __init__(self, chunk_size: int = 100):
        self.chunk_size = chunk_size
        self.logger = Logger()

    async def load_directory_chunks(self, path: Path,
                                  file_processor: Callable,
                                  show_hidden: bool = False) -> AsyncIterator[List[Any]]:
        """Load directory contents in chunks"""
        try:
            items = []

            # Collect all items first
            for item in path.iterdir():
                if not show_hidden and item.name.startswith('.'):
                    continue
                items.append(item)

            # Process in chunks
            for i in range(0, len(items), self.chunk_size):
                chunk = items[i:i + self.chunk_size]

                # Process chunk concurrently
                tasks = [file_processor(item) for item in chunk]
                processed_chunk = await asyncio.gather(*tasks, return_exceptions=True)

                # Filter out exceptions
                valid_items = [item for item in processed_chunk if not isinstance(item, Exception)]

                yield valid_items

                # Allow other tasks to run
                await asyncio.sleep(0)

        except Exception as e:
            self.logger.error(f"Error in lazy loading for {path}: {e}")


class BackgroundProcessor:
    """Background processing for non-critical operations"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.logger = Logger()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks = deque()
        self._processing = False

    def submit_task(self, func: Callable, *args, **kwargs) -> asyncio.Future:
        """Submit a task for background processing"""
        future = asyncio.get_event_loop().run_in_executor(
            self._executor, func, *args, **kwargs
        )
        self._tasks.append(future)
        return future

    async def process_pending_tasks(self, max_concurrent: int = 10):
        """Process pending tasks with concurrency limit"""
        if self._processing:
            return

        self._processing = True

        try:
            while self._tasks:
                # Process up to max_concurrent tasks at once
                current_batch = []
                for _ in range(min(max_concurrent, len(self._tasks))):
                    if self._tasks:
                        current_batch.append(self._tasks.popleft())

                if current_batch:
                    # Wait for batch completion
                    await asyncio.gather(*current_batch, return_exceptions=True)

                # Allow other tasks to run
                await asyncio.sleep(0.01)

        finally:
            self._processing = False

    def shutdown(self):
        """Shutdown the background processor"""
        self._executor.shutdown(wait=True)


class PerformanceOptimizer:
    """Main performance optimization coordinator"""

    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.logger = Logger()

        # Initialize components
        self.memory_monitor = MemoryMonitor(config.memory_threshold_mb)
        self.lazy_loader = LazyLoader(config.chunk_size)
        self.background_processor = BackgroundProcessor(config.max_worker_threads)

        # Performance metrics
        self.metrics = {}
        self._start_time = time.time()

    async def optimize_directory_loading(self, path: Path,
                                       file_processor: Callable,
                                       show_hidden: bool = False) -> List[Any]:
        """Optimize directory loading based on size and system resources"""
        start_time = time.time()

        try:
            # Quick count of items
            item_count = sum(1 for _ in path.iterdir())

            # Decide on loading strategy
            if item_count > self.config.lazy_loading_threshold:
                self.logger.info(f"Using lazy loading for {item_count} items in {path}")
                return await self._lazy_load_directory(path, file_processor, show_hidden)
            else:
                self.logger.debug(f"Using standard loading for {item_count} items in {path}")
                return await self._standard_load_directory(path, file_processor, show_hidden)

        finally:
            # Record performance metric
            duration = time.time() - start_time
            self._record_metric('directory_loading', duration, {'item_count': item_count})

    async def _lazy_load_directory(self, path: Path,
                                 file_processor: Callable,
                                 show_hidden: bool = False) -> List[Any]:
        """Load directory using lazy loading strategy"""
        all_items = []

        async for chunk in self.lazy_loader.load_directory_chunks(path, file_processor, show_hidden):
            all_items.extend(chunk)

            # Check memory pressure
            if self.memory_monitor.is_memory_pressure():
                self.logger.warning("Memory pressure during lazy loading, triggering cleanup")
                self.memory_monitor.force_garbage_collection()
                await asyncio.sleep(0.1)  # Brief pause to allow cleanup

        return all_items

    async def _standard_load_directory(self, path: Path,
                                     file_processor: Callable,
                                     show_hidden: bool = False) -> List[Any]:
        """Load directory using standard strategy with concurrency"""
        items = []

        # Collect items
        for item in path.iterdir():
            if not show_hidden and item.name.startswith('.'):
                continue
            items.append(item)

        # Process with controlled concurrency
        semaphore = asyncio.Semaphore(self.config.max_concurrent_operations)

        async def process_with_semaphore(item):
            async with semaphore:
                return await file_processor(item)

        # Process all items concurrently
        tasks = [process_with_semaphore(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        return [result for result in results if not isinstance(result, Exception)]

    def optimize_memory_usage(self, cache_objects: List[Any]):
        """Optimize memory usage by cleaning up caches"""
        if not self.memory_monitor.is_memory_pressure():
            return

        self.logger.info("Optimizing memory usage")

        # Clear caches if under memory pressure
        for cache_obj in cache_objects:
            if hasattr(cache_obj, 'clear'):
                cache_obj.clear()
            elif hasattr(cache_obj, 'cache') and hasattr(cache_obj.cache, 'clear'):
                cache_obj.cache.clear()

        # Force garbage collection
        self.memory_monitor.force_garbage_collection()

    async def optimize_file_operations(self, operations: List[Callable]) -> List[Any]:
        """Optimize batch file operations"""
        if not operations:
            return []

        start_time = time.time()

        try:
            # Use background processing for non-critical operations
            if self.config.background_processing:
                futures = []
                for operation in operations:
                    future = self.background_processor.submit_task(operation)
                    futures.append(future)

                # Wait for completion with timeout
                results = await asyncio.gather(*futures, return_exceptions=True)
                return [r for r in results if not isinstance(r, Exception)]
            else:
                # Process sequentially
                results = []
                for operation in operations:
                    try:
                        result = await operation() if asyncio.iscoroutinefunction(operation) else operation()
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Error in file operation: {e}")

                return results

        finally:
            duration = time.time() - start_time
            self._record_metric('file_operations', duration, {'operation_count': len(operations)})

    def _record_metric(self, operation: str, duration: float, metadata: Dict[str, Any] = None):
        """Record performance metric"""
        if operation not in self.metrics:
            self.metrics[operation] = []

        metric = PerformanceMetric(
            operation=operation,
            duration=duration,
            memory_used=self.memory_monitor.get_memory_usage().get('rss_mb', 0),
            cpu_percent=psutil.cpu_percent()
        )

        self.metrics[operation].append(metric)

        # Keep only recent metrics (last 100)
        if len(self.metrics[operation]) > 100:
            self.metrics[operation] = self.metrics[operation][-100:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        stats = {
            'uptime': time.time() - self._start_time,
            'memory_usage': self.memory_monitor.get_memory_usage(),
            'operations': {}
        }

        for operation, metrics in self.metrics.items():
            if metrics:
                durations = [m.duration for m in metrics]
                stats['operations'][operation] = {
                    'count': len(metrics),
                    'avg_duration': sum(durations) / len(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'total_duration': sum(durations)
                }

        return stats

    async def start_background_monitoring(self):
        """Start background performance monitoring"""
        await self.memory_monitor.start_monitoring(
            callback=lambda: self.optimize_memory_usage([])
        )

    async def stop_background_monitoring(self):
        """Stop background performance monitoring"""
        await self.memory_monitor.stop_monitoring()
        self.background_processor.shutdown()

    def suggest_optimizations(self) -> List[str]:
        """Suggest performance optimizations based on metrics"""
        suggestions = []

        memory_usage = self.memory_monitor.get_memory_usage()
        if memory_usage.get('rss_mb', 0) > self.config.memory_threshold_mb:
            suggestions.append("Consider increasing memory threshold or reducing cache sizes")

        # Analyze operation performance
        for operation, metrics in self.metrics.items():
            if metrics:
                avg_duration = sum(m.duration for m in metrics) / len(metrics)
                if avg_duration > 1.0:  # Operations taking more than 1 second
                    suggestions.append(f"Operation '{operation}' is slow (avg: {avg_duration:.2f}s), consider optimization")

        if not suggestions:
            suggestions.append("Performance is optimal")

        return suggestions