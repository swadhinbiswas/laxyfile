"""
Plugin Integration System

This module provides integration between the plugin system and the main
LaxyFile application, handling plugin lifecycle and API injection.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from .plugin_manager import PluginManager
from .plugin_api import PluginAPI, APIVersion
from .plugin_loader import PluginLoader
from ..core.config import Config
from ..utils.logger import Logger


@dataclass
class PluginIntegrationConfig:
    """Configuration for plugin integration"""
    enabled: bool = True
    auto_load: bool = True
    auto_enable: bool = True
    plugin_dirs: Optional[List[Path]] = None
    api_version: APIVersion = APIVersion.V2_0
    max_load_time: float = 30.0
    enable_examples: bool = False

    def __post_init__(self):
        if self.plugin_dirs is None:
            self.plugin_dirs = [
                Path.cwd() / "plugins",
                Path.home() / ".laxyfile" / "plugins"
            ]


class PluginIntegration:
    """Main plugin integration system"""

    def __init__(self, config: Config, integration_config: Optional[PluginIntegrationConfig] = None):
        self.config = config
        self.integration_config = integration_config or PluginIntegrationConfig()
        self.logger = Logger()

        # Core components (will be injected)
        self.file_manager = None
        self.theme_manager = None
        self.keyboard_handler = None
        self.preview_system = None
        self.ai_assistant = None

        # Plugin system components
        self.api = PluginAPI(self.integration_config.api_version)
        self.plugin_manager = PluginManager(self.integration_config.plugin_dirs, self.api)
        self.plugin_loader = PluginLoader(self.plugin_manager)

        # Integration state
        self.is_initialized = False
        self.startup_results: List[Any] = []

        # Setup API references
        self._setup_api_references()

    def _setup_api_references(self):
        """Setup API references to core components"""
        # These will be set when the main application initializes
        self.api.file_manager = self.file_manager
        self.api.theme_manager = self.theme_manager
        self.api.keyboard_handler = self.keyboard_handler
        self.api.preview_system = self.preview_system
        self.api.ai_assistant = self.ai_assistant

    def inject_core_components(self, **components):
        """Inject core LaxyFile components into the plugin system"""
        for name, component in components.items():
            if hasattr(self.api, name):
                setattr(self.api, name, component)
                setattr(self, name, component)
                self.logger.info(f"Injected {name} into plugin system")

    async def initialize(self) -> bool:
        """Initialize the plugin system"""
        try:
            if not self.integration_config.enabled:
                self.logger.info("Plugin system disabled by configuration")
                return True

            self.logger.info("Initializing plugin system...")

            # Setup plugin lifecycle hooks
            self._setup_lifecycle_hooks()

            # Load plugins if auto-load is enabled
            if self.integration_config.auto_load:
                self.startup_results = await self.plugin_manager.load_all_plugins()

                # Log results
                successful_loads = [r for r in self.startup_results if r.success]
                failed_loads = [r for r in self.startup_results if not r.success]

                self.logger.info(f"Plugin loading complete: {len(successful_loads)} successful, {len(failed_loads)} failed")

                for result in failed_loads:
                    self.logger.warning(f"Failed to load plugin {result.plugin_id}: {result.message}")

            self.is_initialized = True
            self.logger.info("Plugin system initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing plugin system: {e}")
            return False

    def _setup_lifecycle_hooks(self):
        """Setup plugin lifecycle hooks"""

        async def on_plugin_loaded(plugin_info):
            """Handle plugin loaded event"""
            self.logger.info(f"Plugin loaded: {plugin_info.plugin_id}")

            # Emit application event
            if self.api:
                await self.api.emit_event('plugin_loaded', {
                    'plugin_id': plugin_info.plugin_id,
                    'plugin_info': plugin_info.to_dict()
                })

        async def on_plugin_enabled(plugin_info):
            """Handle plugin enabled event"""
            self.logger.info(f"Plugin enabled: {plugin_info.plugin_id}")

            # Emit application event
            if self.api:
                await self.api.emit_event('plugin_enabled', {
                    'plugin_id': plugin_info.plugin_id,
                    'plugin_info': plugin_info.to_dict()
                })

        async def on_plugin_disabled(plugin_info):
            """Handle plugin disabled event"""
            self.logger.info(f"Plugin disabled: {plugin_info.plugin_id}")

            # Emit application event
            if self.api:
                await self.api.emit_event('plugin_disabled', {
                    'plugin_id': plugin_info.plugin_id,
                    'plugin_info': plugin_info.to_dict()
                })

        async def on_plugin_unloaded(plugin_info):
            """Handle plugin unloaded event"""
            self.logger.info(f"Plugin unloaded: {plugin_info.plugin_id}")

            # Emit application event
            if self.api:
                await self.api.emit_event('plugin_unloaded', {
                    'plugin_id': plugin_info.plugin_id,
                    'plugin_info': plugin_info.to_dict()
                })

        # Register hooks
        self.plugin_manager.add_hook('after_load', on_plugin_loaded)
        self.plugin_manager.add_hook('after_enable', on_plugin_enabled)
        self.plugin_manager.add_hook('after_disable', on_plugin_disabled)
        self.plugin_manager.add_hook('after_unload', on_plugin_unloaded)

    async def install_plugin(self, source: str, **kwargs) -> Dict[str, Any]:
        """Install a plugin from various sources"""
        try:
            result = await self.plugin_loader.install_plugin(source, **kwargs)

            if result.success:
                self.logger.info(f"Plugin installed successfully: {result.plugin_id}")

                # Auto-enable if configured
                if self.integration_config.auto_enable:
                    enable_result = await self.plugin_manager.enable_plugin(result.plugin_id)
                    if enable_result.success:
                        self.logger.info(f"Plugin auto-enabled: {result.plugin_id}")

            return result.to_dict()

        except Exception as e:
            self.logger.error(f"Error installing plugin from {source}: {e}")
            return {
                'success': False,
                'plugin_id': 'unknown',
                'message': f"Installation error: {e}",
                'error': str(e)
            }

    async def uninstall_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Uninstall a plugin"""
        try:
            result = await self.plugin_loader.uninstall_plugin(plugin_id)

            if result.success:
                self.logger.info(f"Plugin uninstalled successfully: {plugin_id}")

            return result.to_dict()

        except Exception as e:
            self.logger.error(f"Error uninstalling plugin {plugin_id}: {e}")
            return {
                'success': False,
                'plugin_id': plugin_id,
                'message': f"Uninstallation error: {e}",
                'error': str(e)
            }

    async def enable_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Enable a plugin"""
        try:
            result = await self.plugin_manager.enable_plugin(plugin_id)
            return result.to_dict()

        except Exception as e:
            self.logger.error(f"Error enabling plugin {plugin_id}: {e}")
            return {
                'success': False,
                'plugin_id': plugin_id,
                'message': f"Enable error: {e}",
                'error': str(e)
            }

    async def disable_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Disable a plugin"""
        try:
            result = await self.plugin_manager.disable_plugin(plugin_id)
            return result.to_dict()

        except Exception as e:
            self.logger.error(f"Error disabling plugin {plugin_id}: {e}")
            return {
                'success': False,
                'plugin_id': plugin_id,
                'message': f"Disable error: {e}",
                'error': str(e)
            }

    async def reload_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Reload a plugin"""
        try:
            result = await self.plugin_manager.reload_plugin(plugin_id)
            return result.to_dict()

        except Exception as e:
            self.logger.error(f"Error reloading plugin {plugin_id}: {e}")
            return {
                'success': False,
                'plugin_id': plugin_id,
                'message': f"Reload error: {e}",
                'error': str(e)
            }

    def get_plugin_status(self) -> Dict[str, Any]:
        """Get status of all plugins"""
        return {
            'initialized': self.is_initialized,
            'enabled': self.integration_config.enabled,
            'api_version': self.api.version.value,
            'plugin_count': len(self.plugin_manager.plugins),
            'enabled_count': len(self.plugin_manager.get_enabled_plugins()),
            'plugins': self.plugin_manager.get_plugin_status(),
            'startup_results': [r.to_dict() for r in self.startup_results]
        }

    def list_available_plugins(self) -> List[Dict[str, Any]]:
        """List available plugins for installation"""
        try:
            packages = self.plugin_loader.list_available_plugins()
            return [pkg.to_dict() for pkg in packages]

        except Exception as e:
            self.logger.error(f"Error listing available plugins: {e}")
            return []

    def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a plugin"""
        plugin_info = self.plugin_manager.get_plugin(plugin_id)
        return plugin_info.to_dict() if plugin_info else None

    def get_plugin_instance(self, plugin_id: str) -> Optional[Any]:
        """Get plugin instance for direct interaction"""
        return self.plugin_manager.get_plugin_instance(plugin_id)

    async def execute_plugin_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute a plugin hook across all plugins"""
        try:
            return await self.api.execute_hook(hook_name, *args, **kwargs)

        except Exception as e:
            self.logger.error(f"Error executing plugin hook {hook_name}: {e}")
            return []

    def register_global_hook(self, hook_name: str, callback, priority: int = 50) -> bool:
        """Register a global hook callback"""
        try:
            return self.api.register_hook_callback(hook_name, callback, priority)

        except Exception as e:
            self.logger.error(f"Error registering global hook {hook_name}: {e}")
            return False

    async def emit_application_event(self, event_name: str, data: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Emit an application event to all plugins"""
        try:
            return await self.api.emit_event(event_name, data or {})

        except Exception as e:
            self.logger.error(f"Error emitting application event {event_name}: {e}")
            return []

    def get_api_capabilities(self) -> Dict[str, Any]:
        """Get available API capabilities"""
        capabilities = self.api.get_capabilities()
        return {name: cap.to_dict() for name, cap in capabilities.items()}

    async def shutdown(self):
        """Shutdown the plugin system"""
        try:
            self.logger.info("Shutting down plugin system...")

            # Emit shutdown event
            await self.emit_application_event('application_shutdown')

            # Shutdown plugin manager
            await self.plugin_manager.shutdown()

            # Cleanup temporary files
            self.plugin_loader.cleanup_temp_files()

            self.is_initialized = False
            self.logger.info("Plugin system shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during plugin system shutdown: {e}")

    def __str__(self) -> str:
        """String representation"""
        return f"PluginIntegration: {len(self.plugin_manager.plugins)} plugins"

    def __repr__(self) -> str:
        """Detailed representation"""
        enabled_count = len(self.plugin_manager.get_enabled_plugins())
        return f"<PluginIntegration: {len(self.plugin_manager.plugins)} loaded, {enabled_count} enabled>"