"""
Advanced Preview System

This module provides a comprehensive file preview system with support for
multiple formats, intelligent content detection, and extensible rendering.
"""

import asyncio
import hashlib
import mimetypes
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json

from ..core.types import OperationResult
from ..core.exceptions import PreviewError
from ..utils.logger import Logger
from .terminal_media import terminal_image_renderer, terminal_video_renderer


class PreviewType(Enum):
    """Types of file previews"""
    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    BINARY = "binary"
    UNKNOWN = "unknown"


class PreviewQuality(Enum):
    """Preview quality levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FULL = "full"


@dataclass
class PreviewResult:
    """Result of file preview generation"""
    file_path: Path
    preview_type: PreviewType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    thumbnail: Optional[str] = None  # Base64 encoded thumbnail
    success: bool = True
    error_message: Optional[str] = None
    generation_time: float = 0.0
    cache_key: Optional[str] = None
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'file_path': str(self.file_path),
            'preview_type': self.preview_type.value,
            'content': self.content,
            'metadata': self.metadata,
            'thumbnail': self.thumbnail,
            'success': self.success,
            'error_message': self.error_message,
            'generation_time': self.generation_time,
            'cache_key': self.cache_key,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


@dataclass
class PreviewConfig:
    """Configuration for preview generation"""
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    max_text_length: int = 10000  # 10K characters
    max_lines: int = 1000  # 1K lines
    quality: PreviewQuality = PreviewQuality.MEDIUM
    enable_thumbnails: bool = True
    enable_syntax_highlighting: bool = True
    enable_metadata_extraction: bool = True
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hour
    timeout: int = 30  # 30 seconds

    # Format-specific settings
    image_max_width: int = 800
    image_max_height: int = 600
    video_thumbnail_time: float = 5.0  # 5 seconds into video
    pdf_max_pages: int = 5
    archive_max_entries: int = 100


class PreviewCache:
    """Cache for preview results"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, PreviewResult] = {}
        self.access_order: List[str] = []
        self.logger = Logger()

    def _generate_cache_key(self, file_path: Path, config: PreviewConfig) -> str:
        """Generate cache key for file and config"""
        try:
            stat = file_path.stat()
            key_data = {
                'path': str(file_path),
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'quality': config.quality.value,
                'max_text_length': config.max_text_length,
                'enable_syntax_highlighting': config.enable_syntax_highlighting
            }
            key_string = json.dumps(key_data, sort_keys=True)
            return hashlib.sha256(key_string.encode()).hexdigest()[:16]
        except Exception:
            return hashlib.sha256(str(file_path).encode()).hexdigest()[:16]

    def get(self, file_path: Path, config: PreviewConfig) -> Optional[PreviewResult]:
        """Get cached preview result"""
        cache_key = self._generate_cache_key(file_path, config)

        if cache_key not in self.cache:
            return None

        result = self.cache[cache_key]

        # Check if expired
        if result.expires_at and datetime.now() > result.expires_at:
            self._remove(cache_key)
            return None

        # Update access order
        if cache_key in self.access_order:
            self.access_order.remove(cache_key)
        self.access_order.append(cache_key)

        return result

    def set(self, file_path: Path, config: PreviewConfig, result: PreviewResult):
        """Cache preview result"""
        cache_key = self._generate_cache_key(file_path, config)
        result.cache_key = cache_key

        if config.cache_ttl > 0:
            result.expires_at = datetime.now() + timedelta(seconds=config.cache_ttl)

        self.cache[cache_key] = result
        self.access_order.append(cache_key)

        # Evict if necessary
        self._evict_if_necessary()

    def _remove(self, cache_key: str):
        """Remove item from cache"""
        if cache_key in self.cache:
            del self.cache[cache_key]
        if cache_key in self.access_order:
            self.access_order.remove(cache_key)

    def _evict_if_necessary(self):
        """Evict least recently used items if cache is full"""
        while len(self.cache) > self.max_size:
            if not self.access_order:
                break

            oldest_key = self.access_order.pop(0)
            if oldest_key in self.cache:
                del self.cache[oldest_key]

    def clear(self):
        """Clear all cached items"""
        self.cache.clear()
        self.access_order.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        expired_count = sum(
            1 for result in self.cache.values()
            if result.expires_at and datetime.now() > result.expires_at
        )

        return {
            'total_items': len(self.cache),
            'expired_items': expired_count,
            'active_items': len(self.cache) - expired_count,
            'max_size': self.max_size
        }


