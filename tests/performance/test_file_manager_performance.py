"""
Performance tests for AdvancedFileManager

Benchmarks file management operations including directory listing, file info retrieval,
search operations, and caching performance under various loads.
"""

import pytest
import asyncio
import time
import psutil
import os
from pathlib import Path
from typing import List
from datetime import datetime

from laxyfile.core.advanced_file_manager import AdvancedFileManager
from laxyfile.core.types import SortType


@pytest.mark.performance
class TestFileManagerPerformance:
    """Performance benchmarks for file manager operations"""

    @pytest.fixture
    def performance_config(self, mock_config):
        """Create performance-optimized configuration"""
        mock_config.get = lambda key, default=None: {
            'cache_size': 2000,
            'ui.use_magic_detection': True,
            'ui.use_nerd_fonts': True,
            'ui.max_files_display': 5000,
            'performance.max_concurrent_operations': 20,
            'performance.chunk_size': 128 * 1024,
            'performance.memory_threshold_mb': 1000,
            'performance.lazy_loading_threshold': 2000,
            'performance.background_processing': True,
            'performance.use_threading': True,
            'performance.max_worker_threads': 8
        }.get(key, default)
        return mock_config

    @pytest.fixture
    def perf_file_manager(self, performance_config):
        """Create performance-optimized file manager"""
        return AdvancedFileManager(performance_config)

    @pytest.fixture
    def large_directory(self, temp_dir):
        """Create large directory with many files for performance testing"""
        large_dir = temp_dir / "large_perf_test"
        large_dir.mkdir()

        # Create files with different sizes and types
        file_types = ['.txt', '.py', '.js', '.md', '.json', '.csv', '.log', '.xml']
        sizes = [100, 1024, 10*1024, 100*1024]  # 100B to 100KB

        created_files = []
        for i in range(1000):  # Create 1000 files
            file_type = file_types[i % len(file_types)]
            size = sizes[i % len(sizes)]

            file_path = large_dir / f"perf_file_{i:04d}{file_type}"
            content = f"Performance test file {i}\n" + "x" * (size - 50)
            file_path.write_text(content[:size])
            created_files.append(file_path)

        return large_dir, created_files

    @pytest.fixture
    def very_large_directory(self, temp_dir):
        """Create very large directory for stress testing"""
        very_large_dir = temp_dir / "very_large_perf_test"
        very_large_dir.mkdir()

        # Create subdirectories
        subdirs = []
        for i in range(10):
