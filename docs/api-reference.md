# LaxyFile API Reference

This document provides comprehensive API documentation for LaxyFile plugin development and integration.

## Table of Contents

1. [Plugin API](#plugin-api)
2. [Core APIs](#core-apis)
3. [UI Integration](#ui-integration)
4. [File Operations API](#file-operations-api)
5. [AI Integration API](#ai-integration-api)
6. [Event System](#event-system)
7. [Configuration API](#configuration-api)
8. [Utilities and Helpers](#utilities-and-helpers)

## Plugin API

### BasePlugin Class

All LaxyFile plugins must inherit from the `BasePlugin` class.

```python
from laxyfile.plugins.base_plugin import BasePlugin
from laxyfile.core.types import FileInfo, PluginCapability
from typing import List, Dict, Any, Optional

class MyPlugin(BasePlugin):
    """Example plugin implementation"""

    # Plugin metadata
    name = "My Custom Plugin"
    version = "1.0.0"
    author = "Your Name"
    description = "A custom plugin for LaxyFile"
    website = "https://github.com/yourname/my-plugin"

    # Plugin capabilities
    capabilities = [
        PluginCapability.FILE_HANDLER,
        PluginCapability.UI_EXTENSION,
        PluginCapability.CONTEXT_MENU
    ]

    # Supported file types
    supported_extensions = [".txt", ".md", ".py"]

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.my_setting = configt("my_setting", "default_value")

    def initialize(self) -> bool:
        """Initialize the plugin"""
        self.logger.info(f"Initializing {self.name}")
        return True

    def cleanup(self) -> None:
        """Clean up plugin resources"""
        self.logger.info(f"Cleaning up {self.name}")

    def can_handle_file(self, file_info: FileInfo) -> bool:
        """Check if plugin can handle the given file"""
        return file_info.path.suffix.lower() in self.supported_extensions

    def handle_file(self, file_info: FileInfo, action: str) -> Any:
        """Handle file operation"""
        if action == "preview":
            return self.generate_preview(file_info)
        elif action == "edit":
            return self.edit_file(file_info)
        return None

    def get_context_menu_items(self, file_info: FileInfo) -> List[Dict[str, Any]]:
        """Return context menu items for the file"""
        if not self.can_handle_file(file_info):
            return []

        return [
            {
                "label": "My Custom Action",
                "action": "my_custom_action",
                "icon": "🔧",
                "callback": self.my_custom_action
            }
        ]

    def my_custom_action(self, file_info: FileInfo) -> None:
        """Custom action implementation"""
        self.logger.info(f"Performing custom action on {file_info.path}")
        # Your custom logic here
```

### Plugin Lifecycle

```python
class PluginLifecycle:
    """Plugin lifecycle management"""

    def on_load(self) -> bool:
        """Called when plugin is loaded"""
        pass

    def on_enable(self) -> bool:
        """Called when plugin is enabled"""
        pass

    def on_disable(self) -> None:
        """Called when plugin is disabled"""
        pass

    def on_unload(self) -> None:
        """Called when plugin is unloaded"""
        pass

    def on_config_change(self, config: Dict[str, Any]) -> None:
        """Called when plugin configuration changes"""
        pass
```

### Plugin Capabilities

```python
from enum import Enum

class PluginCapability(Enum):
    """Plugin capability types"""
    FILE_HANDLER = "file_handler"          # Handle specific file types
    UI_EXTENSION = "ui_extension"          # Extend UI components
    CONTEXT_MENU = "context_menu"          # Add context menu items
    TOOLBAR = "toolbar"                    # Add toolbar buttons
    SIDEBAR = "sidebar"                    # Add sidebar panels
    PREVIEW = "preview"                    # Custom file preview
    SEARCH = "search"                      # Custom search providers
    AI_INTEGRATION = "ai_integration"      # AI assistant extensions
    FILE_OPERATIONS = "file_operations"   # Custom file operations
    THEME = "theme"                        # Theme extensions
    KEYBOARD = "keyboard"                  # Keyboard shortcut handlers
    NETWORK = "network"                    # Network operations
    AUTOMATION = "automation"              # Workflow automation
```

## Core APIs

### File Manager API

```python
from laxyfile.core.advanced_file_manager import AdvancedFileManager
from laxyfile.core.types import FileInfo, SortType, FilterOptions
from pathlib import Path
from typing import List, Optional, AsyncIterator

class FileManagerAPI:
    """Core file manager API"""

    def __init__(self, file_manager: AdvancedFileManager):
        self.file_manager = file_manager

    async def list_directory(
        self,
        path: Path,
        sort_type: SortType = SortType.NAME,
        reverse: bool = False,
        show_hidden: bool = False
    ) -> List[FileInfo]:
        """List directory contents"""
        return await self.file_manager.list_directory(
            path, sort_type, reverse, show_hidden
        )

    async def get_file_info(self, path: Path) -> Optional[FileInfo]:
        """Get detailed file information"""
        return await self.file_manager.get_file_info(path)

    async def search_files(
        self,
        directory: Path,
        query: str,
        recursive: bool = True,
        include_content: bool = False,
        filters: Optional[FilterOptions] = None
    ) -> List[FileInfo]:
        """Search for files"""
        return await self.file_manager.search_files(
            directory, query, recursive, include_content, filters
        )

    async def watch_directory(
        self,
        path: Path,
        callback: callable,
        recursive: bool = True
    ) -> str:
        """Watch directory for changes"""
        return await self.file_manager.watch_directory(path, callback, recursive)

    def stop_watching(self, watch_id: str) -> None:
        """Stop watching directory"""
        self.file_manager.stop_watching(watch_id)

    async def get_directory_size(self, path: Path) -> int:
        """Get total size of directory"""
        return await self.file_manager.get_directory_size(path)

    def get_file_type_stats(self, files: List[FileInfo]) -> Dict[str, Dict[str, Any]]:
        """Get file type statistics"""
        return self.file_manager.get_file_type_stats(files)
```

### Configuration API

```python
from laxyfile.core.config import Config
from typing import Any, Dict, Optional, List

class ConfigAPI:
    """Configuration management API"""

    def __init__(self, config: Config):
        self.config = config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.config.set(key, value)

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.config.get_section(section)

    def set_section(self, section: str, values: Dict[str, Any]) -> None:
        """Set entire configuration section"""
        self.config.set_section(section, values)

    def has(self, key: str) -> bool:
        """Check if configuration key exists"""
        return self.config.has(key)

    def delete(self, key: str) -> None:
        """Delete configuration key"""
        self.config.delete(key)

    def save(self) -> None:
        """Save configuration to disk"""
        self.config.save()

    def reload(self) -> None:
        """Reload configuration from disk"""
        self.config.reload()

    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get plugin-specific configuration"""
        return self.config.get_section(f"plugins.{plugin_name}")

    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """Set plugin-specific configuration"""
        self.config.set_section(f"plugins.{plugin_name}", config)
```

## UI Integration

### UI Extension API

```python
from laxyfile.ui.superfile_ui import SuperFileUI
from rich.panel import Panel
from rich.text import Text
from typing import Dict, Any, Optional, Callable

class UIExtensionAPI:
    """UI extension API for plugins"""

    def __init__(self, ui: SuperFileUI):
        self.ui = ui
        self._custom_panels = {}
        self._toolbar_items = {}
        self._status_items = {}

    def add_sidebar_panel(
        self,
        panel_id: str,
        title: str,
        content_provider: Callable[[], Panel],
        position: int = -1
    ) -> None:
        """Add custom sidebar panel"""
        self._custom_panels[panel_id] = {
            "title": title,
            "content_provider": content_provider,
            "position": position
        }
        self.ui.register_sidebar_panel(panel_id, title, content_provider, position)

    def remove_sidebar_panel(self, panel_id: str) -> None:
        """Remove custom sidebar panel"""
        if panel_id in self._custom_panels:
            del self._custom_panels[panel_id]
            self.ui.unregister_sidebar_panel(panel_id)

    def add_toolbar_button(
        self,
        button_id: str,
        label: str,
        icon: str,
        callback: Callable[[], None],
        tooltip: Optional[str] = None
    ) -> None:
        """Add toolbar button"""
        self._toolbar_items[button_id] = {
            "label": label,
            "icon": icon,
            "callback": callback,
            "tooltip": tooltip
        }
        self.ui.add_toolbar_button(button_id, label, icon, callback, tooltip)

    def remove_toolbar_button(self, button_id: str) -> None:
        """Remove toolbar button"""
        if button_id in self._toolbar_items:
            del self._toolbar_items[button_id]
            self.ui.remove_toolbar_button(button_id)

    def add_status_item(
        self,
        item_id: str,
        content_provider: Callable[[], str],
        position: int = -1
    ) -> None:
        """Add status bar item"""
        self._status_items[item_id] = {
            "content_provider": content_provider,
            "position": position
        }
        self.ui.add_status_item(item_id, content_provider, position)

    def remove_status_item(self, item_id: str) -> None:
        """Remove status bar item"""
        if item_id in self._status_items:
            del self._status_items[item_id]
            self.ui.remove_status_item(item_id)

    def show_notification(
        self,
        message: str,
        type: str = "info",
        duration: int = 3000
    ) -> None:
        """Show notification to user"""
        self.ui.show_notification(message, type, duration)

    def show_dialog(
        self,
        title: str,
        content: Panel,
        buttons: List[Dict[str, Any]] = None
    ) -> str:
        """Show modal dialog"""
        return self.ui.show_dialog(title, content, buttons)

    def get_current_file(self) -> Optional[FileInfo]:
        """Get currently selected file"""
        return self.ui.get_current_file()

    def get_selected_files(self) -> List[FileInfo]:
        """Get all selected files"""
        return self.ui.get_selected_files()

    def refresh_view(self) -> None:
        """Refresh the current view"""
        self.ui.refresh_view()
```

### Theme API

```python
from laxyfile.ui.theme import ThemeManager, Theme
from typing import Dict, Any, Optional

class ThemeAPI:
    """Theme system API"""

    def __init__(self, theme_manager: ThemeManager):
        self.theme_manager = theme_manager

    def get_current_theme(self) -> Theme:
        """Get current active theme"""
        return self.theme_manager.get_current_theme()

    def set_theme(self, theme_name: str) -> bool:
        """Set active theme"""
        return self.theme_manager.set_theme(theme_name)

    def get_available_themes(self) -> List[str]:
        """Get list of available themes"""
        return self.theme_manager.get_available_themes()

    def register_theme(self, theme: Theme) -> bool:
        """Register custom theme"""
        return self.theme_manager.register_theme(theme)

    def unregister_theme(self, theme_name: str) -> bool:
        """Unregister theme"""
        return self.theme_manager.unregister_theme(theme_name)

    def get_color(self, color_key: str) -> str:
        """Get color from current theme"""
        return self.theme_manager.get_color(color_key)

    def get_style(self, style_key: str) -> Dict[str, Any]:
        """Get style from current theme"""
        return self.theme_manager.get_style(style_key)

    def create_themed_panel(
        self,
        content: Any,
        title: Optional[str] = None,
        style_key: str = "default"
    ) -> Panel:
        """Create panel with current theme styling"""
        return self.theme_manager.create_themed_panel(content, title, style_key)
```

## File Operations API

### File Operations

```python
from laxyfile.operations.file_ops import ComprehensiveFileOperations
from laxyfile.core.types import OperationProgress, ConflictResolution
from pathlib import Path
from typing import List, Optional, Callable, AsyncIterator

class FileOperationsAPI:
    """File operations API"""

    def __init__(self, file_ops: ComprehensiveFileOperations):
        self.file_ops = file_ops

    async def copy_files(
        self,
        sources: List[Path],
        destination: Path,
        progress_callback: Optional[Callable[[OperationProgress], None]] = None,
        conflict_resolution: ConflictResolution = ConflictResolution.ASK
    ) -> bool:
        """Copy files with progress tracking"""
        return await self.file_ops.copy_files(
            sources, destination, progress_callback, conflict_resolution
        )

    async def move_files(
        self,
        sources: List[Path],
        destination: Path,
        progress_callback: Optional[Callable[[OperationProgress], None]] = None,
        conflict_resolution: ConflictResolution = ConflictResolution.ASK
    ) -> bool:
        """Move files with progress tracking"""
        return await self.file_ops.move_files(
            sources, destination, progress_callback, conflict_resolution
        )

    async def delete_files(
        self,
        files: List[Path],
        use_trash: bool = True,
        progress_callback: Optional[Callable[[OperationProgress], None]] = None
    ) -> bool:
        """Delete files"""
        return await self.file_ops.delete_files(files, use_trash, progress_callback)

    async def create_archive(
        self,
        files: List[Path],
        archive_path: Path,
        format: str = "zip",
        compression_level: int = 6,
        progress_callback: Optional[Callable[[OperationProgress], None]] = None
    ) -> bool:
        """Create archive from files"""
        return await self.file_ops.create_archive(
            files, archive_path, format, compression_level, progress_callback
        )

    async def extract_archive(
        self,
        archive_path: Path,
        destination: Path,
        progress_callback: Optional[Callable[[OperationProgress], None]] = None
    ) -> bool:
        """Extract archive"""
        return await self.file_ops.extract_archive(
            archive_path, destination, progress_callback
        )

    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel ongoing operation"""
        return self.file_ops.cancel_operation(operation_id)

    def get_operation_status(self, operation_id: str) -> Optional[OperationProgress]:
        """Get operation status"""
        return self.file_ops.get_operation_status(operation_id)
```

### Batch Operations

```python
from typing import Dict, Any, List, Callable

class BatchOperationsAPI:
    """Batch operations API"""

    async def batch_rename(
        self,
        files: List[Path],
        pattern: str,
        preview: bool = True
    ) -> Dict[Path, str]:
        """Batch rename files with pattern"""
        pass

    async def batch_chmod(
        self,
        files: List[Path],
        permissions: str,
        recursive: bool = False
    ) -> bool:
        """Batch change file permissions"""
        pass

    async def batch_convert(
        self,
        files: List[Path],
        target_format: str,
        options: Dict[str, Any] = None
    ) -> List[Path]:
        """Batch convert files to different format"""
        pass
```

## AI Integration API

### AI Assistant API

```python
from laxyfile.ai.advanced_assistant import AdvancedAIAssistant, AnalysisType, AnalysisResult
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncIterator

class AIAssistantAPI:
    """AI assistant integration API"""

    def __init__(self, ai_assistant: AdvancedAIAssistant):
        self.ai_assistant = ai_assistant

    async def analyze_file(
        self,
        file_path: Path,
        analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE
    ) -> AnalysisResult:
        """Analyze single file with AI"""
        return await self.ai_assistant.analyze_file(file_path, analysis_type)

    async def analyze_files_batch(
        self,
        file_paths: List[Path],
        analysis_type: AnalysisType = AnalysisType.QUICK
    ) -> List[AnalysisResult]:
        """Analyze multiple files in batch"""
        return await self.ai_assistant.analyze_files_batch(file_paths, analysis_type)

    async def suggest_organization(
        self,
        directory: Path,
        include_ai_analysis: bool = True
    ) -> List[Dict[str, Any]]:
        """Get AI organization suggestions"""
        return await self.ai_assistant.suggest_organization(directory, include_ai_analysis)

    async def search_by_content(
        self,
        directory: Path,
        query: str,
        semantic: bool = True
    ) -> List[Dict[str, Any]]:
        """Search files by content using AI"""
        return await self.ai_assistant.search_by_content(directory, query, semantic)

    async def chat_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Send query to AI chat"""
        return await self.ai_assistant.chat_query(query, context)

    async def analyze_security(
        self,
        file_path: Path
    ) -> Dict[str, Any]:
        """Analyze file for security issues"""
        return await self.ai_assistant.analyze_security(file_path)

    def register_ai_extension(
        self,
        extension_name: str,
        handler: Callable[[str, Dict[str, Any]], str]
    ) -> None:
        """Register custom AI extension"""
        self.ai_assistant.register_extension(extension_name, handler)

    def get_ai_capabilities(self) -> List[str]:
        """Get available AI capabilities"""
        return self.ai_assistant.get_capabilities()
```

## Event System

### Event Types

```python
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, Optional
from pathlib import Path

class EventType(Enum):
    """LaxyFile event types"""
    # File events
    FILE_SELECTED = "file_selected"
    FILE_OPENED = "file_opened"
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    FILE_MOVED = "file_moved"
    FILE_COPIED = "file_copied"

    # Directory events
    DIRECTORY_CHANGED = "directory_changed"
    DIRECTORY_CREATED = "directory_created"
    DIRECTORY_DELETED = "directory_deleted"

    # UI events
    THEME_CHANGED = "theme_changed"
    VIEW_CHANGED = "view_changed"
    PANEL_RESIZED = "panel_resized"

    # Operation events
    OPERATION_STARTED = "operation_started"
    OPERATION_PROGRESS = "operation_progress"
    OPERATION_COMPLETED = "operation_completed"
    OPERATION_FAILED = "operation_failed"

    # AI events
    AI_ANALYSIS_STARTED = "ai_analysis_started"
    AI_ANALYSIS_COMPLETED = "ai_analysis_completed"
    AI_CHAT_MESSAGE = "ai_chat_message"

    # Plugin events
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    PLUGIN_ERROR = "plugin_error"

@dataclass
class Event:
    """Event data structure"""
    type: EventType
    data: Dict[str, Any]
    source: Optional[str] = None
    timestamp: Optional[float] = None
```

### Event Manager API

```python
from typing import Callable, List, Optional
import asyncio

class EventManagerAPI:
    """Event system API"""

    def __init__(self):
        self._handlers = {}
        self._async_handlers = {}

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[Event], None],
        priority: int = 0
    ) -> str:
        """Subscribe to events"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        handler_id = f"{event_type.value}_{len(self._handlers[event_type])}"
        self._handlers[event_type].append({
            "id": handler_id,
            "handler": handler,
            "priority": priority
        })

        # Sort by priority
        self._handlers[event_type].sort(key=lambda x: x["priority"], reverse=True)

        return handler_id

    def subscribe_async(
        self,
        event_type: EventType,
        handler: Callable[[Event], None],
        priority: int = 0
    ) -> str:
        """Subscribe to events with async handler"""
        if event_type not in self._async_handlers:
            self._async_handlers[event_type] = []

        handler_id = f"{event_type.value}_async_{len(self._async_handlers[event_type])}"
        self._async_handlers[event_type].append({
            "id": handler_id,
            "handler": handler,
            "priority": priority
        })

        # Sort by priority
        self._async_handlers[event_type].sort(key=lambda x: x["priority"], reverse=True)

        return handler_id

    def unsubscribe(self, handler_id: str) -> bool:
        """Unsubscribe from events"""
        for event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h["id"] != handler_id
            ]

        for event_type in self._async_handlers:
            self._async_handlers[event_type] = [
                h for h in self._async_handlers[event_type] if h["id"] != handler_id
            ]

        return True

    def emit(self, event: Event) -> None:
        """Emit synchronous event"""
        if event.type in self._handlers:
            for handler_info in self._handlers[event.type]:
                try:
                    handler_info["handler"](event)
                except Exception as e:
                    # Log error but continue with other handlers
                    print(f"Error in event handler: {e}")

    async def emit_async(self, event: Event) -> None:
        """Emit asynchronous event"""
        tasks = []

        # Synchronous handlers
        if event.type in self._handlers:
            for handler_info in self._handlers[event.type]:
                try:
                    handler_info["handler"](event)
                except Exception as e:
                    print(f"Error in sync event handler: {e}")

        # Asynchronous handlers
        if event.type in self._async_handlers:
            for handler_info in self._async_handlers[event.type]:
                tasks.append(self._call_async_handler(handler_info["handler"], event))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _call_async_handler(self, handler: Callable, event: Event) -> None:
        """Call async handler with error handling"""
        try:
            await handler(event)
        except Exception as e:
            print(f"Error in async event handler: {e}")
```

## Configuration API

### Plugin Configuration Schema

```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ConfigOption:
    """Configuration option definition"""
    key: str
    type: type
    default: Any
    description: str
    required: bool = False
    choices: Optional[List[Any]] = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    validation_regex: Optional[str] = None

class PluginConfigSchema:
    """Plugin configuration schema"""

    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.options: List[ConfigOption] = []

    def add_option(self, option: ConfigOption) -> None:
        """Add configuration option"""
        self.options.append(option)

    def add_string_option(
        self,
        key: str,
        default: str = "",
        description: str = "",
        required: bool = False,
        choices: Optional[List[str]] = None,
        validation_regex: Optional[str] = None
    ) -> None:
        """Add string configuration option"""
        self.add_option(ConfigOption(
            key=key,
            type=str,
            default=default,
            description=description,
            required=required,
            choices=choices,
            validation_regex=validation_regex
        ))

    def add_int_option(
        self,
        key: str,
        default: int = 0,
        description: str = "",
        required: bool = False,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None
    ) -> None:
        """Add integer configuration option"""
        self.add_option(ConfigOption(
            key=key,
            type=int,
            default=default,
            description=description,
            required=required,
            min_value=min_value,
            max_value=max_value
        ))

    def add_bool_option(
        self,
        key: str,
        default: bool = False,
        description: str = "",
        required: bool = False
    ) -> None:
        """Add boolean configuration option"""
        self.add_option(ConfigOption(
            key=key,
            type=bool,
            default=default,
            description=description,
            required=required
        ))

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration against schema"""
        errors = []

        for option in self.options:
            if option.required and option.key not in config:
                errors.append(f"Required option '{option.key}' is missing")
                continue

            if option.key not in config:
                continue

            value = config[option.key]

            # Type validation
            if not isinstance(value, option.type):
                errors.append(f"Option '{option.key}' must be of type {option.type.__name__}")
                continue

            # Choice validation
            if option.choices and value not in option.choices:
                errors.append(f"Option '{option.key}' must be one of {option.choices}")

            # Range validation
            if option.min_value is not None and value < option.min_value:
                errors.append(f"Option '{option.key}' must be >= {option.min_value}")

            if option.max_value is not None and value > option.max_value:
                errors.append(f"Option '{option.key}' must be <= {option.max_value}")

            # Regex validation
            if option.validation_regex and isinstance(value, str):
                import re
                if not re.match(option.validation_regex, value):
                    errors.append(f"Option '{option.key}' does not match required pattern")

        return errors
```

## Utilities and Helpers

### Logging API

```python
import logging
from typing import Optional

class PluginLogger:
    """Plugin logging utility"""

    def __init__(self, plugin_name: str):
        self.logger = logging.getLogger(f"laxyfile.plugins.{plugin_name}")

    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message"""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message"""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message"""
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs) -> None:
        """Log exception with traceback"""
        self.logger.exception(message, *args, **kwargs)
```

### File Utilities

```python
from pathlib import Path
from typing import List, Optional, Dict, Any
import mimetypes
import hashlib

class FileUtils:
    """File utility functions"""

    @staticmethod
    def get_file_type(file_path: Path) -> str:
        """Get file type from path"""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            return mime_type.split('/')[0]
        return 'unknown'

    @staticmethod
    def get_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
        """Calculate file hash"""
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    @staticmethod
    def format_file_size(size: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    @staticmethod
    def is_text_file(file_path: Path) -> bool:
        """Check if file is text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)
            return True
        except (UnicodeDecodeError, IOError):
            return False

    @staticmethod
    def get_file_icon(file_path: Path) -> str:
        """Get appropriate icon for file type"""
        extension = file_path.suffix.lower()

        icon_map = {
            # Documents
            '.txt': '📄', '.md': '📝', '.pdf': '📕', '.doc': '📘', '.docx': '📘',
            '.odt': '📄', '.rtf': '📄', '.tex': '📄',

            # Code files
            '.py': '🐍', '.js': '📜', '.ts': '📜', '.html': '🌐', '.css': '🎨',
            '.json': '📋', '.xml': '📋', '.yaml': '📋', '.yml': '📋',
            '.java': '☕', '.cpp': '⚙️', '.c': '⚙️', '.h': '⚙️',
            '.php': '🐘', '.rb': '💎', '.go': '🐹', '.rs': '🦀',

            # Images
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
            '.bmp': '🖼️', '.svg': '🖼️', '.webp': '🖼️', '.ico': '🖼️',

            # Audio
            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵', '.ogg': '🎵',
            '.m4a': '🎵', '.aac': '🎵', '.wma': '🎵',

            # Video
            '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬', '.mov': '🎬',
            '.wmv': '🎬', '.flv': '🎬', '.webm': '🎬',

            # Archives
            '.zip': '📦', '.tar': '📦', '.gz': '📦', '.bz2': '📦',
            '.xz': '📦', '.7z': '📦', '.rar': '📦',

            # Executables
            '.exe': '⚙️', '.msi': '⚙️', '.deb': '⚙️', '.rpm': '⚙️',
            '.dmg': '⚙️', '.pkg': '⚙️', '.app': '⚙️'
        }

        return icon_map.get(extension, '📄')
```

### Async Utilities

```python
import asyncio
from typing import Any, Callable, Optional, TypeVar, Awaitable
from functools import wraps

T = TypeVar('T')

class AsyncUtils:
    """Async utility functions"""

    @staticmethod
    async def run_in_thread(func: Callable[..., T], *args, **kwargs) -> T:
        """Run synchronous function in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)

    @staticmethod
    def async_cache(ttl: int = 300):
        """Async function caching decorator"""
        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            cache = {}

            @wraps(func)
            async def wrapper(*args, **kwargs):
                key = str(args) + str(sorted(kwargs.items()))

                if key in cache:
                    result, timestamp = cache[key]
                    if asyncio.get_event_loop().time() - timestamp < ttl:
                        return result

                result = await func(*args, **kwargs)
                cache[key] = (result, asyncio.get_event_loop().time())
                return result

            return wrapper
        return decorator

    @staticmethod
    async def timeout_after(seconds: float, coro: Awaitable[T]) -> Optional[T]:
        """Run coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=seconds)
        except asyncio.TimeoutError:
            return None

    @staticmethod
    async def retry_async(
        func: Callable[..., Awaitable[T]],
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        *args,
        **kwargs
    ) -> T:
        """Retry async function with exponential backoff"""
        last_exception = None

        for attempt in range(max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    await asyncio.sleep(delay * (backoff ** attempt))

        raise last_exception
```

## Example Plugin Implementation

Here's a complete example of a plugin that adds Git integration:

```python
from laxyfile.plugins.base_plugin import BasePlugin
from laxyfile.core.types import FileInfo, PluginCapability
from laxyfile.plugins.plugin_api import PluginConfigSchema, ConfigOption
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import asyncio

class GitIntegrationPlugin(BasePlugin):
    """Git integration plugin for LaxyFile"""

    name = "Git Integration"
    version = "1.0.0"
    author = "LaxyFile Team"
    description = "Adds Git version control integration to LaxyFile"
    website = "https://github.com/laxyfile/git-plugin"

    capabilities = [
        PluginCapability.FILE_HANDLER,
        PluginCapability.UI_EXTENSION,
        PluginCapability.CONTEXT_MENU,
        PluginCapability.SIDEBAR
    ]

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.git_executable = config.get("git_executable", "git")
        self.show_status_icons = config.get("show_status_icons", True)
        self.auto_fetch = config.get("auto_fetch", False)
        self.fetch_interval = config.get("fetch_interval", 300)  # 5 minutes

        self._git_repos = {}  # Cache for git repositories
        self._file_status_cache = {}  # Cache for file status

    @classmethod
    def get_config_schema(cls) -> PluginConfigSchema:
        """Get plugin configuration schema"""
        schema = PluginConfigSchema("git_integration")

        schema.add_string_option(
            "git_executable",
            default="git",
            description="Path to git executable",
            required=False
        )

        schema.add_bool_option(
            "show_status_icons",
            default=True,
            description="Show git status icons in file list",
            required=False
        )

        schema.add_bool_option(
            "auto_fetch",
            default=False,
            description="Automatically fetch from remote",
            required=False
        )

        schema.add_int_option(
            "fetch_interval",
            default=300,
            description="Auto-fetch interval in seconds",
            required=False,
            min_value=60,
            max_value=3600
        )

        return schema

    def initialize(self) -> bool:
        """Initialize the plugin"""
        self.logger.info("Initializing Git Integration plugin")

        # Check if git is available
        try:
            subprocess.run([self.git_executable, "--version"],
                         capture_output=True, check=True)
            self.logger.info("Git executable found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.logger.error("Git executable not found")
            return False

        # Subscribe to events
        self.event_manager.subscribe("directory_changed", self._on_directory_changed)
        self.event_manager.subscribe("file_modified", self._on_file_modified)

        # Start auto-fetch if enabled
        if self.auto_fetch:
            asyncio.create_task(self._auto_fetch_loop())

        return True

    def cleanup(self) -> None:
        """Clean up plugin resources"""
        self.logger.info("Cleaning up Git Integration plugin")
        self._git_repos.clear()
        self._file_status_cache.clear()

    def can_handle_file(self, file_info: FileInfo) -> bool:
        """Check if file is in a git repository"""
        return self._find_git_repo(file_info.path) is not None

    def get_context_menu_items(self, file_info: FileInfo) -> List[Dict[str, Any]]:
        """Get git-related context menu items"""
        if not self.can_handle_file(file_info):
            return []

        items = [
            {
                "label": "Git Status",
                "action": "git_status",
                "icon": "📊",
                "callback": lambda: self._show_git_status(file_info)
            },
            {
                "label": "Git Log",
                "action": "git_log",
                "icon": "📜",
                "callback": lambda: self._show_git_log(file_info)
            }
        ]

        # Add more items based on file status
        status = self._get_file_status(file_info.path)
        if status == "modified":
            items.append({
                "label": "Git Diff",
                "action": "git_diff",
                "icon": "🔍",
                "callback": lambda: self._show_git_diff(file_info)
            })

        if status in ["modified", "new"]:
            items.append({
                "label": "Git Add",
                "action": "git_add",
                "icon": "➕",
                "callback": lambda: self._git_add(file_info)
            })

        return items

    def get_file_status_icon(self, file_info: FileInfo) -> Optional[str]:
        """Get git status icon for file"""
        if not self.show_status_icons or not self.can_handle_file(file_info):
            return None

        status = self._get_file_status(file_info.path)
        status_icons = {
            "modified": "📝",
            "new": "🆕",
            "deleted": "🗑️",
            "renamed": "📋",
            "staged": "✅",
            "conflict": "⚠️"
        }

        return status_icons.get(status)

    def create_sidebar_panel(self) -> Optional[Dict[str, Any]]:
        """Create git sidebar panel"""
        return {
            "title": "Git",
            "content_provider": self._render_git_panel,
            "position": 2
        }

    # Private methods

    def _find_git_repo(self, path: Path) -> Optional[Path]:
        """Find git repository root for given path"""
        current = path if path.is_dir() else path.parent

        while current != current.parent:
            git_dir = current / ".git"
            if git_dir.exists():
                return current
            current = current.parent

        return None

    def _get_file_status(self, file_path: Path) -> Optional[str]:
        """Get git status for file"""
        repo_root = self._find_git_repo(file_path)
        if not repo_root:
            return None

        # Check cache first
        cache_key = str(file_path)
        if cache_key in self._file_status_cache:
            return self._file_status_cache[cache_key]

        try:
            # Get relative path from repo root
            rel_path = file_path.relative_to(repo_root)

            # Run git status
            result = subprocess.run(
                [self.git_executable, "status", "--porcelain", str(rel_path)],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout.strip():
                status_code = result.stdout[0]
                status_map = {
                    'M': 'modified',
                    'A': 'staged',
                    'D': 'deleted',
                    'R': 'renamed',
                    '?': 'new',
                    'U': 'conflict'
                }
                status = status_map.get(status_code, 'unknown')
            else:
                status = 'clean'

            # Cache the result
            self._file_status_cache[cache_key] = status
            return status

        except (subprocess.CalledProcessError, ValueError):
            return None

    def _render_git_panel(self) -> str:
        """Render git information panel"""
        current_dir = self.ui_api.get_current_directory()
        repo_root = self._find_git_repo(current_dir)

        if not repo_root:
            return "Not a git repository"

        try:
            # Get current branch
            result = subprocess.run(
                [self.git_executable, "branch", "--show-current"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = result.stdout.strip()

            # Get status summary
            result = subprocess.run(
                [self.git_executable, "status", "--porcelain"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            modified_files = len([line for line in result.stdout.split('\n')
                                if line.startswith(' M')])
            new_files = len([line for line in result.stdout.split('\n')
                           if line.startswith('??')])
            staged_files = len([line for line in result.stdout.split('\n')
                              if line.startswith('A ')])

            panel_content = f"""
Branch: {current_branch}
Modified: {modified_files}
New: {new_files}
Staged: {staged_files}
"""
            return panel_content.strip()

        except subprocess.CalledProcessError:
            return "Error getting git status"

    def _show_git_status(self, file_info: FileInfo) -> None:
        """Show git status for file"""
        repo_root = self._find_git_repo(file_info.path)
        if not repo_root:
            return

        try:
            result = subprocess.run(
                [self.git_executable, "status", str(file_info.path.relative_to(repo_root))],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            self.ui_api.show_dialog(
                "Git Status",
                result.stdout,
                [{"label": "OK", "action": "close"}]
            )

        except subprocess.CalledProcessError as e:
            self.ui_api.show_notification(f"Git error: {e}", "error")

    def _show_git_log(self, file_info: FileInfo) -> None:
        """Show git log for file"""
        repo_root = self._find_git_repo(file_info.path)
        if not repo_root:
            return

        try:
            result = subprocess.run(
                [self.git_executable, "log", "--oneline", "-10",
                 str(file_info.path.relative_to(repo_root))],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            self.ui_api.show_dialog(
                "Git Log",
                result.stdout,
                [{"label": "OK", "action": "close"}]
            )

        except subprocess.CalledProcessError as e:
            self.ui_api.show_notification(f"Git error: {e}", "error")

    def _show_git_diff(self, file_info: FileInfo) -> None:
        """Show git diff for file"""
        repo_root = self._find_git_repo(file_info.path)
        if not repo_root:
            return

        try:
            result = subprocess.run(
                [self.git_executable, "diff", str(file_info.path.relative_to(repo_root))],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            self.ui_api.show_dialog(
                "Git Diff",
                result.stdout,
                [{"label": "OK", "action": "close"}]
            )

        except subprocess.CalledProcessError as e:
            self.ui_api.show_notification(f"Git error: {e}", "error")

    def _git_add(self, file_info: FileInfo) -> None:
        """Add file to git staging area"""
        repo_root = self._find_git_repo(file_info.path)
        if not repo_root:
            return

        try:
            subprocess.run(
                [self.git_executable, "add", str(file_info.path.relative_to(repo_root))],
                cwd=repo_root,
                check=True
            )

            # Clear cache for this file
            cache_key = str(file_info.path)
            if cache_key in self._file_status_cache:
                del self._file_status_cache[cache_key]

            self.ui_api.show_notification("File added to git staging area", "success")
            self.ui_api.refresh_view()

        except subprocess.CalledProcessError as e:
            self.ui_api.show_notification(f"Git error: {e}", "error")

    def _on_directory_changed(self, event) -> None:
        """Handle directory change event"""
        # Clear file status cache when directory changes
        self._file_status_cache.clear()

    def _on_file_modified(self, event) -> None:
        """Handle file modification event"""
        # Clear cache for modified file
        file_path = event.data.get("file_path")
        if file_path:
            cache_key = str(file_path)
            if cache_key in self._file_status_cache:
                del self._file_status_cache[cache_key]

    async def _auto_fetch_loop(self) -> None:
        """Auto-fetch loop"""
        while True:
            await asyncio.sleep(self.fetch_interval)

            # Fetch from all known repositories
            for repo_root in self._git_repos.keys():
                try:
                    subprocess.run(
                        [self.git_executable, "fetch"],
                        cwd=repo_root,
                        capture_output=True,
                        check=True
                    )
                    self.logger.debug(f"Auto-fetched from {repo_root}")
                except subprocess.CalledProcessError:
                    self.logger.warning(f"Failed to fetch from {repo_root}")
```

This comprehensive API reference provides everything needed to develop plugins and integrate with LaxyFile's core functionality. The examples show real-world usage patterns and best practices for plugin development.
