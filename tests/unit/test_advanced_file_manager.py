"""
Unit tests for AdvancedFileManager

Tests the enhanced file management system with comprehensive coverage
of file operations, caching, performance optimizations, and error handling.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from laxyfile.core.advanced_file_manager import AdvancedFileManager, LRUCache, EnhancedFileInfo
from laxyfile.core.types import SortType, FileEvent
from laxyfile.core.exceptions import FileOperationError, PermissionError as LaxyPermissionError


@pytest.mark.unit
class TestLRUCache:
    """Test the LRU cache implementation"""

    def test_cache_initialization(self):
        """Test cache initialization with default and custom sizes"""
        cache = LRUCache()
        assert cache.max_size == 1000
        assert cache.size() == 0

        cache = LRUCache(max_size=50)
        assert cache.max_size == 50
        assert cache.size() == 0

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations"""
        cache = LRUCache(max_size=3)
        timestamp = datetime.now()

        # Set values
        cache.set("key1", "value1", timestamp)
        cache.set("key2", "value2", timestamp)

        # Get values
        result1 = cache.get("key1")
        result2 = cache.get("key2")
        result3 = cache.get("key3")

        assert result1 == ("value1", timestamp)
        assert result2 == ("value2", timestamp)
        assert result3 is None

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        cache = LRUCache(max_size=2)
        timestamp = datetime.now()

        # Fill cache
        cache.set("key1", "value1", timestamp)
        cache.set("key2", "value2", timestamp)

        # Access key1 to make it most recently used
        cache.get("key1")

        # Add new item, should evict key2
        cache.set("key3", "value3", timestamp)

        assert cache.get("key1") is not None
        assert cache.get("key2") is None
        assert cache.get("key3") is not None

    def test_cache_clear(self):
        """Test cache clearing"""
        cache = LRUCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert cache.size() == 2
        cache.clear()
        assert cache.size() == 0
        assert cache.get("key1") is None