dir = very_large_dir / f"subdir_{i:02d}"
            subdir.mkdir()
            subdirs.append(subdir)

        # Create many files across subdirectories
        created_files = []
        for i in range(5000):  # Create 5000 files
            subdir = subdirs[i % len(subdirs)]
            file_path = subdir / f"stress_file_{i:05d}.txt"
            file_path.write_text(f"Stress test file {i} content")
            created_files.append(file_path)

        return very_large_dir, subdirs, created_files

    @pytest.mark.asyncio
    async def test_directory_listing_performance(self, perf_file_manager, large_directory, benchmark):
        """Benchmark directory listing performance"""
        large_dir, created_files = large_directory

        async def list_directory():
            return await perf_file_manager.list_directory(large_dir)

        # Benchmark the operation
        result = benchmark(asyncio.run, list_directory())

        # Verify results
        assert len(result) == len(created_files) + 1  # +1 for parent directory

        # Performance assertions
        stats = perf_file_manager.get_performance_stats()
        if 'list_directory' in stats:
            avg_time = stats['list_directory']['avg_time']
            assert avg_time < 2.0  # Should complete within 2 seconds

    @pytest.mark.asyncio
    async def test_concurrent_directory_listing_performance(self, perf_file_manager, large_directory, benchmark):
        """Benchmark concurrent directory listing performance"""
        large_dir, _ = large_directory

        # Create multiple subdirectories
        subdirs = []
        for i in range(5):
            subdir = large_dir / f"concurrent_subdir_{i}"
            subdir.mkdir()

            # Add files to each subdirectory
            for j in range(100):
                file_path = subdir / f"concurrent_file_{j}.txt"
                file_path.write_text(f"Concurrent test file {i}-{j}")

            subdirs.append(subdir)

        async def concurrent_listing():
            tasks = [perf_file_manager.list_directory(subdir) for subdir in subdirs]
            return await asyncio.gather(*tasks)

        # Benchmark concurrent operations
        results = benchmark(asyncio.run, concurrent_listing())

        # Verify results
        assert len(results) == len(subdirs)
        for result in results:
            assert len(result) == 101  # 100 files + parent directory

    @pytest.mark.asyncio
    async def test_file_info_retrieval_performance(self, perf_file_manager, large_directory, benchmark):
        """Benchmark file info retrieval performance"""
        large_dir, created_files = large_directory

        # Select subset of files for testing
        test_files = created_files[:100]

        async def get_file_infos():
            tasks = [perf_file_manager.get_file_info(file_path) for file_path in test_files]
            return await asyncio.gather(*tasks)

        # Benchmark the operation
        results = benchmark(asyncio.run, get_file_infos())

        # Verify results
        assert len(results) == len(test_files)
        for result in results:
            assert result.name is not None
            assert result.size >= 0

    @pytest.mark.asyncio
    async def test_search_performance(self, perf_file_manager, large_directory, benchmark):
        """Benchmark search operation performance"""
        large_dir, created_files = large_directory

        # Add searchable content to some files
        search_files = created_files[:200]
        for i, file_path in enumerate(search_files):
            if i % 10 == 0:  # Every 10th file gets special content
                content = file_path.read_text() + "\nSPECIAL_SEARCH_MARKER"
                file_path.write_text(content)

        async def search_files():
            return await perf_file_manager.search_files(large_dir, "SPECIAL_SEARCH_MARKER", include_content=True)

        # Benchmark the search
        results = benchmark(asyncio.run, search_files())

        # Verify results
        assert len(results) >= 20  # Should find marked files

        # Performance assertion
        stats = perf_file_manager.get_performance_stats()
        if 'search_files' in stats:
            avg_time = stats['search_files']['avg_time']
            assert avg_time < 5.0  # Should complete within 5 seconds

    @pytest.mark.asyncio
    async def test_cache_performance(self, perf_file_manager, large_directory, benchmark):
        """Benchmark cache performance and hit rates"""
        large_dir, created_files = large_directory

        # First pass - populate cache
        test_files = created_files[:50]

        async def first_pass():
            tasks = [perf_file_manager.get_file_info(file_path) for file_path in test_files]
            return await asyncio.gather(*tasks)

        # Benchmark first pass (cache miss)
        first_results = benchmark.pedantic(asyncio.run, args=(first_pass(),), rounds=1, iterations=1)

        # Second pass - should hit cache
        async def second_pass():
            tasks = [perf_file_manager.get_file_info(file_path) for file_path in test_files]
            return await asyncio.gather(*tasks)

        # Benchmark second pass (cache hit)
        start_time = time.time()
        second_results = await second_pass()
        cache_time = time.time() - start_time

        # Cache should improve performance
        assert len(first_results) == len(second_results)

        # Check cache statistics
        cache_stats = perf_file_manager.get_cache_stats()
        assert cache_stats['file_cache_size'] > 0

        # Cache hit should be faster (allow some variance)
        # This is a rough check since benchmark timing can vary
        assert cache_time < 1.0  # Cached operations should be very fast

    @pytest.mark.asyncio
    async def test_sorting_performance(self, perf_file_manager, large_directory, benchmark):
        """Benchmark file sorting performance"""
        large_dir, _ = large_directory

        # Get files for sorting
        files = await perf_file_manager.list_directory(large_dir)

        def sort_by_name():
            return perf_file_manager._sort_files(files, SortType.NAME, False)

        def sort_by_size():
            return perf_file_manager._sort_files(files, SortType.SIZE, False)

        def sort_by_modified():
            return perf_file_manager._sort_files(files, SortType.MODIFIED, False)

        # Benchmark different sort operations
        name_sorted = benchmark.pedantic(sort_by_name, rounds=5, iterations=1)
        size_sorted = benchmark.pedantic(sort_by_size, rounds=5, iterations=1)
        modified_sorted = benchmark.pedantic(sort_by_modified, rounds=5, iterations=1)

        # Verify sorting worked
        assert len(name_sorted) == len(files)
        assert len(size_sorted) == len(files)
        assert len(modified_sorted) == len(files)

    @pytest.mark.asyncio
    async def test_memory_usage_performance(self, perf_file_manager, large_directory):
        """Test memory usage during large operations"""
        large_dir, created_files = large_directory

        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform memory-intensive operations
        files = await perf_file_manager.list_directory(large_dir)

        # Get file info for many files
        file_info_tasks = [perf_file_manager.get_file_info(file_path) for file_path in created_files[:500]]
        file_infos = await asyncio.gather(*file_info_tasks)

        # Perform searches
        search_results = await perf_file_manager.search_files(large_dir, "test", include_content=True)

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory usage should be reasonable
        assert memory_increase < 200  # Should not use more than 200MB additional

        # Verify operations completed successfully
        assert len(files) > 0
        assert len(file_infos) == 500
        assert len(search_results) >= 0

    @pytest.mark.asyncio
    async def test_stress_test_performance(self, perf_file_manager, very_large_directory):
        """Stress test with very large directory"""
        very_large_dir, subdirs, created_files = very_large_directory

        start_time = time.time()

        # Test directory listing on large directory
        main_files = await perf_file_manager.list_directory(very_large_dir)

        # Test concurrent subdirectory listings
        subdir_tasks = [perf_file_manager.list_directory(subdir) for subdir in subdirs[:5]]
        subdir_results = await asyncio.gather(*subdir_tasks)

        # Test file info retrieval for sample files
        sample_files = created_files[::100]  # Every 100th file
        file_info_tasks = [perf_file_manager.get_file_info(file_path) for file_path in sample_files]
        file_info_results = await asyncio.gather(*file_info_tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Performance assertions
        assert total_time < 10.0  # Should complete within 10 seconds
        assert len(main_files) == len(subdirs) + 1  # Subdirs + parent
        assert len(subdir_results) == 5
        assert len(file_info_results) == len(sample_files)

        # Check cache efficiency
        cache_stats = perf_file_manager.get_cache_stats()
        assert cache_stats['file_cache_size'] > 0
        assert cache_stats['directory_cache_size'] > 0

    @pytest.mark.asyncio
    async def test_directory_size_calculation_performance(self, perf_file_manager, large_directory, benchmark):
        """Benchmark directory size calculation performance"""
        large_dir, _ = large_directory

        async def calculate_size():
            return await perf_file_manager.get_directory_size(large_dir)

        # Benchmark the operation
        total_size = benchmark(asyncio.run, calculate_size())

        # Verify result
        assert total_size > 0
        assert isinstance(total_size, int)

    @pytest.mark.asyncio
    async def test_file_type_detection_performance(self, perf_file_manager, large_directory, benchmark):
        """Benchmark file type detection performance"""
        large_dir, created_files = large_directory

        # Select files with different extensions
        test_files = created_files[:100]

        def detect_file_types():
            results = []
            for file_path in test_files:
                file_type = perf_file_manager._determine_file_type(file_path)
                results.append(file_type)
            return results

        # Benchmark file type detection
        file_types = benchmark(detect_file_types)

        # Verify results
        assert len(file_types) == len(test_files)
        assert all(isinstance(ft, str) for ft in file_types)

    @pytest.mark.asyncio
    async def test_concurrent_cache_access_performance(self, perf_file_manager, large_directory):
        """Test cache performance under concurrent access"""
        large_dir, created_files = large_directory

        # Select files for concurrent access
        test_files = created_files[:200]

        # First, populate cache
        for file_path in test_files[:50]:
            await perf_file_manager.get_file_info(file_path)

        # Now test concurrent access (mix of cache hits and misses)
        async def concurrent_access():
            tasks = []
            for file_path in test_files:
                tasks.append(perf_file_manager.get_file_info(file_path))
            return await asyncio.gather(*tasks)

        start_time = time.time()
        results = await concurrent_access()
        end_time = time.time()

        concurrent_time = end_time - start_time

        # Performance assertions
        assert concurrent_time < 3.0  # Should complete within 3 seconds
        assert len(results) == len(test_files)

        # Check cache statistics
        cache_stats = perf_file_manager.get_cache_stats()
        assert cache_stats['file_cache_size'] > 50  # Should have cached items

    def test_cache_memory_efficiency(self, perf_file_manager, large_directory):
        """Test cache memory efficiency and cleanup"""
        large_dir, created_files = large_directory

        # Get initial cache stats
        initial_stats = perf_file_manager.get_cache_stats()

        # Fill cache beyond capacity
        asyncio.run(self._fill_cache_beyond_capacity(perf_file_manager, created_files))

        # Check cache size limits are respected
        final_stats = perf_file_manager.get_cache_stats()
        assert final_stats['file_cache_size'] <= final_stats['file_cache_max']
        assert final_stats['directory_cache_size'] <= final_stats['directory_cache_max']

        # Test cache cleanup
        asyncio.run(perf_file_manager.cleanup_cache())
        cleanup_stats = perf_file_manager.get_cache_stats()

        # Cache should be cleaned up
        assert cleanup_stats['file_cache_size'] <= final_stats['file_cache_size']

    async def _fill_cache_beyond_capacity(self, file_manager, created_files):
        """Helper to fill cache beyond its capacity"""
        # Try to cache more items than the cache can hold
        cache_stats = file_manager.get_cache_stats()
        max_cache_size = cache_stats['file_cache_max']

        # Cache more files than the limit
        files_to_cache = created_files[:max_cache_size + 100]

        for file_path in files_to_cache:
            await file_manager.get_file_info(file_path)

    @pytest.mark.asyncio
    async def test_performance_regression_detection(self, perf_file_manager, large_directory):
        """Test for performance regressions by establishing baselines"""
        large_dir, created_files = large_directory

        # Establish baseline performance metrics
        baseline_operations = {
            'list_directory': lambda: perf_file_manager.list_directory(large_dir),
            'get_file_info': lambda: perf_file_manager.get_file_info(created_files[0]),
            'search_files': lambda: perf_file_manager.search_files(large_dir, "test")
        }

        performance_results = {}

        for operation_name, operation_func in baseline_operations.items():
            times = []

            # Run operation multiple times to get average
            for _ in range(5):
                start_time = time.time()
                await operation_func()
                end_time = time.time()
                times.append(end_time - start_time)

            avg_time = sum(times) / len(times)
            performance_results[operation_name] = {
                'avg_time': avg_time,
                'min_time': min(times),
                'max_time': max(times)
            }

        # Performance regression thresholds (adjust based on requirements)
        thresholds = {
            'list_directory': 2.0,  # 2 seconds max
            'get_file_info': 0.1,   # 100ms max
            'search_files': 5.0     # 5 seconds max
        }

        # Check for regressions
        for operation, threshold in thresholds.items():
            if operation in performance_results:
                avg_time = performance_results[operation]['avg_time']
                assert avg_time < threshold, f"{operation} exceeded threshold: {avg_time:.3f}s > {threshold}s"

        return performance_results