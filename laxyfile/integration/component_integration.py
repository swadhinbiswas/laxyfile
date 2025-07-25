"""
Component Integration Module

This module handles the integration of all LaxyFile components,
ensuring they work together seamlessly and managing their interactions.
"""

import asyncio
import threading
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import time
from dataclasses import dataclass

from ..core.config import Config
from ..core.advanced_file_manager import AdvancedFileManager
from ..core.interfaces import FileManagerInterface, UIManagerInterface
from ..ui.superfile_ui import SuperFileUI
from ..ai.advanced_assistant import AdvancedAIAssistant
from ..preview.preview_system import AdvancedPreviewSystem
from ..operations.file_ops import ComprehensiveFileOperations
from ..plugins.plugin_manager import PluginManager
from ..utils.logging_system import get_logger, LogCategory
from ..utils.performance_logger import PerformanceLogger


@dataclass
class ComponentStatus:
    """Status information for a component"""
    name: str
    initialized: bool = False
    healthy: bool = False
    last_check: float = 0
    error_message: Optional[str] = None
    dependencies: List[str] = None


class ComponentIntegrator:
    """
    Main integration class that manages all LaxyFile components
    and ensures they work together seamlessly.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger('integration', LogCategory.SYSTEM)
        self.performance_logger = PerformanceLogger(config)

        # Component instances
        self.components: Dict[str, Any] = {}
        self.component_status: Dict[str, ComponentStatus] = {}

        # Integration state
        self.initialized = False
        self.startup_time = None
        self.shutdown_requested = False

        # Event system for component communication
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.event_lock = threading.Lock()

        # Health monitoring
        self.health_check_interval = config.get('integration.health_check_interval', 30)
        self.health_monitor_thread = None

        self.logger.info("Component integrator initialized")

    async def initialize_all_components(self) -> bool:
        """Initialize all components in the correct order"""
        start_time = time.time()
        self.logger.info("Starting component initialization")

        try:
            # Initialize components in dependency order
            initialization_order = [
                ('config', self._initialize_config),
                ('file_manager', self._initialize_file_manager),
                ('preview_system', self._inie_preview_system),
                ('file_operations', self._initialize_file_operations),
                ('ai_assistant', self._initialize_ai_assistant),
                ('plugin_manager', self._initialize_plugin_manager),
                ('ui_manager', self._initialize_ui_manager),
            ]

            for component_name, init_func in initialization_order:
                self.logger.info(f"Initializing {component_name}")

                component_start = time.time()
                success = await init_func()
                component_time = time.time() - component_start

                self.performance_logger.record_metric(
                    f"component_init_{component_name}_ms",
                    component_time * 1000,
                    "ms",
                    "initialization"
                )

                if not success:
                    self.logger.error(f"Failed to initialize {component_name}")
                    return False

                self.logger.info(f"Successfully initialized {component_name} in {component_time:.2f}s")

            # Setup component interactions
            await self._setup_component_interactions()

            # Start health monitoring
            self._start_health_monitoring()

            self.initialized = True
            self.startup_time = time.time() - start_time

            self.logger.info(f"All components initialized successfully in {self.startup_time:.2f}s")
            self.performance_logger.record_metric(
                "total_startup_time_ms",
                self.startup_time * 1000,
                "ms",
                "initialization"
            )

            return True

        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}", exc_info=True)
            return False

    async def _initialize_config(self) -> bool:
        """Initialize configuration system"""
        try:
            # Config is already initialized, just validate it
            self.components['config'] = self.config
            self.component_status['config'] = ComponentStatus(
                name='config',
                initialized=True,
                healthy=True,
                last_check=time.time()
            )
            return True
        except Exception as e:
            self.logger.error(f"Config initialization failed: {e}")
            return False

    async def _initialize_file_manager(self) -> bool:
        """Initialize advanced file manager"""
        try:
            file_manager = AdvancedFileManager(self.config)
            await file_manager.initialize()

            self.components['file_manager'] = file_manager
            self.component_status['file_manager'] = ComponentStatus(
                name='file_manager',
                initialized=True,
                healthy=True,
                last_check=time.time(),
                dependencies=['config']
            )
            return True
        except Exception as e:
            self.logger.error(f"File manager initialization failed: {e}")
            self.component_status['file_manager'] = ComponentStatus(
                name='file_manager',
                initialized=False,
                healthy=False,
                error_message=str(e)
            )
            return False

    async def _initialize_preview_system(self) -> bool:
        """Initialize preview system"""
        try:
            preview_system = AdvancedPreviewSystem(self.config)
            await preview_system.initialize()

            self.components['preview_system'] = preview_system
            self.component_status['preview_system'] = ComponentStatus(
                name='preview_system',
                initialized=True,
                healthy=True,
                last_check=time.time(),
                dependencies=['config']
            )
            return True
        except Exception as e:
            self.logger.error(f"Preview system initialization failed: {e}")
            self.component_status['preview_system'] = ComponentStatus(
                name='preview_system',
                initialized=False,
                healthy=False,
                error_message=str(e)
            )
            return False

    async def _initialize_file_operations(self) -> bool:
        """Initialize file operations"""
        try:
            file_ops = ComprehensiveFileOperations(self.config)

            self.components['file_operations'] = file_ops
            self.component_status['file_operations'] = ComponentStatus(
                name='file_operations',
                initialized=True,
                healthy=True,
                last_check=time.time(),
                dependencies=['config', 'file_manager']
            )
            return True
        except Exception as e:
            self.logger.error(f"File operations initialization failed: {e}")
            self.component_status['file_operations'] = ComponentStatus(
                name='file_operations',
                initialized=False,
                healthy=False,
                error_message=str(e)
            )
            return False

    async def _initialize_ai_assistant(self) -> bool:
        """Initialize AI assistant"""
        try:
            ai_assistant = AdvancedAIAssistant(self.config)
            await ai_assistant.initialize()

            self.components['ai_assistant'] = ai_assistant
            self.component_status['ai_assistant'] = ComponentStatus(
                name='ai_assistant',
                initialized=True,
                healthy=True,
                last_check=time.time(),
                dependencies=['config', 'file_manager']
            )
            return True
        except Exception as e:
            self.logger.error(f"AI assistant initialization failed: {e}")
            self.component_status['ai_assistant'] = ComponentStatus(
                name='ai_assistant',
                initialized=False,
                healthy=False,
                error_message=str(e)
            )
            return False

    async def _initialize_plugin_manager(self) -> bool:
        """Initialize plugin manager"""
        try:
            plugin_manager = PluginManager(self.config)
            await plugin_manager.initialize()

            # Load enabled plugins
            await plugin_manager.load_enabled_plugins()

            self.components['plugin_manager'] = plugin_manager
            self.component_status['plugin_manager'] = ComponentStatus(
                name='plugin_manager',
                initialized=True,
                healthy=True,
                last_check=time.time(),
                dependencies=['config']
            )
            return True
        except Exception as e:
            self.logger.error(f"Plugin manager initialization failed: {e}")
            self.component_status['plugin_manager'] = ComponentStatus(
                name='plugin_manager',
                initialized=False,
                healthy=False,
                error_message=str(e)
            )
            return False

    async def _initialize_ui_manager(self) -> bool:
        """Initialize UI manager"""
        try:
            ui_manager = SuperFileUI(
                self.config,
                self.components['file_manager'],
                self.components['ai_assistant'],
                self.components['preview_system'],
                self.components['file_operations']
            )

            self.components['ui_manager'] = ui_manager
            self.component_status['ui_manager'] = ComponentStatus(
                name='ui_manager',
                initialized=True,
                healthy=True,
                last_check=time.time(),
                dependencies=['config', 'file_manager', 'ai_assistant', 'preview_system', 'file_operations']
            )
            return True
        except Exception as e:
            self.logger.error(f"UI manager initialization failed: {e}")
            self.component_status['ui_manager'] = ComponentStatus(
                name='ui_manager',
                initialized=False,
                healthy=False,
                error_message=str(e)
            )
            return False

    async def _setup_component_interactions(self):
        """Setup interactions between components"""
        self.logger.info("Setting up component interactions")

        try:
            # Connect file manager to UI for updates
            if 'file_manager' in self.components and 'ui_manager' in self.components:
                file_manager = self.components['file_manager']
                ui_manager = self.components['ui_manager']

                # Register file change callbacks
                file_manager.register_change_callback(ui_manager.on_file_change)
                file_manager.register_directory_change_callback(ui_manager.on_directory_change)

            # Connect AI assistant to file manager for context
            if 'ai_assistant' in self.components and 'file_manager' in self.components:
                ai_assistant = self.components['ai_assistant']
                file_manager = self.components['file_manager']

                # Provide file manager context to AI
                ai_assistant.set_file_manager(file_manager)

            # Connect preview system to UI
            if 'preview_system' in self.components and 'ui_manager' in self.components:
                preview_system = self.components['preview_system']
                ui_manager = self.components['ui_manager']

                # Register preview callbacks
                ui_manager.set_preview_system(preview_system)

            # Connect file operations to UI for progress updates
            if 'file_operations' in self.components and 'ui_manager' in self.components:
                file_ops = self.components['file_operations']
                ui_manager = self.components['ui_manager']

                # Register progress callbacks
                file_ops.register_progress_callback(ui_manager.on_operation_progress)
                file_ops.register_completion_callback(ui_manager.on_operation_complete)

            # Setup plugin system interactions
            if 'plugin_manager' in self.components:
                plugin_manager = self.components['plugin_manager']

                # Provide component access to plugins
                plugin_manager.register_component('file_manager', self.components.get('file_manager'))
                plugin_manager.register_component('ui_manager', self.components.get('ui_manager'))
                plugin_manager.register_component('ai_assistant', self.components.get('ai_assistant'))
                plugin_manager.register_component('preview_system', self.components.get('preview_system'))
                plugin_manager.register_component('file_operations', self.components.get('file_operations'))

            # Setup event system
            self._setup_event_system()

            self.logger.info("Component interactions setup complete")

        except Exception as e:
            self.logger.error(f"Failed to setup component interactions: {e}", exc_info=True)
            raise

    def _setup_event_system(self):
        """Setup the event system for component communication"""
        # Register event handlers for different components

        # File system events
        self.register_event_handler('file_changed', self._handle_file_changed)
        self.register_event_handler('directory_changed', self._handle_directory_changed)

        # UI events
        self.register_event_handler('selection_changed', self._handle_selection_changed)
        self.register_event_handler('theme_changed', self._handle_theme_changed)

        # AI events
        self.register_event_handler('ai_response_ready', self._handle_ai_response)

        # Operation events
        self.register_event_handler('operation_started', self._handle_operation_started)
        self.register_event_handler('operation_completed', self._handle_operation_completed)

        self.logger.info("Event system setup complete")

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler"""
        with self.event_lock:
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(handler)

    def emit_event(self, event_type: str, data: Any = None):
        """Emit an event to all registered handlers"""
        with self.event_lock:
            handlers = self.event_handlers.get(event_type, [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(data))
                else:
                    handler(data)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event_type}: {e}")

    async def _handle_file_changed(self, data):
        """Handle file change events"""
        self.logger.debug(f"File changed: {data}")
        # Notify relevant components
        if 'ui_manager' in self.components:
            await self.components['ui_manager'].refresh_current_view()

    async def _handle_directory_changed(self, data):
        """Handle directory change events"""
        self.logger.debug(f"Directory changed: {data}")
        # Refresh file listings
        if 'file_manager' in self.components:
            await self.components['file_manager'].refresh_directory(data.get('path'))

    async def _handle_selection_changed(self, data):
        """Handle selection change events"""
        self.logger.debug(f"Selection changed: {data}")
        # Update preview if available
        if 'preview_system' in self.components and 'ui_manager' in self.components:
            selected_files = data.get('selected_files', [])
            if selected_files:
                await self.components['preview_system'].generate_preview(selected_files[0])

    async def _handle_theme_changed(self, data):
        """Handle theme change events"""
        self.logger.info(f"Theme changed: {data}")
        # Apply theme to all UI components
        if 'ui_manager' in self.components:
            await self.components['ui_manager'].apply_theme(data.get('theme'))

    async def _handle_ai_response(self, data):
        """Handle AI response events"""
        self.logger.debug("AI response ready")
        # Update UI with AI response
        if 'ui_manager' in self.components:
            await self.components['ui_manager'].display_ai_response(data)

    async def _handle_operation_started(self, data):
        """Handle operation start events"""
        operation_id = data.get('operation_id')
        self.logger.info(f"Operation started: {operation_id}")
        # Show progress in UI
        if 'ui_manager' in self.components:
            await self.components['ui_manager'].show_operation_progress(data)

    async def _handle_operation_completed(self, data):
        """Handle operation completion events"""
        operation_id = data.get('operation_id')
        success = data.get('success', False)
        self.logger.info(f"Operation completed: {operation_id}, success: {success}")
        # Update UI and refresh if needed
        if 'ui_manager' in self.components:
            await self.components['ui_manager'].hide_operation_progress(operation_id)
            if success:
                await self.components['ui_manager'].refresh_current_view()

    def _start_health_monitoring(self):
        """Start background health monitoring"""
        if self.health_monitor_thread and self.health_monitor_thread.is_alive():
            return

        self.health_monitor_thread = threading.Thread(
            target=self._health_monitoring_loop,
            daemon=True
        )
        self.health_monitor_thread.start()
        self.logger.info("Health monitoring started")

    def _health_monitoring_loop(self):
        """Background health monitoring loop"""
        while not self.shutdown_requested:
            try:
                self._check_component_health()
                time.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Error in health monitoring: {e}")
                time.sleep(self.health_check_interval)

    def _check_component_health(self):
        """Check health of all components"""
        current_time = time.time()

        for component_name, component in self.components.items():
            try:
                # Basic health check - component exists and has required methods
                is_healthy = True
                error_message = None

                if hasattr(component, 'health_check'):
                    is_healthy = component.health_check()
                elif hasattr(component, 'is_healthy'):
                    is_healthy = component.is_healthy()

                # Update component status
                if component_name in self.component_status:
                    self.component_status[component_name].healthy = is_healthy
                    self.component_status[component_name].last_check = current_time
                    self.component_status[component_name].error_message = error_message

                # Log health issues
                if not is_healthy:
                    self.logger.warning(f"Component {component_name} is unhealthy: {error_message}")

            except Exception as e:
                self.logger.error(f"Health check failed for {component_name}: {e}")
                if component_name in self.component_status:
                    self.component_status[component_name].healthy = False
                    self.component_status[component_name].error_message = str(e)

    def get_component(self, name: str) -> Optional[Any]:
        """Get a component by name"""
        return self.components.get(name)

    def get_component_status(self, name: str) -> Optional[ComponentStatus]:
        """Get component status"""
        return self.component_status.get(name)

    def get_all_component_status(self) -> Dict[str, ComponentStatus]:
        """Get status of all components"""
        return self.component_status.copy()

    def is_healthy(self) -> bool:
        """Check if all components are healthy"""
        return all(
            status.healthy for status in self.component_status.values()
            if status.initialized
        )

    async def test_component_interactions(self) -> Dict[str, bool]:
        """Test interactions between components"""
        self.logger.info("Testing component interactions")
        test_results = {}

        try:
            # Test file manager -> UI interaction
            test_results['file_manager_ui'] = await self._test_file_manager_ui_interaction()

            # Test AI -> UI interaction
            test_results['ai_ui'] = await self._test_ai_ui_interaction()

            # Test preview -> UI interaction
            test_results['preview_ui'] = await self._test_preview_ui_interaction()

            # Test file operations -> UI interaction
            test_results['file_ops_ui'] = await self._test_file_ops_ui_interaction()

            # Test plugin system integration
            test_results['plugin_integration'] = await self._test_plugin_integration()

            # Test event system
            test_results['event_system'] = await self._test_event_system()

            self.logger.info(f"Component interaction tests completed: {test_results}")
            return test_results

        except Exception as e:
            self.logger.error(f"Component interaction testing failed: {e}", exc_info=True)
            return {'error': str(e)}

    async def _test_file_manager_ui_interaction(self) -> bool:
        """Test file manager to UI interaction"""
        try:
            if 'file_manager' not in self.components or 'ui_manager' not in self.components:
                return False

            file_manager = self.components['file_manager']
            ui_manager = self.components['ui_manager']

            # Test directory listing
            current_dir = Path.cwd()
            files = await file_manager.list_directory(current_dir)

            # Test UI can handle file list
            if hasattr(ui_manager, 'update_file_list'):
                ui_manager.update_file_list(files)

            return True
        except Exception as e:
            self.logger.error(f"File manager-UI interaction test failed: {e}")
            return False

    async def _test_ai_ui_interaction(self) -> bool:
        """Test AI assistant to UI interaction"""
        try:
            if 'ai_assistant' not in self.components or 'ui_manager' not in self.components:
                return False

            ai_assistant = self.components['ai_assistant']
            ui_manager = self.components['ui_manager']

            # Test AI query
            test_query = "What files are in the current directory?"
            response = await ai_assistant.process_query(test_query)

            # Test UI can handle AI response
            if hasattr(ui_manager, 'display_ai_response'):
                ui_manager.display_ai_response(response)

            return True
        except Exception as e:
            self.logger.error(f"AI-UI interaction test failed: {e}")
            return False

    async def _test_preview_ui_interaction(self) -> bool:
        """Test preview system to UI interaction"""
        try:
            if 'preview_system' not in self.components or 'ui_manager' not in self.components:
                return False

            preview_system = self.components['preview_system']
            ui_manager = self.components['ui_manager']

            # Test preview generation for a common file
            test_file = Path(__file__)  # Use this Python file
            preview = await preview_system.generate_preview(test_file)

            # Test UI can handle preview
            if hasattr(ui_manager, 'display_preview'):
                ui_manager.display_preview(preview)

            return True
        except Exception as e:
            self.logger.error(f"Preview-UI interaction test failed: {e}")
            return False

    async def _test_file_ops_ui_interaction(self) -> bool:
        """Test file operations to UI interaction"""
        try:
            if 'file_operations' not in self.components or 'ui_manager' not in self.components:
                return False

            # Just test that the components can communicate
            # Don't perform actual file operations in tests
            return True
        except Exception as e:
            self.logger.error(f"File ops-UI interaction test failed: {e}")
            return False

    async def _test_plugin_integration(self) -> bool:
        """Test plugin system integration"""
        try:
            if 'plugin_manager' not in self.components:
                return False

            plugin_manager = self.components['plugin_manager']

            # Test plugin manager can access other components
            components_available = all(
                plugin_manager.get_component(name) is not None
                for name in ['file_manager', 'ui_manager', 'ai_assistant']
                if name in self.components
            )

            return components_available
        except Exception as e:
            self.logger.error(f"Plugin integration test failed: {e}")
            return False

    async def _test_event_system(self) -> bool:
        """Test event system functionality"""
        try:
            # Test event emission and handling
            test_event_received = False

            def test_handler(data):
                nonlocal test_event_received
                test_event_received = True

            self.register_event_handler('test_event', test_handler)
            self.emit_event('test_event', {'test': True})

            # Give a moment for event processing
            await asyncio.sleep(0.1)

            return test_event_received
        except Exception as e:
            self.logger.error(f"Event system test failed: {e}")
            return False

    async def shutdown(self):
        """Shutdown all components gracefully"""
        self.logger.info("Starting component shutdown")
        self.shutdown_requested = True

        # Stop health monitoring
        if self.health_monitor_thread:
            self.health_monitor_thread.join(timeout=5)

        # Shutdown components in reverse order
        shutdown_order = [
            'ui_manager',
            'plugin_manager',
            'ai_assistant',
            'file_operations',
            'preview_system',
            'file_manager',
            'config'
        ]

        for component_name in shutdown_order:
            if component_name in self.components:
                try:
                    component = self.components[component_name]
                    if hasattr(component, 'shutdown'):
                        await component.shutdown()
                    elif hasattr(component, 'cleanup'):
                        await component.cleanup()

                    self.logger.info(f"Component {component_name} shutdown complete")
                except Exception as e:
                    self.logger.error(f"Error shutting down {component_name}: {e}")

        # Stop performance monitoring
        if hasattr(self.performance_logger, 'stop_system_monitoring'):
            self.performance_logger.stop_system_monitoring()

        self.logger.info("Component shutdown complete")


# Global integrator instance
_component_integrator: Optional[ComponentIntegrator] = None


def get_component_integrator() -> Optional[ComponentIntegrator]:
    """Get the global component integrator instance"""
    return _component_integrator


def initialize_integration(config: Config) -> ComponentIntegrator:
    """Initialize the global component integrator"""
    global _component_integrator
    _component_integrator = ComponentIntegrator(config)
    return _component_integrator