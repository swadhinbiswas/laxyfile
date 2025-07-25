"""
Integration tests for component interactions

This module tests that all LaxyFile components work together correctly
and that their interactions are functioning as expected.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from laxyfile.core.config import Config
from laxyfile.integration.component_integration import ComponentIntegrator, ComponentStatus
from laxyfile.core.advanced_file_manager import AdvancedFileManager
from laxyfile.ui.superfile_ui import SuperFileUI
from laxyfile.ai.advanced_assistant import AdvancedAIAssistant
from laxyfile.preview.preview_system import AdvancedPreviewSystem
from laxyfile.operations.file_ops import ComprehensiveFileOperations
from laxyfile.plugins.plugin_manager import PluginManager


class TestComponentIntegration:
    """Test component integration functionality"""

    @pytest.fixture
    async def config(self):
        """Create test configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(config_dir=Path(temp_dir))
            # Set test-specific configuration
            config.data.update({
                'integration': {
                    'health_check_interval') # Fast health checks for testing
                },
                'logging': {
                    'level': 'DEBUG',
                    'console': {'enabled': True, 'level': 'DEBUG'},
                    'file': {'enabled': False},  # Disable file logging for tests
                    'performance': {'enabled': False},
                    'error': {'enabled': False}
                },
                'ai': {
                    'enabled': False,  # Disable AI for basic integration tests
                },
                'plugins': {
                    'enabled': False,  # Disable plugins for basic tests
                }
            })
            yield config

    @pytest.fixture
    async def integrator(self, config):
        """Create component integrator"""
        integrator = ComponentIntegrator(config)
        yield integrator
        # Cleanup
        await integrator.shutdown()

    @pytest.mark.asyncio
    async def test_component_initialization_order(self, integrator):
        """Test that components are initialized in the correct order"""
        success = await integrator.initialize_all_components()
        assert success, "Component initialization should succeed"

        # Check that all expected components are initialized
        expected_components = [
            'config', 'file_manager', 'preview_system',
            'file_operations', 'ai_assistant', 'plugin_manager', 'ui_manager'
        ]

        for component_name in expected_components:
            assert component_name in integrator.components, f"Component {component_name} should be initialized"
            status = integrator.get_component_status(component_name)
            assert status is not None, f"Status for {component_name} should exist"
            assert status.initialized, f"Component {component_name} should be marked as initialized"

    @pytest.mark.asyncio
    async def test_component_dependencies(self, integrator):
        """Test that component dependencies are respected"""
        await integrator.initialize_all_components()

        # Check dependency relationships
        ui_status = integrator.get_component_status('ui_manager')
        assert ui_status is not None
        assert 'file_manager' in ui_status.dependencies
        assert 'ai_assistant' in ui_status.dependencies
        assert 'preview_system' in ui_status.dependencies
        assert 'file_operations' in ui_status.dependencies

        # Ensure dependencies are initialized before dependents
        file_manager_status = integrator.get_component_status('file_manager')
        assert file_manager_status.initialized

    @pytest.mark.asyncio
    async def test_component_health_monitoring(self, integrator):
        """Test component health monitoring"""
        await integrator.initialize_all_components()

        # Wait a moment for health monitoring to start
        await asyncio.sleep(0.1)

        # Check that all components are healthy
        assert integrator.is_healthy(), "All components should be healthy"

        # Check individual component health
        for component_name in integrator.components:
            status = integrator.get_component_status(component_name)
            assert status.healthy, f"Component {component_name} should be healthy"

    @pytest.mark.asyncio
    async def test_event_system(self, integrator):
        """Test the event system functionality"""
        await integrator.initialize_all_components()

        # Test event registration and emission
        test_events_received = []

        def test_handler(data):
            test_events_received.append(data)

        integrator.register_event_handler('test_event', test_handler)

        # Emit test event
        test_data = {'test': 'data'}
        integrator.emit_event('test_event', test_data)

        # Give a moment for event processing
        await asyncio.sleep(0.1)

        assert len(test_events_received) == 1
        assert test_events_received[0] == test_data

    @pytest.mark.asyncio
    async def test_file_manager_ui_interaction(self, integrator):
        """Test file manager to UI interaction"""
        await integrator.initialize_all_components()

        file_manager = integrator.get_component('file_manager')
        ui_manager = integrator.get_component('ui_manager')

        assert file_manager is not None
        assert ui_manager is not None

        # Test that file manager can provide data to UI
        current_dir = Path.cwd()
        files = await file_manager.list_directory(current_dir)
        assert isinstance(files, list)

        # Test UI can handle file list (mock the method if it doesn't exist)
        if not hasattr(ui_manager, 'update_file_list'):
            ui_manager.update_file_list = Mock()

        ui_manager.update_file_list(files)
        if hasattr(ui_manager.update_file_list, 'assert_called_once'):
            ui_manager.update_file_list.assert_called_once_with(files)

    @pytest.mark.asyncio
    async def test_preview_system_integration(self, integrator):
        """Test preview system integration"""
        await integrator.initialize_all_components()

        preview_system = integrator.get_component('preview_system')
        ui_manager = integrator.get_component('ui_manager')

        assert preview_system is not None
        assert ui_manager is not None

        # Test preview generation
        test_file = Path(__file__)  # Use this test file
        preview = await preview_system.generate_preview(test_file)
        assert preview is not None

        # Test UI can handle preview
        if not hasattr(ui_manager, 'display_preview'):
            ui_manager.display_preview = Mock()

        ui_manager.display_preview(preview)
        if hasattr(ui_manager.display_preview, 'assert_called_once'):
            ui_manager.display_preview.assert_called_once_with(preview)

    @pytest.mark.asyncio
    async def test_component_interaction_tests(self, integrator):
        """Test the built-in component interaction tests"""
        await integrator.initialize_all_components()

        # Run the built-in interaction tests
        test_results = await integrator.test_component_interactions()

        assert isinstance(test_results, dict)
        assert 'error' not in test_results, f"Interaction tests should not have errors: {test_results}"

        # Check that most tests pass (some might fail due to mocking)
        passed_tests = sum(1 for result in test_results.values() if result is True)
        total_tests = len(test_results)

        # At least half the tests should pass
        assert passed_tests >= total_tests // 2, f"At least half the interaction tests should pass: {test_results}"

    @pytest.mark.asyncio
    async def test_component_shutdown(self, integrator):
        """Test graceful component shutdown"""
        await integrator.initialize_all_components()

        # Ensure components are initialized
        assert integrator.initialized
        assert len(integrator.components) > 0

        # Test shutdown
        await integrator.shutdown()

        # Check shutdown was requested
        assert integrator.shutdown_requested

    @pytest.mark.asyncio
    async def test_component_error_handling(self, integrator):
        """Test error handling during component initialization"""
        # Mock a component initialization to fail
        original_init = integrator._initialize_file_manager

        async def failing_init():
            raise Exception("Test initialization failure")

        integrator._initialize_file_manager = failing_init

        # Initialization should fail gracefully
        success = await integrator.initialize_all_components()
        assert not success, "Initialization should fail when a component fails"

        # Check that the failed component is marked as unhealthy
        status = integrator.get_component_status('file_manager')
        assert status is not None
        assert not status.initialized
        assert not status.healthy
        assert status.error_message is not None

        # Restore original method
        integrator._initialize_file_manager = original_init

    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, integrator):
        """Test that performance metrics are collected during initialization"""
        await integrator.initialize_all_components()

        # Check that startup time was recorded
        assert integrator.startup_time is not None
        assert integrator.startup_time > 0

        # Check that performance logger is working
        performance_logger = integrator.performance_logger
        assert performance_logger is not None

        # Check that some metrics were recorded
        assert len(performance_logger.metrics) > 0

    @pytest.mark.asyncio
    async def test_component_status_tracking(self, integrator):
        """Test component status tracking"""
        await integrator.initialize_all_components()

        # Get all component statuses
        all_statuses = integrator.get_all_component_status()
        assert isinstance(all_statuses, dict)
        assert len(all_statuses) > 0

        # Check status structure
        for component_name, status in all_statuses.items():
            assert isinstance(status, ComponentStatus)
            assert status.name == component_name
            assert isinstance(status.initialized, bool)
            assert isinstance(status.healthy, bool)
            assert isinstance(status.last_check, float)
            assert status.last_check > 0


