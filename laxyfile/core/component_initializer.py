"""
ComponentInitializer - Manages proper initialization order and dependency resolution

This module ensures that components are initialized in the correct order with proper
dependency management and error handling.
"""

import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .file_manager_service import FileManagerService
from .config import Config
from ..utils.logger import Logger


@dataclass
class InitializationState:
    """Tracks initialization status and component health"""
    file_manager_ready: bool = False
    ui_components_ready: bool = False
    initialization_errors: List[str] = field(default_factory=list)
    last_initialization_attempt: Optional[datetime] = None
    component_status: Dict[str, bool] = field(default_factory=dict)
    initialization_time: float = 0.0


@dataclass
class ComponentHealth:
    """Tracks individual component health status"""
    component_name: str
    is_healthy: bool
    last_check: datetime
    error_message: Optional[str] = None
    dependency_status: Dict[str, bool] = field(default_factory=dict)
    initialization_time: float = 0.0


class ComponentInitializer:
    """Manages proper initialization order and dependency resolution"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = Logger()
        self.state = InitializationState()
        self.component_health: Dict[str, ComponentHealth] = {}
        self.initialization_callbacks: Dict[str, List[Callable]] = {}

        # Component dependencies mapping
        self.dependencies = {
            'file_manager': [],
            'theme_manager': ['file_manager'],
            'panel_manager': ['file_manager', 'theme_manager'],
            'media_viewer': ['file_manager'],
            'ai_assistant': ['file_manager'],
            'performance_optimizer': [],
            'animation_optimizer': [],
            'hotkey_manager': [],
            'ui_components': ['file_manager', 'theme_manager', 'panel_manager']
        }

    def initialize_core_services(self) -> bool:
        """Initialize core services (file manager and essential services)

        Returns:
            bool: True if core services initialized successfully
        """
        start_time = time.time()
        self.state.last_initialization_attempt = datetime.now()

        try:
            self.logger.info("Starting core services initialization")

            # Initialize file manager service first
            if not self._initialize_file_manager():
                return False

            # Initiiguration-dependent services
            if not self._initialize_config_services():
                return False

            self.state.file_manager_ready = True
            self.state.initialization_time = time.time() - start_time

            self.logger.info(f"Core services initialized successfully in {self.state.initialization_time:.3f}s")
            return True

        except Exception as e:
            error_msg = f"Core services initialization failed: {e}"
            self.logger.error(error_msg)
            self.state.initialization_errors.append(error_msg)
            return False

    def initialize_ui_components(self) -> bool:
        """Initialize UI components after core services are ready

        Returns:
            bool: True if UI components initialized successfully
        """
        if not self.state.file_manager_ready:
            error_msg = "Cannot initialize UI components: core services not ready"
            self.logger.error(error_msg)
            self.state.initialization_errors.append(error_msg)
            return False

        start_time = time.time()

        try:
            self.logger.info("Starting UI components initialization")

            # Initialize theme manager
            if not self._initialize_theme_manager():
                return False

            # Initialize panel manager
            if not self._initialize_panel_manager():
                return False

            # Initialize media viewer
            if not self._initialize_media_viewer():
                return False

            # Initialize other UI components
            if not self._initialize_other_ui_components():
                return False

            self.state.ui_components_ready = True
            ui_init_time = time.time() - start_time

            self.logger.info(f"UI components initialized successfully in {ui_init_time:.3f}s")
            return True

        except Exception as e:
            error_msg = f"UI components initialization failed: {e}"
            self.logger.error(error_msg)
            self.state.initialization_errors.append(error_msg)
            return False

    def verify_dependencies(self) -> List[str]:
        """Check all components have required dependencies

        Returns:
            List of missing dependencies or empty list if all satisfied
        """
        missing_dependencies = []

        try:
            # Check file manager service
            file_manager_service = FileManagerService.get_instance()
            if not file_manager_service.is_healthy():
                missing_dependencies.append("file_manager_service")

            # Check each component's dependencies
            for component, deps in self.dependencies.items():
                component_health = self.component_health.get(component)
                if component_health and not component_health.is_healthy:
                    continue  # Skip unhealthy components

                for dep in deps:
                    if not self._check_dependency_available(dep):
                        missing_dependencies.append(f"{component} -> {dep}")

            return missing_dependencies

        except Exception as e:
            self.logger.error(f"Error verifying dependencies: {e}")
            return [f"dependency_check_error: {e}"]

    def get_initialization_status(self) -> Dict[str, Any]:
        """Get detailed initialization status

        Returns:
            Dict containing initialization status information
        """
        return {
            'core_services_ready': self.state.file_manager_ready,
            'ui_components_ready': self.state.ui_components_ready,
            'initialization_errors': self.state.initialization_errors,
            'last_attempt': self.state.last_initialization_attempt,
            'initialization_time': self.state.initialization_time,
            'component_status': self.state.component_status,
            'missing_dependencies': self.verify_dependencies(),
            'component_health': {
                name: {
                    'healthy': health.is_healthy,
                    'last_check': health.last_check,
                    'error': health.error_message,
                    'dependencies': health.dependency_status
                }
                for name, health in self.component_health.items()
            }
        }

    def register_initialization_callback(self, component: str, callback: Callable) -> None:
        """Register a callback to be called when a component is initialized

        Args:
            component: Component name
            callback: Callback function to call
        """
        if component not in self.initialization_callbacks:
            self.initialization_callbacks[component] = []
        self.initialization_callbacks[component].append(callback)

    def _initialize_file_manager(self) -> bool:
        """Initialize the file manager service"""
        try:
            start_time = time.time()

            file_manager_service = FileManagerService.get_instance()

            # Determine if we should use advanced file manager
            use_advanced = self.config.get('performance.use_advanced_file_manager', False)

            success = file_manager_service.initialize(self.config, use_advanced)

            init_time = time.time() - start_time

            # Update component health
            self.component_health['file_manager'] = ComponentHealth(
                component_name='file_manager',
                is_healthy=success and file_manager_service.is_healthy(),
                last_check=datetime.now(),
                error_message=None if success else "Initialization failed",
                initialization_time=init_time
            )

            self.state.component_status['file_manager'] = success

            if success:
                self.logger.info(f"File manager initialized in {init_time:.3f}s")
                self._call_initialization_callbacks('file_manager')
            else:
                self.logger.error("File manager initialization failed")

            return success

        except Exception as e:
            error_msg = f"File manager initialization error: {e}"
            self.logger.error(error_msg)
            self.state.initialization_errors.append(error_msg)

            self.component_health['file_manager'] = ComponentHealth(
                component_name='file_manager',
                is_healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            )

            return False

    def _initialize_config_services(self) -> bool:
        """Initialize configuration-dependent services"""
        try:
            # Initialize performance optimizer if enabled
            if self.config.get('performance.enable_optimizer', True):
                if not self._initialize_performance_optimizer():
                    self.logger.warning("Performance optimizer initialization failed")

            # Initialize other core services as needed
            return True

        except Exception as e:
            self.logger.error(f"Config services initialization error: {e}")
            return False

    def _initialize_theme_manager(self) -> bool:
        """Initialize theme manager"""
        try:
            start_time = time.time()

            # Import here to avoid circular imports
            from ..ui.theme import ThemeManager

            theme_manager = ThemeManager(self.config)
            init_time = time.time() - start_time

            self.component_health['theme_manager'] = ComponentHealth(
                component_name='theme_manager',
                is_healthy=True,
                last_check=datetime.now(),
                initialization_time=init_time,
                dependency_status={'file_manager': True}
            )

            self.state.component_status['theme_manager'] = True
            self.logger.info(f"Theme manager initialized in {init_time:.3f}s")
            self._call_initialization_callbacks('theme_manager')

            return True

        except Exception as e:
            error_msg = f"Theme manager initialization error: {e}"
            self.logger.error(error_msg)
            self.state.initialization_errors.append(error_msg)

            self.component_health['theme_manager'] = ComponentHealth(
                component_name='theme_manager',
                is_healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            )

            return False

    def _initialize_panel_manager(self) -> bool:
        """Initialize panel manager"""
        try:
            start_time = time.time()

            # Import here to avoid circular imports
            from ..ui.panels import PanelManager
            from ..ui.theme import ThemeManager

            # Get theme manager (should be initialized by now)
            theme_manager = ThemeManager(self.config)
            panel_manager = PanelManager(theme_manager)

            init_time = time.time() - start_time

            self.component_health['panel_manager'] = ComponentHealth(
                component_name='panel_manager',
                is_healthy=True,
                last_check=datetime.now(),
                initialization_time=init_time,
                dependency_status={
                    'file_manager': True,
                    'theme_manager': True
                }
            )

            self.state.component_status['panel_manager'] = True
            self.logger.info(f"Panel manager initialized in {init_time:.3f}s")
            self._call_initialization_callbacks('panel_manager')

            return True

        except Exception as e:
            error_msg = f"Panel manager initialization error: {e}"
            self.logger.error(error_msg)
            self.state.initialization_errors.append(error_msg)

            self.component_health['panel_manager'] = ComponentHealth(
                component_name='panel_manager',
                is_healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            )

            return False

    def _initialize_media_viewer(self) -> bool:
        """Initialize media viewer"""
        try:
            start_time = time.time()

            # Import here to avoid circular imports
            from ..ui.image_viewer import MediaViewer
            from rich.console import Console

            console = Console()
            media_viewer = MediaViewer(console)

            init_time = time.time() - start_time

            self.component_health['media_viewer'] = ComponentHealth(
                component_name='media_viewer',
                is_healthy=True,
                last_check=datetime.now(),
                initialization_time=init_time,
                dependency_status={'file_manager': True}
            )

            self.state.component_status['media_viewer'] = True
            self.logger.info(f"Media viewer initialized in {init_time:.3f}s")
            self._call_initialization_callbacks('media_viewer')

            return True

        except Exception as e:
            error_msg = f"Media viewer initialization error: {e}"
            self.logger.error(error_msg)
            self.state.initialization_errors.append(error_msg)

            self.component_health['media_viewer'] = ComponentHealth(
                component_name='media_viewer',
                is_healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            )

            return False

    def _initialize_performance_optimizer(self) -> bool:
        """Initialize performance optimizer"""
        try:
            start_time = time.time()

            # Import here to avoid circular imports
            from ..core.performance_optimizer import PerformanceOptimizer, PerformanceConfig

            perf_config = PerformanceConfig(
                max_concurrent_operations=self.config.get('performance.max_concurrent_operations', 10),
                chunk_size=self.config.get('performance.chunk_size', 100),
                memory_threshold_mb=self.config.get('performance.memory_threshold_mb', 500),
                lazy_loading_threshold=self.config.get('performance.lazy_loading_threshold', 1000),
                background_processing=self.config.get('performance.background_processing', True),
                use_threading=self.config.get('performance.use_threading', True),
                max_worker_threads=self.config.get('performance.max_worker_threads', 4)
            )

            performance_optimizer = PerformanceOptimizer(perf_config)
            init_time = time.time() - start_time

            self.component_health['performance_optimizer'] = ComponentHealth(
                component_name='performance_optimizer',
                is_healthy=True,
                last_check=datetime.now(),
                initialization_time=init_time
            )

            self.state.component_status['performance_optimizer'] = True
            self.logger.info(f"Performance optimizer initialized in {init_time:.3f}s")
            self._call_initialization_callbacks('performance_optimizer')

            return True

        except Exception as e:
            error_msg = f"Performance optimizer initialization error: {e}"
            self.logger.error(error_msg)
            self.state.initialization_errors.append(error_msg)

            self.component_health['performance_optimizer'] = ComponentHealth(
                component_name='performance_optimizer',
                is_healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            )

            return False

    def _initialize_other_ui_components(self) -> bool:
        """Initialize other UI components"""
        try:
            # Initialize hotkey manager
            if not self._initialize_hotkey_manager():
                self.logger.warning("Hotkey manager initialization failed")

            # Initialize AI assistant if enabled
            if self.config.get('ai.enable_assistant', False):
                if not self._initialize_ai_assistant():
                    self.logger.warning("AI assistant initialization failed")

            return True

        except Exception as e:
            self.logger.error(f"Other UI components initialization error: {e}")
            return False

    def _initialize_hotkey_manager(self) -> bool:
        """Initialize hotkey manager"""
        try:
            start_time = time.time()

            # Import here to avoid circular imports
            from ..utils.hotkeys import HotkeyManager

            hotkey_manager = HotkeyManager()
            init_time = time.time() - start_time

            self.component_health['hotkey_manager'] = ComponentHealth(
                component_name='hotkey_manager',
                is_healthy=True,
                last_check=datetime.now(),
                initialization_time=init_time
            )

            self.state.component_status['hotkey_manager'] = True
            self.logger.info(f"Hotkey manager initialized in {init_time:.3f}s")
            self._call_initialization_callbacks('hotkey_manager')

            return True

        except Exception as e:
            error_msg = f"Hotkey manager initialization error: {e}"
            self.logger.error(error_msg)

            self.component_health['hotkey_manager'] = ComponentHealth(
                component_name='hotkey_manager',
                is_healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            )

            return False

    def _initialize_ai_assistant(self) -> bool:
        """Initialize AI assistant"""
        try:
            start_time = time.time()

            # Import here to avoid circular imports
            from ..ai.assistant import AdvancedAIAssistant

            ai_assistant = AdvancedAIAssistant(self.config)
            init_time = time.time() - start_time

            self.component_health['ai_assistant'] = ComponentHealth(
                component_name='ai_assistant',
                is_healthy=True,
                last_check=datetime.now(),
                initialization_time=init_time,
                dependency_status={'file_manager': True}
            )

            self.state.component_status['ai_assistant'] = True
            self.logger.info(f"AI assistant initialized in {init_time:.3f}s")
            self._call_initialization_callbacks('ai_assistant')

            return True

        except Exception as e:
            error_msg = f"AI assistant initialization error: {e}"
            self.logger.error(error_msg)

            self.component_health['ai_assistant'] = ComponentHealth(
                component_name='ai_assistant',
                is_healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            )

            return False

    def _check_dependency_available(self, dependency: str) -> bool:
        """Check if a dependency is available and healthy"""
        if dependency == 'file_manager':
            file_manager_service = FileManagerService.get_instance()
            return file_manager_service.is_healthy()

        component_health = self.component_health.get(dependency)
        return component_health is not None and component_health.is_healthy

    def _call_initialization_callbacks(self, component: str) -> None:
        """Call initialization callbacks for a component"""
        callbacks = self.initialization_callbacks.get(component, [])
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in initialization callback for {component}: {e}")

    def health_check(self) -> bool:
        """Perform a comprehensive health check of all components

        Returns:
            bool: True if all components are healthy
        """
        try:
            all_healthy = True

            # Check file manager service
            file_manager_service = FileManagerService.get_instance()
            if not file_manager_service.is_healthy():
                all_healthy = False
                self.logger.warning("File manager service is not healthy")

            # Check each component
            for component_name, health in self.component_health.items():
                # Update health status
                try:
                    # Perform component-specific health checks here
                    health.last_check = datetime.now()
                    # For now, assume components remain healthy once initialized
                    # In a real implementation, you'd add specific health checks

                except Exception as e:
                    health.is_healthy = False
                    health.error_message = str(e)
                    all_healthy = False
                    self.logger.warning(f"Component {component_name} health check failed: {e}")

            return all_healthy

        except Exception as e:
            self.logger.error(f"Health check error: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up resources and reset state"""
        try:
            self.logger.info("Cleaning up component initializer")

            # Clear callbacks
            self.initialization_callbacks.clear()

            # Reset state
            self.state = InitializationState()
            self.component_health.clear()

        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")