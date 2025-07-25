"""
Plugin Base Classes and Interfaces

This module defines the base classes and interfaces that all plugins must implement,
along with the plugin API and hook system.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import inspect

from ..core.exceptions import PluginError
from ..utils.logger import Logger


class PluginHookType(Enum):
    """Types of plugin hooks"""
    FILE_OPERATION = "file_operation"
    UI_EVENT = "ui_event"
    COMMAND = "command"
    PREVIEW = "preview"
    THEME = "theme"
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    CUSTOM = "custom"


@dataclass
class PluginHook:
    """Represents a plugin hook"""
    name: str
    hook_type: PluginHookType
    description: str
    callback: Callable
    priority: int = 0
    enabled: bool = True

    def __post_init__(self):
        # Validate callback signature
        if not callable(self.callback):
            raise PluginError(f"Hook callback must be callable: {self.name}")


class PluginAPI:
    """API interface provided to plugins"""

    def __init__(self, app_context: Any):
        self.app_context = app_context
        self.logger = Logger()

        # Core APIs
        self.file_manager = getattr(app_context, 'file_manager', None)
        self.ui_manager = getattr(app_context, 'ui_manager', None)
        self.theme_manager = getattr(app_context, 'theme_manager', None)
        self.config_manager = getattr(app_context, 'config_manager', None)
        self.keyboard_handler = getattr(app_context, 'keyboard_handler', None)

        # Plugin-specific storage
        self._plugin_storage: Dict[str, Dict[str, Any]] = {}

    def get_file_manager(self):
        """Get file manager instance"""
        return self.file_manager

    def get_ui_manager(self):
        """Get UI manager instance"""
        return self.ui_manager

    def get_theme_manager(self):
        """Get theme manager instance"""
        return self.theme_manager

    def get_config_manager(self):
        """Get configuration manager instance"""
        return self.config_manager

    def get_keyboard_handler(self):
        """Get keyboard handler instance"""
        return self.keyboard_handler

    def log_info(self, message: str, plugin_id: str = None):
        """Log info message"""
        prefix = f"[{plugin_id}] " if plugin_id else ""
        self.logger.info(f"{prefix}{message}")

    def log_warning(self, message: str, plugin_id: str = None):
        """Log warning message"""
        prefix = f"[{plugin_id}] " if plugin_id else ""
        self.logger.warning(f"{prefix}{message}")

    def log_error(self, message: str, plugin_id: str = None):
        """Log error message"""
        prefix = f"[{plugin_id}] " if plugin_id else ""
        self.logger.error(f"{prefix}{message}")

    def get_plugin_storage(self, plugin_id: str) -> Dict[str, Any]:
        """Get plugin-specific storage"""
        if plugin_id not in self._plugin_storage:
            self._plugin_storage[plugin_id] = {}
        return self._plugin_storage[plugin_id]

    def set_plugin_data(self, plugin_id: str, key: str, value: Any):
        """Set plugin data"""
        storage = self.get_plugin_storage(plugin_id)
        storage[key] = value

    def get_plugin_data(self, plugin_id: str, key: str, default: Any = None) -> Any:
        """Get plugin data"""
        storage = self.get_plugin_storage(plugin_id)
        return storage.get(key, default)

    def register_command(self, plugin_id: str, command_name: str,
                        handler: Callable, description: str = ""):
        """Register a command handler"""
        if self.keyboard_handler:
            full_command_name = f"{plugin_id}.{command_name}"
            self.keyboard_handler.command_processor.register_command(
                full_command_name, handler, description
            )

    def unregister_command(self, plugin_id: str, command_name: str):
        """Unregister a command handler"""
        if self.keyboard_handler:
            full_command_name = f"{plugin_id}.{command_name}"
            self.keyboard_handler.command_processor.unregister_command(full_command_name)

    def add_hotkey_binding(self, plugin_id: str, key_combination: str,
                          command: str, description: str = ""):
        """Add hotkey binding"""
        if self.keyboard_handler:
            from ..utils.hotkeys import HotkeyBinding, KeyCombination, InputMode

            binding = HotkeyBinding(
                key_combination=KeyCombination.from_string(key_combination),
                command=f"{plugin_id}.{command}",
                description=description,
                category=f"plugin_{plugin_id}"
            )

            self.keyboard_handler.add_binding(binding)

    def show_notification(self, message: str, notification_type: str = "info"):
        """Show notification to user"""
        if self.ui_manager and hasattr(self.ui_manager, 'show_notification'):
            self.ui_manager.show_notification(message, notification_type)
        else:
            self.log_info(f"Notification: {message}")

    def get_selected_files(self) -> List[str]:
        """Get currently selected files"""
        if self.file_manager and hasattr(self.file_manager, 'get_selected_files'):
            return self.file_manager.get_selected_files()
        return []

    def get_current_directory(self) -> str:
        """Get current directory"""
        if self.file_manager and hasattr(self.file_manager, 'get_current_directory'):
            return self.file_manager.get_current_directory()
        return ""

    def refresh_view(self):
        """Refresh the current view"""
        if self.ui_manager and hasattr(self.ui_manager, 'refresh_view'):
            self.ui_manager.refresh_view()


class BasePlugin(ABC):
    """Base class for all plugins"""

    def __init__(self, plugin_id: str, api: PluginAPI):
        self.plugin_id = plugin_id
        self.api = api
        self.logger = Logger()

        # Plugin metadata
        self.name = "Unknown Plugin"
        self.version = "1.0.0"
        self.author = "Unknown"
        self.description = "No description provided"
        self.dependencies: List[str] = []

        # Plugin state
        self.enabled = False
        self.loaded_at: Optional[datetime] = None
        self.hooks: List[PluginHook] = []

        # Configuration
    self.config: Dict[str, Any] = {}

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        pass

    @abstractmethod
    async def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        return {
            'id': self.plugin_id,
            'name': self.name,
            'version': self.version,
            'author': self.author,
            'description': self.description,
            'dependencies': self.dependencies,
            'enabled': self.enabled,
            'loaded_at': self.loaded_at.isoformat() if self.loaded_at else None,
            'hooks_count': len(self.hooks)
        }

    def register_hook(self, name: str, hook_type: PluginHookType,
                     callback: Callable, description: str = "", priority: int = 0):
        """Register a plugin hook"""
        hook = PluginHook(
            name=f"{self.plugin_id}.{name}",
            hook_type=hook_type,
            description=description,
            callback=callback,
            priority=priority
        )

        self.hooks.append(hook)
        self.api.log_info(f"Registered hook: {hook.name}", self.plugin_id)

    def unregister_hook(self, name: str):
        """Unregister a plugin hook"""
        full_name = f"{self.plugin_id}.{name}"
        self.hooks = [hook for hook in self.hooks if hook.name != full_name]
        self.api.log_info(f"Unregistered hook: {full_name}", self.plugin_id)

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value

    def log_info(self, message: str):
        """Log info message"""
        self.api.log_info(message, self.plugin_id)

    def log_warning(self, message: str):
        """Log warning message"""
        self.api.log_warning(message, self.plugin_id)

    def log_error(self, message: str):
        """Log error message"""
        self.api.log_error(message, self.plugin_id)

    def store_data(self, key: str, value: Any):
        """Store plugin data"""
        self.api.set_plugin_data(self.plugin_id, key, value)

    def get_data(self, key: str, default: Any = None) -> Any:
        """Get plugin data"""
        return self.api.get_plugin_data(self.plugin_id, key, default)

    def register_command(self, command_name: str, handler: Callable, description: str = ""):
        """Register a command"""
        self.api.register_command(self.plugin_id, command_name, handler, description)

    def add_hotkey(self, key_combination: str, command: str, description: str = ""):
        """Add hotkey binding"""
        self.api.add_hotkey_binding(self.plugin_id, key_combination, command, description)

    def show_notification(self, message: str, notification_type: str = "info"):
        """Show notification"""
        self.api.show_notification(message, notification_type)

    async def on_file_operation(self, operation: str, files: List[str]) -> bool:
        """Called when file operation occurs (override in subclass)"""
        return True

    async def on_ui_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Called when UI event occurs (override in subclass)"""
        return True

    async def on_command(self, command: str, args: List[str]) -> bool:
        """Called when command is executed (override in subclass)"""
        return True

    async def on_startup(self) -> bool:
        """Called during application startup (override in subclass)"""
        return True

    async def on_shutdown(self) -> bool:
        """Called during application shutdown (override in subclass)"""
        return True


