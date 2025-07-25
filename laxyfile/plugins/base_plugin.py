"""
Base Plugin System

This module provides the base plugin class and interfaces that all plugins
must implement to integrate with LaxyFile.
"""

import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json

from ..core.exceptions import PluginError
from ..utils.logger import Logger


class PluginType(Enum):
    """Types of plugins"""
    FILE_HANDLER = "file_handler"
    PREVIEW_RENDERER = "preview_renderer"
    THEME_PROVIDER = "theme_provider"
    COMMAND_EXTENSION = "command_extension"
    UI_COMPONENT = "ui_component"
    INTEGRATION = "integration"
    UTILITY = "utility"


class PluginCapability(Enum):
    """Plugin capabilities"""
    FILE_OPERATIONS = "file_operations"
    PREVIEW_GENERATION = "preview_generation"
    THEME_CUSTOMIZATION = "theme_customization"
    COMMAND_PROCESSING = "command_processing"
    UI_EXTENSION = "ui_extension"
    EXTERNAL_INTEGRATION = "external_integration"
    AUTOMATION = "automation"
    ANALYSIS = "analysis"


class PluginPriority(Enum):
    """Plugin execution priority"""
    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100


@dataclass
class PluginMetadata:
    """Plugin metadata information"""
    name: str
    version: str
    author: str
    description: str
    plugin_type: PluginType
    capabilities: Set[PluginCapability]

    # Optional metadata
    homepage: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    min_laxyfile_version: Optional[str] = None
    max_laxyfile_version: Optional[str] = None

    # Runtime metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'version': self.version,
            'author': self.author,
            'description': self.description,
            'plugin_type': self.plugin_type.value,
            'capabilities': [cap.value for cap in self.capabilities],
            'homepage': self.homepage,
            'license': self.license,
            'tags': self.tags,
            'dependencies': self.dependencies,
            'min_laxyfile_version': self.min_laxyfile_version,
            'max_laxyfile_version': self.max_laxyfile_version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Create from dictionary"""
        return cls(
            name=data['name'],
            version=data['version'],
            author=data['author'],
            description=data['description'],
            plugin_type=PluginType(data['plugin_type']),
            capabilities={PluginCapability(cap) for cap in data.get('capabilities', [])},
            homepage=data.get('homepage'),
            license=data.get('license'),
            tags=data.get('tags', []),
            dependencies=data.get('dependencies', []),
            min_laxyfile_version=data.get('min_laxyfile_version'),
            max_laxyfile_version=data.get('max_laxyfile_version'),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
        )


@dataclass
class PluginConfig:
    """Plugin configuration"""
    enabled: bool = True
    priority: PluginPriority = PluginPriority.NORMAL
    settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'enabled': self.enabled,
            'priority': self.priority.value,
            'settings': self.settings
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginConfig':
        """Create from dictionary"""
        return cls(
            enabled=data.get('enabled', True),
            priority=PluginPriority(data.get('priority', PluginPriority.NORMAL.value)),
            settings=data.get('settings', {})
        )


class PluginHook:
    """Plugin hook for extending functionality"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.callbacks: List[Callable] = []
        self.logger = Logger()

    def register(self, callback: Callable, priority: int = 50):
        """Register a callback for this hook"""
        self.callbacks.append((callback, priority))
        # Sort by priority (higher priority first)
        self.callbacks.sort(key=lambda x: x[1], reverse=True)

    def unregister(self, callback: Callable):
        """Unregister a callback"""
        self.callbacks = [(cb, pri) for cb, pri in self.callbacks if cb != callback]

    async def execute(self, *args, **kwargs) -> List[Any]:
        """Execute all registered callbacks"""
        results = []

        for callback, priority in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    result = await callback(*args, **kwargs)
                else:
                    result = callback(*args, **kwargs)
                results.append(result)
            except Exception:
                      self.logger.error(f"Error executing hook '{self.name}' callback: {e}")

        return results

    def execute_sync(self, *args, **kwargs) -> List[Any]:
        """Execute all registered callbacks synchronously"""
        results = []

        for callback, priority in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    self.logger.warning(f"Skipping async callback in sync hook execution: {callback}")
                    continue

                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error executing hook '{self.name}' callback: {e}")

        return results


