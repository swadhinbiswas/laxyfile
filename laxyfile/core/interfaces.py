"""
Core Interfaces and Abstract Base Classes

This module defines the interfaces and abstract base classes for all major
components in LaxyFile, ensuring consistent APIs and enabling dependency injection.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator, Callable, Tuple
from pathlib import Path

from .types import (
    FileInfo, FileEvent, DirectoryStats, PreviewInfo, OperationResult,
    PanelData, SidebarData, StatusData, Theme, ArchiveFormat
)


class FileManagerInterface(ABC):
    """Interface for file management operations"""

    @abstractmethod
    async def list_directory(self, path: Path, show_hidden: bool = False) -> List[FileInfo]:
        """List directory contents with file information"""
        pass

    @abstractmethod
    async def get_file_info(self, path: Path) -> FileInfo:
        """Get detailed information about a file"""
        pass

    @abstractmethod
    async def watch_directory(self, path: Path) -> AsyncIterator[FileEvent]:
        """Watch directory for changes"""
        pass

    @abstractmethod
    def get_file_icon(self, file_info: FileInfo) -> str:
        """Get icon for file based on type"""
        pass

    @abstractmethod
    def get_file_preview(self, path: Path) -> PreviewInfo:
        """Get preview information for a file"""
        pass

    @abstractmethod
    async def analyze_directory_stats(self, path: Path) -> DirectoryStats:
        """Analyze directory statistics"""
        pass


class UIManagerInterface(ABC):
    """Interface for UI management and rendering"""

    @abstractmethod
    def create_layout(self):
        """Create the main UI layout"""
        pass

    @abstractmethod
    def render_file_panel(self, panel_data: PanelData):
        """Render a file panel"""
        pass

    @abstractmethod
    def render_sidebar(self, sidebar_data: SidebarData):
        """Render the sidebar"""
        pass

    @abstractmethod
    def render_footer(self, status_data: StatusData):
        """Render the footer"""
        pass

    @abstractmethod
    def handle_resize(self, width: int, height: int) -> None:
        """Handle terminal resize events"""
        pass

    @abstractmethod
    def apply_theme(self, theme_name: str) -> None:
        """Apply a theme to the UI"""
        pass


class OperationInterface(ABC):
    """Interface for file operations"""

    @abstractmethod
    async def copy_files(self, sources: List[Path], destination: Path,
                        progress_callback: Optional[Callable] = None) -> OperationResult:
        """Copy files to destination"""
        pass

    @abstractmethod
    async def move_files(self, sources: List[Path], destination: Path,
                        progress_callback: Optional[Callable] = None) -> OperationResult:
        """Move files to destination"""
        pass

    @abstractmethod
    async def delete_files(self, files: List[Path], use_trash: bool = True,
                          progress_callback: Optional[Callable] = None) -> OperationResult:
        """Delete files"""
        pass

    @abstractmethod
    def rename_file(self, old_path: Path, new_name: str) -> OperationResult:
        """Rename a file"""
        pass


class ArchiveOperationInterface(ABC):
    """Interface for archive operations"""

    @abstractmethod
    async def create_archive(self, files: List[Path], archive_path: Path,
                           format: ArchiveFormat, compression_level: int = 6) -> OperationResult:
        """Create an archive from files"""
        pass

    @abstractmethod
    async def extract_archive(self, archive_path: Path, destination: Path,
                            progress_callback: Optional[Callable] = None) -> OperationResult:
        """Extract an archive"""
        pass

    @abstractmethod
    def list_archive_contents(self, archive_path: Path) -> List[str]:
        """List contents of an archive"""
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[ArchiveFormat]:
        """Get list of supported archive formats"""
        pass


class PreviewInterface(ABC):
    """Interface for file preview generation"""

    @abstractmethod
    async def generate_preview(self, path: Path, max_width: int = 80,
                             max_height: int = 24) -> PreviewInfo:
        """Generate preview for a file"""
        pass

    @abstractmethod
    def supports_format(self, file_type: str) -> bool:
        """Check if format is supported for preview"""
        pass

    @abstractmethod
    async def get_metadata(self, path: Path) -> Dict[str, Any]:
        """Get metadata for a file"""
        pass


class ThemeInterface(ABC):
    """Interface for theme management"""

    @abstractmethod
    def load_theme(self, theme_name: str) -> Theme:
        """Load a theme by name"""
        pass

    @abstractmethod
    def apply_theme(self, theme: Theme) -> None:
        """Apply a theme"""
        pass

    @abstractmethod
    def get_available_themes(self) -> List[str]:
        """Get list of available themes"""
        pass

    @abstractmethod
    def create_custom_theme(self, base_theme: str, modifications: Dict[str, Any]) -> Theme:
        """Create a custom theme"""
        pass


class AIInterface(ABC):
    """Interface for AI assistant functionality"""

    @abstractmethod
    async def analyze_directory(self, path: Path, include_content: bool = False) -> Dict[str, Any]:
        """Analyze directory with AI"""
        pass

    @abstractmethod
    async def suggest_organization(self, path: Path) -> Dict[str, Any]:
        """Get AI suggestions for file organization"""
        pass

    @abstractmethod
    async def security_audit(self, path: Path) -> Dict[str, Any]:
        """Perform AI-powered security audit"""
        pass

    @abstractmethod
    async def chat_query(self, query: str, context: Dict[str, Any]) -> str:
        """Process a chat query with AI"""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if AI is properly configured"""
        pass


class ConfigInterface(ABC):
    """Interface for configuration management"""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        pass

    @abstractmethod
    def save(self) -> None:
        """Save configuration to disk"""
        pass

    @abstractmethod
    def load(self) -> None:
        """Load configuration from disk"""
        pass

    @abstractmethod
    def validate(self) -> List[str]:
        """Validate configuration and return errors"""
        pass


class PluginInterface(ABC):
    """Interface for plugin system"""

    @abstractmethod
    def load_plugin(self, plugin_path: Path) -> bool:
        """Load a plugin"""
        pass

    @abstractmethod
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        pass

    @abstractmethod
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugins"""
        pass

    @abstractmethod
    def call_plugin_hook(self, hook_name: str, *args, **kwargs) -> Any:
        """Call a plugin hook"""
        pass


class PlatformInterface(ABC):
    """Interface for platform-specific operations"""

    @abstractmethod
    def get_platform_name(self) -> str:
        """Get platform name"""
        pass

    @abstractmethod
    def open_file_with_default_app(self, path: Path) -> bool:
        """Open file with default application"""
        pass

    @abstractmethod
    def move_to_trash(self, path: Path) -> bool:
        """Move file to trash/recycle bin"""
        pass

    @abstractmethod
    def get_file_associations(self, extension: str) -> List[str]:
        """Get file associations for extension"""
        pass

    @abstractmethod
    def create_desktop_shortcut(self, name: str, target: Path, icon: Optional[Path] = None) -> bool:
        """Create desktop shortcut"""
        pass


class KeyboardInterface(ABC):
    """Interface for keyboard input handling"""

    @abstractmethod
    def register_hotkey(self, key_combination: str, callback: Callable) -> bool:
        """Register a hotkey"""
        pass

    @abstractmethod
    def unregister_hotkey(self, key_combination: str) -> bool:
        """Unregister a hotkey"""
        pass

    @abstractmethod
    def get_registered_hotkeys(self) -> Dict[str, Callable]:
        """Get all registered hotkeys"""
        pass

    @abstractmethod
    async def get_key_input(self) -> Optional[str]:
        """Get keyboard input"""
        pass


class CacheInterface(ABC):
    """Interface for caching system"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value with optional TTL"""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete cached value"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached values"""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        pass