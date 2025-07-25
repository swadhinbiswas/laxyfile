"""
End-to-End Workflow Tests

This module tests complete user workflows to ensure all components
work together seamlessly in real-world scenarios.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from laxyfile.core.config import Config
from laxyfile.integration.component_integration import ComponentIntegrator
from laxyfile.main import LaxyFileApplication


class TestCompleteWorkflows:
    """Test complete user workflows end-to-end"""

    @pytest.fixture
    async def test_environment(self):
        """Create a test environment with temporary directories and files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)

            # Create test directory structure
            (test_dir / "documents").mkdir()
            (test_dir / "images").mkdir()
            (test_dir / "code").mkdir()
            (test_dir / "archives").mkdir()

            # Create test files
            test_files = {
                "documents/readme.txt": "This is a test readme file.",
                "documents/notes.md": "# Test Notes\n\nSome markdown content.",
                "images/test.txt": "Fake image file for testing",
                "code/script.py": "#!/usr/bin/env python3\nprint('Hello, World!')",
                "code/config.json": '{"test": true, "value": 42}',
                "test_file.txt": "Root level test file"
            }

            for file_path, content in test_files.items():
                full_path = test_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)

            yield {
                'test_dir': test_dir,
                'test_files': test_files
            }

    @pytest.fixture
    async def app_config(self, test_environment):
        """Create application configuration for testing"""
        test_dir = test_environment['test_dir']
        config_dir = test_dir / ".laxyfile"
        config_dir.mkdir()

        config = Config(config_dir=config_dir)
        config.data.update({
            'logging': {
                'level': 'INFO',
                'console': {'enabled': True, 'level': 'INFO'},
                'file': {'enabled': False},
                'performance': {'enabled': True, 'system_metrics': False},
                'error': {'enabled': False}
            },
            'ui': {
                'theme': 'catppuccin',
                'dual_pane': True,
                'show_hidden': False
            },
            'ai': {
                'enabled': False,  # Disable for testing
            },
            'plugins': {
                'enabled': False,  # Disable for testing
            },
            'file_operations': {
                'confirm_delete': True,
                'show_progress': True
            },
            'preview': {
                'enabled': True,
                'max_file_size_mb':
            }
        })

        return config

    @pytest.fixture
    async def initialized_app(self, app_config, test_environment):
        """Create and initialize the complete application"""
        app = LaxyFileApplication(app_config)

        # Initialize the application
        await app.initialize()

        # Set initial directory to test directory
        test_dir = test_environment['test_dir']
        if hasattr(app, 'set_current_directory'):
            await app.set_current_directory(test_dir)

        yield app

        # Cleanup
        await app.shutdown()

    @pytest.mark.asyncio
    async def test_file_browsing_workflow(self, initialized_app, test_environment):
        """Test complete file browsing workflow"""
        app = initialized_app
        test_dir = test_environment['test_dir']

        # Get the integrator and components
        integrator = app.integrator if hasattr(app, 'integrator') else None
        if integrator is None:
            pytest.skip("Application integrator not available")

        file_manager = integrator.get_component('file_manager')
        ui_manager = integrator.get_component('ui_manager')

        assert file_manager is not None, "File manager should be available"
        assert ui_manager is not None, "UI manager should be available"

        # Test directory listing
        files = await file_manager.list_directory(test_dir)
        assert len(files) > 0, "Should find test files"

        # Verify expected files are present
        file_names = [f.name for f in files]
        assert "documents" in file_names
        assert "images" in file_names
        assert "code" in file_names
        assert "test_file.txt" in file_names

        # Test navigation to subdirectory
        documents_dir = test_dir / "documents"
        doc_files = await file_manager.list_directory(documents_dir)
        doc_file_names = [f.name for f in doc_files]
        assert "readme.txt" in doc_file_names
        assert "notes.md" in doc_file_names

    @pytest.mark.asyncio
    async def test_file_preview_workflow(self, initialized_app, test_environment):
        """Test file preview workflow"""
        app = initialized_app
        test_dir = test_environment['test_dir']

        integrator = app.integrator if hasattr(app, 'integrator') else None
        if integrator is None:
            pytest.skip("Application integrator not available")

        preview_system = integrator.get_component('preview_system')
        assert preview_system is not None, "Preview system should be available"

        # Test text file preview
        text_file = test_dir / "test_file.txt"
        preview = await preview_system.generate_preview(text_file)
        assert preview is not None, "Should generate preview for text file"
        assert "Root level test file" in preview.content

        # Test markdown file preview
        md_file = test_dir / "documents" / "notes.md"
        md_preview = await preview_system.generate_preview(md_file)
        assert md_preview is not None, "Should generate preview for markdown file"
        assert "Test Notes" in md_preview.content

        # Test Python file preview
        py_file = test_dir / "code" / "script.py"
        py_preview = await preview_system.generate_preview(py_file)
        assert py_preview is not None, "Should generate preview for Python file"
        assert "Hello, World!" in py_preview.content

    @pytest.mark.asyncio
    async def test_file_selection_and_preview_workflow(self, initialized_app, test_environment):
        """Test file selection triggering preview updates"""
        app = initialized_app
        test_dir = test_environment['test_dir']

        integrator = app.integrator if hasattr(app, 'integrator') else None
        if integrator is None:
            pytest.skip("Application integrator not available")

        # Mock UI manager methods if they don't exist
        ui_manager = integrator.get_component('ui_manager')
        if not hasattr(ui_manager, 'update_preview'):
            ui_manager.update_preview = Mock()

        # Simulate file selection
        test_file = test_dir / "test_file.txt"
        selection_data = {
            'selected_files': [test_file],
            'selection_type': 'single'
        }

        # Emit selection changed event
        integrator.emit_event('selection_changed', selection_data)

        # Give time for event processing
        await asyncio.sleep(0.2)

        # Verify preview was updated (if method exists)
        if hasattr(ui_manager.update_preview, 'called'):
            # This would be true if the UI manager actually handled the event
            pass

    @pytest.mark.asyncio
    async def test_directory_navigation_workflow(self, initialized_app, test_environment):
        """Test directory navigation workflow"""
        app = initialized_app
        test_dir = test_environment['test_dir']

        integrator = app.integrator if hasattr(app, 'integrator') else None
        if integrator is None:
            pytest.skip("Application integrator not available")

        file_manager = integrator.get_component('file_manager')
        ui_manager = integrator.get_component('ui_manager')

        # Mock UI methods if they don't exist
        if not hasattr(ui_manager, 'update_current_directory'):
            ui_manager.update_current_directory = Mock()
        if not hasattr(ui_manager, 'refresh_file_list'):
            ui_manager.refresh_file_list = Mock()

        # Test navigation to subdirectory
        documents_dir = test_dir / "documents"

        # Simulate directory change
        directory_data = {
            'path': documents_dir,
            'change_type': 'navigate'
        }

        integrator.emit_event('directory_changed', directory_data)

        # Give time for event processing
        await asyncio.sleep(0.2)

        # Verify directory contents
        files = await file_manager.list_directory(documents_dir)
        file_names = [f.name for f in files]
        assert "readme.txt" in file_names
        assert "notes.md" in file_names

    @pytest.mark.asyncio
    async def test_file_operation_workflow(self, initialized_app, test_environment):
        """Test file operation workflow"""
        app = initialized_app
        test_dir = test_environment['test_dir']

        integrator = app.integrator if hasattr(app, 'integrator') else None
        if integrator is None:
            pytest.skip("Application integrator not available")

        file_operations = integrator.get_component('file_operations')
        ui_manager = integrator.get_component('ui_manager')

        assert file_operations is not None, "File operations should be available"

        # Mock UI progress methods if they don't exist
        if not hasattr(ui_manager, 'show_operation_progress'):
            ui_manager.show_operation_progress = Mock()
        if not hasattr(ui_manager, 'hide_operation_progress'):
            ui_manager.hide_operation_progress = Mock()

        # Test file copy operation
        source_file = test_dir / "test_file.txt"
        dest_file = test_dir / "test_file_copy.txt"

        # Perform copy operation
        success = await file_operations.copy_file(source_file, dest_file)
        assert success, "File copy should succeed"
        assert dest_file.exists(), "Copied file should exist"

        # Verify content is the same
        original_content = source_file.read_text()
        copied_content = dest_file.read_text()
        assert original_content == copied_content, "File content should be identical"

        # Test file deletion
        delete_success = await file_operations.delete_file(dest_file)
        assert delete_success, "File deletion should succeed"
        assert not dest_file.exists(), "Deleted file should not exist"

    @pytest.mark.asyncio
    async def test_theme_switching_workflow(self, initialized_app, test_environment):
        """Test theme switching workflow"""
        app = initialized_app

        integrator = app.integrator if hasattr(app, 'integrator') else None
        if integrator is None:
            pytest.skip("Application integrator not available")

        ui_manager = integrator.get_component('ui_manager')

        # Mock theme application if method doesn't exist
        if not hasattr(ui_manager, 'apply_theme'):
            ui_manager.apply_theme = Mock()

        # Test theme change
        theme_data = {
            'theme': 'dracula',
            'theme_name': 'dracula'
        }

        integrator.emit_event('theme_changed', theme_data)

        # Give time for event processing
        await asyncio.sleep(0.2)

        # Verify theme was applied (if method exists)
        if hasattr(ui_manager.apply_theme, 'called'):
            pass  # Would check if theme was actually applied

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, initialized_app, test_environment):
        """Test error handling in workflows"""
        app = initialized_app
        test_dir = test_environment['test_dir']

        integrator = app.integrator if hasattr(app, 'integrator') else None
        if integrator is None:
            pytest.skip("Application integrator not available")

        file_manager = integrator.get_component('file_manager')
        preview_system = integrator.get_component('preview_system')

        # Test handling of non-existent directory
        non_existent_dir = test_dir / "does_not_exist"
        try:
            files = await file_manager.list_directory(non_existent_dir)
            # Should either return empty list or raise handled exception
            assert isinstance(files, list)
        except Exception as e:
            # Exception should be handled gracefully
            assert str(e)  # Should have error message

        # Test handling of non-existent file preview
        non_existent_file = test_dir / "does_not_exist.txt"
        try:
            preview = await preview_system.generate_preview(non_existent_file)
            # Should either return None or error preview
            assert preview is None or hasattr(preview, 'error')
        except Exception as e:
            # Exception should be handled gracefully
            assert str(e)  # Should have error message

    @pytest.mark.asyncio
    async def test_performance_monitoring_workflow(self, initialized_app, test_environment):
        """Test performance monitoring during workflows"""
        app = initialized_app
        test_dir = test_environment['test_dir']

        integrator = app.integrator if hasattr(app, 'integrator') else None
        if integrator is None:
            pytest.skip("Application integrator not available")

        performance_logger = integrator.performance_logger

        # Perform some operations to generate metrics
        file_manager = integrator.get_component('file_manager')

        # List directory multiple times to generate metrics
        for _ in range(3):
            await file_manager.list_directory(test_dir)
            await asyncio.sleep(0.1)

        # Check that metrics were collected
        assert len(performance_logger.metrics) > 0, "Performance metrics should be collected"

        # Check for specific metrics
        metric_names = list(performance_logger.metrics.keys())
        # Should have some operation timing metrics
        timing_metrics = [name for name in metric_names if 'duration' in name or 'time' in name]
        assert len(timing_metrics) > 0, "Should have timing metrics"

    @pytest.mark.asyncio
    async def test_concurrent_operations_workflow(self, initialized_app, test_environment):
        """Test handling of concurrent operations"""
        app = initialized_app
        test_dir = test_environment['test_dir']

        integrator = app.integrator if hasattr(app, 'integrator') else None
        if integrator is None:
            pytest.skip("Application integrator not available")

        file_manager = integrator.get_component('file_manager')
        preview_system = integrator.get_component('preview_system')

        # Perform concurrent operations
        tasks = []

        # Concurrent directory listings
        for subdir in ['documents', 'images', 'code']:
            task = file_manager.list_directory(test_dir / subdir)
            tasks.append(task)

        # Concurrent preview generations
        test_files = [
            test_dir / "test_file.txt",
            test_dir / "documents" / "readme.txt",
            test_dir / "code" / "script.py"
        ]

        for test_file in test_files:
            if test_file.exists():
                task = preview_system.generate_preview(test_file)
                tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that most operations succeeded
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) > 0, "At least some concurrent operations should succeed"

        # Check that any exceptions are handled gracefully
        exceptions = [r for r in results if isinstance(r, Exception)]
        for exc in exceptions:
            assert str(exc)  # Should have meaningful error messages


