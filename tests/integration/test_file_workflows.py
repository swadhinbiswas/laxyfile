"""
Integration tests for file management workflows

Tests the integration between file manager, file operations, and UI components
for complete file management workflows.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from laxyfile.core.advanced_file_manager import AdvancedFileManager
from laxyfile.operations.file_ops import ComprehensiveFileOperations
from laxyfile.ui.superfile_ui import SuperFileUI
from laxyfile.ui.enhanced_panels import EnhancedPanelManager
from laxyfile.core.types import PanelData, SidebarData, StatusData
from laxyfile.core.exceptions import FileOperationError


@pytest.mark.integration
class TestFileManagerOperationsIntegration:
    """Test integration between file manager and file operations"""

    @pytest.fixture
    def integrated_system(self, mock_config, temp_dir):
        """Create integrated file management system"""
        file_manager = AdvancedFileManager(mock_config)
        file_operations = ComprehensiveFileOperations(mock_config)

        return {
            'file_manager': file_manager,
            'file_operations': file_operations,
            'temp_dir': temp_dir
        }

    @pytest.mark.asyncio
    async def test_copy_workflow_integration(self, integrated_system, sample_files):
        """Test complete copy workflow from file manager to operations"""
        file_manager = integrated_system['file_manager']
        file_operations = integrated_system['file_operations']
        temp_dir = integrated_system['temp_dir']

        # Step 1: List source directory
        source_files = await file_manager.list_directory(temp_dir)
        assert len(source_files) > 0

        # Step 2: Select files to copy
        files_to_copy = [f for f in source_files if f.name.endswith('.txt')]
        assert len(files_to_copy) > 0

        # Step 3: Create destination directory
        dest_dir = temp_dir / "copy_destination"
        dest_dir.mkdir()

        # Step 4: Perform copy operation
        progress_updates = []
        def progress_callback(current, total, speed=None):
            progress_updates.append((current, total))

        source_paths = [f.path for f in files_to_copy]
        result = await file_operations.copy_files(source_paths, dest_dir, progress_callback)

        # Step 5: Verify operation success
        assert result.success is True
        assert len(result.affected_files) == len(files_to_copy)
        assert len(progress_updates) > 0

        # Step 6: Verify files in destination using file manager
        dest_files = await file_manager.list_directory(dest_dir)
        copied_file_names = [f.name for f in dest_files if f.name != ".."]
        original_file_names = [f.name for f in files_to_copy]

        for original_name in original_file_names:
            assert original_name in copied_file_names

    @pytest.mark.asyncio
    async def test_move_workflow_integration(self, integrated_system, sample_files):
        """Test complete move workflow"""
        file_manager = integrated_system['file_manager']
        file_operations = integrated_system['file_operations']
        temp_dir = integrated_system['temp_dir']

        # Create test file
        test_file = temp_dir / "move_test.txt"
        test_file.write_text("Content to move")

        # Step 1: Get file info
        file_info = await file_manager.get_file_info(test_file)
        assert file_info.name == "move_test.txt"

        # Step 2: Create destination
        dest_dir = temp_dir / "move_destination"
        dest_dir.mkdir()

        # Step 3: Perform move operation
        progress_updates = []
        def progress_callback(current, total, speed=None):
            progress_updates.append((current, total))

        result = await file_operations.move_files([test_file], dest_dir, progress_callback)

        # Step 4: Verify move success
        assert result.success is True
        assert not test_file.exists()  # Original should be gone

        # Step 5: Verify file in destination
        dest_files = await file_manager.list_directory(dest_dir)
        moved_files = [f for f in dest_files if f.name == "move_test.txt"]
        assert len(moved_files) == 1
        assert moved_files[0].size == len("Content to move")

    @pytest.mark.asyncio
    async def test_delete_workflow_integration(self, integrated_system):
        """Test complete delete workflow"""
        file_manager = integrated_system['file_manager']
        file_operations = integrated_system['file_operations']
        temp_dir = integrated_system['temp_dir']

        # Create test files
        test_files = []
        for i in range(3):
            test_file = temp_dir / f"delete_test_{i}.txt"
            test_file.write_text(f"Content {i}")
            test_files.append(test_file)

        # Step 1: List directory and verify files exist
        initial_files = await file_manager.list_directory(temp_dir)
        initial_names = [f.name for f in initial_files]
        for test_file in test_files:
            assert test_file.name in initial_names

        # Step 2: Perform delete operation
        progress_updates = []
        def progress_callback(current, total, speed=None):
            progress_updates.append((current,)

        result = await file_operations.delete_files(test_files, use_trash=False, progress_callback=progress_callback)

        # Step 3: Verify deletion success
        assert result.success is True
        assert len(result.affected_files) == 3

        # Step 4: Verify files are gone
        final_files = await file_manager.list_directory(temp_dir)
        final_names = [f.name for f in final_files]
        for test_file in test_files:
            assert test_file.name not in final_names

    @pytest.mark.asyncio
    async def test_archive_workflow_integration(self, integrated_system, sample_files):
        """Test complete archive creation and extraction workflow"""
        file_manager = integrated_system['file_manager']
        file_operations = integrated_system['file_operations']
        temp_dir = integrated_system['temp_dir']

        # Step 1: Select files to archive
        source_files = await file_manager.list_directory(temp_dir)
        files_to_archive = [f.path for f in source_files if f.name.endswith('.txt')]
        assert len(files_to_archive) > 0

        # Step 2: Create archive
        archive_path = temp_dir / "test_archive.zip"
        from laxyfile.operations.file_ops import ArchiveFormat

        result = await file_operations.create_archive(files_to_archive, archive_path, ArchiveFormat.ZIP)
        assert result.success is True
        assert archive_path.exists()

        # Step 3: Verify archive using file manager
        archive_info = await file_manager.get_file_info(archive_path)
        assert archive_info.name == "test_archive.zip"
        assert archive_info.size > 0

        # Step 4: Extract archive
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir()

        extract_result = await file_operations.extract_archive(archive_path, extract_dir)
        assert extract_result.success is True

        # Step 5: Verify extracted files
        extracted_files = await file_manager.list_directory(extract_dir)
        extracted_names = [f.name for f in extracted_files if f.name != ".."]
        original_names = [Path(p).name for p in files_to_archive]

        for original_name in original_names:
            assert original_name in extracted_names

    @pytest.mark.asyncio
    async def test_search_and_operations_integration(self, integrated_system):
        """Test search integration with file operations"""
        file_manager = integrated_system['file_manager']
        file_operations = integrated_system['file_operations']
        temp_dir = integrated_system['temp_dir']

        # Create test files with searchable content
        search_files = []
        for i in range(5):
            test_file = temp_dir / f"search_test_{i}.txt"
            content = f"This is test file {i} with searchable content"
            if i % 2 == 0:
                content += " SPECIAL_MARKER"
            test_file.write_text(content)
            search_files.append(test_file)

        # Step 1: Search for files with specific content
        search_results = await file_manager.search_files(temp_dir, "SPECIAL_MARKER", include_content=True)
        assert len(search_results) == 3  # Files 0, 2, 4

        # Step 2: Use search results for batch operation
        search_paths = [f.path for f in search_results]
        dest_dir = temp_dir / "search_results"
        dest_dir.mkdir()

        progress_updates = []
        def progress_callback(current, total, speed=None):
            progress_updates.append((current, total))

        # Step 3: Copy search results
        result = await file_operations.copy_files(search_paths, dest_dir, progress_callback)
        assert result.success is True
        assert len(result.affected_files) == 3

        # Step 4: Verify copied files
        copied_files = await file_manager.list_directory(dest_dir)
        copied_names = [f.name for f in copied_files if f.name != ".."]
        expected_names = ["search_test_0.txt", "search_test_2.txt", "search_test_4.txt"]

        for expected_name in expected_names:
            assert expected_name in copied_names

    @pytest.mark.asyncio
    async def test_concurrent_operations_integration(self, integrated_system):
        """Test concurrent file operations with file manager"""
        file_manager = integrated_system['file_manager']
        file_operations = integrated_system['file_operations']
        temp_dir = integrated_system['temp_dir']

        # Create multiple source directories
        source_dirs = []
        for i in range(3):
            source_dir = temp_dir / f"source_{i}"
            source_dir.mkdir()

            # Create files in each source directory
            for j in range(5):
                test_file = source_dir / f"file_{j}.txt"
                test_file.write_text(f"Content from source {i}, file {j}")

            source_dirs.append(source_dir)

        # Create destination directories
        dest_dirs = []
        for i in range(3):
            dest_dir = temp_dir / f"dest_{i}"
            dest_dir.mkdir()
            dest_dirs.append(dest_dir)

        # Step 1: List all source files concurrently
        list_tasks = [file_manager.list_directory(source_dir) for source_dir in source_dirs]
        source_file_lists = await asyncio.gather(*list_tasks)

        # Verify all directories were listed
        for file_list in source_file_lists:
            assert len(file_list) == 6  # 5 files + parent directory

        # Step 2: Perform concurrent copy operations
        copy_tasks = []
        for i, (source_dir, dest_dir) in enumerate(zip(source_dirs, dest_dirs)):
            source_files = [f.path for f in source_file_lists[i] if f.name != ".."]
            progress_callback = Mock()
            copy_task = file_operations.copy_files(source_files, dest_dir, progress_callback)
            copy_tasks.append(copy_task)

        copy_results = await asyncio.gather(*copy_tasks)

        # Step 3: Verify all operations succeeded
        for result in copy_results:
            assert result.success is True
            assert len(result.affected_files) == 5

        # Step 4: Verify all files were copied using file manager
        verify_tasks = [file_manager.list_directory(dest_dir) for dest_dir in dest_dirs]
        dest_file_lists = await asyncio.gather(*verify_tasks)

        for file_list in dest_file_lists:
            file_names = [f.name for f in file_list if f.name != ".."]
            expected_names = [f"file_{j}.txt" for j in range(5)]
            for expected_name in expected_names:
                assert expected_name in file_names

    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, integrated_system):
        """Test error recovery in integrated workflows"""
        file_manager = integrated_system['file_manager']
        file_operations = integrated_system['file_operations']
        temp_dir = integrated_system['temp_dir']

        # Create test files with one that will cause an error
        test_files = []
        for i in range(3):
            test_file = temp_dir / f"error_test_{i}.txt"
            test_file.write_text(f"Content {i}")
            test_files.append(test_file)

        # Add a non-existent file to cause an error
        non_existent = temp_dir / "non_existent.txt"
        test_files.append(non_existent)

        # Step 1: Attempt to copy files (some will fail)
        dest_dir = temp_dir / "error_dest"
        dest_dir.mkdir()

        progress_updates = []
        def progress_callback(current, total, speed=None):
            progress_updates.append((current, total))

        result = await file_operations.copy_files(test_files, dest_dir, progress_callback)

        # Step 2: Verify partial success
        assert len(result.affected_files) == 3  # Only existing files copied
        assert len(result.errors) == 1  # One error for non-existent file

        # Step 3: Verify successful files using file manager
        dest_files = await file_manager.list_directory(dest_dir)
        copied_names = [f.name for f in dest_files if f.name != ".."]

        # Should have the 3 existing files
        expected_names = ["error_test_0.txt", "error_test_1.txt", "error_test_2.txt"]
        for expected_name in expected_names:
            assert expected_name in copied_names

        # Should not have the non-existent file
        assert "non_existent.txt" not in copied_names

    @pytest.mark.asyncio
    async def test_cache_integration_workflow(self, integrated_system, sample_files):
        """Test file manager cache integration with operations"""
        file_manager = integrated_system['file_manager']
        file_operations = integrated_system['file_operations']
        temp_dir = integrated_system['temp_dir']

        # Step 1: List directory to populate cache
        initial_files = await file_manager.list_directory(temp_dir)
        initial_count = len(initial_files)

        # Verify cache is populated
        cache_stats = file_manager.get_cache_stats()
        assert cache_stats['directory_cache_size'] > 0

        # Step 2: Create new file using operations
        new_file = temp_dir / "cache_test.txt"
        new_file.write_text("New file content")

        # Step 3: List directory again (should use cache initially)
        cached_files = await file_manager.list_directory(temp_dir)
        # Cache might not reflect new file immediately

        # Step 4: Invalidate cache and list again
        file_manager.invalidate_cache(temp_dir)
        updated_files = await file_manager.list_directory(temp_dir)

        # Should now see the new file
        assert len(updated_files) == initial_count + 1
        new_file_names = [f.name for f in updated_files]
        assert "cache_test.txt" in new_file_names

        # Step 5: Perform operation and verify cache invalidation
        dest_dir = temp_dir / "cache_dest"
        dest_dir.mkdir()

        progress_callback = Mock()
        result = await file_operations.copy_files([new_file], dest_dir, progress_callback)
        assert result.success is True

        # Verify destination has the file
        dest_files = await file_manager.list_directory(dest_dir)
        dest_names = [f.name for f in dest_files if f.name != ".."]
        assert "cache_test.txt" in dest_names


@pytest.mark.integration
class TestUIFileManagerIntegration:
    """Test integration between UI components and file manager"""

    @pytest.fixture
    def ui_system(self, mock_config, theme_manager, console):
        """Create integrated UI system"""
        file_manager = AdvancedFileManager(mock_config)
        ui = SuperFileUI(theme_manager, console, mock_config)
        panel_manager = EnhancedPanelManager(file_manager)

        return {
            'file_manager': file_manager,
            'ui': ui,
            'panel_manager': panel_manager
        }

    @pytest.mark.asyncio
    async def test_panel_data_integration(self, ui_system, temp_dir, sample_files):
        """Test integration between file manager and panel data"""
        file_manager = ui_system['file_manager']
        ui = ui_system['ui']

        # Step 1: Get files from file manager
        files = await file_manager.list_directory(temp_dir)
        assert len(files) > 0

        # Step 2: Create panel data
        panel_data = PanelData(
            path=temp_dir,
            files=files,
            current_selection=0,
            selected_files=set(),
            sort_type="name",
            reverse_sort=False,
            search_query=""
        )

        # Step 3: Render panel using UI
        panel = ui.render_file_panel(panel_data)
        assert panel is not None

        # Step 4: Verify panel content includes file information
        panel_content = str(panel)
        file_names = [f.name for f in files if f.name != ".."]
        for file_name in file_names[:3]:  # Check first few files
            assert file_name in panel_content

    @pytest.mark.asyncio
    async def test_sidebar_integration(self, ui_system, temp_dir):
        """Test sidebar integration with file manager"""
        file_manager = ui_system['file_manager']
        ui = ui_system['ui']

        # Step 1: Create bookmarks and recent paths
        bookmarks = [temp_dir / "documents", temp_dir / "images"]
        recent_paths = [temp_dir / "code"]

        # Create directories for bookmarks
        for bookmark in bookmarks:
            bookmark.mkdir(exist_ok=True)
        for recent in recent_paths:
            recent.mkdir(exist_ok=True)

        # Step 2: Create sidebar data
        sidebar_data = SidebarData(
            current_path=temp_dir,
            bookmarks=bookmarks,
            recent_paths=recent_paths,
            directory_tree={}
        )

        # Step 3: Render sidebar
        sidebar_panel = ui.render_sidebar(sidebar_data)
        assert sidebar_panel is not None

        # Step 4: Verify sidebar content
        sidebar_content = str(sidebar_panel)
        assert "Current Path" in sidebar_content
        assert "Bookmarks" in sidebar_content
        assert "Recent" in sidebar_content
        assert "documents" in sidebar_content
        assert "images" in sidebar_content

    @pytest.mark.asyncio
    async def test_status_integration(self, ui_system, temp_dir, sample_files):
        """Test status bar integration with file manager"""
        file_manager = ui_system['file_manager']
        ui = ui_system['ui']

        # Step 1: Get file info from file manager
        files = await file_manager.list_directory(temp_dir)
        current_file = next((f for f in files if f.name != ".."), None)
        assert current_file is not None

        # Step 2: Calculate statistics
        total_files = len([f for f in files if f.name != ".."])
        total_size = sum(f.size for f in files if f.name != "..")

        # Step 3: Create status data
        status_data = StatusData(
            current_file=current_file,
            selected_count=2,
            total_files=total_files,
            total_size=total_size,
            operation_status="Ready",
            ai_status=""
        )

        # Step 4: Render footer
        footer_panel = ui.render_footer(status_data)
        assert footer_panel is not None

        # Step 5: Verify footer content
        footer_content = str(footer_panel)
        assert current_file.name in footer_content
        assert "2 selected" in footer_content
        assert f"{total_files} items" in footer_content

    @pytest.mark.asyncio
    async def test_panel_manager_integration(self, ui_system, temp_dir, sample_files):
        """Test panel manager integration with file manager and UI"""
        file_manager = ui_system['file_manager']
        ui = ui_system['ui']
        panel_manager = ui_system['panel_manager']

        # Step 1: Create panel using panel manager
        panel = panel_manager.create_panel(temp_dir)
        assert panel is not None
        assert panel.path == temp_dir

        # Step 2: Navigate using panel manager
        files = await file_manager.list_directory(temp_dir)
        subdirs = [f for f in files if f.is_dir and f.name != ".."]

        if subdirs:
            # Navigate to subdirectory
            subdir = subdirs[0]
            panel_manager.navigate(panel.id, str(subdir.path))

            # Verify navigation
            assert panel.path == subdir.path

        # Step 3: Test selection
        panel_manager.select_files(panel.id, [files[0].path] if files else [])

        # Step 4: Test search
        panel_manager.search(panel.id, "test")
        assert panel.search_query == "test"

        # Step 5: Test sorting
        from laxyfile.core.types import SortType
        panel_manager.sort(panel.id, SortType.SIZE)
        assert panel.sort_type == SortType.SIZE

    @pytest.mark.asyncio
    async def test_responsive_ui_integration(self, ui_system, temp_dir):
        """Test responsive UI behavior with different data sizes"""
        file_manager = ui_system['file_manager']
        ui = ui_system['ui']

        # Create layout
        layout = ui.create_layout()
        assert layout is not None

        # Test with different terminal sizes
        test_sizes = [(80, 24), (120, 30), (50, 20)]

        for width, height in test_sizes:
            # Step 1: Handle resize
            ui.handle_resize(width, height)
            assert ui.current_width == width
            assert ui.current_height == height

            # Step 2: Get files and create panel data
            files = await file_manager.list_directory(temp_dir)
            panel_data = PanelData(
                path=temp_dir,
                files=files,
                current_selection=0,
                selected_files=set(),
                sort_type="name",
                reverse_sort=False,
                search_query=""
            )

            # Step 3: Render components
            panel = ui.render_file_panel(panel_data)
            header = ui.render_header()

            # Should render without errors regardless of size
            assert panel is not None
            assert header is not None

    @pytest.mark.asyncio
    async def test_theme_integration_workflow(self, ui_system, temp_dir, sample_files):
        """Test theme integration across all UI components"""
        file_manager = ui_system['file_manager']
        ui = ui_system['ui']

        # Step 1: Apply different themes
        themes = ["cappuccino", "dracula", "nord"]

        for theme_name in themes:
            # Apply theme
            ui.apply_theme(theme_name)

            # Step 2: Get data from file manager
            files = await file_manager.list_directory(temp_dir)

            # Step 3: Create UI data structures
            panel_data = PanelData(
                path=temp_dir,
                files=files,
                current_selection=0,
                selected_files=set(),
                sort_type="name",
                reverse_sort=False,
                search_query=""
            )

            sidebar_data = SidebarData(
                current_path=temp_dir,
                bookmarks=[],
                recent_paths=[],
                directory_tree={}
            )

            status_data = StatusData(
                current_file=files[0] if files else None,
                selected_count=0,
                total_files=len(files),
                total_size=sum(f.size for f in files),
                operation_status="",
                ai_status=""
            )

            # Step 4: Render all components
            panel = ui.render_file_panel(panel_data)
            sidebar = ui.render_sidebar(sidebar_data)
            footer = ui.render_footer(status_data)
            header = ui.render_header()

            # All should render successfully with theme applied
            assert panel is not None
            assert sidebar is not None
            assert footer is not None
            assert header is not None

    @pytest.mark.asyncio
    async def test_large_directory_ui_integration(self, ui_system, temp_dir):
        """Test UI integration with large directories"""
        file_manager = ui_system['file_manager']
        ui = ui_system['ui']

        # Step 1: Create large directory
        large_dir = temp_dir / "large_directory"
        large_dir.mkdir()

        # Create many files
        num_files = 100
        for i in range(num_files):
            test_file = large_dir / f"file_{i:03d}.txt"
            test_file.write_text(f"Content {i}")

        # Step 2: List directory using file manager
        files = await file_manager.list_directory(large_dir)
        assert len(files) == num_files + 1  # +1 for parent directory

        # Step 3: Create panel data
        panel_data = PanelData(
            path=large_dir,
            files=files,
            current_selection=0,
            selected_files=set(),
            sort_type="name",
            reverse_sort=False,
            search_query=""
        )

        # Step 4: Render panel (should handle large data efficiently)
        panel = ui.render_file_panel(panel_data)
        assert panel is not None

        # Step 5: Test with selection
        selected_files = {files[i].path for i in range(0, min(10, len(files)))}
        panel_data.selected_files = selected_files

        panel_with_selection = ui.render_file_panel(panel_data)
        assert panel_with_selection is not None

        # Step 6: Test status with large data
        status_data = StatusData(
            current_file=files[1] if len(files) > 1 else None,  # Skip parent dir
            selected_count=len(selected_files),
            total_files=len(files) - 1,  # Exclude parent dir
            total_size=sum(f.size for f in files if f.name != ".."),
            operation_status="",
            ai_status=""
        )

        footer = ui.render_footer(status_data)
        assert footer is not None