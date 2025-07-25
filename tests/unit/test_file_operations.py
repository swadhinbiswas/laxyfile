"""
Unit tests for File Operations

Tests the comprehensive file operations system including copy, move, delete,
archive operations, and batch processing with progress tracking.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, call
from datetime import datetime

from laxyfile.operations.file_ops import (
    ComprehensiveFileOperations, OperationResult, OperationError,
    ArchiveFormat, ConflictResolution
)
from laxyfile.core.exceptions import FileOperationError, PermissionError as LaxyPermissionError


@pytest.mark.unit
class TestOperationResult:
    """Test the OperationResult dataclass"""

    def test_operation_result_creation(self):
        """Test operation result creation"""
        result = OperationResult(
            success=True,
            message="Operation completed",
            affected_files=[Path("test.txt")],
            errors=[],
            progress=100.0,
            duration=1.5,
            bytes_processed=1024
        )

        assert result.success is True
        assert result.message == "Operation completed"
        assert result.affected_files == [Path("test.txt")]
        assert result.errors == []
        assert result.progress == 100.0
        assert result.duration == 1.5
        assert result.bytes_processed == 1024

    def test_operation_result_with_errors(self):
        """Test operation result with errors"""
        error = OperationError("test_error", Path("test.txt"), "Test error message")
        result = OperationResult(
            success=False,
            message="Operation failed",
            affected_files=[],
            errors=[error],
            progress=50.0,
            duration=0.5,
            bytes_processed=512
        )

        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].operation == "test_error"


@pytest.mark.unit
class TestComprehensiveFileOperations:
    """Test the ComprehensiveFileOperations class"""

    def test_initialization(self, mock_config):
        """Test file operations initialization"""
        ops = ComprehensiveFileOperations(mock_config)

        assert ops.config == mock_config
        assert ops.max_concurrent_operations == 5  # From mock config
        assert ops.chunk_size == 50

    @pytest.mark.asyncio
    async def test_copy_single_file(self, temp_dir, sample_files):
        """Test copying a single file"""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None: {
            'performance.max_concurrent_operations': 5,
            'performance.chunk_size': 1024,
            'performance.use_threading': True
        }.get(key, default))

        ops = ComprehensiveFileOperations(config)

        source = sample_files['text_file']
        destination = temp_dir / "copied_readme.txt"

        # Mock progress callback
        progress_callback = Mock()

        result = await ops.copy_files([source], destination, progress_callback)

        assert result.success is True
        assert destination.exists()
        assert destination.read_text() == source.read_text()
        assert len(result.affected_files) == 1
        assert result.affected_files[0] == destination

    @pytest.mark.asyncio
    async def test_copy_multiple_files(self, temp_dir, sample_files):
        """Test copying multiple files"""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None: {
            'performance.max_concurrent_operations': 5,
            'performance.chunk_size': 1024
        }.get(key, default))

        ops = ComprehensiveFileOperations(config)

        sources = [sample_files['text_file'], sample_files['empty_file']]
        destination_dir = temp_dir / "copied_files"
        destination_dir.mkdir()

        progress_callback =

        result = await ops.copy_files(sources, destination_dir, progress_callback)

        assert result.success is True
        assert len(result.affected_files) == 2
        assert (destination_dir / "readme.txt").exists()
        assert (destination_dir / "empty.txt").exists()

    @pytest.mark.asyncio
    async def test_copy_file_conflict_resolution(self, temp_dir, sample_files):
        """Test copy operation with file conflicts"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        source = sample_files['text_file']
        destination = temp_dir / "readme.txt"

        # Create conflicting file
        destination.write_text("Existing content")

        progress_callback = Mock()

        # Test with overwrite resolution
        with patch.object(ops, '_resolve_conflict', return_value=ConflictResolution.OVERWRITE):
            result = await ops.copy_files([source], destination, progress_callback)

            assert result.success is True
            assert destination.read_text() == source.read_text()

    @pytest.mark.asyncio
    async def test_move_files(self, temp_dir, sample_files):
        """Test moving files"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        source = sample_files['text_file']
        original_content = source.read_text()
        destination = temp_dir / "moved_readme.txt"

        progress_callback = Mock()

        result = await ops.move_files([source], destination, progress_callback)

        assert result.success is True
        assert not source.exists()  # Source should be gone
        assert destination.exists()
        assert destination.read_text() == original_content

    @pytest.mark.asyncio
    async def test_delete_files_to_trash(self, temp_dir, sample_files):
        """Test deleting files to trash"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        file_to_delete = sample_files['empty_file']
        progress_callback = Mock()

        # Mock send2trash
        with patch('send2trash.send2trash') as mock_send2trash:
            result = await ops.delete_files([file_to_delete], use_trash=True, progress_callback=progress_callback)

            assert result.success is True
            mock_send2trash.assert_called_once_with(str(file_to_delete))

    @pytest.mark.asyncio
    async def test_delete_files_permanent(self, temp_dir, sample_files):
        """Test permanent file deletion"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        file_to_delete = sample_files['empty_file']
        progress_callback = Mock()

        result = await ops.delete_files([file_to_delete], use_trash=False, progress_callback=progress_callback)

        assert result.success is True
        assert not file_to_delete.exists()

    @pytest.mark.asyncio
    async def test_create_archive_zip(self, temp_dir, sample_files):
        """Test creating ZIP archive"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        files_to_archive = [sample_files['text_file'], sample_files['empty_file']]
        archive_path = temp_dir / "test_archive.zip"

        result = await ops.create_archive(files_to_archive, archive_path, ArchiveFormat.ZIP)

        assert result.success is True
        assert archive_path.exists()

        # Verify archive contents
        import zipfile
        with zipfile.ZipFile(archive_path, 'r') as zf:
            names = zf.namelist()
            assert "readme.txt" in names
            assert "empty.txt" in names

    @pytest.mark.asyncio
    async def test_create_archive_tar(self, temp_dir, sample_files):
        """Test creating TAR archive"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        files_to_archive = [sample_files['text_file']]
        archive_path = temp_dir / "test_archive.tar"

        result = await ops.create_archive(files_to_archive, archive_path, ArchiveFormat.TAR)

        assert result.success is True
        assert archive_path.exists()

        # Verify archive contents
        import tarfile
        with tarfile.open(archive_path, 'r') as tf:
            names = tf.getnames()
            assert any("readme.txt" in name for name in names)

    @pytest.mark.asyncio
    async def test_extract_archive_zip(self, temp_dir):
        """Test extracting ZIP archive"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        # Create test archive
        archive_path = temp_dir / "test.zip"
        extraction_dir = temp_dir / "extracted"
        extraction_dir.mkdir()

        import zipfile
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("test_file.txt", "Test content")
            zf.writestr("subdir/another_file.txt", "Another content")

        result = await ops.extract_archive(archive_path, extraction_dir)

        assert result.success is True
        assert (extraction_dir / "test_file.txt").exists()
        assert (extraction_dir / "subdir" / "another_file.txt").exists()

    @pytest.mark.asyncio
    async def test_extract_archive_tar(self, temp_dir):
        """Test extracting TAR archive"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        # Create test archive
        archive_path = temp_dir / "test.tar"
        extraction_dir = temp_dir / "extracted"
        extraction_dir.mkdir()

        import tarfile
        with tarfile.open(archive_path, 'w') as tf:
            # Create a temporary file to add to archive
            temp_file = temp_dir / "temp_for_archive.txt"
            temp_file.write_text("Test content")
            tf.add(temp_file, arcname="test_file.txt")

        result = await ops.extract_archive(archive_path, extraction_dir)

        assert result.success is True
        assert (extraction_dir / "test_file.txt").exists()

    def test_rename_file(self, temp_dir, sample_files):
        """Test file renaming"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        original_file = sample_files['text_file']
        original_content = original_file.read_text()
        new_name = "renamed_readme.txt"

        result = ops.rename_file(original_file, new_name)

        assert result.success is True
        new_path = original_file.parent / new_name
        assert new_path.exists()
        assert new_path.read_text() == original_content
        assert not original_file.exists()

    def test_rename_file_conflict(self, temp_dir, sample_files):
        """Test file renaming with name conflict"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        original_file = sample_files['text_file']
        conflicting_name = sample_files['empty_file'].name

        result = ops.rename_file(original_file, conflicting_name)

        # Should fail due to conflict
        assert result.success is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_progress_tracking(self, temp_dir, sample_files):
        """Test progress tracking during operations"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        source = sample_files['large_file']  # 1MB file
        destination = temp_dir / "copied_large.dat"

        progress_calls = []

        def progress_callback(current, total, speed=None):
            progress_calls.append((current, total, speed))

        result = await ops.copy_files([source], destination, progress_callback)

        assert result.success is True
        assert len(progress_calls) > 0

        # Check that progress was reported
        final_call = progress_calls[-1]
        assert final_call[0] == final_call[1]  # current == total at end

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, temp_dir, sample_files):
        """Test concurrent file operations"""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None: {
            'performance.max_concurrent_operations': 3,
            'performance.chunk_size': 1024
        }.get(key, default))

        ops = ComprehensiveFileOperations(config)

        # Create multiple source files
        sources = []
        for i in range(5):
            source = temp_dir / f"source_{i}.txt"
            source.write_text(f"Content {i}")
            sources.append(source)

        destination_dir = temp_dir / "concurrent_dest"
        destination_dir.mkdir()

        progress_callback = Mock()

        result = await ops.copy_files(sources, destination_dir, progress_callback)

        assert result.success is True
        assert len(result.affected_files) == 5

        # Verify all files were copied
        for i in range(5):
            dest_file = destination_dir / f"source_{i}.txt"
            assert dest_file.exists()
            assert dest_file.read_text() == f"Content {i}"

    @pytest.mark.asyncio
    async def test_error_handling_permission_denied(self, temp_dir):
        """Test error handling for permission denied"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        # Create a file and remove read permissions
        source = temp_dir / "protected.txt"
        source.write_text("Protected content")

        # Mock permission error
        with patch('pathlib.Path.read_bytes', side_effect=PermissionError("Access denied")):
            destination = temp_dir / "copied_protected.txt"
            progress_callback = Mock()

            result = await ops.copy_files([source], destination, progress_callback)

            assert result.success is False
            assert len(result.errors) > 0
            assert any("permission" in error.message.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_error_handling_disk_full(self, temp_dir, sample_files):
        """Test error handling for disk full scenario"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        source = sample_files['text_file']
        destination = temp_dir / "copied_readme.txt"

        # Mock disk full error
        with patch('pathlib.Path.write_bytes', side_effect=OSError("No space left on device")):
            progress_callback = Mock()

            result = await ops.copy_files([source], destination, progress_callback)

            assert result.success is False
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_operation_cancellation(self, temp_dir):
        """Test operation cancellation"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        # Create large files for slow operation
        sources = []
        for i in range(3):
            source = temp_dir / f"large_{i}.dat"
            source.write_bytes(b"x" * (1024 * 1024))  # 1MB each
            sources.append(source)

        destination_dir = temp_dir / "cancel_dest"
        destination_dir.mkdir()

        # Create a cancellation token
        cancellation_event = asyncio.Event()

        def progress_callback(current, total, speed=None):
            if current > total * 0.5:  # Cancel at 50%
                cancellation_event.set()

        # Start operation
        task = asyncio.create_task(
            ops.copy_files(sources, destination_dir, progress_callback)
        )

        # Wait a bit then cancel
        await asyncio.sleep(0.1)
        cancellation_event.set()
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected

    def test_get_archive_format_from_extension(self):
        """Test archive format detection from file extension"""
        config = Mock()
        ops = ComprehensiveFileOperations(config)

        assert ops._get_archive_format(Path("test.zip")) == ArchiveFormat.ZIP
        assert ops._get_archive_format(Path("test.tar")) == ArchiveFormat.TAR
        assert ops._get_archive_format(Path("test.tar.gz")) == ArchiveFormat.TAR_GZ
        assert ops._get_archive_format(Path("test.7z")) == ArchiveFormat.SEVEN_ZIP
        assert ops._get_archive_format(Path("test.unknown")) is None

    def test_calculate_total_size(self, temp_dir, sample_files):
        """Test total size calculation for operations"""
        config = Mock()
        ops = ComprehensiveFileOperations(config)

        files = [sample_files['text_file'], sample_files['large_file']]
        total_size = ops._calculate_total_size(files)

        expected_size = sample_files['text_file'].stat().st_size + sample_files['large_file'].stat().st_size
        assert total_size == expected_size

    def test_resolve_conflict_skip(self):
        """Test conflict resolution - skip"""
        config = Mock()
        ops = ComprehensiveFileOperations(config)

        # Mock user input for skip
        with patch('builtins.input', return_value='s'):
            resolution = ops._resolve_conflict(Path("source.txt"), Path("dest.txt"))
            assert resolution == ConflictResolution.SKIP

    def test_resolve_conflict_overwrite(self):
        """Test conflict resolution - overwrite"""
        config = Mock()
        ops = ComprehensiveFileOperations(config)

        # Mock user input for overwrite
        with patch('builtins.input', return_value='o'):
            resolution = ops._resolve_conflict(Path("source.txt"), Path("dest.txt"))
            assert resolution == ConflictResolution.OVERWRITE

    def test_resolve_conflict_rename(self):
        """Test conflict resolution - rename"""
        config = Mock()
        ops = ComprehensiveFileOperations(config)

        # Mock user input for rename
        with patch('builtins.input', return_value='r'):
            resolution = ops._resolve_conflict(Path("source.txt"), Path("dest.txt"))
            assert resolution == ConflictResolution.RENAME

    @pytest.mark.asyncio
    async def test_batch_operation_with_mixed_results(self, temp_dir, sample_files):
        """Test batch operation with some successes and some failures"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        # Mix of valid and invalid sources
        sources = [
            sample_files['text_file'],  # Valid
            temp_dir / "nonexistent.txt",  # Invalid
            sample_files['empty_file']  # Valid
        ]

        destination_dir = temp_dir / "batch_dest"
        destination_dir.mkdir()

        progress_callback = Mock()

        result = await ops.copy_files(sources, destination_dir, progress_callback)

        # Should have partial success
        assert len(result.affected_files) == 2  # Only valid files copied
        assert len(result.errors) == 1  # One error for nonexistent file

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_large_file_operation_performance(self, temp_dir, performance_timer):
        """Test performance with large file operations"""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None: {
            'performance.max_concurrent_operations': 10,
            'performance.chunk_size': 64 * 1024,  # 64KB chunks
            'performance.use_threading': True
        }.get(key, default))

        ops = ComprehensiveFileOperations(config)

        # Create a large file (10MB)
        large_file = temp_dir / "large_test.dat"
        large_file.write_bytes(b"x" * (10 * 1024 * 1024))

        destination = temp_dir / "copied_large_test.dat"
        progress_callback = Mock()

        performance_timer.start()
        result = await ops.copy_files([large_file], destination, progress_callback)
        performance_timer.stop()

        assert result.success is True
        assert destination.exists()
        assert destination.stat().st_size == large_file.stat().st_size

        # Should complete within reasonable time (adjust threshold as needed)
        assert performance_timer.elapsed < 5.0  # 5 seconds max for 10MB

    def test_operation_statistics(self, temp_dir, sample_files):
        """Test operation statistics tracking"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        # Perform some operations to generate stats
        ops.rename_file(sample_files['text_file'], "renamed.txt")

        stats = ops.get_operation_statistics()

        assert 'total_operations' in stats
        assert 'successful_operations' in stats
        assert 'failed_operations' in stats
        assert 'total_bytes_processed' in stats
        assert 'average_operation_time' in stats

    @pytest.mark.asyncio
    async def test_archive_with_compression_levels(self, temp_dir, sample_files):
        """Test archive creation with different compression levels"""
        config = Mock()
        config.get = Mock(return_value=5)

        ops = ComprehensiveFileOperations(config)

        files_to_archive = [sample_files['text_file'], sample_files['large_file']]

        # Test different compression levels
        for level in [1, 5, 9]:  # Low, medium, high compression
            archive_path = temp_dir / f"test_compression_{level}.zip"

            result = await ops.create_archive(
                files_to_archive,
                archive_path,
                ArchiveFormat.ZIP,
                compression_level=level
            )

            assert result.success is True
            assert archive_path.exists()

    @pytest.mark.asyncio
    async def test_operation_with_custom_chunk_size(self, temp_dir, sample_files):
        """Test operations with custom chunk sizes"""
        config = Mock()
        config.get = Mock(side_effect=lambda key, default=None: {
            'performance.max_concurrent_operations': 5,
            'performance.chunk_size': 512,  # Small chunks
            'performance.use_threading': True
        }.get(key, default))

        ops = ComprehensiveFileOperations(config)

        source = sample_files['large_file']
        destination = temp_dir / "chunked_copy.dat"

        progress_calls = []

        def progress_callback(current, total, speed=None):
            progress_calls.append((current, total))

        result = await ops.copy_files([source], destination, progress_callback)

        assert result.success is True
        assert destination.exists()

        # Should have multiple progress updates due to small chunk size
        assert len(progress_calls) > 1