"""
Integration tests for performance optimization

Tests the integration between performance monitoring, caching systems,
and optimization strategies across all components.
"""

import pytest
import asyncio
import time
from pathlib import Path
from unittest.mock import Mock, patch

from laxyfile.core.advanced_file_manager import AdvancedFileManager
from laxyfile.operations.file_ops import ComprehensiveFileOperations
from laxyfile.ui.superfile_ui import SuperFileUI
from laxyfile.ai.advanced_assistant import AdvancedAIAssistant


@pytest.mark.integration
@pytest.mark.performance
class TestPerformanceIntegration:
    """Test performance optimization integration across components"""

    @pytest.fixture
    def performance_system(self, mock_config, theme_manager, console, temp_dir):
        """Create performance-optimized system"""
        # Configure for performance testing
        perf_config = Mock()
        perf_config.get = Mock(side_effect=lambda key, default=None: {
            'cache_size': 500,
            'ui.max_files_display': 1000,
            'performance.max_concurrent_operations': 10,
            'performance.chunk_size': 64 * 1024,
            'performance.memory_threshold_mb': 200,
            'performance.lazy_loading_threshold': 500,
            'performance.background_processing': True,
            'performance.use_threading': True,
            'performance.max_worker_threads': 4
        }.get(key, default))

        file_manager = AdvancedFileManager(perf_config)
        file_operations = ComprehensiveFileOperations(perf_config)
        ui = SuperFileUI(theme_manager, console, perf_config)

        return {
            'file_manager': file_manager,
            'file_operations': file_operations,
            'ui': ui,
            'temp_dir': temp_dir
        }

    @pytest.mark.asyncio
    async def test_large_directory_performance_integration(self, performance_system, performance_timer):
        """Test performance with large directories across all components"""
        file_manager = performance_system['file_manager']
        ui = performance_system['ui']
        temp_dir = performance_system['temp_dir']

        # Create large directory
        large_dir = temp_dir / "large_test"
        large_dir.mkdir()

        # Create many files
        num_files = 1000
        for i in range(num_files):
            test_file = large_dir / f"file_{i:04d}.txt"
            test_file.write_text(f"Content for file {i}")

        # Test file manager performance
        performance_timer.start()
        files = await file_manager.list_directory(large_dir)
        performance_timer.stop()

        list_time = performance_timer.elapsed
        assert list_time < 3.0  # Should complete within 3 seconds
        assert len(files) == num_files + 1  # +1 for parent directory

        # Test UI rendering performance
        from laxyfile.core.types import PanelData
        panel_data = PanelData(
            path=large_dir,
            files=files,
            current_selection=0,
            selected_files=set(),
            sort_type="name",
            reverse_sort=False,
            search_query=""
        )

        performance_timer.start()
        panel = ui.render_file_panel(panel_data)
        performance_timer.stop()

        render_time = performance_timer.elapsed
        assert render_time < 2.0  # Should render within 2 seconds
        assert panel is not None

        # Test cache performance
        cache_stats = file_manager.get_cache_stats()
        assert cache_stats['directory_cache_size'] > 0

        # Test second listing (should use cache)
        performance_timer.start()
        cached_files = await file_manager.list_directory(large_dir)
        performance_timer.stop()

        cached_time = performance_timer.elapsed
        assert cached_time < list_time  # Should be faster with cache
        assert len(cached_files) == len(files)

    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(self, performance_system, performance_timer):
        """Test concurrent operations performance"""
        file_manager = performance_system['file_manager']
        file_operations = performance_system['file_operations']
        temp_dir = performance_system['temp_dir']