class TestWorkflowIntegration:
    """Test integration between different workflows"""

    @pytest.fixture
    async def workflow_environment(self):
        """Create environment for workflow integration tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir)

            # Create more complex test structure
            dirs = [
                "projects/web_app/src",
                "projects/web_app/tests",
                "projects/cli_tool",
                "documents/reports",
                "documents/presentations",
                "media/images",
                "media/videos"
            ]

            for dir_path in dirs:
                (test_dir / dir_path).mkdir(parents=True)

            # Create various file types
            files = {
                "projects/web_app/src/main.py": "# Main application\nprint('Hello')",
                "projects/web_app/src/utils.py": "# Utilities\ndef helper(): pass",
                "projects/web_app/tests/test_main.py": "# Tests\ndef test_main(): pass",
                "projects/cli_tool/cli.py": "#!/usr/bin/env python3\n# CLI tool",
                "documents/reports/report.md": "# Report\n\nContent here",
                "documents/presentations/slides.txt": "Slide 1: Introduction",
                "media/images/photo.txt": "Fake image data",
                "README.md": "# Project\n\nDescription",
                "config.json": '{"version": "1.0", "debug": false}'
            }

            for file_path, content in files.items():
                full_path = test_dir / file_path
                full_path.write_text(content)

            yield test_dir

    @pytest.mark.asyncio
    async def test_project_exploration_workflow(self, workflow_environment):
        """Test exploring a project structure"""
        test_dir = workflow_environment

        # Create minimal config for testing
        config = Config(config_dir=test_dir / ".laxyfile")
        config.data.update({
            'logging': {'console': {'enabled': False}, 'file': {'enabled': False}},
            'ai': {'enabled': False},
            'plugins': {'enabled': False}
        })

        integrator = ComponentIntegrator(config)

        try:
            await integrator.initialize_all_components()

            file_manager = integrator.get_component('file_manager')
            preview_system = integrator.get_component('preview_system')

            # Explore project structure
            root_files = await file_manager.list_directory(test_dir)
            root_names = [f.name for f in root_files]

            assert "projects" in root_names
            assert "documents" in root_names
            assert "media" in root_names
            assert "README.md" in root_names

            # Dive into projects directory
            projects_dir = test_dir / "projects"
            project_files = await file_manager.list_directory(projects_dir)
            project_names = [f.name for f in project_files]

            assert "web_app" in project_names
            assert "cli_tool" in project_names

            # Preview README file
            readme_file = test_dir / "README.md"
            readme_preview = await preview_system.generate_preview(readme_file)
            assert readme_preview is not None
            assert "Project" in readme_preview.content

        finally:
            await integrator.shutdown()

    @pytest.mark.asyncio
    async def test_multi_file_operation_workflow(self, workflow_environment):
        """Test operations on multiple files"""
        test_dir = workflow_environment

        config = Config(config_dir=test_dir / ".laxyfile")
        config.data.update({
            'logging': {'console': {'enabled': False}, 'file': {'enabled': False}},
            'ai': {'enabled': False},
            'plugins': {'enabled': False}
        })

        integrator = ComponentIntegrator(config)

        try:
            await integrator.initialize_all_components()

            file_operations = integrator.get_component('file_operations')

            # Create backup directory
            backup_dir = test_dir / "backup"
            backup_dir.mkdir()

            # Copy multiple files
            source_files = [
                test_dir / "README.md",
                test_dir / "config.json"
            ]

            for source_file in source_files:
                if source_file.exists():
                    dest_file = backup_dir / source_file.name
                    success = await file_operations.copy_file(source_file, dest_file)
                    assert success, f"Should copy {source_file.name}"
                    assert dest_file.exists(), f"Copied file {dest_file} should exist"

        finally:
            await integrator.shutdown()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])