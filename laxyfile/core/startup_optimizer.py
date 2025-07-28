"""
Startup Optimizer

Optimizes application startup time through lazy loading, preloading strategies,
and initialization prioritization for LaxyFile.
"""

import asyncio
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future

from ..utils.logger import Logger


@dataclass
class StartupConfig:
    """Configuration for startup optimization"""
    enable_lazy_loading: bool = True
    enable_preloading: bool = True
    enable_background_init: bool = True
    max_startup_threads: int = 4
    startup_timeout_seconds: int = 30
    critical_components: List[str] = field(default_factory=lambda: [
        'config', 'logger', 'theme_manager'
    ])
    preload_components: List[str] = field(default_factory=lambda: [
        'file_manager', 'ui_manager'
    ])
    background_components: List[str] = field(default_factory=lambda: [
        'ai_assistant', 'preview_system', 'plugin_manager'
    ])


@dataclass
class ComponentInfo:
    """Information about a component"""
    name: str
    priority: int = 0
    is_critical: bool = False
    is_preloadable: bool = False
    is_background: bool = False
    init_function: Optional[Callable] = None
    dependencies: List[str] = field(default_factory=list)
    init_time: Optional[float] = None
    status: str = "not_started"  # not_started, initializing, ready, failed


class StartupOptimizer:
    """Main startup optimization system"""

    def __init__(self, config: StartupConfig):
        self.config = config
        self.logger = Logger()

        # Component management
        self.components: Dict[str, ComponentInfo] = {}
        self.initialized_components: Set[str] = set()
        self.failed_components: Set[str] = set()

        # Threading
        self.thread_pool = ThreadPoolExecutor(max_workers=config.max_startup_threads)
        self.background_tasks: Dict[str, Future] = {}

        # Timing and metrics
        self.startup_start_time = None
        self.startup_metrics = {
            'total_time': 0.0,
            'critical_time': 0.0,
            'preload_time': 0.0,
            'background_time': 0.0,
            'component_times': {},
            'failed_components': []
        }

    def register_component(self, name: str, init_function: Callable,
                          dependencies: List[str] = None, priority: int = 0) -> None:
        """Register a component for startup optimization"""
        dependencies = dependencies or []

        component = ComponentInfo(
            name=name,
            priority=priority,
            is_critical=name in self.config.critical_components,
            is_preloadable=name in self.config.preload_components,
            is_background=name in self.config.background_components,
            init_function=init_function,
            dependencies=dependencies
        )

        self.components[name] = component
        self.logger.debug(f"Registered component: {name} (critical={component.is_critical})")

    async def optimize_startup(self) -> Dict[str, Any]:
        """Perform optimized startup sequence"""
        self.startup_start_time = time.time()
        self.logger.info("Starting optimized startup sequence")

        try:
            # Phase 1: Initialize critical components synchronously
            critical_start = time.time()
            await self._initialize_critical_components()
            self.startup_metrics['critical_time'] = time.time() - critical_start

            # Phase 2: Preload important components
            if self.config.enable_preloading:
                preload_start = time.time()
                await self._preload_components()
                self.startup_metrics['preload_time'] = time.time() - preload_start

            # Phase 3: Start background initialization
            if self.config.enable_background_init:
                background_start = time.time()
                self._start_background_initialization()
                self.startup_metrics['background_time'] = time.time() - background_start

            # Calculate total startup time
            self.startup_metrics['total_time'] = time.time() - self.startup_start_time

            self.logger.info(f"Startup optimization complete in {self.startup_metrics['total_time']:.3f}s")
            return self.startup_metrics

        except Exception as e:
            self.logger.error(f"Error during startup optimization: {e}")
            raise

    async def _initialize_critical_components(self) -> None:
        """Initialize critical components that must be ready before UI starts"""
        critical_components = [
            comp for comp in self.components.values()
            if comp.is_critical
        ]

        # Sort by priority and dependencies
        sorted_components = self._sort_components_by_dependencies(critical_components)

        for component in sorted_components:
            try:
                start_time = time.time()
                component.status = "initializing"

                self.logger.debug(f"Initializing critical component: {component.name}")

                if asyncio.iscoroutinefunction(component.init_function):
                    await component.init_function()
                else:
                    component.init_function()

                component.init_time = time.time() - start_time
                component.status = "ready"
                self.initialized_components.add(component.name)

                self.startup_metrics['component_times'][component.name] = component.init_time
                self.logger.debug(f"Critical component {component.name} initialized in {component.init_time:.3f}s")

            except Exception as e:
                component.status = "failed"
                self.failed_components.add(component.name)
                self.startup_metrics['failed_components'].append(component.name)
                self.logger.error(f"Failed to initialize critical component {component.name}: {e}")
                raise  # Critical components must succeed

    async def _preload_components(self) -> None:
        """Preload important components concurrently"""
        preloadable_components = [
            comp for comp in self.components.values()
            if comp.is_preloadable and comp.name not in self.initialized_components
        ]

        if not preloadable_components:
            return

        # Create tasks for concurrent initialization
        tasks = []
        for component in preloadable_components:
            if self._dependencies_satisfied(component):
                task = self._initialize_component_async(component)
                tasks.append(task)

        # Wait for all preload tasks to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log results
            for i, result in enumerate(results):
                component = preloadable_components[i]
                if isinstance(result, Exception):
                    self.logger.warning(f"Preload failed for {component.name}: {result}")
                else:
                    self.logger.debug(f"Preloaded component: {component.name}")

    def _start_background_initialization(self) -> None:
        """Start background initialization of remaining components"""
        background_components = [
            comp for comp in self.components.values()
            if comp.is_background and comp.name not in self.initialized_components
        ]

        for component in background_components:
            if self._dependencies_satisfied(component):
                future = self.thread_pool.submit(self._initialize_component_sync, component)
                self.background_tasks[component.name] = future

    async def _initialize_component_async(self, component: ComponentInfo) -> None:
        """Initialize a component asynchronously"""
        try:
            start_time = time.time()
            component.status = "initializing"

            if asyncio.iscoroutinefunction(component.init_function):
                await component.init_function()
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.thread_pool, component.init_function)

            component.init_time = time.time() - start_time
            component.status = "ready"
            self.initialized_components.add(component.name)
            self.startup_metrics['component_times'][component.name] = component.init_time

        except Exception as e:
            component.status = "failed"
            self.failed_components.add(component.name)
            self.startup_metrics['failed_components'].append(component.name)
            self.logger.error(f"Failed to initialize component {component.name}: {e}")

    def _initialize_component_sync(self, component: ComponentInfo) -> None:
        """Initialize a component synchronously (for background thread)"""
        try:
            start_time = time.time()
            component.status = "initializing"

            if asyncio.iscoroutinefunction(component.init_function):
                # Can't run async function in sync context
                self.logger.warning(f"Cannot run async component {component.name} in background thread")
                return

            component.init_function()

            component.init_time = time.time() - start_time
            component.status = "ready"
            self.initialized_components.add(component.name)
            self.startup_metrics['component_times'][component.name] = component.init_time

            self.logger.debug(f"Background component {component.name} initialized in {component.init_time:.3f}s")

        except Exception as e:
            component.status = "failed"
            self.failed_components.add(component.name)
            self.startup_metrics['failed_components'].append(component.name)
            self.logger.error(f"Failed to initialize background component {component.name}: {e}")

    def _sort_components_by_dependencies(self, components: List[ComponentInfo]) -> List[ComponentInfo]:
        """Sort components by their dependencies using topological sort"""
        # Simple topological sort implementation
        sorted_components = []
        remaining = components.copy()

        while remaining:
            # Find components with no unresolved dependencies
            ready = []
            for comp in remaining:
                if all(dep in self.initialized_components or
                      dep in [c.name for c in sorted_components]
                      for dep in comp.dependencies):
                    ready.append(comp)

            if not ready:
                # Circular dependency or missing dependency
                self.logger.warning("Circular dependency detected, initializing remaining components by priority")
                ready = sorted(remaining, key=lambda c: c.priority, reverse=True)[:1]

            # Sort ready components by priority
            ready.sort(key=lambda c: c.priority, reverse=True)

            # Add to sorted list and remove from remaining
            for comp in ready:
                sorted_components.append(comp)
                remaining.remove(comp)

        return sorted_components

    def _dependencies_satisfied(self, component: ComponentInfo) -> bool:
        """Check if component dependencies are satisfied"""
        return all(dep in self.initialized_components for dep in component.dependencies)

    def is_component_ready(self, component_name: str) -> bool:
        """Check if a component is ready"""
        return component_name in self.initialized_components

    def wait_for_component(self, component_name: str, timeout: float = 10.0) -> bool:
        """Wait for a component to be ready"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.is_component_ready(component_name):
                return True

            # Check if component is being initialized in background
            if component_name in self.background_tasks:
                future = self.background_tasks[component_name]
                try:
                    future.result(timeout=0.1)  # Short timeout
                except:
                    pass  # Continue waiting

            time.sleep(0.1)

        return False

    async def wait_for_component_async(self, component_name: str, timeout: float = 10.0) -> bool:
        """Asynchronously wait for a component to be ready"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.is_component_ready(component_name):
                return True

            await asyncio.sleep(0.1)

        return False

    def get_startup_stats(self) -> Dict[str, Any]:
        """Get comprehensive startup statistics"""
        stats = self.startup_metrics.copy()

        # Add component status information
        stats['component_status'] = {}
        for name, component in self.components.items():
            stats['component_status'][name] = {
                'status': component.status,
                'init_time': component.init_time,
                'is_critical': component.is_critical,
                'is_preloadable': component.is_preloadable,
                'is_background': component.is_background
            }

        # Add summary statistics
        stats['summary'] = {
            'total_components': len(self.components),
            'initialized_components': len(self.initialized_components),
            'failed_components': len(self.failed_components),
            'background_tasks_running': len([
                f for f in self.background_tasks.values() if not f.done()
            ])
        }

        return stats

    def get_component_status(self, component_name: str) -> Optional[str]:
        """Get status of a specific component"""
        component = self.components.get(component_name)
        return component.status if component else None

    def shutdown(self) -> None:
        """Shutdown the startup optimizer"""
        try:
            # Cancel background tasks
            for future in self.background_tasks.values():
                if not future.done():
                    future.cancel()

            # Shutdown thread pool
            self.thread_pool.shutdown(wait=True)

            self.logger.info("StartupOptimizer shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during startup optimizer shutdown: {e}")

    def create_lazy_loader(self, component_name: str, init_function: Callable) -> Callable:
        """Create a lazy loader for a component"""
        def lazy_init(*args, **kwargs):
            if not self.is_component_ready(component_name):
                self.logger.debug(f"Lazy loading component: {component_name}")
                try:
                    if asyncio.iscoroutinefunction(init_function):
                        # Can't run async in sync context, schedule for later
                        self.logger.warning(f"Cannot lazy load async component {component_name} synchronously")
                        return None
                    else:
                        result = init_function(*args, **kwargs)
                        self.initialized_components.add(component_name)
                        return result
                except Exception as e:
                    self.logger.error(f"Lazy loading failed for {component_name}: {e}")
                    return None

            return init_function(*args, **kwargs)

        return lazy_init

    def optimize_import_time(self, module_name: str) -> Callable:
        """Decorator to optimize import time for modules"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                import_time = time.time() - start_time

                if import_time > 0.1:  # Log slow imports
                    self.logger.debug(f"Slow import detected: {module_name} took {import_time:.3f}s")

                return result
            return wrapper
        return decorator

    def preload_common_paths(self, paths: List[Path]) -> None:
        """Preload common file paths in background"""
        def preload_paths():
            for path in paths:
                try:
                    if path.exists():
                        # Just stat the path to warm up filesystem cache
                        path.stat()
                        if path.is_dir():
                            # List first few items
                            list(path.iterdir())[:10]
                except Exception as e:
                    self.logger.debug(f"Error preloading path {path}: {e}")

        if self.config.enable_preloading:
            self.thread_pool.submit(preload_paths)

    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.shutdown()
        except:
            pass