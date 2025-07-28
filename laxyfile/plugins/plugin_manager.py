"""
Plugin Manager System

This module provides the main plugin management functionality including
loading, enabling, disabling, and managing plugin lifecycle.
"""

import asyncio
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Type
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import yaml

from .base_plugin import BasePlugin, PluginMetadata, PluginConfig, PluginPriority
from .plugin_api import PluginAPI, APIVersion
from ..core.exceptions import PluginError
from ..utils.logger import Logger
from typing import Callable


class PluginStatus(Enum):
    """Plugin status states"""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    ENABLING = "enabling"
    ENABLED = "enabled"
    DISABLING = "disabling"
    DISABLED = "disabled"
    UNLOADING = "unloading"
    ERROR = "error"


@dataclass
class PluginInfo:
    """Plugin information and state"""
    plugin_id: str
    plugin_path: Path
    metadata: PluginMetadata
    config: PluginConfig
    status: PluginStatus = PluginStatus.NOT_LOADED

    # Runtime information
    plugin_instance: Optional[BasePlugin] = None
    load_time: Optional[datetime] = None
    error_message: Optional[str] = None
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'plugin_id': self.plugin_id,
            'plugin_path': str(self.plugin_path),
            'metadata': self.metadata.to_dict(),
            'config': self.config.to_dict(),
            'status': self.status.value,
            'load_time': self.load_time.isoformat() if self.load_time else None,
            'error_message': self.error_message,
            'dependencies': list(self.dependencies),
            'dependents': list(self.dependents)
        }


@dataclass
class LoadResult:
    """Result of plugin loading operation"""
    success: bool
    plugin_id: str
    message: str
    error: Optional[Exception] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'success': self.success,
            'plugin_id': self.plugin_id,
            'message': self.message,
            'error': str(self.error) if self.error else None
        }