class BasePreviewRenderer:
    """Base class for preview renderers"""

    def __init__(self, config: PreviewConfig):
        self.config = config
        self.logger = Logger()

    def can_preview(self, file_path: Path) -> bool:
        """Check if this renderer can preview the file"""
        raise NotImplementedError

    async def generate_preview(self, file_path: Path) -> PreviewResult:
        """Generate preview for the file"""
        raise NotImplementedError

    def _create_error_result(self, file_path: Path, error: str) -> PreviewResult:
        """Create error result"""
        return PreviewResult(
            file_path=file_path,
            preview_type=PreviewType.UNKNOWN,
            content="",
            success=False,
            error_message=error
        )

    def _is_file_too_large(self, file_path: Path) -> bool:
        """Check if file is too large for preview"""
        try:
            return file_path.stat().st_size > self.config.max_file_size
        except Exception:
            return True


class TextPreviewRenderer(BasePreviewRenderer):
    """Renderer for plain text files"""

    def can_preview(self, file_path: Path) -> bool:
        """Check if file is a text file"""
        text_extensions = {'.txt', '.md', '.rst', '.log', '.cfg', '.ini', '.conf'}

        if file_path.suffix.lower() in text_extensions:
            return True

        # Check MIME type
        mime_type = mimetypes.guess_type(str(file_path))[0]
        if mime_type and mime_type.startswith('text/'):
            return True

        # Check if file is likely text by sampling content
        try:
            if self._is_file_too_large(file_path):
                return False

            with open(file_path, 'rb') as f:
                sample = f.read(1024)
                if not sample:
                    return True  # Empty file

                # Check if sample is mostly printable ASCII
                printable_ratio = sum(1 for b in sample if 32 <= b <= 126 or b in [9, 10, 13]) / len(sample)
                return printable_ratio > 0.7
        except Exception:
            return False

    async def generate_preview(self, file_path: Path) -> PreviewResult:
        """Generate text preview"""
        start_time = time.time()

        try:
            if self._is_file_too_large(file_path):
                return self._create_error_result(file_path, "File too large for preview")

            # Read file content
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except UnicodeDecodeError:
                # Try other encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        content = file_path.read_text(encoding=encoding, errors='ignore')
                        break
                    except:
                        continue
                else:
                    return self._create_error_result(file_path, "Could not decode file")

            # Truncate if too long
            lines = content.split('\n')
            if len(lines) > self.config.max_lines:
                lines = lines[:self.config.max_lines]
                lines.append(f"... (truncated, showing first {self.config.max_lines} lines)")
                content = '\n'.join(lines)

            if len(content) > self.config.max_text_length:
                content = content[:self.config.max_text_length] + "\n... (truncated)"

            # Extract metadata
            metadata = {
                'encoding': 'utf-8',
                'line_count': len(lines),
                'character_count': len(content),
                'word_count': len(content.split()),
                'file_size': file_path.stat().st_size
            }

            return PreviewResult(
                file_path=file_path,
                preview_type=PreviewType.TEXT,
                content=content,
                metadata=metadata,
                generation_time=time.time() - start_time
            )

        except Exception as e:
            self.logger.error(f"Error generating text preview for {file_path}: {e}")
            return self._create_error_result(file_path, str(e))


