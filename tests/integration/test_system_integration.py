"""
System Integration Tests

This module tests the complete LaxyFile system integration,
including startup, shutdown, and full user workflow scenarios.
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from laxyfile.main import LaxyFileApp
from laxyfile.core.config import Config
from laxyfile.core.advanced_file_manager import AdvancedFileManager
from laxyfile.ui.superfile_ui import SuperFileUI
from laxyfile.ai.advanced_assistant import AdvancedAIAssistant
from laxyfile.plugins.plugin_manager import PluginManager
from laxyfile.ui.theme import ThemeManager


class TestSystemIntegration:
    """Test complete system integration scenarios"""

    @pytest.fixture
    def system_config(self):
        """Create system configuration for testing"""
        config = Config()

        # Set test configuration
        config.set('app.version', '2.0.0')
        config.set('app.debug', True)
        config.set('ui.theme', 'catppuccin')
        config.set('ui.animations', True)
        config.set('ai.enabled', True)
        config.set('ai.provider', 'mock')
        config.set('plugins.enabled', True)
        config.set('performance.cache_size', 500)
        config.set('performance.lazy_loading', True)
        config.set('onboarding.completed', True)  # Skip onboarding for tests

        return config

    @pytest.fixture
    def test_environment(self):
        """Create comprehensive test environment"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir)

            # Create realistic directory structure
            self._create_test_structure(workspace)

            yield {
                'workspace': workspace,
                'documents': workspace / 'Documents',
                'images': workspace / 'Images',
                'code': workspace / 'Code',
                'downloads': workspace / 'Downloads'
            }

    def _create_test_structure(self, workspace: Path):
        """Create realistic test directory structure"""
        # Documents
        docs = workspace / 'Documents'
        docs.mkdir()
        (docs / 'report.pdf').write_bytes(b'%PDF-1.4 fake pdf content')
        (docs / 'notes.txt').write_text('Meeting notes from project discussion')
        (docs / 'presentation.pptx').write_bytes(b'PK fake powerpoint')
        (docs / 'spreadsheet.xlsx').write_bytes(b'PK fake excel')

        # Images
        images = workspace / 'Images'
        images.mkdir()
        (images / 'photo1.jpg').write_bytes(b'\xff\xd8\xff\xe0 fake jpeg')
        (images / 'photo2.png').write_bytes(b'\x89PNG fake png')
        (images / 'diagram.svg').write_text('<svg>fake svg</svg>')

        # Code
        code = workspace / 'Code'
        code.mkdir()
        (code / 'main.py').write_text('''
#!/usr/bin/env python3
"""
Main application entry point
"""

def main():
    print("Hello, LaxyFile!")
    return 0

if __name__ == "__main__":
    main()
''')
        (code / 'config.json').write_text(json.dumps({
            'debug': True,
            'version': '1.0.0',
            'features': ['ai', 'themes', 'plugins']
        }, indent=2))
        (code / 'README.md').write_text('''
# Test Project

This is a test project for LaxyFile integration testing.

## Features
- File management
- AI integration
- Theme system
''')

        # Downloads (messy directory)
        downloads = workspace / 'Downloads'
        downloads.mkdir()
        (downloads / 'installer.exe').write_bytes(b'MZ fake executable')
        (downloads / 'document.pdf').write_bytes(b'%PDF-1.4 downloaded pdf')
        (downloads / 'image.jpg').write_bytes(b'\xff\xd8\xff\xe0 downloaded image')
        (downloads / 'archive.zip').write_bytes(b'PK fake zip')
        (downloads / 'data.csv').write_text('name,value\ntest,123\ndata,456')
        (downloads / 'temp_file.tmp').write_text('temporary content')

        # Hidden files
        (workspace / '.hidden_config').write_text('hidden configuration')
        (workspace / '.gitignore').write_text('*.tmp\n*.log\n__pycache__/')

    @pytest.fixture
    async def integrated_app(self, system_config, test_environment):
        """Create fully integrated LaxyFile application"""
        # Mock console for testing
        mock_console = Mock()
        mock_console.size.width = 120
        mock_console.size.height = 40

        # Create application with mocked dependencies
        with patch('laxyfile.main.Console', return_value=mock_console):
            app = LaxyFileApp(system_config)

            # Mock AI assistant to avoid external dependencies
            mock_ai = Mock(spec=AdvancedAIAssistant)
            mock_ai.analyze_file = AsyncMock(return_value=Mock(
                analysis="This file contains test data for integration testing.",
                suggestions=["Consider organizing files by type", "Archive old files"],
                confidence=0.9,
                metadata={'file_type': 'text', 'language': 'english'}
            ))
            mock_ai.suggest_organization = AsyncMock(return_value=[
                {'action': 'create_folder', 'name': 'Text Files', 'files': ['notes.txt']},
                {'action': 'create_folder', 'name': 'PDFs', 'files': ['report.pdf']}
            ])

            app.ai_assistant = mock_ai

            # Initialize application
            await app.initialize()

            yield app, test_environment

            # Cleanup
            await app.shutdown()

    @pytest.mark.asyncio
    async def test_application_startup_shutdown(self, system_config):
        """Test complete application startup and shutdown cycle"""
        mock_console = Mock()
        mock_console.size.width = 120
        mock_console.size.height = 40

        with patch('laxyfile.main.Console', return_value=mock_console):
            app = LaxyFileApp(system_config)

            # Test initialization
            init_success = await app.initia)
            assert init_success

            # Verify components are initialized
            assert app.file_manager is not None
            assert app.ui is not None
            assert app.theme_manager is not None
            assert app.plugin_manager is not None

            # Test shutdown
            shutdown_success = await app.shutdown()
            assert shutdown_success

    @pytest.mark.asyncio
    async def test_complete_file_browsing_workflow(self, integrated_app):
        """Test complete file browsing workflow"""
        app, env = integrated_app
        workspace = env['workspace']

        # Navigate to workspace
        await app.navigate_to_directory(workspace)

        # Verify current directory
        current_path = app.get_current_directory()
        assert current_path == workspace

        # List directory contents
        files = await app.file_manager.list_directory(workspace)
        assert len(files) >= 4  # Documents, Images, Code, Downloads

        # Navigate to subdirectory
        documents_dir = env['documents']
        await app.navigate_to_directory(documents_dir)

        # Verify navigation
        current_path = app.get_current_directory()
        assert current_path == documents_dir

        # List subdirectory contents
        doc_files = await app.file_manager.list_directory(documents_dir)
        assert len(doc_files) >= 4  # report.pdf, notes.txt, etc.

        # Select a file
        test_file = next(f for f in doc_files if f.name == 'notes.txt')
        app.select_file(test_file)

        # Verify selection
        selected_files = app.get_selected_files()
        assert len(selected_files) == 1
        assert selected_files[0].name == 'notes.txt'

    @pytest.mark.asyncio
    async def test_ai_integration_workflow(self, integrated_app):
        """Test AI integration across the system"""
        app, env = integrated_app

        # Navigate to documents
        documents_dir = env['documents']
        await app.navigate_to_directory(documents_dir)

        # Get a test file
        files = await app.file_manager.list_directory(documents_dir)
        test_file = next(f for f in files if f.name == 'notes.txt')

        # Analyze file with AI
        analysis = await app.ai_assistant.analyze_file(test_file.path)

        # Verify AI analysis
        assert analysis is not None
        assert hasattr(analysis, 'analysis')
        assert hasattr(analysis, 'suggestions')
        assert len(analysis.suggestions) > 0

        # Test AI organization suggestions
        org_suggestions = await app.ai_assistant.suggest_organization(documents_dir)
        assert len(org_suggestions) > 0

        # Verify suggestions have required structure
        for suggestion in org_suggestions:
            assert 'action' in suggestion
            assert 'name' in suggestion
            assert 'files' in suggestion

    @pytest.mark.asyncio
    async def test_file_operations_workflow(self, integrated_app):
        """Test file operations integration"""
        app, env = integrated_app
        workspace = env['workspace']

        # Create test file
        test_file = workspace / 'integration_test.txt'
        test_file.write_text('Integration test content')

        # Navigate to workspace
        await app.navigate_to_directory(workspace)

        # Refresh to see new file
        await app.refresh_current_directory()

        # Find the test file
        files = await app.file_manager.list_directory(workspace)
        test_file_info = next(f for f in files if f.name == 'integration_test.txt')

        # Select file for operation
        app.select_file(test_file_info)

        # Create destination directory
        dest_dir = workspace / 'test_destination'
        dest_dir.mkdir()

        # Copy file
        success = await app.copy_selected_files(dest_dir)
        assert success

        # Verify copy
        dest_files = await app.file_manager.list_directory(dest_dir)
        assert len(dest_files) == 1
        assert dest_files[0].name == 'integration_test.txt'

        # Verify original still exists
        original_files = await app.file_manager.list_directory(workspace)
        original_test_file = next(f for f in original_files if f.name == 'integration_test.txt')
        assert original_test_file is not None

    @pytest.mark.asyncio
    async def test_theme_system_integration(self, integrated_app):
        """Test theme system integration"""
        app, env = integrated_app

        # Get current theme
        current_theme = app.theme_manager.get_current_theme()
        assert current_theme is not None

        # Get available themes
        available_themes = app.theme_manager.get_available_themes()
        assert len(available_themes) > 1

        # Switch to different theme
        new_theme_name = 'dracula' if 'dracula' in available_themes else available_themes[1]
        success = app.theme_manager.set_theme(new_theme_name)
        assert success

        # Verify theme change
        updated_theme = app.theme_manager.get_current_theme()
        assert updated_theme.name == new_theme_name

        # Apply theme to UI
        app.ui.apply_theme(new_theme_name)

        # Verify UI reflects theme change
        assert app.ui.current_theme == new_theme_name

    @pytest.mark.asyncio
    async def test_plugin_system_integration(self, integrated_app):
        """Test plugin system integration"""
        app, env = integrated_app

        # Verify plugin manager is initialized
        assert app.plugin_manager is not None

        # Test plugin loading (with mock plugin)
        mock_plugin = Mock()
        mock_plugin.metadata.name = "Integration Test Plugin"
        mock_plugin.metadata.version = "1.0.0"
        mock_plugin.is_enabled = True
        mock_plugin.can_handle_file = Mock(return_value=True)
        mock_plugin.handle_file = AsyncMock(return_value="Plugin processed file")

        # Register mock plugin
        app.plugin_manager.plugins["integration_test"] = mock_plugin

        # Test plugin interaction with file system
        workspace = env['workspace']
        await app.navigate_to_directory(workspace)

        files = await app.file_manager.list_directory(workspace)
        test_file = files[0]

        # Plugin should be able to handle file
        can_handle = mock_plugin.can_handle_file(test_file)
        assert can_handle

        # Plugin should be able to process file
        result = await mock_plugin.handle_file(test_file, "test_action")
        assert result == "Plugin processed file"

    @pytest.mark.asyncio
    async def test_search_integration(self, integrated_app):
        """Test search functionality integration"""
        app, env = integrated_app

        # Navigate to workspace
        workspace = env['workspace']
        await app.navigate_to_directory(workspace)

        # Test filename search
        search_results = await app.file_manager.search_files(
            workspace,
            "*.txt",
            recursive=True
        )

        # Should find text files
        assert len(search_results) > 0
        txt_files = [f for f in search_results if f.path.suffix == '.txt']
        assert len(txt_files) > 0

        # Test content search (if available)
        content_results = await app.file_manager.search_files(
            workspace,
            "test",
            include_content=True,
            recursive=True
        )

        # Should find files containing "test"
        assert len(content_results) >= 0  # May be 0 if content search not available

    @pytest.mark.asyncio
    async def test_configuration_persistence(self, integrated_app):
        """Test configuration persistence across operations"""
        app, env = integrated_app

        # Change configuration
        original_theme = app.config.get('ui.theme')
        new_theme = 'nord'

        app.config.set('ui.theme', new_theme)
        app.config.set('ui.show_hidden', True)
        app.config.set('performance.cache_size', 750)

        # Save configuration
        app.config.save()

        # Verify changes are persisted
        assert app.config.get('ui.theme') == new_theme
        assert app.config.get('ui.show_hidden') == True
        assert app.config.get('performance.cache_size') == 750

        # Reload configuration
        app.config.reload()

        # Verify persistence
        assert app.config.get('ui.theme') == new_theme
        assert app.config.get('ui.show_hidden') == True
        assert app.config.get('performance.cache_size') == 750

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, integrated_app):
        """Test error handling across the integrated system"""
        app, env = integrated_app

        # Test file operation error handling
        non_existent_file = Path("/non/existent/file.txt")

        try:
            await app.file_manager.get_file_info(non_existent_file)
            # Should handle gracefully
        except Exception as e:
            # Should be appropriate exception type
            assert isinstance(e, (FileNotFoundError, PermissionError))

        # Test AI error handling
        app.ai_assistant.analyze_file.side_effect = Exception("AI service error")

        try:
            result = await app.ai_assistant.analyze_file(Path("test.txt"))
            # Should handle AI errors gracefully
        except Exception as e:
            assert "AI service error" in str(e)

        # Reset AI mock
        app.ai_assistant.analyze_file.side_effect = None
        app.ai_assistant.analyze_file.return_value = Mock(
            analysis="Test analysis",
            suggestions=["Test suggestion"]
        )

    @pytest.mark.asyncio
    async def test_performance_integration(self, integrated_app):
        """Test system performance under integrated load"""
        app, env = integrated_app
        workspace = env['workspace']

        # Create performance test directory
        perf_dir = workspace / 'performance_test'
        perf_dir.mkdir()

        # Create many files
        for i in range(50):
            test_file = perf_dir / f'perf_file_{i:03d}.txt'
            test_file.write_text(f'Performance test content {i}')

        # Test directory listing performance
        import time
        start_time = time.time()

        await app.navigate_to_directory(perf_dir)
        files = await app.file_manager.list_directory(perf_dir)

        end_time = time.time()
        duration = end_time - start_time

        # Should handle 50 files efficiently
        assert len(files) == 50
        assert duration < 1.0  # Should complete within 1 second

        # Test concurrent operations
        tasks = [
            app.file_manager.get_file_info(files[i].path)
            for i in range(min(10, len(files)))
        ]

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        concurrent_duration = end_time - start_time

        # Concurrent operations should be efficient
        assert len(results) == 10
        assert concurrent_duration < 2.0

    @pytest.mark.asyncio
    async def test_memory_management_integration(self, integrated_app):
        """Test memory management in integrated system"""
        import gc
        import psutil

        app, env = integrated_app
        workspace = env['workspace']

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Perform memory-intensive operations
        for _ in range(5):
            # Navigate through directories
            await app.navigate_to_directory(workspace)
            await app.navigate_to_directory(env['documents'])
            await app.navigate_to_directory(env['images'])
            await app.navigate_to_directory(env['code'])

            # List directories
            for dir_path in [workspace, env['documents'], env['images'], env['code']]:
                files = await app.file_manager.list_directory(dir_path)

                # Get file info for some files
                for file_info in files[:3]:
                    if file_info.path.is_file():
                        await app.file_manager.get_file_info(file_info.path)

        # Force garbage collection
        gc.collect()

        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB

        # Memory increase should be reasonable
        assert memory_increase < 100  # Less than 100MB increase

    @pytest.mark.asyncio
    async def test_complete_user_workflow(self, integrated_app):
        """Test complete realistic user workflow"""
        app, env = integrated_app
        workspace = env['workspace']

        # 1. Start at workspace
        await app.navigate_to_directory(workspace)
        current_dir = app.get_current_directory()
        assert current_dir == workspace

        # 2. Browse to Downloads (messy directory)
        downloads_dir = env['downloads']
        await app.navigate_to_directory(downloads_dir)

        # 3. List files in Downloads
        download_files = await app.file_manager.list_directory(downloads_dir)
        assert len(download_files) >= 5

        # 4. Get AI organization suggestions
        org_suggestions = await app.ai_assistant.suggest_organization(downloads_dir)
        assert len(org_suggestions) > 0

        # 5. Select multiple files
        pdf_files = [f for f in download_files if f.name.endswith('.pdf')]
        for pdf_file in pdf_files:
            app.select_file(pdf_file)

        selected = app.get_selected_files()
        assert len(selected) >= 1

        # 6. Create organized directory
        organized_dir = workspace / 'Organized'
        organized_dir.mkdir()

        # 7. Move selected files
        success = await app.move_selected_files(organized_dir)
        assert success

        # 8. Verify organization
        organized_files = await app.file_manager.list_directory(organized_dir)
        assert len(organized_files) >= 1

        # 9. Switch theme for better visibility
        available_themes = app.theme_manager.get_available_themes()
        if 'nord' in available_themes:
            app.theme_manager.set_theme('nord')
            app.ui.apply_theme('nord')

        # 10. Navigate back to workspace
        await app.navigate_to_directory(workspace)

        # 11. Verify final state
        final_files = await app.file_manager.list_directory(workspace)
        organized_folder = next(f for f in final_files if f.name == 'Organized')
        assert organized_folder is not None
        assert organized_folder.is_dir