"""
Performance Tests for File Manager

Tests the performance characteristics of the AdvancedFileManager.
"""

import pytest
import asyncio
import time
import psutil
import os
from pathlib import Path
from unittest.mock import Mock

from laxyfile.core.advanced_file_manager import AdvancedFileManager


@pytest.mark.performance
class TestFileManagerPerformance:
    """Performance test cases for the AdvancedFileManager."""

    @pytest.mark.asyncio
    async def test_large_directory_listing_performance(self, test_config, large_directory, performance_monitor):
        """Test performance of listing large directories."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        performance_monitor.start()

        # List large directory
        files = await file_manager.list_directory(large_directory)

        measurement = performance_monitor.stop()

        # Performance assertions
        assert measurement['duration'] < 2.0  # Should complete within 2 seconds
        assert len(files) > 200  # Should handle large number of files
        assert measurement['memory_delta'] < 50 * 1024 * 1024  # Less than 50MB memory increase

    @pytest.mark.asyncio
    async def test_concurrent_file_operations_performance(self, test_config, temp_dir, performance_monitor):
        """Test performance of concurrent file operations."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        # Create test files
        test_files = []
        for i in range(50):
            file_path = temp_dir / f'perf_test_{i}.txt'
            file_path.write_text(f'Performance test content {i}' * 100)
            test_files.append(file_path)

        performance_monitor.start()

        # Concurrent file info retrieval
        tasks = [file_manager.get_file_info(f) for f in test_files]
        results = await asyncio.gather(*tasks)

        measurement = performance_monitor.stop()

        # Performance assertions
        assert len(results) == 50
        assert measurement['duration'] < 3.0  # Should complete within 3 seconds
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_file_caching_performance(self, test_config, sample_files, performance_monitor):
        """Test performance benefits of file caching."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        file_path = sample_files['text1']

        # First call (no cache)
        performance_monitor.start()
        info1 = await file_manager.get_file_info(file_path)
        first_call =_monitor.stop()

        # Second call (with cache)
        performance_monitor.start()
        info2 = await file_manager.get_file_info(file_path)
        second_call = performance_monitor.stop()

        # Cache should improve performance
        assert second_call['duration'] < first_call['duration']
        assert info1.name == info2.name

    @pytest.mark.asyncio
    async def test_batch_operations_performance(self, test_config, temp_dir, performance_monitor):
        """Test performance of batch file operations."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        # Create source files
        source_files = []
        for i in range(20):
            file_path = temp_dir / f'batch_source_{i}.txt'
            file_path.write_text(f'Batch content {i}')
            source_files.append(file_path)

        # Create destination directory
        dest_dir = temp_dir / 'batch_dest'
        dest_dir.mkdir()

        # Prepare batch operations
        copy_operations = [
            {'source': f, 'destination': dest_dir / f.name}
            for f in source_files
        ]

        performance_monitor.start()

        # Execute batch copy
        results = await file_manager.batch_copy(copy_operations)

        measurement = performance_monitor.stop()

        # Performance assertions
        assert len(results) == 20
        assert all(r['success'] for r in results)
        assert measurement['duration'] < 5.0  # Should complete within 5 seconds

    @pytest.mark.asyncio
    async def test_memory_usage_large_files(self, test_config, temp_dir, performance_monitor):
        """Test memory usage when handling large files."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        # Create a large file (10MB)
        large_file = temp_dir / 'large_file.txt'
        large_content = 'Large file content\n' * 500000  # ~10MB
        large_file.write_text(large_content)

        performance_monitor.start()

        # Get file info for large file
        file_info = await file_manager.get_file_info(large_file)

        measurement = performance_monitor.stop()

        # Memory usage should be reasonable
        assert measurement['memory_delta'] < 20 * 1024 * 1024  # Less than 20MB
        assert file_info.size > 10 * 1024 * 1024  # File should be large

    @pytest.mark.asyncio
    async def test_directory_monitoring_performance(self, test_config, temp_dir, performance_monitor):
        """Test performance of directory monitoring."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        performance_monitor.start()

        # Start monitoring
        await file_manager.start_monitoring(temp_dir)

        # Create files while monitoring
        for i in range(10):
            file_path = temp_dir / f'monitored_{i}.txt'
            file_path.write_text(f'Monitored content {i}')
            await asyncio.sleep(0.01)  # Small delay

        # Stop monitoring
        await file_manager.stop_monitoring()

        measurement = performance_monitor.stop()

        # Check monitoring detected changes
        changes = file_manager.get_recent_changes()
        assert len(changes) > 0
        assert measurement['duration'] < 2.0  # Should complete quickly

    @pytest.mark.asyncio
    async def test_sorting_performance(self, test_config, large_directory, performance_monitor):
        """Test performance of different sorting algorithms."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        from laxyfile.core.advanced_file_manager import SortType

        sort_types = [SortType.NAME, SortType.SIZE, SortType.MODIFIED]

        for sort_type in sort_types:
            performance_monitor.start()

            files = await file_manager.list_directory(
                large_directory,
                sort_type=sort_type
            )

            measurement = performance_monitor.stop()

            # Each sort should complete quickly
            assert measurement['duration'] < 1.0
            assert len(files) > 0

    @pytest.mark.asyncio
    async def test_filtering_performance(self, test_config, large_directory, performance_monitor):
        """Test performance of file filtering."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        filters = ['.txt', '.py', 'test', '001']

        for filter_pattern in filters:
            performance_monitor.start()

            filtered_files = await file_manager.list_directory(
                large_directory,
                filter_pattern=filter_pattern
            )

            measurement = performance_monitor.stop()

            # Filtering should be fast
            assert measurement['duration'] < 0.5
            # Should return some results for most filters
            assert isinstance(filtered_files, list)

    @pytest.mark.asyncio
    async def test_cache_efficiency(self, test_config, large_directory, performance_monitor):
        """Test cache efficiency with repeated operations."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        # First pass - populate cache
        performance_monitor.start()
        files1 = await file_manager.list_directory(large_directory)
        first_pass = performance_monitor.stop()

        # Second pass - use cache
        performance_monitor.start()
        files2 = await file_manager.list_directory(large_directory)
        second_pass = performance_monitor.stop()

        # Cache should improve performance
        assert second_pass['duration'] < first_pass['duration']
        assert len(files1) == len(files2)

        # Check cache stats
        cache_stats = file_manager.get_cache_stats()
        assert cache_stats['directory_cache_size'] > 0

    @pytest.mark.asyncio
    async def test_optimization_for_large_directories(self, test_config, performance_monitor):
        """Test optimization strategies for large directories."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        # Test optimization for different directory sizes
        sizes = [100, 500, 1000, 2000]

        for size in sizes:
            performance_monitor.start()

            optimization = await file_manager.optimize_for_large_directory(size)

            measurement = performance_monitor.stop()

            # Optimization should be fast
            assert measurement['duration'] < 0.1
            assert optimization['file_count'] == size
            assert len(optimization['optimizations_applied']) > 0

    @pytest.mark.asyncio
    async def test_cleanup_performance(self, test_config, sample_files, performance_monitor):
        """Test performance of cleanup operations."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        # Populate caches
        for file_path in sample_files.values():
            if file_path.is_file():
                await file_manager.get_file_info(file_path)

        performance_monitor.start()

        # Perform cleanup
        await file_manager.cleanup_cache()

        measurement = performance_monitor.stop()

        # Cleanup should be fast
        assert measurement['duration'] < 1.0

        # Cache should be cleaned
        cache_stats = file_manager.get_cache_stats()
        assert isinstance(cache_stats, dict)


@pytest.mark.performance
class TestFileManagerScalability:
    """Scalability test cases for the AdvancedFileManager."""

    @pytest.mark.asyncio
    async def test_scalability_with_file_count(self, test_config, temp_dir):
        """Test scalability with increasing file counts."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        file_counts = [10, 50, 100, 500]
        performance_results = []

        for count in file_counts:
            # Create test directory with specific file count
            test_dir = temp_dir / f'scale_test_{count}'
            test_dir.mkdir()

            for i in range(count):
                file_path = test_dir / f'file_{i:04d}.txt'
                file_path.write_text(f'Content {i}')

            # Measure performance
            start_time = time.time()
            files = await file_manager.list_directory(test_dir)
            end_time = time.time()

            duration = end_time - start_time
            performance_results.append((count, duration))

            # Performance should scale reasonably
            assert duration < count * 0.01  # Linear scaling with reasonable constant
            assert len(files) >= count  # Should find all files

        # Performance should not degrade exponentially
        for i in range(1, len(performance_results)):
            prev_count, prev_time = performance_results[i-1]
            curr_count, curr_time = performance_results[i]

            # Time should not increase more than proportionally
            time_ratio = curr_time / prev_time if prev_time > 0 else 1
            count_ratio = curr_count / prev_count

            assert time_ratio <= count_ratio * 2  # Allow some overhead

    @pytest.mark.asyncio
    async def test_memory_scalability(self, test_config, temp_dir):
        """Test memory usage scalability."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        file_counts = [100, 200, 500]
        memory_usage = []

        for count in file_counts:
            # Create test directory
            test_dir = temp_dir / f'memory_test_{count}'
            test_dir.mkdir()

            for i in range(count):
                file_path = test_dir / f'file_{i:04d}.txt'
                file_path.write_text(f'Content {i}')

            # List directory and measure memory
            await file_manager.list_directory(test_dir)
            current_memory = process.memory_info().rss
            memory_increase = current_memory - initial_memory

            memory_usage.append((count, memory_increase))

            # Memory usage should be reasonable
            assert memory_increase < count * 1024  # Less than 1KB per file

        # Memory usage should scale linearly, not exponentially
        for i in range(1, len(memory_usage)):
            prev_count, prev_memory = memory_usage[i-1]
            curr_count, curr_memory = memory_usage[i]

            if prev_memory > 0:
                memory_ratio = curr_memory / prev_memory
                count_ratio = curr_count / prev_count

                # Memory should not increase more than proportionally
                assert memory_ratio <= count_ratio * 1.5

    @pytest.mark.asyncio
    async def test_concurrent_scalability(self, test_config, temp_dir):
        """Test scalability with concurrent operations."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        # Create test files
        test_files = []
        for i in range(100):
            file_path = temp_dir / f'concurrent_{i}.txt'
            file_path.write_text(f'Concurrent content {i}')
            test_files.append(file_path)

        concurrency_levels = [1, 5, 10, 20]

        for concurrency in concurrency_levels:
            start_time = time.time()

            # Create batches of concurrent operations
            for i in range(0, len(test_files), concurrency):
                batch = test_files[i:i+concurrency]
                tasks = [file_manager.get_file_info(f) for f in batch]
                await asyncio.gather(*tasks)

            end_time = time.time()
            duration = end_time - start_time

            # Higher concurrency should not significantly degrade performance
            assert duration < 10.0  # Should complete within reasonable time

        # Verify all operations completed successfully
        cache_stats = file_manager.get_cache_stats()
        assert cache_stats['file_cache_size'] > 0