class PluginManager:
    """Main plugin management system"""

    def __init__(self, plugin_dirs: List[Path] = None, api: PluginAPI = None):
        self.logger = Logger()

        # Plugin directories to search
        self.plugin_dirs = plugin_dirs or [
            Path.cwd() / "plugins",
            Path.home() / ".laxyfile" / "plugins",
            Path(__file__).parent.parent.parent / "plugins"
        ]

        # Plugin API
        self.api = api or PluginAPI()
        self.api.plugin_manager = self

        # Plugin registry
        self.plugins: Dict[str, PluginInfo] = {}
        self.plugin_classes: Dict[str, Type[BasePlugin]] = {}

        # Dependency tracking
        self.dependency_graph: Dict[str, Set[str]] = {}

        # Event hooks
        self.hooks = {
            'before_load': [],
            'after_load': [],
            'before_enable': [],
            'after_enable': [],
  'before_disable': [],
            'after_disable': [],
            'before_unload': [],
            'after_unload': []
        }

        # Configuration
        self.config_file = Path.home() / ".laxyfile" / "plugins.yaml"
        self.plugin_configs: Dict[str, PluginConfig] = {}

        # Initialize
        self._load_configuration()

        # Component registry for plugin access
        self.registered_components: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize the plugin manager"""
        try:
            self.logger.info("Initializing PluginManager")

            # Discover available plugins
            await self.discover_plugins()

            self.logger.info("PluginManager initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize PluginManager: {e}")
            raise

    def register_component(self, name: str, component: Any) -> None:
        """Register a component for plugin access"""
        self.registered_components[name] = component
        self.logger.debug(f"Registered component: {name}")

    def get_component(self, name: str) -> Optional[Any]:
        """Get a registered component"""
        return self.registered_components.get(name)

    async def load_enabled_plugins(self) -> List[LoadResult]:
        """Load all enabled plugins"""
        results = []

        # Get enabled plugin configurations
        enabled_configs = {
            plugin_id: config for plugin_id, config in self.plugin_configs.items()
            if config.enabled
        }

        # Load enabled plugins
        for plugin_id in enabled_configs:
            # Find plugin path
            plugin_paths = await self.discover_plugins()
            plugin_path = None

            for path in plugin_paths:
                if path.stem == plugin_id or path.parent.name == plugin_id:
                    plugin_path = path
                    break

            if plugin_path:
                result = await self.load_plugin(plugin_path)
                results.append(result)
            else:
                self.logger.warning(f"Plugin path not found for enabled plugin: {plugin_id}")

        return results

    def _load_configuration(self):
        """Load plugin configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = yaml.safe_load(f) or {}

                for plugin_id, plugin_config in config_data.get('plugins', {}).items():
                    self.plugin_configs[plugin_id] = PluginConfig.from_dict(plugin_config)

        except Exception as e:
            self.logger.error(f"Error loading plugin configuration: {e}")

    def _save_configuration(self):
        """Save plugin configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            config_data = {
                'plugins': {
                    plugin_id: config.to_dict()
                    for plugin_id, config in self.plugin_configs.items()
                }
            }

            with open(self.config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)

        except Exception as e:
            self.logger.error(f"Error saving plugin configuration: {e}")

    async def discover_plugins(self) -> List[Path]:
        """Discover available plugins in plugin directories"""
        discovered_plugins = []

        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue

            try:
                # Look for plugin.py files or directories with __init__.py
                for item in plugin_dir.iterdir():
                    if item.is_file() and item.name == "plugin.py":
                        discovered_plugins.append(item)
                    elif item.is_dir():
                        plugin_file = item / "plugin.py"
                        init_file = item / "__init__.py"

                        if plugin_file.exists():
                            discovered_plugins.append(plugin_file)
                        elif init_file.exists():
                            discovered_plugins.append(init_file)

            except Exception as e:
                self.logger.error(f"Error discovering plugins in {plugin_dir}: {e}")

        self.logger.info(f"Discovered {len(discovered_plugins)} plugins")
        return discovered_plugins

    def _load_plugin_metadata(self, plugin_path: Path) -> Optional[PluginMetadata]:
        """Load plugin metadata from plugin file"""
        try:
            # Try to load metadata from plugin.yaml first
            metadata_file = plugin_path.parent / "plugin.yaml"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata_data = yaml.safe_load(f)
                    return PluginMetadata.from_dict(metadata_data)

            # Fallback to loading from Python file
            spec = importlib.util.spec_from_file_location("temp_plugin", plugin_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for plugin class
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, BasePlugin) and
                        attr != BasePlugin):

                        # Create temporary instance to get metadata
                        temp_config = PluginConfig()
                        temp_instance = attr(plugin_path.parent, temp_config)
                        return temp_instance.metadata

            return None

        except Exception as e:
            self.logger.error(f"Error loading plugin metadata from {plugin_path}: {e}")
            return None

    def _load_plugin_class(self, plugin_path: Path) -> Optional[Type[BasePlugin]]:
        """Load plugin class from file"""
        try:
            plugin_id = plugin_path.stem if plugin_path.name == "plugin.py" else plugin_path.parent.name

            spec = importlib.util.spec_from_file_location(f"plugin_{plugin_id}", plugin_path)
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[f"plugin_{plugin_id}"] = module
            spec.loader.exec_module(module)

            # Find plugin class
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, BasePlugin) and
                    attr != BasePlugin):
                    return attr

            return None

        except Exception as e:
            self.logger.error(f"Error loading plugin class from {plugin_path}: {e}")
            return None

    async def load_plugin(self, plugin_path: Path) -> LoadResult:
        """Load a single plugin"""
        plugin_id = plugin_path.stem if plugin_path.name == "plugin.py" else plugin_path.parent.name

        try:
            # Check if already loaded
            if plugin_id in self.plugins:
                return LoadResult(
                    success=False,
                    plugin_id=plugin_id,
                    message="Plugin already loaded"
                )

            # Load metadata
            metadata = self._load_plugin_metadata(plugin_path)
            if not metadata:
                return LoadResult(
                    success=False,
                    plugin_id=plugin_id,
                    message="Failed to load plugin metadata"
                )

            # Load plugin class
            plugin_class = self._load_plugin_class(plugin_path)
            if not plugin_class:
                return LoadResult(
                    success=False,
                    plugin_id=plugin_id,
                    message="Failed to load plugin class"
                )

            # Get or create plugin configuration
            config = self.plugin_configs.get(plugin_id, PluginConfig())

            # Create plugin info
            plugin_info = PluginInfo(
                plugin_id=plugin_id,
                plugin_path=plugin_path,
                metadata=metadata,
                config=config,
                status=PluginStatus.LOADING
            )

            # Execute before_load hooks
            await self._execute_hooks('before_load', plugin_info)

            # Create plugin instance
            plugin_instance = plugin_class(plugin_path.parent, config)
            plugin_instance.api = self.api

            # Load the plugin
            if await plugin_instance.load():
                plugin_info.plugin_instance = plugin_instance
                plugin_info.status = PluginStatus.LOADED
                plugin_info.load_time = datetime.now()

                # Store plugin info
                self.plugins[plugin_id] = plugin_info
                self.plugin_classes[plugin_id] = plugin_class

                # Update configuration
                self.plugin_configs[plugin_id] = config
                self._save_configuration()

                # Execute after_load hooks
                await self._execute_hooks('after_load', plugin_info)

                self.logger.info(f"Successfully loaded plugin: {plugin_id}")
                return LoadResult(
                    success=True,
                    plugin_id=plugin_id,
                    message="Plugin loaded successfully"
                )
            else:
                plugin_info.status = PluginStatus.ERROR
                plugin_info.error_message = "Plugin load method returned False"

                return LoadResult(
                    success=False,
                    plugin_id=plugin_id,
                    message="Plugin load method failed"
                )

        except Exception as e:
            self.logger.error(f"Error loading plugin {plugin_id}: {e}")

            if plugin_id in self.plugins:
                self.plugins[plugin_id].status = PluginStatus.ERROR
                self.plugins[plugin_id].error_message = str(e)

            return LoadResult(
                success=False,
                plugin_id=plugin_id,
                message=f"Error loading plugin: {e}",
                error=e
            )

    async def unload_plugin(self, plugin_id: str) -> LoadResult:
        """Unload a plugin"""
        try:
            if plugin_id not in self.plugins:
                return LoadResult(
                    success=False,
                    plugin_id=plugin_id,
                    message="Plugin not found"
                )

            plugin_info = self.plugins[plugin_id]

            # Check if plugin has dependents
            if plugin_info.dependents:
                return LoadResult(
                    success=False,
                    plugin_id=plugin_id,
                    message=f"Plugin has dependents: {', '.join(plugin_info.dependents)}"
                )

            # Disable if enabled
            if plugin_info.status == PluginStatus.ENABLED:
                disable_result = await self.disable_plugin(plugin_id)
                if not disable_result.success:
                    return disable_result

            plugin_info.status = PluginStatus.UNLOADING

            # Execute before_unload hooks
            await self._execute_hooks('before_unload', plugin_info)

            # Unload the plugin
            if plugin_info.plugin_instance:
                await plugin_info.plugin_instance.unload()

            # Remove from registry
            del self.plugins[plugin_id]
            if plugin_id in self.plugin_classes:
                del self.plugin_classes[plugin_id]

            # Remove from sys.modules
            module_name = f"plugin_{plugin_id}"
            if module_name in sys.modules:
                del sys.modules[module_name]

            # Execute after_unload hooks
            await self._execute_hooks('after_unload', plugin_info)

            self.logger.info(f"Successfully unloaded plugin: {plugin_id}")
            return LoadResult(
                success=True,
                plugin_id=plugin_id,
                message="Plugin unloaded successfully"
            )

        except Exception as e:
            self.logger.error(f"Error unloading plugin {plugin_id}: {e}")
            return LoadResult(
                success=False,
                plugin_id=plugin_id,
                message=f"Error unloading plugin: {e}",
                error=e
            )

    async def enable_plugin(self, plugin_id: str) -> LoadResult:
        """Enable a plugin"""
        try:
            if plugin_id not in self.plugins:
                return LoadResult(
                    success=False,
                    plugin_id=plugin_id,
                    message="Plugin not found"
                )

            plugin_info = self.plugins[plugin_id]

            if plugin_info.status == PluginStatus.ENABLED:
                return LoadResult(
                    success=True,
                    plugin_id=plugin_id,
                    message="Plugin already enabled"
                )

            if plugin_info.status != PluginStatus.LOADED:
                return LoadResult(
                    success=False,
                    plugin_id=plugin_id,
                    message=f"Plugin not in loaded state: {plugin_info.status.value}"
                )

            plugin_info.status = PluginStatus.ENABLING

            # Execute before_enable hooks
            await self._execute_hooks('before_enable', plugin_info)

            # Enable the plugin
            if plugin_info.plugin_instance:
                if await plugin_info.plugin_instance.enable():
                    plugin_info.status = PluginStatus.ENABLED
                    plugin_info.config.enabled = True

                    # Update configuration
                    self.plugin_configs[plugin_id] = plugin_info.config
                    self._save_configuration()

                    # Execute after_enable hooks
                    await self._execute_hooks('after_enable', plugin_info)

                    self.logger.info(f"Successfully enabled plugin: {plugin_id}")
                    return LoadResult(
                        success=True,
                        plugin_id=plugin_id,
                        message="Plugin enabled successfully"
                    )
                else:
                    plugin_info.status = PluginStatus.ERROR
                    plugin_info.error_message = "Plugin enable method returned False"

                    return LoadResult(
                        success=False,
                        plugin_id=plugin_id,
                        message="Plugin enable method failed"
                    )
            else:
                return LoadResult(
                    success=False,
                    plugin_id=plugin_id,
                    message="Plugin instance not available"
                )

        except Exception as e:
            self.logger.error(f"Error enabling plugin {plugin_id}: {e}")

            if plugin_id in self.plugins:
                self.plugins[plugin_id].status = PluginStatus.ERROR
                self.plugins[plugin_id].error_message = str(e)

            return LoadResult(
                success=False,
                plugin_id=plugin_id,
                message=f"Error enabling plugin: {e}",
                error=e
            )

    async def disable_plugin(self, plugin_id: str) -> LoadResult:
        """Disable a plugin"""
        try:
            if plugin_id not in self.plugins:
                return LoadResult(
                    success=False,
                    plugin_id=plugin_id,
                    message="Plugin not found"
                )

            plugin_info = self.plugins[plugin_id]

            if plugin_info.status != PluginStatus.ENABLED:
                return LoadResult(
                    success=True,
                    plugin_id=plugin_id,
                    message="Plugin already disabled"
                )

            plugin_info.status = PluginStatus.DISABLING

            # Execute before_disable hooks
            await self._execute_hooks('before_disable', plugin_info)

            # Disable the plugin
            if plugin_info.plugin_instance:
                if await plugin_info.plugin_instance.disable():
                    plugin_info.status = PluginStatus.LOADED
                    plugin_info.config.enabled = False

                    # Update configuration
                    self.plugin_configs[plugin_id] = plugin_info.config
                    self._save_configuration()

                    # Execute after_disable hooks
                    await self._execute_hooks('after_disable', plugin_info)

                    self.logger.info(f"Successfully disabled plugin: {plugin_id}")
                    return LoadResult(
                        success=True,
                        plugin_id=plugin_id,
                        message="Plugin disabled successfully"
                    )
                else:
                    plugin_info.status = PluginStatus.ERROR
                    plugin_info.error_message = "Plugin disable method returned False"

                    return LoadResult(
                        success=False,
                        plugin_id=plugin_id,
                        message="Plugin disable method failed"
                    )
            else:
                return LoadResult(
                    success=False,
                    plugin_id=plugin_id,
                    message="Plugin instance not available"
                )

        except Exception as e:
            self.logger.error(f"Error disabling plugin {plugin_id}: {e}")

            if plugin_id in self.plugins:
                self.plugins[plugin_id].status = PluginStatus.ERROR
                self.plugins[plugin_id].error_message = str(e)

            return LoadResult(
                success=False,
                plugin_id=plugin_id,
                message=f"Error disabling plugin: {e}",
                error=e
            )

    async def load_all_plugins(self) -> List[LoadResult]:
        """Load all discovered plugins"""
        plugin_paths = await self.discover_plugins()
        results = []

        for plugin_path in plugin_paths:
            result = await self.load_plugin(plugin_path)
            results.append(result)

        # Auto-enable plugins that are configured to be enabled
        for plugin_id, plugin_info in self.plugins.items():
            if plugin_info.config.enabled and plugin_info.status == PluginStatus.LOADED:
                enable_result = await self.enable_plugin(plugin_id)
                results.append(enable_result)

        return results

    async def _execute_hooks(self, hook_name: str, plugin_info: PluginInfo):
        """Execute plugin lifecycle hooks"""
        try:
            for hook_callback in self.hooks.get(hook_name, []):
                if asyncio.iscoroutinefunction(hook_callback):
                    await hook_callback(plugin_info)
                else:
                    hook_callback(plugin_info)

        except Exception as e:
            self.logger.error(f"Error executing {hook_name} hook: {e}")

    def add_hook(self, hook_name: str, callback: Callable):
        """Add a lifecycle hook callback"""
        if hook_name in self.hooks:
            self.hooks[hook_name].append(callback)

    def remove_hook(self, hook_name: str, callback: Callable):
        """Remove a lifecycle hook callback"""
        if hook_name in self.hooks and callback in self.hooks[hook_name]:
            self.hooks[hook_name].remove(callback)

    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get plugin information"""
        return self.plugins.get(plugin_id)

    def get_plugin_instance(self, plugin_id: str) -> Optional[BasePlugin]:
        """Get plugin instance"""
        plugin_info = self.plugins.get(plugin_id)
        return plugin_info.plugin_instance if plugin_info else None

    def list_plugins(self, status_filter: PluginStatus = None) -> List[PluginInfo]:
        """List all plugins, optionally filtered by status"""
        plugins = list(self.plugins.values())

        if status_filter:
            plugins = [p for p in plugins if p.status == status_filter]

        return plugins

    def get_enabled_plugins(self) -> List[PluginInfo]:
        """Get all enabled plugins"""
        return self.list_plugins(PluginStatus.ENABLED)

    def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all plugins"""
        return {
            plugin_id: plugin_info.to_dict()
            for plugin_id, plugin_info in self.plugins.items()
        }

    async def reload_plugin(self, plugin_id: str) -> LoadResult:
        """Reload a plugin"""
        if plugin_id not in self.plugins:
            return LoadResult(
                success=False,
                plugin_id=plugin_id,
                message="Plugin not found"
            )

        plugin_info = self.plugins[plugin_id]
        plugin_path = plugin_info.plugin_path

        # Unload first
        unload_result = await self.unload_plugin(plugin_id)
        if not unload_result.success:
            return unload_result

        # Load again
        return await self.load_plugin(plugin_path)

    def set_plugin_config(self, plugin_id: str, config: PluginConfig):
        """Set plugin configuration"""
        self.plugin_configs[plugin_id] = config

        if plugin_id in self.plugins:
            self.plugins[plugin_id].config = config
            if self.plugins[plugin_id].plugin_instance:
                self.plugins[plugin_id].plugin_instance.config = config

        self._save_configuration()

    def get_plugin_config(self, plugin_id: str) -> Optional[PluginConfig]:
        """Get plugin configuration"""
        return self.plugin_configs.get(plugin_id)

    async def shutdown(self):
        """Shutdown plugin manager and all plugins"""
        self.logger.info("Shutting down plugin manager...")

        # Disable all enabled plugins
        enabled_plugins = self.get_enabled_plugins()
        for plugin_info in enabled_plugins:
            await self.disable_plugin(plugin_info.plugin_id)

        # Unload all loaded plugins
        loaded_plugins = list(self.plugins.keys())
        for plugin_id in loaded_plugins:
            await self.unload_plugin(plugin_id)

        self.logger.info("Plugin manager shutdown complete")

    def __str__(self) -> str:
        """String representation"""
        return f"PluginManager: {len(self.plugins)} plugins loaded"

    def __repr__(self) -> str:
        """Detailed representation"""
        enabled_count = len(self.get_enabled_plugins())
        return f"<PluginManager: {len(self.plugins)} loaded, {enabled_count} enabled>"