# Create test directories
        num_dirs = 5
        test_dirs = []
        for i in range(num_dirs):
            test_dir = temp_dir / f"concurrent_test_{i}"
            test_dir.mkdir()

            # Create files in each directory
            for j in range(20):
                test_file = test_dir / f"file_{j}.txt"
                test_file.write_text(f"Content {i}-{j}")

            test_dirs.append(test_dir)

        # Test concurrent directory listings
        performance_timer.start()
        list_tasks = [file_manager.list_directory(test_dir) for test_dir in test_dirs]
        results = await asyncio.gather(*list_tasks)
        performance_timer.stop()

        concurrent_time = performance_timer.elapsed
        assert concurrent_time < 2.0  # Should complete within 2 seconds
        assert len(results) == num_dirs
        for result in results:
            assert len(result) == 21  # 20 files + parent directory

        # Test concurrent file operations
        dest_dirs = []
        for i in range(num_dirs):
            dest_dir = temp_dir / f"concurrent_dest_{i}"
            dest_dir.mkdir()
            dest_dirs.append(dest_dir)

        performance_timer.start()
        copy_tasks = []
        for i, (test_dir, dest_dir) in enumerate(zip(test_dirs, dest_dirs)):
            files_to_copy = [f.path for f in results[i] if f.name != ".."]
            progress_callback = Mock()
            copy_task = file_operations.copy_files(files_to_copy, dest_dir, progress_callback)
            copy_tasks.append(copy_task)

        copy_results = await asyncio.gather(*copy_tasks)
        performance_timer.stop()

        copy_time = performance_timer.elapsed
        assert copy_time < 5.0  # Should complete within 5 seconds
        for result in copy_results:
            assert result.success is True

    @pytest.mark.asyncio
    async def test_memory_usage_integration(self, performance_system):
        """Test memory usage across integrated components"""
        file_manager = performance_system['file_manager']
        temp_dir = performance_system['temp_dir']

        # Create files of various sizes
        file_sizes = [1024, 10*1024, 100*1024, 1024*1024]  # 1KB to 1MB
        created_files = []

        for i, size in enumerate(file_sizes):
            test_file = temp_dir / f"memory_test_{i}.dat"
            test_file.write_bytes(b"x" * size)
            created_files.append(test_file)

        # Test memory-efficient file info retrieval
        file_infos = []
        for test_file in created_files:
            file_info = await file_manager.get_file_info(test_file)
            file_infos.append(file_info)
            assert file_info.size == test_file.stat().st_size

        # Test cache memory management
        initial_cache_stats = file_manager.get_cache_stats()

        # Fill cache with many entries
        for i in range(200):
            dummy_file = temp_dir / f"dummy_{i}.txt"
            dummy_file.write_text(f"Dummy content {i}")
            await file_manager.get_file_info(dummy_file)

        # Check cache size limits
        final_cache_stats = file_manager.get_cache_stats()
        assert final_cache_stats['file_cache_size'] <= final_cache_stats['file_cache_max']

        # Test cache cleanup
        await file_manager.cleanup_cache()
        cleanup_stats = file_manager.get_cache_stats()
        assert cleanup_stats['file_cache_size'] <= final_cache_stats['file_cache_size']

    @pytest.mark.asyncio
    async def test_search_performance_integration(self, performance_system, performance_timer):
        """Test search performance integration"""
        file_manager = performance_system['file_manager']
        temp_dir = performance_system['temp_dir']

        # Create searchable content
        search_terms = ["python", "javascript", "database", "algorithm", "network"]
        num_files_per_term = 50

        for term in search_terms:
            for i in range(num_files_per_term):
                test_file = temp_dir / f"{term}_file_{i}.txt"
                content = f"This file contains information about {term} programming."
                if i % 10 == 0:  # Add special marker to some files
                    content += f" SPECIAL_{term.upper()}_MARKER"
                test_file.write_text(content)

        # Test filename search performance
        performance_timer.start()
        python_files = await file_manager.search_files(temp_dir, "python")
        performance_timer.stop()

        filename_search_time = performance_timer.elapsed
        assert filename_search_time < 1.0  # Should complete within 1 second
        assert len(python_files) >= num_files_per_term

        # Test content search performance
        performance_timer.start()
        special_files = await file_manager.search_files(temp_dir, "SPECIAL_PYTHON_MARKER", include_content=True)
        performance_timer.stop()

        content_search_time = performance_timer.elapsed
        assert content_search_time < 3.0  # Should complete within 3 seconds
        assert len(special_files) >= 5  # Should find marked files

        # Test recursive search performance
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        for i in range(20):
            sub_file = subdir / f"sub_file_{i}.txt"
            sub_file.write_text(f"Subdirectory file {i} with algorithm content")

        performance_timer.start()
        recursive_results = await file_manager.search_files(temp_dir, "algorithm", recursive=True)
        performance_timer.stop()

        recursive_search_time = performance_timer.elapsed
        assert recursive_search_time < 2.0  # Should complete within 2 seconds
        assert len(recursive_results) >= num_files_per_term + 20  # Main dir + subdir files

    def test_ui_rendering_performance_integration(self, performance_system, performance_timer):
        """Test UI rendering performance with various data sizes"""
        ui = performance_system['ui']
        temp_dir = performance_system['temp_dir']

        # Test different file list sizes
        file_counts = [10, 50, 100, 500, 1000]

        for count in file_counts:
            # Create file list
            from laxyfile.core.types import EnhancedFileInfo, PanelData
            from datetime import datetime

            files = []
            for i in range(count):
                file_info = EnhancedFileInfo(
                    path=temp_dir / f"perf_file_{i}.txt",
                    name=f"perf_file_{i}.txt",
                    size=1024 * i,
                    modified=datetime.now(),
                    is_dir=False,
                    is_symlink=False,
                    file_type="text",
                    icon="📄"
                )
                files.append(file_info)

            # Test panel rendering performance
            panel_data = PanelData(
                path=temp_dir,
                files=files,
                current_selection=0,
                selected_files=set(),
                sort_type="name",
                reverse_sort=False,
                search_query=""
            )

            performance_timer.start()
            panel = ui.render_file_panel(panel_data)
            performance_timer.stop()

            render_time = performance_timer.elapsed

            # Performance should scale reasonably
            max_time = 0.1 + (count / 10000)  # Base time + scaling factor
            assert render_time < max_time
            assert panel is not None

            # Test with selections
            selected_files = {files[i].path for i in range(min(10, count))}
            panel_data.selected_files = selected_files

            performance_timer.start()
            selected_panel = ui.render_file_panel(panel_data)
            performance_timer.stop()

            selected_render_time = performance_timer.elapsed
            assert selected_render_time < max_time * 1.5  # Allow some overhead for selections
            assert selected_panel is not None

    @pytest.mark.asyncio
    async def test_cache_efficiency_integration(self, performance_system):
        """Test cache efficiency across components"""
        file_manager = performance_system['file_manager']
        temp_dir = performance_system['temp_dir']

        # Create test files
        test_files = []
        for i in range(50):
            test_file = temp_dir / f"cache_test_{i}.txt"
            test_file.write_text(f"Cache test content {i}")
            test_files.append(test_file)

        # First pass - populate cache
        first_pass_times = []
        for test_file in test_files:
            start_time = time.time()
            await file_manager.get_file_info(test_file)
            end_time = time.time()
            first_pass_times.append(end_time - start_time)

        # Second pass - should use cache
        second_pass_times = []
        for test_file in test_files:
            start_time = time.time()
            await file_manager.get_file_info(test_file)
            end_time = time.time()
            second_pass_times.append(end_time - start_time)

        # Cache should improve performance
        avg_first_pass = sum(first_pass_times) / len(first_pass_times)
        avg_second_pass = sum(second_pass_times) / len(second_pass_times)

        # Second pass should be faster (cache hit)
        assert avg_second_pass <= avg_first_pass

        # Test cache hit ratio
        cache_stats = file_manager.get_cache_stats()
        assert cache_stats['file_cache_size'] > 0

        # Test directory listing cache
        first_list_start = time.time()
        first_list = await file_manager.list_directory(temp_dir)
        first_list_end = time.time()

        second_list_start = time.time()
        second_list = await file_manager.list_directory(temp_dir)
        second_list_end = time.time()

        first_list_time = first_list_end - first_list_start
        second_list_time = second_list_end - second_list_start

        # Second listing should be faster due to caching
        assert second_list_time <= first_list_time
        assert len(first_list) == len(second_list)

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, performance_system):
        """Test performance monitoring across all components"""
        file_manager = performance_system['file_manager']
        file_operations = performance_system['file_operations']
        temp_dir = performance_system['temp_dir']

        # Perform various operations to generate performance data
        test_files = []
        for i in range(10):
            test_file = temp_dir / f"monitor_test_{i}.txt"
            test_file.write_text(f"Monitoring test content {i}")
            test_files.append(test_file)

        # File manager operations
        await file_manager.list_directory(temp_dir)
        for test_file in test_files[:5]:
            await file_manager.get_file_info(test_file)
        await file_manager.search_files(temp_dir, "monitor")

        # File operations
        dest_dir = temp_dir / "monitor_dest"
        dest_dir.mkdir()
        progress_callback = Mock()
        await file_operations.copy_files(test_files[:3], dest_dir, progress_callback)

        # Check performance statistics
        fm_stats = file_manager.get_performance_stats()
        assert 'list_directory' in fm_stats
        assert fm_stats['list_directory']['count'] >= 1

        if 'search_files' in fm_stats:
            assert fm_stats['search_files']['count'] >= 1

        # Verify performance data structure
        for operation, stats in fm_stats.items():
            assert 'count' in stats
            assert 'avg_time' in stats
            assert 'min_time' in stats
            assert 'max_time' in stats
            assert stats['count'] > 0
            assert stats['avg_time'] >= 0
            assert stats['min_time'] >= 0
            assert stats['max_time'] >= stats['min_time']