@pytest.mark.performance
class TestFileManagerResourceUsage:
    """Resource usage test cases for the AdvancedFileManager."""

    @pytest.mark.asyncio
    async def test_cpu_usage(self, test_config, large_directory):
        """Test CPU usage during intensive operations."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        process = psutil.Process(os.getpid())

        # Measure CPU usage during directory listing
        cpu_before = process.cpu_percent()

        # Perform CPU-intensive operation
        for _ in range(5):
            await file_manager.list_directory(large_directory)

        cpu_after = process.cpu_percent()

        # CPU usage should be reasonable
        cpu_increase = cpu_after - cpu_before
        assert cpu_increase < 50.0  # Should not use more than 50% CPU

    @pytest.mark.asyncio
    async def test_file_descriptor_usage(self, test_config, temp_dir):
        """Test file descriptor usage."""
        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        process = psutil.Process(os.getpid())
        initial_fds = process.num_fds() if hasattr(process, 'num_fds') else 0

        # Create many files and access them
        for i in range(100):
            file_path = temp_dir / f'fd_test_{i}.txt'
            file_path.write_text(f'FD test content {i}')
            await file_manager.get_file_info(file_path)

        final_fds = process.num_fds() if hasattr(process, 'num_fds') else 0

        # File descriptor usage should not leak
        if initial_fds > 0 and final_fds > 0:
            fd_increase = final_fds - initial_fds
            assert fd_increase < 10  # Should not leak file descriptors

    @pytest.mark.asyncio
    async def test_cache_memory_limits(self, test_config, temp_dir):
        """Test cache memory limits and eviction."""
        # Configure small cache for testing
        test_config.set('performance.cache_size_mb', 1)  # 1MB cache limit

        file_manager = AdvancedFileManager(test_config)
        await file_manager.initialize()

        # Create many files to exceed cache limit
        large_files = []
        for i in range(50):
            file_path = temp_dir / f'cache_test_{i}.txt'
            # Create files with substantial content
            content = f'Cache test content {i}\n' * 1000
            file_path.write_text(content)
            large_files.append(file_path)

        # Access all files to populate cache
        for file_path in large_files:
            await file_manager.get_file_info(file_path)

        # Check that cache size is within limits
        cache_stats = file_manager.get_cache_stats()

        # Cache should have evicted some entries to stay within limits
        assert cache_stats['file_cache_size'] <= len(large_files)

        # Cache should still be functional
        info = await file_manager.get_file_info(large_files[0])
        assert info is not None