"""
Plugin API System

This module provides the API interface that plugins use to interact
with LaxyFile core functionality.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from ..core.types import OperationResult
from ..core.exceptions import PluginError, APIError
from ..utils.logger import Logger


class APIVersion(Enum):
    """API version compatibility"""
    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"


@dataclass
class APICapability:
    """API capability definition"""
    name: str
    version: APIVersion
    description: str
    methods: List[str]
    deprecated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'version': self.version.value,
            'description': self.description,
            'methods': self.methods,
            'deprecated': self.deprecated
        }


class PluginAPI:
    """Main API interface for plugins"""

    def __init__(self, version: APIVersion = APIVersion.V2_0):
        self.version = version
        self.logger = Logger()

        # Core system references (injected by plugin manager)
        self.file_manager = None
        self.theme_manager = None
        self.keyboard_handler = None
        self.preview_system = None
        self.ai_assistant = None

        # Plugin system references
        self.plugin_manager = None
        self.hook_registry = {}

        # API capabilities
        self.capabilities = self._initialize_capabilities()

        # Event system
        self.event_handlers: Dict[str, List[Callable]] = {}

    def _initialize_capabilities(self) -> Dict[str, APICapability]:
        """Initialize API capabilities"""
        capabilities = {
            'file_operations': APICapability(
                name="file_operations",
                version=self.version,
                description="File system operations",
                methods=[
                    'read_file', 'write_file', 'copy_file', 'move_file', 'delete_file',
                    'list_directory', 'create_directory', 'get_file_info'
                ]
            ),
            'ui_integration': APICapability(
                name="ui_integration",
                version=self.version,
                description="User interface integration",
                methods=[
                    'show_notification', 'show_dialog', 'add_menu_item', 'add_toolbar_button',
                    'register_view', 'update_status_bar'
                ]
            ),
            'theme_system': APICapability(
                name="theme_system",
                version=self.version,
                description="Theme and styling system",
                methods=[
                    'get_current_theme', 'set_theme', 'register_theme', 'get_color',
                    'apply_style', 'create_custom_theme'
                ]
            ),
            'preview_system': APICapability(
                name="preview_system",
                version=self.version,
                description="File preview system",
                methods=[
                    'register_preview_renderer', 'generate_preview', 'get_preview_cache',
                    'clear_preview_cache', 'set_preview_config'
                ]
            ),
            'command_system': APICapability(
                name="command_system",
                version=self.version,
                description="Command processing system",
                methods=[
                    'register_command', 'execute_command', 'get_command_history',
                    'add_hotkey', 'remove_hotkey', 'get_hotkeys'
                ]
            ),
            'ai_integration': APICapability(
                name="ai_integration",
                version=self.version,
                description="AI assistant integration",
                methods=[
                    'analyze_file', 'get_suggestions', 'process_query',
                    'register_ai_provider', 'get_analysis_history'
                ]
            ),
            'event_system': APICapability(
                name="event_system",
                version=self.version,
                description="Event handling system",
                methods=[
                    'register_event_handler', 'emit_event', 'remove_event_handler',
                    'get_event_history', 'create_custom_event'
                ]
            ),
            'storage_system': APICapability(
                name="storage_system",
                version=self.version,
                description="Data storage and persistence",
                methods=[
                    'store_data', 'retrieve_data', 'delete_data', 'list_stored_data',
                    'create_database', 'query_database'
                ]
            )
        }

        return capabilities

    def get_capabilities(self) -> Dict[str, APICapability]:
        """Get available API capabilities"""
        return self.capabilities.copy()

    def has_capability(self, capability_name: str) -> bool:
        """Check if API has specific capability"""
        return capability_name in self.capabilities

    # File Operations API
    async def read_file(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Read file content"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise APIError(f"File not found: {path}")

            return path.read_text(encoding=encoding)

        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            raise APIError(f"Failed to read file: {e}")

    async def write_file(self, file_path: Union[str, Path], content: str,
                        encoding: str = 'utf-8') -> bool:
        """Write content to file"""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=encoding)
            return True

        except Exception as e:
            self.logger.error(f"Error writing file {file_path}: {e}")
            raise APIError(f"Failed to write file: {e}")

    async def copy_file(self, source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """Copy file"""
        try:
            if self.file_manager:
                result = await self.file_manager.copy_files([Path(source)], Path(destination).parent)
                return result.success
            else:
                import shutil
                shutil.copy2(source, destination)
                return True

        except Exception as e:
            self.logger.error(f"Error copying file {source} to {destination}: {e}")
            raise APIError(f"Failed to copy file: {e}")

    async def move_file(self, source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """Move file"""
        try:
            if self.file_manager:
                result = await self.file_manager.move_files([Path(source)], Path(destination).parent)
                return result.success
            else:
                import shutil
                shutil.move(source, destination)
                return True

        except Exception as e:
            self.logger.error(f"Error moving file {source} to {destination}: {e}")
            raise APIError(f"Failed to move file: {e}")

    async def delete_file(self, file_path: Union[str, Path]) -> bool:
        """Delete file"""
        try:
            if self.file_manager:
                result = await self.file_manager.delete_files([Path(file_path)])
                return result.success
            else:
                path = Path(file_path)
                if path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                else:
                    path.unlink()
                return True

        except Exception as e:
            self.logger.error(f"Error deleting file {file_path}: {e}")
            raise APIError(f"Failed to delete file: {e}")

    async def list_directory(self, directory_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """List directory contents"""
        try:
            path = Path(directory_path)
            if not path.exists() or not path.is_dir():
                raise APIError(f"Directory not found: {path}")

            if self.file_manager:
                files = await self.file_manager.list_directory(path)
                return [file.to_dict() for file in files]
            else:
                files = []
                for item in path.iterdir():
                    files.append({
                        'name': item.name,
                        'path': str(item),
                        'is_dir': item.is_dir(),
                        'size': item.stat().st_size if item.is_file() else 0,
                        'modified': datetime.fromtimestamp(item.stat().st_mtime)
                    })
                return files

        except Exception as e:
            self.logger.error(f"Error listing directory {directory_path}: {e}")
            raise APIError(f"Failed to list directory: {e}")

    async def create_directory(self, directory_path: Union[str, Path]) -> bool:
        """Create directory"""
        try:
            path = Path(directory_path)
            path.mkdir(parents=True, exist_ok=True)
            return True

        except Exception as e:
            self.logger.error(f"Error creating directory {directory_path}: {e}")
            raise APIError(f"Failed to create directory: {e}")

    async def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get detailed file information"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise APIError(f"File not found: {path}")

            if self.file_manager:
                file_info = await self.file_manager.get_file_info(path)
                return file_info.to_dict()
            else:
                stat = path.stat()
                return {
                    'name': path.name,
                    'path': str(path),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'created': datetime.fromtimestamp(stat.st_ctime),
                    'is_dir': path.is_dir(),
                    'is_file': path.is_file(),
                    'is_symlink': path.is_symlink(),
                    'permissions': oct(stat.st_mode)[-3:]
                }

        except Exception as e:
            self.logger.error(f"Error getting file info for {file_path}: {e}")
            raise APIError(f"Failed to get file info: {e}")

    # UI Integration API
    async def show_notification(self, message: str, level: str = "info", duration: int = 3000) -> bool:
        """Show notification to user"""
        try:
            # This would integrate with the UI system
            self.logger.info(f"Notification ({level}): {message}")
            return True

        except Exception as e:
            self.logger.error(f"Error showing notification: {e}")
            return False

    async def show_dialog(self, title: str, message: str, dialog_type: str = "info",
                         buttons: List[str] = None) -> str:
        """Show dialog to user"""
        try:
            # This would integrate with the UI system
            buttons = buttons or ["OK"]
            self.logger.info(f"Dialog ({dialog_type}): {title} - {message}")
            return buttons[0]  # Default to first button

        except Exception as e:
            self.logger.error(f"Error showing dialog: {e}")
            return "Cancel"

    def add_menu_item(self, menu_path: str, label: str, callback: Callable,
                     shortcut: str = None) -> bool:
        """Add menu item to UI"""
        try:
            # This would integrate with the UI system
            self.logger.info(f"Adding menu item: {menu_path}/{label}")
            return True

        except Exception as e:
            self.logger.error(f"Error adding menu item: {e}")
            return False

    def add_toolbar_button(self, label: str, callback: Callable, icon: str = None) -> bool:
        """Add toolbar button to UI"""
        try:
            # This would integrate with the UI system
            self.logger.info(f"Adding toolbar button: {label}")
            return True

        except Exception as e:
            self.logger.error(f"Error adding toolbar button: {e}")
            return False

    def register_view(self, view_id: str, view_class: type, title: str = None) -> bool:
        """Register custom view"""
        try:
            # This would integrate with the UI system
            self.logger.info(f"Registering view: {view_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error registering view: {e}")
            return False

    def update_status_bar(self, message: str, section: str = "main") -> bool:
        """Update status bar"""
        try:
            # This would integrate with the UI system
            self.logger.info(f"Status bar ({section}): {message}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating status bar: {e}")
            return False

    # Theme System API
    def get_current_theme(self) -> Dict[str, Any]:
        """Get current theme"""
        try:
            if self.theme_manager:
                return self.theme_manager.get_current_theme().to_dict()
            else:
                return {"name": "default", "colors": {}, "styles": {}}

        except Exception as e:
            self.logger.error(f"Error getting current theme: {e}")
            return {}

    def set_theme(self, theme_name: str) -> bool:
        """Set current theme"""
        try:
            if self.theme_manager:
                return self.theme_manager.set_theme(theme_name)
            else:
                self.logger.warning("Theme manager not available")
                return False

        except Exception as e:
            self.logger.error(f"Error setting theme: {e}")
            return False

    def register_theme(self, theme_data: Dict[str, Any]) -> bool:
        """Register custom theme"""
        try:
            if self.theme_manager:
                return self.theme_manager.register_theme(theme_data)
            else:
                self.logger.warning("Theme manager not available")
                return False

        except Exception as e:
            self.logger.error(f"Error registering theme: {e}")
            return False

    def get_color(self, color_name: str, fallback: str = "#ffffff") -> str:
        """Get color from current theme"""
        try:
            if self.theme_manager:
                return self.theme_manager.get_color(color_name, fallback)
            else:
                return fallback

        except Exception as e:
            self.logger.error(f"Error getting color: {e}")
            return fallback

    # Preview System API
    def register_preview_renderer(self, file_types: List[str], renderer: Callable) -> bool:
        """Register preview renderer for file types"""
        try:
            if self.preview_system:
                return self.preview_system.register_renderer(file_types, renderer)
            else:
                self.logger.warning("Preview system not available")
                return False

        except Exception as e:
            self.logger.error(f"Error registering preview renderer: {e}")
            return False

    async def generate_preview(self, file_path: Union[str, Path], **kwargs) -> Dict[str, Any]:
        """Generate preview for file"""
        try:
            if self.preview_system:
                preview = await self.preview_system.generate_preview(Path(file_path), **kwargs)
                return preview.to_dict() if preview else {}
            else:
                return {"error": "Preview system not available"}

        except Exception as e:
            self.logger.error(f"Error generating preview: {e}")
            return {"error": str(e)}

    # Command System API
    def register_command(self, command_name: str, callback: Callable,
                        description: str = "", hotkey: str = None) -> bool:
        """Register custom command"""
        try:
            # This would integrate with the command system
            self.logger.info(f"Registering command: {command_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error registering command: {e}")
            return False

    async def execute_command(self, command_name: str, args: List[str] = None) -> Any:
        """Execute command"""
        try:
            # This would integrate with the command system
            args = args or []
            self.logger.info(f"Executing command: {command_name} with args: {args}")
            return {"success": True, "result": "Command executed"}

        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            return {"success": False, "error": str(e)}

    def add_hotkey(self, key_combination: str, callback: Callable,
                  description: str = "") -> bool:
        """Add hotkey binding"""
        try:
            if self.keyboard_handler:
                return self.keyboard_handler.add_hotkey(key_combination, callback, description)
            else:
                self.logger.warning("Keyboard handler not available")
                return False

        except Exception as e:
            self.logger.error(f"Error adding hotkey: {e}")
            return False

    # AI Integration API
    async def analyze_file(self, file_path: Union[str, Path], analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze file using AI"""
        try:
            if self.ai_assistant:
                result = await self.ai_assistant.analyze_file(Path(file_path), analysis_type)
                return result.to_dict() if result else {}
            else:
                return {"error": "AI assistant not available"}

        except Exception as e:
            self.logger.error(f"Error analyzing file: {e}")
            return {"error": str(e)}

    async def get_suggestions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get AI suggestions based on context"""
        try:
            if self.ai_assistant:
                suggestions = await self.ai_assistant.get_suggestions(context)
                return [s.to_dict() for s in suggestions]
            else:
                return []

        except Exception as e:
            self.logger.error(f"Error getting suggestions: {e}")
            return []

    async def process_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """Process natural language query"""
        try:
            if self.ai_assistant:
                return await self.ai_assistant.process_query(query, context or {})
            else:
                return "AI assistant not available"

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return f"Error: {e}"

    # Event System API
    def register_event_handler(self, event_name: str, handler: Callable, priority: int = 50) -> bool:
        """Register event handler"""
        try:
            if event_name not in self.event_handlers:
                self.event_handlers[event_name] = []

            self.event_handlers[event_name].append((handler, priority))
            # Sort by priority (higher first)
            self.event_handlers[event_name].sort(key=lambda x: x[1], reverse=True)

            self.logger.info(f"Registered event handler for: {event_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error registering event handler: {e}")
            return False

    async def emit_event(self, event_name: str, data: Dict[str, Any] = None) -> List[Any]:
        """Emit event to all handlers"""
        try:
            data = data or {}
            results = []

            if event_name in self.event_handlers:
                for handler, priority in self.event_handlers[event_name]:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            result = await handler(event_name, data)
                        else:
                            result = handler(event_name, data)
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Error in event handler for {event_name}: {e}")

            return results

        except Exception as e:
            self.logger.error(f"Error emitting event: {e}")
            return []

    def remove_event_handler(self, event_name: str, handler: Callable) -> bool:
        """Remove event handler"""
        try:
            if event_name in self.event_handlers:
                self.event_handlers[event_name] = [
                    (h, p) for h, p in self.event_handlers[event_name] if h != handler
                ]
                return True
            return False

        except Exception as e:
            self.logger.error(f"Error removing event handler: {e}")
            return False

    # Hook System API
    def register_hook_callback(self, hook_name: str, callback: Callable, priority: int = 50) -> bool:
        """Register callback for plugin hook"""
        try:
            if hook_name not in self.hook_registry:
                from .base_plugin import PluginHook
                self.hook_registry[hook_name] = PluginHook(hook_name)

            self.hook_registry[hook_name].register(callback, priority)
            self.logger.info(f"Registered hook callback for: {hook_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error registering hook callback: {e}")
            return False

    async def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute hook callbacks"""
        try:
            if hook_name in self.hook_registry:
                return await self.hook_registry[hook_name].execute(*args, **kwargs)
            return []

        except Exception as e:
            self.logger.error(f"Error executing hook: {e}")
            return []

    # Storage System API
    async def store_data(self, key: str, data: Any, namespace: str = "default") -> bool:
        """Store data persistently"""
        try:
            # This would integrate with a storage system
            self.logger.info(f"Storing data: {namespace}.{key}")
            return True

        except Exception as e:
            self.logger.error(f"Error storing data: {e}")
            return False

    async def retrieve_data(self, key: str, namespace: str = "default", default: Any = None) -> Any:
        """Retrieve stored data"""
        try:
            # This would integrate with a storage system
            self.logger.info(f"Retrieving data: {namespace}.{key}")
            return default

        except Exception as e:
            self.logger.error(f"Error retrieving data: {e}")
            return default

    async def delete_data(self, key: str, namespace: str = "default") -> bool:
        """Delete stored data"""
        try:
            # This would integrate with a storage system
            self.logger.info(f"Deleting data: {namespace}.{key}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting data: {e}")
            return False

    # Utility Methods
    def get_version(self) -> str:
        """Get API version"""
        return self.version.value

    def is_compatible(self, required_version: APIVersion) -> bool:
        """Check if API is compatible with required version"""
        version_order = {
            APIVersion.V1_0: 1,
            APIVersion.V1_1: 2,
            APIVersion.V2_0: 3
        }

        return version_order.get(self.version, 0) >= version_order.get(required_version, 0)

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        import platform
        import sys

        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': sys.version,
            'api_version': self.version.value,
            'capabilities': list(self.capabilities.keys())
        }

    def log_info(self, message: str) -> None:
        """Log info message"""
        self.logger.info(message)

    def log_warning(self, message: str) -> None:
        """Log warning message"""
        self.logger.warning(message)

    def log_error(self, message: str) -> None:
        """Log error message"""
        self.logger.error(message)

    def __str__(self) -> str:
        """String representation"""
        return f"PluginAPI v{self.version.value}"

    def __repr__(self) -> str:
        """Detailed representation"""
        return f"<PluginAPI: version={self.version.value}, capabilities={len(self.capabilities)}>"