class PluginInterface:
    """Interface for plugin communication"""

    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.hooks: Dict[PluginHookType, List[PluginHook]] = {}
        self.logger = Logger()

    def register_plugin(self, plugin: BasePlugin):
        """Register a plugin"""
        self.plugins[plugin.plugin_id] = plugin

        # Register plugin hooks
        for hook in plugin.hooks:
            if hook.hook_type not in self.hooks:
                self.hooks[hook.hook_type] = []
            self.hooks[hook.hook_type].append(hook)

    def unregister_plugin(self, plugin_id: str):
        """Unregister a plugin"""
        if plugin_id in self.plugins:
            plugin = self.plugins[plugin_id]

            # Remove plugin hooks
            for hook_type, hooks in self.hooks.items():
                self.hooks[hook_type] = [
                    hook for hook in hooks
                    if not hook.name.startswith(f"{plugin_id}.")
                ]

            del self.plugins[plugin_id]

    async def call_hooks(self, hook_type: PluginHookType, *args, **kwargs) -> List[Any]:
        """Call all hooks of a specific type"""
        results = []
        hooks = self.hooks.get(hook_type, [])

        # Sort hooks by priority (higher priority first)
        sorted_hooks = sorted(hooks, key=lambda h: h.priority, reverse=True)

        for hook in sorted_hooks:
            if not hook.enabled:
                continue

            try:
                if asyncio.iscoroutinefunction(hook.callback):
                    result = await hook.callback(*args, **kwargs)
                else:
                    result = hook.callback(*args, **kwargs)

                results.append(result)

            except Exception as e:
                self.logger.error(f"Error calling hook {hook.name}: {e}")

        return results

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """Get plugin by ID"""
        return self.plugins.get(plugin_id)

    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """Get all registered plugins"""
        return self.plugins.copy()

    def get_hooks(self, hook_type: PluginHookType) -> List[PluginHook]:
        """Get hooks of specific type"""
        return self.hooks.get(hook_type, []).copy()