class BasePlugin(ABC):
    """Base class for all LaxyFile plugins"""

    def __init__(self, plugin_dir: Path, config: PluginConfig):
        self.plugin_dir = Path(plugin_dir)
        self.config = config
        self.logger = Logger()

        # Plugin state
        self.is_loaded = False
        self.is_enabled = config.enabled
        self.load_time: Optional[datetime] = None
        self.error_count = 0
        self.last_error: Optional[str] = None

        # Plugin API will be injected by the plugin manager
        self.api: Optional['PluginAPI'] = None

        # Hooks this plugin provides
        self.hooks: Dict[str, PluginHook] = {}

        # Initialize plugin-specific setup
        self._initialize()

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin metadata - must be implemented by subclasses"""
        pass

    def _initialize(self):
        """Initialize plugin-specific setup - can be overridden"""
        pass

    async def load(self) -> bool:
        """Load the plugin"""
        try:
            if self.is_loaded:
                return True

            # Perform plugin-specific loading
            success = await self._load()

            if success:
                self.is_loaded = True
                self.load_time = datetime.now()
                self.logger.info(f"Plugin '{self.metadata.name}' loaded successfully")
            else:
                self.logger.error(f"Plugin '{self.metadata.name}' failed to load")

            return success

        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.logger.error(f"Error loading plugin '{self.metadata.name}': {e}")
            return False

    async def unload(self) -> bool:
        """Unload the plugin"""
        try:
            if not self.is_loaded:
                return True

            # Perform plugin-specific unloading
            success = await self._unload()

            if success:
                self.is_loaded = False
                self.load_time = None
                self.logger.info(f"Plugin '{self.metadata.name}' unloaded successfully")
            else:
                self.logger.error(f"Plugin '{self.metadata.name}' failed to unload")

            return success

        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.logger.error(f"Error unloading plugin '{self.metadata.name}': {e}")
            return False

    async def enable(self) -> bool:
        """Enable the plugin"""
        try:
            if self.is_enabled:
                return True

            # Load if not already loaded
            if not self.is_loaded:
                if not await self.load():
                    return False

            # Perform plugin-specific enabling
            success = await self._enable()

            if success:
                self.is_enabled = True
                self.config.enabled = True
                self.logger.info(f"Plugin '{self.metadata.name}' enabled")

            return success

        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.logger.error(f"Error enabling plugin '{self.metadata.name}': {e}")
            return False

    async def disable(self) -> bool:
        """Disable the plugin"""
        try:
            if not self.is_enabled:
                return True

            # Perform plugin-specific disabling
            success = await self._disable()

            if success:
                self.is_enabled = False
                self.config.enabled = False
                self.logger.info(f"Plugin '{self.metadata.name}' disabled")

            return success

        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.logger.error(f"Error disabling plugin '{self.metadata.name}': {e}")
            return False

    @abstractmethod
    async def _load(self) -> bool:
        """Plugin-specific loading logic - must be implemented"""
        pass

    @abstractmethod
    async def _unload(self) -> bool:
        """Plugin-specific unloading logic - must be implemented"""
        pass

    async def _enable(self) -> bool:
        """Plugin-specific enabling logic - can be overridden"""
        return True

    async def _disable(self) -> bool:
        """Plugin-specific disabling logic - can be overridden"""
        return True

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get plugin setting"""
        return self.config.settings.get(key, default)

    def set_setting(self, key: str, value: Any):
        """Set plugin setting"""
        self.config.settings[key] = value

    def create_hook(self, name: str, description: str = "") -> PluginHook:
        """Create a new hook"""
        hook = PluginHook(name, description)
        self.hooks[name] = hook
        return hook

    def get_hook(self, name: str) -> Optional[PluginHook]:
        """Get a hook by name"""
        return self.hooks.get(name)

    def register_hook_callback(self, hook_name: str, callback: Callable, priority: int = 50):
        """Register a callback for a hook"""
        if self.api:
            self.api.register_hook_callback(hook_name, callback, priority)

    def get_resource_path(self, resource_name: str) -> Path:
        """Get path to plugin resource"""
        return self.plugin_dir / "resources" / resource_name

    def get_data_path(self, data_name: str) -> Path:
        """Get path to plugin data file"""
        data_dir = self.plugin_dir / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir / data_name

    def save_data(self, data_name: str, data: Any):
        """Save plugin data"""
        try:
            data_path = self.get_data_path(data_name)

            if isinstance(data, (dict, list)):
                data_path.write_text(json.dumps(data, indent=2))
            else:
                data_path.write_text(str(data))

        except Exception as e:
            self.logger.error(f"Error saving plugin data '{data_name}': {e}")

    def load_data(self, data_name: str, default: Any = None) -> Any:
        """Load plugin data"""
        try:
            data_path = self.get_data_path(data_name)

            if not data_path.exists():
                return default

            content = data_path.read_text()

            # Try to parse as JSON first
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return content

        except Exception as e:
            self.logger.error(f"Error loading plugin data '{data_name}': {e}")
            return default

    def get_status(self) -> Dict[str, Any]:
        """Get plugin status information"""
        return {
            'name': self.metadata.name,
            'version': self.metadata.version,
            'type': self.metadata.plugin_type.value,
            'is_loaded': self.is_loaded,
            'is_enabled': self.is_enabled,
            'load_time': self.load_time.isoformat() if self.load_time else None,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'capabilities': [cap.value for cap in self.metadata.capabilities],
            'priority': self.config.priority.value
        }

    def __str__(self) -> str:
        """String representation"""
        return f"{self.metadata.name} v{self.metadata.version} ({self.metadata.plugin_type.value})"

    def __repr__(self) -> str:
        """Detailed representation"""
        return f"<{self.__class__.__name__}: {self}>"