class BinaryPreviewRenderer(BasePreviewRenderer):
    """Renderer for binary files"""

    def can_preview(self, file_path: Path) -> bool:
        """Can preview any file as binary"""
        return True  # Fallback renderer

    async def generate_preview(self, file_path: Path) -> PreviewResult:
        """Generate binary preview (hex dump)"""
        start_time = time.time()

        try:
            if self._is_file_too_large(file_path):
                return self._create_error_result(file_path, "File too large for preview")

            # Read first chunk of file
            chunk_size = min(1024, self.config.max_text_length // 4)  # Account for hex formatting

            with open(file_path, 'rb') as f:
                data = f.read(chunk_size)

            if not data:
                content = "(Empty file)"
            else:
                # Create hex dump
                lines = []
                for i in range(0, len(data), 16):
                    chunk = data[i:i+16]
                    hex_part = ' '.join(f'{b:02x}' for b in chunk)
                    ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
                    lines.append(f'{i:08x}  {hex_part:<48} |{ascii_part}|')

                content = '\n'.join(lines)

                if len(data) == chunk_size and file_path.stat().st_size > chunk_size:
                    content += f"\n... (showing first {chunk_size} bytes of {file_path.stat().st_size})"

            # Extract metadata
            stat = file_path.stat()
            metadata = {
                'file_size': stat.st_size,
                'mime_type': mimetypes.guess_type(str(file_path))[0],
                'is_binary': True,
                'bytes_shown': len(data) if data else 0
            }

            return PreviewResult(
                file_path=file_path,
                preview_type=PreviewType.BINARY,
                content=content,
                metadata=metadata,
                generation_time=time.time() - start_time
            )

        except Exception as e:
            self.logger.error(f"Error generating binary preview for {file_path}: {e}")
            return self._create_error_result(file_path, str(e))


class AdvancedPreviewSystem:
    """Advanced file preview system with multiple format support"""

    def __init__(self, config: Optional[PreviewConfig] = None):
        self.config = config or PreviewConfig()
        self.logger = Logger()
        self.cache = PreviewCache() if self.config.cache_enabled else None

        # Initialize renderers
        self.renderers: List[BasePreviewRenderer] = []
        self._initialize_renderers()

        # Statistics
        self.stats = {
            'previews_generated': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'total_generation_time': 0.0
        }

    def _initialize_renderers(self):
        """Initialize preview renderers in priority order"""
        # Import here to avoid circular imports
        from .code_preview import CodePreviewRenderer
        from .media_preview import MediaPreviewRenderer
        from .document_preview import DocumentPreviewRenderer

        # Add renderers in priority order (most specific first)
        self.renderers = [
            CodePreviewRenderer(self.config),
            MediaPreviewRenderer(self.config),
            DocumentPreviewRenderer(self.config),
            TextPreviewRenderer(self.config),
            BinaryPreviewRenderer(self.config)  # Fallback
        ]

    async def generate_preview(self, file_path: Path,
                             force_refresh: bool = False) -> PreviewResult:
        """Generate preview for a file"""
        try:
            if not file_path.exists():
                return PreviewResult(
                    file_path=file_path,
                    preview_type=PreviewType.UNKNOWN,
                    content="",
                    success=False,
                    error_message="File does not exist"
                )

            # Check cache first
            if self.cache and not force_refresh:
                cached_result = self.cache.get(file_path, self.config)
                if cached_result:
                    self.stats['cache_hits'] += 1
                    return cached_result
                else:
                    self.stats['cache_misses'] += 1

            # Find appropriate renderer
            renderer = self._find_renderer(file_path)
            if not renderer:
                return PreviewResult(
                    file_path=file_path,
                    preview_type=PreviewType.UNKNOWN,
                    content="",
                    success=False,
                    error_message="No suitable renderer found"
                )

            # Generate preview with timeout
            try:
                result = await asyncio.wait_for(
                    renderer.generate_preview(file_path),
                    timeout=self.config.timeout
                )
            except asyncio.TimeoutError:
                result = PreviewResult(
                    file_path=file_path,
                    preview_type=PreviewType.UNKNOWN,
                    content="",
                    success=False,
                    error_message="Preview generation timed out"
                )

            # Update statistics
            self.stats['previews_generated'] += 1
            self.stats['total_generation_time'] += result.generation_time

            if not result.success:
                self.stats['errors'] += 1

            # Cache result
            if self.cache and result.success:
                self.cache.set(file_path, self.config, result)

            return result

        except Exception as e:
            self.logger.error(f"Error generating preview for {file_path}: {e}")
            self.stats['errors'] += 1
            return PreviewResult(
                file_path=file_path,
                preview_type=PreviewType.UNKNOWN,
                content="",
                success=False,
                error_message=str(e)
            )

    def _find_renderer(self, file_path: Path) -> Optional[BasePreviewRenderer]:
        """Find appropriate renderer for file"""
        for renderer in self.renderers:
            try:
                if renderer.can_preview(file_path):
                    return renderer
            except Exception as e:
                self.logger.error(f"Error checking renderer {type(renderer).__name__}: {e}")

        return None

    async def generate_thumbnail(self, file_path: Path) -> Optional[str]:
        """Generate thumbnail for file (base64 encoded)"""
        try:
            # Find media renderer for thumbnail generation
            from .media_preview import MediaPreviewRenderer

            for renderer in self.renderers:
                if isinstance(renderer, MediaPreviewRenderer) and renderer.can_preview(file_path):
                    result = await renderer.generate_preview(file_path)
                    return result.thumbnail

            return None

        except Exception as e:
            self.logger.error(f"Error generating thumbnail for {file_path}: {e}")
            return None

    def detect_preview_type(self, file_path: Path) -> PreviewType:
        """Detect preview type for file"""
        try:
            renderer = self._find_renderer(file_path)
            if renderer:
                # Get preview type from renderer
                if hasattr(renderer, 'get_preview_type'):
                    return renderer.get_preview_type(file_path)

                # Infer from renderer type
                renderer_name = type(renderer).__name__
                if 'Code' in renderer_name:
                    return PreviewType.CODE
                elif 'Media' in renderer_name:
                    # Would need to check specific media type
                    return PreviewType.IMAGE  # Default
                elif 'Document' in renderer_name:
                    return PreviewType.DOCUMENT
                elif 'Text' in renderer_name:
                    return PreviewType.TEXT
                else:
                    return PreviewType.BINARY

            return PreviewType.UNKNOWN

        except Exception:
            return PreviewType.UNKNOWN

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get list of supported file formats by category"""
        formats = {}

        for renderer in self.renderers:
            renderer_name = type(renderer).__name__
            if hasattr(renderer, 'get_supported_extensions'):
                formats[renderer_name] = renderer.get_supported_extensions()

        return formats

    def clear_cache(self):
        """Clear preview cache"""
        if self.cache:
            self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.cache:
            return self.cache.get_stats()
        return {}

    def get_stats(self) -> Dict[str, Any]:
        """Get preview system statistics"""
        stats = self.stats.copy()

        if stats['previews_generated'] > 0:
            stats['average_generation_time'] = stats['total_generation_time'] / stats['previews_generated']
        else:
            stats['average_generation_time'] = 0.0

        if self.cache:
            stats['cache_stats'] = self.get_cache_stats()

        return stats

    def add_renderer(self, renderer: BasePreviewRenderer, priority: int = -1):
        """Add custom renderer"""
        if priority == -1:
            self.renderers.append(renderer)
        else:
            self.renderers.insert(priority, renderer)

    def remove_renderer(self, renderer_class: type):
        """Remove renderer by class"""
        self.renderers = [r for r in self.renderers if not isinstance(r, renderer_class)]

    async def batch_preview(self, file_paths: List[Path],
                          max_concurrent: int = 5) -> List[PreviewResult]:
        """Generate previews for multiple files concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_single(file_path: Path) -> PreviewResult:
            async with semaphore:
                return await self.generate_preview(file_path)

        tasks = [generate_single(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(PreviewResult(
                    file_path=file_paths[i],
                    preview_type=PreviewType.UNKNOWN,
                    content="",
                    success=False,
                    error_message=str(result)
                ))
            else:
                final_results.append(result)

        return final_results

    def update_config(self, **kwargs):
        """Update configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # Reinitialize renderers with new config
        self._initialize_renderers()

    async def preload_previews(self, directory_path: Path,
                             max_files: int = 100) -> Dict[str, Any]:
        """Preload previews for files in directory"""
        try:
            file_paths = []
            for file_path in directory_path.rglob('*'):
                if file_path.is_file() and len(file_paths) < max_files:
                    file_paths.append(file_path)

            results = await self.batch_preview(file_paths)

            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful

            return {
                'total_files': len(file_paths),
                'successful_previews': successful,
                'failed_previews': failed,
                'preload_time': time.time()
            }

        except Exception as e:
            self.logger.error(f"Error preloading previews: {e}")
            return {'error': str(e)}