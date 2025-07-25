"""
Type Definitions

This module contains all type definitions, data classes, and enums
used throughout LaxyFile for type safety and consistency.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union, Callable
from pathlib import Path
from datetime import datetime
from enum import Enum, auto


class FileType(Enum):
    """File type enumeration"""
    DIRECTORY = "directory"
    FILE = "file"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    ARCHIVE = "archive"
    CODE = "code"
    DOCUMENT = "document"
    EXECUTABLE = "executable"
    SYMLINK = "symlink"
    UNKNOWN = "unknown"


class ArchiveFormat(Enum):
    """Archive format enumeration"""
    ZIP = "zip"
    TAR = "tar"
    TAR_GZ = "tar.gz"
    TAR_BZ2 = "tar.bz2"
    TAR_XZ = "tar.xz"
    SEVEN_ZIP = "7z"
    RAR = "rar"


class OperationStatus(Enum):
    """Operation status enumeration"""
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class SortType(Enum):
    """File sorting type enumeration"""
    NAME = auto()
    SIZE = auto()
    MODIFIED = auto()
    TYPE = auto()
    EXTENSION = auto()


class PreviewType(Enum):
    """Preview type enumeration"""
    NONE = "none"
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    ARCHIVE = "archive"
    DOCUMENT = "document"


@dataclass
class FileInfo:
    """Basic file information"""
    path: Path
    name: str
    size: int
    modified: datetime
    is_dir: bool
    is_symlink: bool
    file_type: str
    permissions: str = ""
    mime_type: Optional[str] = None


@dataclass
class EnhancedFileInfo(FileInfo):
    """Enhanced file information with additional metadata"""
    icon: str = ""
    color: str = ""
    preview_available: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    category: str = ""
    duplicate_group: Optional[str] = None
    security_flags: List[str] = field(default_factory=list)


@dataclass
class FileEvent:
    """File system event"""
    path: Path
    event_type: str
    is_directory: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DirectoryStats:
    """Directory statistics"""
    total_files: int = 0
    total_directories: int = 0
    total_size: int = 0
    file_types: Dict[str, int] = field(default_factory=dict)
    largest_files: List[Dict[str, Any]] = field(default_factory=list)
    oldest_files: List[Dict[str, Any]] = field(default_factory=list)
    newest_files: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PreviewInfo:
    """File preview information"""
    available: bool
    preview_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    thumbnail: Optional[str] = None
    error: Optional[str] = None


@dataclass
class OperationResult:
    """Result of a file operation"""
    success: bool
    message: str
    affected_files: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    progress: float = 0.0
    duration: float = 0.0
    bytes_processed: int = 0


@dataclass
class OperationError:
    """Error during file operation"""
    path: Path
    error_type: str
    message: str
    recoverable: bool = False


@dataclass
class PanelData:
    """Data for file panel rendering"""
    path: Path
    files: List[FileInfo]
    current_selection: int
    selected_files: List[Path]
    sort_type: SortType
    sort_reverse: bool
    show_hidden: bool
    search_query: str = ""


@dataclass
class SidebarData:
    """Data for sidebar rendering"""
    current_path: Path
    bookmarks: List[Path]
    recent_paths: List[Path]
    drives: List[Dict[str, Any]]
    system_info: Dict[str, Any]


@dataclass
class StatusData:
    """Data for status bar rendering"""
    current_file: Optional[FileInfo]
    selected_count: int
    total_files: int
    total_size: int
    operation_status: Optional[str]
    ai_status: str


@dataclass
class Theme:
    """Theme configuration"""
    name: str
    colors: Dict[str, str]
    styles: Dict[str, str]
    icons: Dict[str, str]
    borders: Dict[str, str]


@dataclass
class HotkeyMapping:
    """Hotkey mapping configuration"""
    key_combination: str
    action: str
    description: str
    context: str = "global"


@dataclass
class PluginInfo:
    """Plugin information"""
    name: str
    version: str
    description: str
    author: str
    path: Path
    enabled: bool
    dependencies: List[str] = field(default_factory=list)


@dataclass
class AIAnalysisResult:
    """Result of AI analysis"""
    analysis_type: str
    timestamp: datetime
    summary: str
    recommendations: List[str]
    insights: List[str]
    actions: List[str]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityFlag:
    """Security analysis flag"""
    flag_type: str
    severity: str  # low, medium, high, critical
    description: str
    recommendation: str
    file_path: Optional[Path] = None


@dataclass
class PerformanceMetric:
    """Performance measurement"""
    operation: str
    duration: float
    memory_used: int
    cpu_percent: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created: datetime
    accessed: datetime
    ttl: Optional[int] = None
    size: int = 0


@dataclass
class ConfigSection:
    """Configuration section"""
    name: str
    values: Dict[str, Any]
    schema: Optional[Dict[str, Any]] = None
    description: str = ""


@dataclass
class LogEntry:
    """Log entry"""
    timestamp: datetime
    level: str
    message: str
    module: str
    function: str
    line_number: int
    extra_data: Dict[str, Any] = field(default_factory=dict)


# Type aliases for better readability
FilePath = Union[str, Path]
FileList = List[FileInfo]
ProgressCallback = Callable[[float, str], None]
ErrorCallback = Callable[[Exception], None]
EventCallback = Callable[[FileEvent], None]


# Constants
DEFAULT_CACHE_TTL = 300  # 5 minutes
MAX_PREVIEW_SIZE = 1024 * 1024  # 1MB
MAX_DIRECTORY_ITEMS = 10000
DEFAULT_THEME = "cappuccino"
CONFIG_FILE_NAME = "config.yaml"
CACHE_DIR_NAME = ".cache"
PLUGINS_DIR_NAME = "plugins"
THEMES_DIR_NAME = "themes"