# Example plugin implementations for reference

class FileOperationPlugin(BasePlugin):
    """Example plugin for file operations"""

    def __init__(self, plugin_id: str, api: PluginAPI):
        super().__init__(plugin_id, api)
        self.name = "File Operation Plugin"
        self.description = "Provides additional file operations"

    async def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            # Register hooks
            self.register_hook(
                "before_file_operation",
                PluginHookType.FILE_OPERATION,
                self.on_file_operation,
                "Called before file operations"
            )

            # Register commands
            self.register_command("duplicate", self.duplicate_file, "Duplicate selected file")
            self.register_command("compress", self.compress_files, "Compress selected files")

            # Register hotkeys
            self.add_hotkey("Ctrl+D", "duplicate", "Duplicate file")
            self.add_hotkey("Ctrl+Shift+C", "compress", "Compress files")

            self.log_info("File operation plugin initialized")
            return True

        except Exception as e:
            self.log_error(f"Failed to initialize: {e}")
            return False

    async def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        self.log_info("File operation plugin cleaned up")
        return True

    async def duplicate_file(self, *args, context=None):
        """Duplicate selected file"""
        selected_files = self.api.get_selected_files()
        if not selected_files:
            self.show_notification("No files selected", "warning")
            return

        for file_path in selected_files:
            # Implementation would go here
            self.log_info(f"Duplicating file: {file_path}")

        self.show_notification(f"Duplicated {len(selected_files)} files", "success")

    async def compress_files(self, *args, context=None):
        """Compress selected files"""
        selected_files = self.api.get_selected_files()
        if not selected_files:
            self.show_notification("No files selected", "warning")
            return

        # Implementation would go here
        self.log_info(f"Compressing {len(selected_files)} files")
        self.show_notification("Files compressed successfully", "success")


class UIEnhancementPlugin(BasePlugin):
    """Example plugin for UI enhancements"""

    def __init__(self, plugin_id: str, api: PluginAPI):
        super().__init__(plugin_id, api)
        self.name = "UI Enhancement Plugin"
        self.description = "Provides UI enhancements and customizations"

    async def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            # Register UI event hooks
            self.register_hook(
                "ui_theme_changed",
                PluginHookType.UI_EVENT,
                self.on_theme_changed,
                "Called when theme changes"
            )

            # Register commands
            self.register_command("toggle_sidebar", self.toggle_sidebar, "Toggle sidebar visibility")
            self.register_command("cycle_theme", self.cycle_theme, "Cycle through themes")

            self.log_info("UI enhancement plugin initialized")
            return True

        except Exception as e:
            self.log_error(f"Failed to initialize: {e}")
            return False

    async def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        self.log_info("UI enhancement plugin cleaned up")
        return True

    async def on_theme_changed(self, theme_name: str):
        """Handle theme change event"""
        self.log_info(f"Theme changed to: {theme_name}")
        self.store_data("last_theme", theme_name)

    async def toggle_sidebar(self, *args, context=None):
        """Toggle sidebar visibility"""
        # Implementation would go here
        self.log_info("Toggling sidebar")
        self.show_notification("Sidebar toggled", "info")

    async def cycle_theme(self, *args, context=None):
        """Cycle through available themes"""
        theme_manager = self.api.get_theme_manager()
        if theme_manager:
            # Implementation would go here
            self.log_info("Cycling theme")
            self.show_notification("Theme cycled", "info")