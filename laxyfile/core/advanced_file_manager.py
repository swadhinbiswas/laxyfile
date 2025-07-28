"""
Advanced File Manager

Enhanced file management system with SuperFile-inspired features,
performance optimizations, and comprehensive metadata handling.
"""

import asyncio
import os
import stat
import mimetypes
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncIterator, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, OrderedDict

from .interfaces import FileManagerInterface, CacheInterface
from .types import FileInfo, FileEvent, DirectoryStats, PreviewInfo, SortType
from .exceptions import FileOperationError, PermissionError as LaxyPermissionError
from .file_type_detector import AdvancedFileTypeDetector, IconStyle
from .performance_optimizer import PerformanceOptimizer, PerformanceConfig
from ..utils.logger import Logger


@dataclass
class EnhancedFileInfo(FileInfo):
    """Enhanced file information with additional metadata"""
    owner: str = ""
    group: str = ""
    permissions_octal: str = ""
    is_hidden: bool = False
    icon: str = ""
    preview_available: bool = False
    security_flags: List[str] = None
    ai_tags: List[str] = None

    def __post_init__(self):
        if self.security_flags is None:
            self.security_flags = []
        if self.ai_tags is None:
            self.ai_tags = []


class LRUCache:
    """Simple LRU cache implementation"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()

    def get(self, key: str) -> Optional[Tuple[Any, datetime]]:
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: Any, timestamp: datetime = None) -> None:
        if timestamp is None:
            timestamp = datetime.now()

        if key in self.cache:
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.max_size:
            # Remove least recently used
            self.cache.popitem(last=False)

        self.cache[key] = (value, timestamp)

    def clear(self) -> None:
        self.cache.clear()

    def size(self) -> int:
        return len(self.cache)


class AdvancedFileManager(FileManagerInterface):
    """Advanced file manager with enhanced capabilities and performance optimizations"""

    def __init__(self, config):
        self.config = config
        self.logger = Logger()

        # Enhanced caching system
        cache_size = getattr(config, 'cache_size', 1000)
        self._file_cache = LRUCache(cache_size)
        self._directory_cache = LRUCache(cache_size // 2)
        self._stats_cache = LRUCache(cache_size // 4)

        # File watching
        self._watch_tasks = {}
        self._observers = {}

        # Performance tracking
        self._performance_stats = defaultdict(list)

        # Initialize advanced file type detector
        use_magic = config.get('ui.use_magic_detection', True)
        self.file_type_detector = AdvancedFileTypeDetector(use_magic=use_magic)

        # Determine icon style based on configuration
        if config.get('ui.use_nerd_fonts', False):
            self.icon_style = IconStyle.NERD_FONT
        elif config.get('ui.use_ascii_icons', False):
            self.icon_style = IconStyle.ASCII
        else:
            self.icon_style = IconStyle.UNICODE

        # Initialize performance optimizer
        perf_config = PerformanceConfig(
            max_concurrent_operations=config.get('performance.max_concurrent_operations', 10),
            chunk_size=config.get('performance.chunk_size', 100),
            memory_threshold_mb=config.get('performance.memory_threshold_mb', 500),
            lazy_loading_threshold=config.get('performance.lazy_loading_threshold', 1000),
            background_processing=config.get('performance.background_processing', True),
            use_threading=config.get('performance.use_threading', True),
            max_worker_threads=config.get('performance.max_worker_threads', 4)
        )
        self.performance_optimizer = PerformanceOptimizer(perf_config)

        # Callback registration for component integration
        self.change_callbacks: List[Callable] = []
        self.directory_change_callbacks: List[Callable] = []

    def register_change_callback(self, callback: Callable) -> None:
        """Register a callback for file change events"""
        self.change_callbacks.append(callback)

    def register_directory_change_callback(self, callback: Callable) -> None:
        """Register a callback for directory change events"""
        self.directory_change_callbacks.append(callback)

    def _notify_change_callbacks(self, file_path: Path) -> None:
        """Notify all change callbacks"""
        for callback in self.change_callbacks:
            try:
                callback(file_path)
            except Exception as e:
                self.logger.error(f"Error in change callback: {e}")

    def _notify_directory_change_callbacks(self, directory_path: Path) -> None:
        """Notify all directory change callbacks"""
        for callback in self.directory_change_callbacks:
            try:
                callback(directory_path)
            except Exception as e:
                self.logger.error(f"Error in directory change callback: {e}")

    async def initialize(self) -> None:
        """Initialize the advanced file manager"""
        try:
            self.logger.info("Initializing AdvancedFileManager")

            # Initialize file type detector
            if hasattr(self.file_type_detector, 'initialize'):
                await self.file_type_detector.initialize()

            # Initialize performance optimizer
            if hasattr(self.performance_optimizer, 'initialize'):
                await self.performance_optimizer.initialize()

            # Clear caches to start fresh
            self.invalidate_cache()

            self.logger.info("AdvancedFileManager initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize AdvancedFileManager: {e}")
            raise

    async def list_directory(self, path: Path, show_hidden: bool = False,
                           sort_type: SortType = SortType.NAME, reverse: bool = False,
                           filter_pattern: str = "", lazy_load: bool = False,
                           chunk_size: int = None) -> List[EnhancedFileInfo]:
        """List directory contents with enhanced file information and performance optimizations"""
        start_time = time.time()

        try:
            # Check cache first
            cache_key = f"{path}:{show_hidden}:{sort_type}:{reverse}:{filter_pattern}"
            cached_result = self._directory_cache.get(cache_key)
            if cached_result:
                cached_files, cache_time = cached_result
                # Use cache if less than 3 seconds old for better performance
                if (datetime.now() - cache_time).seconds < 3:
                    return cached_files

            files = []

            # Add parent directory entry if not root
            if path.parent != path:
                parent_info = EnhancedFileInfo(
                    path=path.parent,
                    name="..",
                    size=0,
                    modified=datetime.now(),
                    is_dir=True,
                    is_symlink=False,
                    file_type="directory",
                    icon="📁"
                )
                files.append(parent_info)

            # List directory contents with performance optimization
            try:
                items = list(path.iterdir())
                item_count = len(items)

                # Performance optimization for large directories
                max_items = self.config.get('ui.max_files_display', 1000)
                if item_count > max_items:
                    self.logger.warning(f"Directory has {item_count} items, limiting to {max_items}")
                    items = items[:max_items]

                # Adaptive chunk size based on directory size
                if chunk_size is None:
                    if item_count > 10000:
                        chunk_size = 50
                    elif item_count > 1000:
                        chunk_size = 100
                    else:
                        chunk_size = 200

                # Filter items early to reduce processing
                filtered_items = []
                for item in items:
                    # Skip hidden files if not requested
                    if not show_hidden and item.name.startswith('.'):
                        continue

                    # Apply filter pattern
                    if filter_pattern and filter_pattern.lower() not in item.name.lower():
                        continue

                    filtered_items.append(item)

                # Process items in chunks for better memory management
                if lazy_load and len(filtered_items) > chunk_size:
                    # Process first chunk immediately, rest in background
                    immediate_items = filtered_items[:chunk_size]
                    background_items = filtered_items[chunk_size:]

                    # Process immediate items
                    tasks = [self.get_file_info(item) for item in immediate_items]
                    file_infos = await asyncio.gather(*tasks, return_exceptions=True)

                    # Add valid file infos
                    for file_info in file_infos:
                        if not isinstance(file_info, Exception):
                            files.append(file_info)

                    # Schedule background processing
                    if background_items and hasattr(self.performance_optimizer, 'submit_background_task'):
                        self.performance_optimizer.submit_background_task(
                            'file_processing',
                            self._process_background_items,
                            background_items, cache_key
                        )
                else:
                    # Process all items concurrently with chunking
                    for i in range(0, len(filtered_items), chunk_size):
                        chunk = filtered_items[i:i + chunk_size]
                        tasks = [self.get_file_info(item) for item in chunk]

                        # Process chunk
                        file_infos = await asyncio.gather(*tasks, return_exceptions=True)

                        # Add valid file infos
                        for file_info in file_infos:
                            if not isinstance(file_info, Exception):
                                files.append(file_info)

                        # Small delay between chunks for large directories
                        if item_count > 5000 and i + chunk_size < len(filtered_items):
                            await asyncio.sleep(0.001)  # 1ms delay

            except PermissionError:
                self.logger.warning(f"Permission denied accessing {path}")
                raise LaxyPermissionError(path, "list_directory")

            # Sort files
            files = self._sort_files(files, sort_type, reverse)

            # Cache the result with shorter TTL for large directories
            cache_ttl = 1 if item_count > 5000 else 3
            self._directory_cache.set(cache_key, files, datetime.now())

            # Track performance
            duration = time.time() - start_time
            self._performance_stats['list_directory'].append(duration)

            # Log performance for large directories
            if item_count > 1000:
                self.logger.debug(f"Listed {item_count} items in {duration:.3f}s")

            return files

        except Exception as e:
            self.logger.error(f"Error listing directory {path}: {e}")
            if isinstance(e, LaxyPermissionError):
                raise
            raise FileOperationError("list_directory", path, str(e), e)

    async def get_file_info(self, path: Path) -> EnhancedFileInfo:
        """Get comprehensive file information"""
        try:
            # Check cache first
            if str(path) in self._file_cache:
                cached_info, cache_time = self._file_cache[str(path)]
                # Use cache if file hasn't been modified since cache time
                if path.stat().st_mtime <= cache_time.timestamp():
                    return cached_info

            stat_info = path.stat()

            # Basic file information
            file_info = EnhancedFileInfo(
                path=path,
                name=path.name,
                size=stat_info.st_size,
                modified=datetime.fromtimestamp(stat_info.st_mtime),
                is_dir=path.is_dir(),
                is_symlink=path.is_symlink(),
                file_type=self._determine_file_type(path),
                permissions_octal=oct(stat_info.st_mode)[-3:],
                is_hidden=path.name.startswith('.')
            )

            # Add icon based on file type
            file_info.icon = self._get_file_icon(file_info)

            # Add owner/group information (Unix-like systems)
            try:
                import pwd
                import grp
                file_info.owner = pwd.getpwuid(stat_info.st_uid).pw_name
                file_info.group = grp.getgrgid(stat_info.st_gid).gr_name
            except (ImportError, KeyError):
                file_info.owner = str(stat_info.st_uid)
                file_info.group = str(stat_info.st_gid)

            # Check if preview is available
            file_info.preview_available = self._can_preview(file_info)

            # Add security flags
            file_info.security_flags = self._analyze_security(file_info, stat_info)

            # Cache the result
            self._file_cache[str(path)] = (file_info, datetime.now())

            return file_info

        except Exception as e:
            self.logger.error(f"Error getting file info for {path}: {e}")
            # Return minimal file info on error
            return EnhancedFileInfo(
                path=path,
                name=path.name,
                size=0,
                modified=datetime.now(),
                is_dir=False,
                is_symlink=False,
                file_type="unknown"
            )

    async def watch_directory(self, path: Path) -> AsyncIterator[FileEvent]:
        """Watch directory for changes"""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            class AsyncFileHandler(FileSystemEventHandler):
                def __init__(self, queue):
                    self.queue = queue

                def on_any_event(self, event):
                    file_event = FileEvent(
                        path=Path(event.src_path),
                        event_type=event.event_type,
                        is_directory=event.is_directory
                    )
                    asyncio.create_task(self.queue.put(file_event))

            queue = asyncio.Queue()
            handler = AsyncFileHandler(queue)
            observer = Observer()
            observer.schedule(handler, str(path), recursive=False)
            observer.start()

            try:
                while True:
                    event = await queue.get()
                    yield event
            finally:
                observer.stop()
                observer.join()

        except ImportError:
            self.logger.warning("Watchdog not available, directory watching disabled")
            return
        except Exception as e:
            self.logger.error(f"Error watching directory {path}: {e}")
            return

    def get_file_icon(self, file_info: EnhancedFileInfo) -> str:
        """Get icon for file based on type and properties"""
        return self._get_file_icon(file_info)

    def get_file_preview(self, path: Path) -> PreviewInfo:
        """Get preview information for a file"""
        # This will be implemented in the preview system
        return PreviewInfo(
            available=False,
            preview_type="none",
            content=""
        )

    async def analyze_directory_stats(self, path: Path) -> DirectoryStats:
        """Analyze directory statistics"""
        stats = DirectoryStats(
            total_files=0,
            total_directories=0,
            total_size=0,
            file_types={},
            largest_files=[],
            oldest_files=[],
            newest_files=[]
        )

        try:
            for item in path.rglob('*'):
                try:
                    if item.is_file():
                        stats.total_files += 1
                        stats.total_size += item.stat().st_size

                        # Track file types
                        file_type = self._determine_file_type(item)
                        stats.file_types[file_type] = stats.file_types.get(file_type, 0) + 1

                    elif item.is_dir():
                        stats.total_directories += 1

                except (PermissionError, OSError):
                    continue

        except Exception as e:
            self.logger.error(f"Error analyzing directory stats for {path}: {e}")

        return stats

    def _determine_file_type(self, path: Path) -> str:
        """Determine file type using the advanced file type detector"""
        try:
            file_type_info = self.file_type_detector.detect_file_type(path)
            return file_type_info.file_type.value
        except Exception as e:
            self.logger.error(f"Error detecting file type for {path}: {e}")
            return "unknown"

    def _get_file_icon(self, file_info: EnhancedFileInfo) -> str:
        """Get appropriate icon for file using the advanced file type detector"""
        try:
            file_type_info = self.file_type_detector.detect_file_type(file_info.path)
            return self.file_type_detector.get_icon(file_type_info, self.icon_style)
        except Exception as e:
            self.logger.error(f"Error getting icon for {file_info.path}: {e}")
            # Fallback to basic icon
            if file_info.is_symlink:
                return '🔗'
            elif file_info.is_dir:
                return '📁'
            else:
                return '📄'

    def _can_preview(self, file_info: EnhancedFileInfo) -> bool:
        """Check if file can be previewed"""
        previewable_types = ['image', 'video', 'audio', 'code', 'document']
        return file_info.file_type in previewable_types

    def _analyze_security(self, file_info: EnhancedFileInfo, stat_info) -> List[str]:
        """Analyze file for security issues"""
        flags = []

        # Check for overly permissive permissions
        if file_info.permissions_octal in ['777', '666']:
            flags.append('overly_permissive')

        # Check for suspicious extensions
        suspicious_extensions = ['.exe', '.bat', '.cmd', '.scr', '.vbs', '.js']
        if file_info.path.suffix.lower() in suspicious_extensions:
            flags.append('suspicious_extension')

        # Check for hidden executables
        if file_info.is_hidden and os.access(file_info.path, os.X_OK):
            flags.append('hidden_executable')

        return flags

    def _sort_files(self, files: List[EnhancedFileInfo], sort_type: SortType, reverse: bool) -> List[EnhancedFileInfo]:
        """Sort files based on the specified criteria"""
        # Always keep parent directory (..) at the top
        parent_dir = None
        other_files = []

        for file_info in files:
            if file_info.name == "..":
                parent_dir = file_info
            else:
                other_files.append(file_info)

        # Sort based on type
        if sort_type == SortType.NAME:
            # Sort by name, directories first
            other_files.sort(key=lambda f: (not f.is_dir, f.name.lower()), reverse=reverse)
        elif sort_type == SortType.SIZE:
            # Sort by size, directories first (size 0)
            other_files.sort(key=lambda f: (not f.is_dir, f.size), reverse=reverse)
        elif sort_type == SortType.MODIFIED:
            # Sort by modification time, directories first
            other_files.sort(key=lambda f: (not f.is_dir, f.modified), reverse=reverse)
        elif sort_type == SortType.TYPE:
            # Sort by file type, then name
            other_files.sort(key=lambda f: (not f.is_dir, f.file_type, f.name.lower()), reverse=reverse)
        elif sort_type == SortType.EXTENSION:
            # Sort by extension, then name
            other_files.sort(key=lambda f: (not f.is_dir, f.path.suffix.lower(), f.name.lower()), reverse=reverse)

        # Reconstruct the list with parent directory first
        result = []
        if parent_dir:
            result.append(parent_dir)
        result.extend(other_files)

        return result

    def invalidate_cache(self, path: Path = None) -> None:
        """Invalidate cache for a specific path or all caches"""
        if path:
            # Invalidate specific path caches
            path_str = str(path)

            # Remove from file cache
            if path_str in self._file_cache.cache:
                del self._file_cache.cache[path_str]

            # Remove from directory cache (all entries containing this path)
            keys_to_remove = []
            for key in self._directory_cache.cache:
                if path_str in key:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._directory_cache.cache[key]
        else:
            # Clear all caches
            self._file_cache.clear()
            self._directory_cache.clear()
            self._stats_cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'file_cache_size': self._file_cache.size(),
            'directory_cache_size': self._directory_cache.size(),
            'stats_cache_size': self._stats_cache.size(),
            'file_cache_max': self._file_cache.max_size,
            'directory_cache_max': self._directory_cache.max_size,
            'stats_cache_max': self._stats_cache.max_size
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}
        for operation, times in self._performance_stats.items():
            if times:
                stats[operation] = {
                    'count': len(times),
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'total_time': sum(times)
                }
        return stats

    async def search_files(self, path: Path, pattern: str, recursive: bool = False,
                          include_content: bool = False) -> List[EnhancedFileInfo]:
        """Search for files matching a pattern"""
        start_time = time.time()
        results = []

        try:
            if recursive:
                search_paths = path.rglob('*')
            else:
                search_paths = path.iterdir()

            for item in search_paths:
                try:
                    # Skip if no read permission
                    if not os.access(item, os.R_OK):
                        continue

                    # Check filename match
                    if pattern.lower() in item.name.lower():
                        file_info = await self.get_file_info(item)
                        results.append(file_info)
                        continue

                    # Check content match for text files if requested
                    if include_content and item.is_file() and item.stat().st_size < 1024 * 1024:  # Max 1MB
                        try:
                            with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read(10000)  # Read first 10KB
                                if pattern.lower() in content.lower():
                                    file_info = await self.get_file_info(item)
                                    results.append(file_info)
                        except (UnicodeDecodeError, PermissionError, OSError):
                            continue

                except (PermissionError, OSError):
                    continue

        except Exception as e:
            self.logger.error(f"Error searching files in {path}: {e}")

        # Track performance
        duration = time.time() - start_time
        self._performance_stats['search_files'].append(duration)

        return results

    async def get_directory_size(self, path: Path) -> int:
        """Get total size of directory recursively"""
        total_size = 0

        try:
            for item in path.rglob('*'):
                try:
                    if item.is_file():
                        total_size += item.stat().st_size
                except (PermissionError, OSError):
                    continue
        except Exception as e:
            self.logger.error(f"Error calculating directory size for {path}: {e}")

        return total_size

    def get_file_type_stats(self, files: List[EnhancedFileInfo]) -> Dict[str, int]:
        """Get statistics about file types in a list"""
        stats = defaultdict(int)

        for file_info in files:
            if file_info.name != "..":  # Skip parent directory
                stats[file_info.file_type] += 1

        return dict(stats)

    def filter_files(self, files: List[EnhancedFileInfo],
                    file_types: List[str] = None,
                    size_range: Tuple[int, int] = None,
                    date_range: Tuple[datetime, datetime] = None) -> List[EnhancedFileInfo]:
        """Filter files based on various criteria"""
        filtered = []

        for file_info in files:
            # Skip parent directory
            if file_info.name == "..":
                filtered.append(file_info)
                continue

            # Filter by file type
            if file_types and file_info.file_type not in file_types:
                continue

            # Filter by size range
            if size_range and not (size_range[0] <= file_info.size <= size_range[1]):
                continue

            # Filter by date range
            if date_range and not (date_range[0] <= file_info.modified <= date_range[1]):
                continue

            filtered.append(file_info)

        return filtered

    async def cleanup_cache(self) -> None:
        """Clean up expired cache entries"""
        current_time = datetime.now()
        cache_ttl = timedelta(minutes=5)  # 5 minute TTL

        # Clean file cache
        expired_keys = []
        for key, (value, timestamp) in self._file_cache.cache.items():
            if current_time - timestamp > cache_ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self._file_cache.cache[key]

        # Clean directory cache
        expired_keys = []
        for key, (value, timestamp) in self._directory_cache.cache.items():
            if current_time - timestamp > cache_ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self._directory_cache.cache[key]

        self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def _process_background_items(self, items: List[Path], cache_key: str) -> None:
        """Process background items for lazy loading"""
        try:
            # This would be called in a background thread
            background_files = []

            for item in items:
                try:
                    # Create a synchronous version of get_file_info for background processing
                    stat_info = item.stat()
                    file_info = EnhancedFileInfo(
                        path=item,
                        name=item.name,
                        size=stat_info.st_size,
                        modified=datetime.fromtimestamp(stat_info.st_mtime),
                        is_dir=item.is_dir(),
                        is_symlink=item.is_symlink(),
                        file_type=self._determine_file_type(item),
                        permissions_octal=oct(stat_info.st_mode)[-3:],
                        is_hidden=item.name.startswith('.')
                    )

                    # Add icon
                    file_info.icon = self._get_file_icon(file_info)
                    background_files.append(file_info)

                except Exception as e:
                    self.logger.error(f"Error processing background item {item}: {e}")
                    continue

            # Update cache with background results
            if background_files:
                cached_result = self._directory_cache.get(cache_key)
                if cached_result:
                    cached_files, cache_time = cached_result
                    # Merge background files with cached files
                    all_files = cached_files + background_files
                    self._directory_cache.set(cache_key, all_files, cache_time)

                self.logger.debug(f"Processed {len(background_files)} background items")

        except Exception as e:
            self.logger.error(f"Error in background processing: {e}")

    async def optimize_for_large_directory(self, file_count: int) -> Dict[str, Any]:
        """Optimize performance for large directory operations"""
        try:
            optimizations = []

            # Use performance optimizer if available
            if hasattr(self.performance_optimizer, 'optimize_for_large_directory'):
                perf_result = await self.performance_optimizer.optimize_for_large_directory(file_count)
                optimizations.extend(perf_result.get('optimizations_applied', []))

            # File manager specific optimizations
            if file_count > 10000:
                # Reduce cache TTL for very large directories
                self._directory_cache.cache.clear()
                optimizations.append("Cleared directory cache for large directory")

            if file_count > 5000:
                # Trigger cache cleanup
                await self.cleanup_cache()
                optimizations.append("Performed cache cleanup")

            return {
                'file_count': file_count,
                'optimizations_applied': optimizations,
                'cache_stats': self.get_cache_stats(),
                'performance_stats': self.get_performance_stats()
            }

        except Exception as e:
            self.logger.error(f"Error optimizing for large directory: {e}")
            return {'error': str(e)}