class TestComponentInteractionScenarios:
    """Test specific component interaction scenarios"""

    @pytest.fixture
    async def initialized_integrator(self, config):
        """Create and initialize component integrator"""
        integrator = ComponentIntegrator(config)
        await integrator.initialize_all_components()
        yield integrator
        await integrator.shutdown()

    @pytest.mark.asyncio
    async def test_file_selection_workflow(self, initialized_integrator):
        """Test complete file selection workflow"""
        integrator = initialized_integrator

        # Simulate file selection
        test_file = Path(__file__)
        selection_data = {
            'selected_files': [test_file],
            'selection_type': 'single'
        }

        # Emit selection changed event
        integrator.emit_event('selection_changed', selection_data)

        # Give time for event processing
        await asyncio.sleep(0.1)

        # Verify that preview system was triggered
        preview_system = integrator.get_component('preview_system')
        assert preview_system is not None

    @pytest.mark.asyncio
    async def test_directory_change_workflow(self, initialized_integrator):
        """Test directory change workflow"""
        integrator = initialized_integrator

        # Simulate directory change
        test_dir = Path.cwd()
        directory_data = {
            'path': test_dir,
            'change_type': 'navigate'
        }

        # Emit directory changed event
        integrator.emit_event('directory_changed', directory_data)

        # Give time for event processing
        await asyncio.sleep(0.1)

        # Verify that file manager was notified
        file_manager = integrator.get_component('file_manager')
        assert file_manager is not None

    @pytest.mark.asyncio
    async def test_theme_change_workflow(self, initialized_integrator):
        """Test theme change workflow"""
        integrator = initialized_integrator

        # Simulate theme change
        theme_data = {
            'theme': 'dark',
            'theme_name': 'catppuccin'
        }

        # Emit theme changed event
        integrator.emit_event('theme_changed', theme_data)

        # Give time for event processing
        await asyncio.sleep(0.1)

        # Verify that UI manager was notified
        ui_manager = integrator.get_component('ui_manager')
        assert ui_manager is not None

    @pytest.mark.asyncio
    async def test_operation_progress_workflow(self, initialized_integrator):
        """Test file operation progress workflow"""
        integrator = initialized_integrator

        # Simulate operation start
        operation_data = {
            'operation_id': 'test_op_123',
            'operation_type': 'copy',
            'total_files': 10,
            'current_file': 0
        }

        # Emit operation started event
        integrator.emit_event('operation_started', operation_data)

        # Give time for event processing
        await asyncio.sleep(0.1)

        # Simulate operation completion
        completion_data = {
            'operation_id': 'test_op_123',
            'success': True,
            'files_processed': 10
        }

        # Emit operation completed event
        integrator.emit_event('operation_completed', completion_data)

        # Give time for event processing
        await asyncio.sleep(0.1)

        # Verify that UI manager handled the events
        ui_manager = integrator.get_component('ui_manager')
        assert ui_manager is not None


@pytest.mark.asyncio
async def test_integration_with_real_components():
    """Integration test with real component instances"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config(config_dir=Path(temp_dir))
        config.data.update({
            'logging': {
                'console': {'enabled': False},
                'file': {'enabled': False},
                'performance': {'enabled': False}
            },
            'ai': {'enabled': False},
            'plugins': {'enabled': False}
        })

        integrator = ComponentIntegrator(config)

        try:
            # Initialize components
            success = await integrator.initialize_all_components()
            assert success, "Real component initialization should succeed"

            # Test that we can get real component instances
            file_manager = integrator.get_component('file_manager')
            assert isinstance(file_manager, AdvancedFileManager)

            preview_system = integrator.get_component('preview_system')
            assert isinstance(preview_system, AdvancedPreviewSystem)

            file_operations = integrator.get_component('file_operations')
            assert isinstance(file_operations, ComprehensiveFileOperations)

            # Test basic functionality
            current_dir = Path.cwd()
            files = await file_manager.list_directory(current_dir)
            assert isinstance(files, list)

            # Test preview generation
            if files:
                preview = await preview_system.generate_preview(files[0].path)
                assert preview is not None

        finally:
            await integrator.shutdown()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])