@pytest.mark.unit
class TestAdvancedFileManager:
    """Test the AdvancedFileManager class"""

    def test_initialization(self, mock_config):
        """Test file manager initialization"""
        fm = AdvancedFileManager(mock_config)

        assert fm.config == mock_config
        assert fm._file_cache.max_size == 100  # From mock config
        assert fm._directory_cache.max_size == 50
        assert fm._stats_cache.max_size == 25

    @pytest.mark.asyncio
    async def test_get_file_info_basic(self, file_manager, temp_dir, sample_files):
        """Test basic file info retrieval"""
        file_path = sample_files['text_file']
        file_info = await file_manager.get_file_info(file_path)

        assert isinstance(file_info, EnhancedFileInfo)
        assert file_info.path == file_path
        assert file_info.name == "readme.txt"
        assert file_info.size > 0
        assert not file_info.is_dir
        assert not file_info.is_symlink
        assert file_info.file_type == "text"

    @pytest.mark.asyncio
    async def test_get_file_info_directory(self, file_manager, temp_dir):
        """Test file info for directory"""
        dir_path = temp_dir / "documents"
        file_info = await file_manager.get_file_info(dir_path)

        assert file_info.is_dir
        assert file_info.name == "documents"
        assert file_info.size == 0  # Directories typically have size 0

    @pytest.mark.asyncio
    async def test_get_file_info_symlink(self, file_manager, sample_files):
        """Test file info for symlink if available"""
        if 'symlink' in sample_files:
            symlink_path = sample_files['symlink']
            file_info = await file_manager.get_file_info(symlink_path)

            assert file_info.is_symlink
            assert file_info.name == "link_to_readme.txt"

    @pytest.mark.asyncio
    async def test_get_file_info_nonexistent(self, file_manager, temp_dir):
        """Test file info for nonexistent file"""
        nonexistent_path = temp_dir / "nonexistent.txt"
        file_info = await file_manager.get_file_info(nonexistent_path)

        # Should return minimal file info without crashing
        assert file_info.name == "nonexistent.txt"
        assert file_info.size == 0

    @pytest.mark.asyncio
    async def test_list_directory_basic(self, file_manager, temp_dir, sample_files):
        """Test basic directory listing"""
        files = await file_manager.list_directory(temp_dir)

        # Should include parent directory (..) and created files/dirs
        assert len(files) > 0

        # Check for parent directory
        parent_entries = [f for f in files if f.name == ".."]
        assert len(parent_entries) == 1

        # Check for created files
        file_names = [f.name for f in files]
        assert "readme.txt" in file_names
        assert "documents" in file_names
        assert "images" in file_names

    @pytest.mark.asyncio
    async def test_list_directory_hidden_files(self, file_manager, temp_dir, sample_files):
        """Test directory listing with hidden files"""
        # Without hidden files
        files_no_hidden = await file_manager.list_directory(temp_dir, show_hidden=False)
        file_names_no_hidden = [f.name for f in files_no_hidden]
        assert ".hidden" not in file_names_no_hidden

        # With hidden files
        files_with_hidden = await file_manager.list_directory(temp_dir, show_hidden=True)
        file_names_with_hidden = [f.name for f in files_with_hidden]
        assert ".hidden" in file_names_with_hidden

    @pytest.mark.asyncio
    async def test_list_directory_sorting(self, file_manager, temp_dir, sample_files):
        """Test directory listing with different sort options"""
        # Sort by name
        files_by_name = await file_manager.list_directory(temp_dir, sort_type=SortType.NAME)

        # Sort by size
        files_by_size = await file_manager.list_directory(temp_dir, sort_type=SortType.SIZE)

        # Sort by modified time
        files_by_time = await file_manager.list_directory(temp_dir, sort_type=SortType.MODIFIED)

        # All should have same number of files
        assert len(files_by_name) == len(files_by_size) == len(files_by_time)

        # Parent directory should always be first
        assert files_by_name[0].name == ".."
        assert files_by_size[0].name == ".."
        assert files_by_time[0].name == ".."

    @pytest.mark.asyncio
    async def test_list_directory_filter(self, file_manager, temp_dir, sample_files):
        """Test directory listing with filter pattern"""
        # Filter for .txt files
        txt_files = await file_manager.list_directory(temp_dir, filter_pattern="txt")
        txt_file_names = [f.name for f in txt_files if f.name != ".."]

        # Should include readme.txt and empty.txt
        assert any("readme.txt" in name for name in txt_file_names)
        assert any("empty.txt" in name for name in txt_file_names)

        # Filter for documents
        doc_files = await file_manager.list_directory(temp_dir, filter_pattern="doc")
        doc_file_names = [f.name for f in doc_files if f.name != ".."]
        assert any("documents" in name for name in doc_file_names)

    @pytest.mark.asyncio
    async def test_list_directory_permission_error(self, file_manager, temp_dir):
        """Test directory listing with permission error"""
        # Create a directory and remove read permissions
        restricted_dir = temp_dir / "restricted"
        restricted_dir.mkdir()

        # This test is platform-dependent, so we'll mock the permission error
        with patch('pathlib.Path.iterdir', side_effect=PermissionError("Access denied")):
            with pytest.raises(LaxyPermissionError):
                await file_manager.list_directory(restricted_dir)

    @pytest.mark.asyncio
    async def test_search_files_basic(self, file_manager, temp_dir, sample_files):
        """Test basic file search functionality"""
        # Search for "readme"
        results = await file_manager.search_files(temp_dir, "readme")
        result_names = [f.name for f in results]
        assert any("readme.txt" in name for name in result_names)

        # Search for "script"
        results = await file_manager.search_files(temp_dir, "script", recursive=True)
        result_names = [f.name for f in results]
        assert any("script.py" in name for name in result_names)

    @pytest.mark.asyncio
    async def test_search_files_content(self, file_manager, temp_dir, sample_files):
        """Test file search with content matching"""
        # Search for content in files
        results = await file_manager.search_files(temp_dir, "sample", include_content=True)

        # Should find readme.txt which contains "sample"
        result_paths = [f.path for f in results]
        assert sample_files['text_file'] in result_paths

    @pytest.mark.asyncio
    async def test_get_directory_size(self, file_manager, temp_dir, sample_files):
        """Test directory size calculation"""
        total_size = await file_manager.get_directory_size(temp_dir)

        # Should be greater than 0 due to created files
        assert total_size > 0

        # Should include the large file size
        assert total_size >= 1024 * 1024  # At least 1MB from large_file.dat

    def test_file_type_stats(self, file_manager, sample_file_info):
        """Test file type statistics"""
        stats = file_manager.get_file_type_stats(sample_file_info)

        assert "text" in stats
        assert "directory" in stats
        assert stats["text"] == 1
        assert stats["directory"] == 1

    def test_filter_files_by_type(self, file_manager, sample_file_info):
        """Test file filtering by type"""
        # Filter for text files only
        text_files = file_manager.filter_files(sample_file_info, file_types=["text"])
        assert len(text_files) == 2  # Parent dir + text file

        # Filter for directories only
        dir_files = file_manager.filter_files(sample_file_info, file_types=["directory"])
        assert len(dir_files) == 2  # Parent dir + directory

    def test_filter_files_by_size(self, file_manager, sample_file_info):
        """Test file filtering by size range"""
        # Filter for files between 500-2000 bytes
        filtered = file_manager.filter_files(sample_file_info, size_range=(500, 2000))

        # Should include the text file (1024 bytes) but not the directory (0 bytes)
        non_parent_files = [f for f in filtered if f.name != ".."]
        assert len(non_parent_files) == 1
        assert non_parent_files[0].file_type == "text"

    def test_cache_operations(self, file_manager, temp_dir):
        """Test cache operations"""
        # Get initial cache stats
        initial_stats = file_manager.get_cache_stats()
        assert initial_stats['file_cache_size'] == 0

        # Add something to cache (simulate by directly setting)
        file_manager._file_cache.set("test_key", "test_value")

        # Check cache stats
        stats = file_manager.get_cache_stats()
        assert stats['file_cache_size'] == 1

        # Test cache invalidation
        file_manager.invalidate_cache()
        stats = file_manager.get_cache_stats()
        assert stats['file_cache_size'] == 0

    def test_performance_stats(self, file_manager):
        """Test performance statistics tracking"""
        # Add some mock performance data
        file_manager._performance_stats['list_directory'] = [0.1, 0.2, 0.15]
        file_manager._performance_stats['search_files'] = [0.5, 0.3]

        stats = file_manager.get_performance_stats()

        assert 'list_directory' in stats
        assert 'search_files' in stats

        list_stats = stats['list_directory']
        assert list_stats['count'] == 3
        assert list_stats['avg_time'] == 0.15
        assert list_stats['min_time'] == 0.1
        assert list_stats['max_time'] == 0.2

    @pytest.mark.asyncio
    async def test_cleanup_cache(self, file_manager):
        """Test cache cleanup functionality"""
        # Add entries with old timestamps
        old_time = datetime.now() - timedelta(minutes=10)
        file_manager._file_cache.set("old_key", "old_value", old_time)
        file_manager._file_cache.set("new_key", "new_value", datetime.now())

        # Run cleanup
        await file_manager.cleanup_cache()

        # Old entry should be removed, new entry should remain
        assert file_manager._file_cache.get("old_key") is None
        assert file_manager._file_cache.get("new_key") is not None

    def test_sort_files_by_name(self, file_manager):
        """Test file sorting by name"""
        from datetime import datetime

        files = [
            EnhancedFileInfo(Path(".."), "..", 0, datetime.now(), True, False, "directory"),
            EnhancedFileInfo(Path("zebra.txt"), "zebra.txt", 100, datetime.now(), False, False, "text"),
            EnhancedFileInfo(Path("alpha.txt"), "alpha.txt", 200, datetime.now(), False, False, "text"),
            EnhancedFileInfo(Path("beta_dir"), "beta_dir", 0, datetime.now(), True, False, "directory"),
        ]

        sorted_files = file_manager._sort_files(files, SortType.NAME, False)

        # Parent directory should be first
        assert sorted_files[0].name == ".."

        # Directories should come before files, then alphabetical
        non_parent = sorted_files[1:]
        assert non_parent[0].name == "beta_dir"  # Directory first
        assert non_parent[1].name == "alpha.txt"  # Then files alphabetically
        assert non_parent[2].name == "zebra.txt"

    def test_sort_files_by_size(self, file_manager):
        """Test file sorting by size"""
        from datetime import datetime

        files = [
            EnhancedFileInfo(Path(".."), "..", 0, datetime.now(), True, False, "directory"),
            EnhancedFileInfo(Path("small.txt"), "small.txt", 100, datetime.now(), False, False, "text"),
            EnhancedFileInfo(Path("large.txt"), "large.txt", 1000, datetime.now(), False, False, "text"),
            EnhancedFileInfo(Path("medium.txt"), "medium.txt", 500, datetime.now(), False, False, "text"),
        ]

        sorted_files = file_manager._sort_files(files, SortType.SIZE, False)

        # Parent directory should be first
        assert sorted_files[0].name == ".."

        # Files should be sorted by size (ascending)
        non_parent = sorted_files[1:]
        assert non_parent[0].size <= non_parent[1].size <= non_parent[2].size

    def test_security_analysis(self, file_manager):
        """Test security analysis functionality"""
        from datetime import datetime
        import stat

        # Mock stat info with different permissions
        mock_stat = Mock()
        mock_stat.st_mode = stat.S_IFREG | 0o777  # Regular file with 777 permissions
        mock_stat.st_uid = 1000
        mock_stat.st_gid = 1000

        file_info = EnhancedFileInfo(
            path=Path("test.exe"),
            name="test.exe",
            size=1000,
            modified=datetime.now(),
            is_dir=False,
            is_symlink=False,
            file_type="executable",
            permissions_octal="777",
            is_hidden=False
        )

        flags = file_manager._analyze_security(file_info, mock_stat)

        # Should detect overly permissive permissions and suspicious extension
        assert 'overly_permissive' in flags
        assert 'suspicious_extension' in flags

    @pytest.mark.asyncio
    async def test_watch_directory_mock(self, file_manager, temp_dir, mock_watchdog):
        """Test directory watching with mocked watchdog"""
        # This test requires mocking since watchdog might not be available
        with patch('laxyfile.core.advanced_file_manager.Observer', mock_watchdog['observer']):
            with patch('laxyfile.core.advanced_file_manager.FileSystemEventHandler', mock_watchdog['handler']):
                # Test that watch_dectory can be called without error
                try:
                    async for event in file_manager.watch_directory(temp_dir):
                        # Just test that the async generator works
                        break
                except ImportError:
                    # Expected if watchdog is not available
                    pass

    def test_can_preview(self, file_manager):
        """Test preview availability detection"""
        from datetime import datetime

        # Text file should be previewable
        text_file = EnhancedFileInfo(
            path=Path("test.txt"),
            name="test.txt",
            size=100,
            modified=datetime.now(),
            is_dir=False,
            is_symlink=False,
            file_type="text"
        )
        assert file_manager._can_preview(text_file)

        # Image file should be previewable
        image_file = EnhancedFileInfo(
            path=Path("test.jpg"),
            name="test.jpg",
            size=100,
            modified=datetime.now(),
            is_dir=False,
            is_symlink=False,
            file_type="image"
        )
        assert file_manager._can_preview(image_file)

        # Unknown file type should not be previewable
        unknown_file = EnhancedFileInfo(
            path=Path("test.unknown"),
            name="test.unknown",
            size=100,
            modified=datetime.now(),
            is_dir=False,
            is_symlink=False,
            file_type="unknown"
        )
        assert not file_manager._can_preview(unknown_file)

    @pytest.mark.asyncio
    async def test_error_handling(self, file_manager, temp_dir):
        """Test error handling in various scenarios"""
        # Test with invalid path
        invalid_path = Path("/nonexistent/path/that/does/not/exist")

        # Should not raise exception, but return empty or minimal results
        try:
            files = await file_manager.list_directory(invalid_path)
            # If it doesn't raise an exception, it should return empty list or handle gracefully
        except FileOperationError:
            # This is expected behavior
            pass

        # Test file info for invalid path
        file_info = await file_manager.get_file_info(invalid_path)
        assert file_info is not None  # Should return minimal file info

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_large_directory_performance(self, file_manager, temp_dir, performance_timer):
        """Test performance with large directory"""
        # Create many files for performance testing
        num_files = 100
        for i in range(num_files):
            (temp_dir / f"file_{i:03d}.txt").write_text(f"Content {i}")

        # Time the directory listing
        performance_timer.start()
        files = await file_manager.list_directory(temp_dir)
        performance_timer.stop()

        # Should complete within reasonable time (adjust threshold as needed)
        assert performance_timer.elapsed < 2.0  # 2 seconds max
        assert len(files) == num_files + 1  # +1 for parent directory

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, file_manager, temp_dir, sample_files):
        """Test concurrent file operations"""
        # Run multiple operations concurrently
        tasks = [
            file_manager.list_directory(temp_dir),
            file_manager.get_file_info(sample_files['text_file']),
            file_manager.search_files(temp_dir, "readme"),
            file_manager.get_directory_size(temp_dir)
        ]

        # All should complete without errors
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that no exceptions were raised
        for result in results:
            assert not isinstance(result, Exception), f"Unexpected exception: {result}"

        # Verify results
        files, file_info, search_results, dir_size = results
        assert len(files) > 0
        assert file_info.name == "readme.txt"
        assert len(search_results) > 0
        assert dir_size > 0