# Specialized plugin base classes for common plugin types

class FileHandlerPlugin(BasePlugin):
    """Base class for file handler plugins"""

    @property
    def metadata(self) -> PluginMetadata:
        """Default metadata for file handler plugins"""
        return PluginMetadata(
            name="File Handler Plugin",
            version="1.0.0",
            author="LaxyFile",
            description="Base file handler plugin",
            plugin_type=PluginType.FILE_HANDLER,
            capabilities={PluginCapability.FILE_OPERATIONS}
        )

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Check if this plugin can handle the file"""
        pass

    @abstractmethod
    async def handle_file(self, file_path: Path, action: str, **kwargs) -> Any:
        """Handle file operation"""
        pass


class PreviewRendererPlugin(BasePlugin):
    """Base class for preview renderer plugins"""

    @property
    def metadata(self) -> PluginMetadata:
        """Default metadata for preview renderer plugins"""
        return PluginMetadata(
            name="Preview Renderer Plugin",
            version="1.0.0",
            author="LaxyFile",
            description="Base preview renderer plugin",
            plugin_type=PluginType.PREVIEW_RENDERER,
            capabilities={PluginCapability.PREVIEW_GENERATION}
        )

    @abstractmethod
    def can_preview(self, file_path: Path) -> bool:
        """Check if this plugin can preview the file"""
        pass

    @abstractmethod
    async def generate_preview(self, file_path: Path, **kwargs) -> Any:
        """Generate preview for file"""
        pass


class ThemeProviderPlugin(BasePlugin):
    """Base class for theme provider plugins"""

    @property
    def metadata(self) -> PluginMetadata:
        """Default metadata for theme provider plugins"""
        return PluginMetadata(
            name="Theme Provider Plugin",
            version="1.0.0",
            author="LaxyFile",
            description="Base theme provider plugin",
            plugin_type=PluginType.THEME_PROVIDER,
            capabilities={PluginCapability.THEME_CUSTOMIZATION}
        )

    @abstractmethod
    def get_themes(self) -> List[Dict[str, Any]]:
        """Get available themes from this provider"""
        pass

    @abstractmethod
    def get_theme(self, theme_id: str) -> Optional[Dict[str, Any]]:
        """Get specific theme by ID"""
        pass


class CommandExtensionPlugin(BasePlugin):
    """Base class for command extension plugins"""

    @property
    def metadata(self) -> PluginMetadata:
        """Default metadata for command extension plugins"""
        return PluginMetadata(
            name="Command Extension Plugin",
            version="1.0.0",
            author="LaxyFile",
            description="Base command extension plugin",
            plugin_type=PluginType.COMMAND_EXTENSION,
            capabilities={PluginCapability.COMMAND_PROCESSING}
        )

    @abstractmethod
    def get_commands(self) -> Dict[str, Callable]:
        """Get commands provided by this plugin"""
        pass

    @abstractmethod
    async def execute_command(self, command: str, args: List[str], **kwargs) -> Any:
        """Execute plugin command"""
        pass