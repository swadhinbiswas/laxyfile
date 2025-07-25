"""
Archive Operations

This module provides comprehensive archive creation and extraction
with support for multiple formats and progress tracking.
"""

import os
import tarfile
import zipfile
import gzip
import bz2
import lzma
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum

from ..core.interfaces import ArchiveOperationInterface
from ..core.types import OperationResult, ArchiveFormat
from ..core.exceptions import (
    ArchiveError, UnsupportedArchiveFormatError,
    CorruptedArchiveError, FileOperationError
)
from ..utils.logger import Logger


class CompressionLevel(Enum):
    """Compression level options"""
    NONE = 0
    FASTEST = 1
    FAST = 3
    NORMAL = 6
    BEST = 9


@dataclass
class ArchiveInfo:
    """Information about an archive"""
    path: Path
    format: ArchiveFormat
    compressed_size: int
    uncompressed_size: int
    file_count: int
    created_date: Optional[str] = None
    compression_ratio: float = 0.0

    def __post_init__(self):
        if self.uncompressed_size > 0:
            self.compression_ratio = (1 - self.compressed_size / self.uncompressed_size) * 100


class ArchiveOperations(ArchiveOperationInterface):
    """Comprehensive archive operations with multiple format support"""

    def __init__(self, config: Any = None):
        self.config = config
        self.logger = Logger()

        # Supported formats and their handlers
        self.format_handlers = {
            ArchiveFormat.ZIP: self._handle_zip,
            ArchiveFormat.TAR: self._handle_tar,
            ArchiveFormat.TAR_GZ: self._handle_tar_gz,
            ArchiveFormat.TAR_BZ2: self._handle_tar_bz2,
            ArchiveFormat.TAR_XZ: self._handle_tar_xz,
            ArchiveFormat.SEVEN_ZIP: self._handle_7z,
            ArchiveFormat.RAR: self._handle_rar
        }

        # Format detection by extension
        self.extension_map = {
            '.zip': ArchiveFormat.ZIP,
            '.tar': ArchiveFormat.TAR,
            '.tar.gz': ArchiveFormat.TAR_GZ,
            '.tgz': ArchiveFormat.TAR_GZ,
            '.tar.bz2': ArchiveFormat.TAR_BZ2,
            '.tbz2': ArchiveFormat.TAR_BZ2,
            '.tar.xz': ArchiveFormat.TAR_XZ,
            '.txz': ArchiveFormat.TAR_XZ,
            '.7z': ArchiveFormat.SEVEN_ZIP,
            '.rar': ArchiveFormat.RAR
        }

        # Default settings
        self.default_compression_level = CompressionLevel.NORMAL
        self.chunk_size = 64 * 1024  # 64KB chunks
        self.verify_archives = True

    async def create_archive(self, files: List[Path], archive_path: Path,
                           format: ArchiveFormat, compression_level: int = 6,
                           progress_callback: Optional[Callable] = None) -> OperationResult:
        """Create archive from files with progress tracking"""
        try:
            # Validate inputs
            if not files:
                raise ArchiveError(archive_path, "create", "No files specified for archiving")

            # Check if format is supported
            if format not in self.format_handlers:
                raise UnsupportedArchiveFormatError(archive_path, format.value)

            # Calculate total size for progress tracking
            total_size = 0
            total_files = 0

            for file_path in files:
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    total_files += 1
                elif file_path.is_dir():
                    for item in file_path.rglob('*'):
                        if item.is_file():
                            total_size += item.stat().st_size
                            total_files += 1

            # Create archive using appropriate handler
            handler = self.format_handlers[format]
            result = await handler(
                'create', files, archive_path, compression_level,
                progress_callback, total_size, total_files
            )

            # Verify archive if enabled
            if self.verify_archives and result.success:
                try:
                    await self._verify_archive(archive_path, format)
                except Exception as e:
                    self.logger.warning(f"Archive verification failed: {e}")
                    # Don't fail the operation, just log the warning

            return result

        except Exception as e:
            if isinstance(e, ArchiveError):
                raise
            raise ArchiveError(archive_path, "create", str(e), e)

    async def extract_archive(self, archive_path: Path, destination: Path,
                            progress_callback: Optional[Callable] = None) -> OperationResult:
        """Extract archive with progress tracking"""
        try:
            # Validate inputs
            if not archive_path.exists():
                raise ArchiveError(archive_path, "extract", "Archive file does not exist")

            # Detect archive format
            format = self._detect_archive_format(archive_path)
            if not format:
                raise UnsupportedArchiveFormatError(archive_path, "unknown")

            # Check if format is supported
            if format not in self.format_handlers:
                raise UnsupportedArchiveFormatError(archive_path, format.value)

            # Create destination directory
            destination.mkdir(parents=True, exist_ok=True)

            # Get archive info for progress tracking
            archive_info = await self.get_archive_info(archive_path)

            # Extract using appropriate handler
            handler = self.format_handlers[format]
            result = await handler(
                'extract', [archive_path], destination, 0,
                progress_callback, archive_info.uncompressed_size, archive_info.file_count
            )

            return result

        except Exception as e:
            if isinstance(e, ArchiveError):
                raise
            raise ArchiveError(archive_path, "extract", str(e), e)

    def list_archive_contents(self, archive_path: Path) -> List[str]:
        """List contents of an archive"""
        try:
            format = self._detect_archive_format(archive_path)
            if not format:
                raise UnsupportedArchiveFormatError(archive_path, "unknown")

            contents = []

            if format == ArchiveFormat.ZIP:
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    contents = zf.namelist()

            elif format in [ArchiveFormat.TAR, ArchiveFormat.TAR_GZ,
                           ArchiveFormat.TAR_BZ2, ArchiveFormat.TAR_XZ]:
                mode = self._get_tar_mode(format, 'r')
                with tarfile.open(archive_path, mode) as tf:
                    contents = tf.getnames()

            elif format == ArchiveFormat.SEVEN_ZIP:
                # Would need py7zr library
                contents = self._list_7z_contents(archive_path)

            elif format == ArchiveFormat.RAR:
                # Would need rarfile library
                contents = self._list_rar_contents(archive_path)

            return contents

        except Exception as e:
            raise ArchiveError(archive_path, "list", str(e), e)

    def get_supported_formats(self) -> List[ArchiveFormat]:
        """Get list of supported archive formats"""
        return list(self.format_handlers.keys())

    async def get_archive_info(self, archive_path: Path) -> ArchiveInfo:
        """Get detailed information about an archive"""
        try:
            format = self._detect_archive_format(archive_path)
            if not format:
                raise UnsupportedArchiveFormatError(archive_path, "unknown")

            compressed_size = archive_path.stat().st_size
            uncompressed_size = 0
            file_count = 0

            # Calculate uncompressed size and file count
            if format == ArchiveFormat.ZIP:
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    for info in zf.infolist():
                        if not info.is_dir():
                            uncompressed_size += info.file_size
                            file_count += 1

            elif format in [ArchiveFormat.TAR, ArchiveFormat.TAR_GZ,
                           ArchiveFormat.TAR_BZ2, ArchiveFormat.TAR_XZ]:
                mode = self._get_tar_mode(format, 'r')
                with tarfile.open(archive_path, mode) as tf:
                    for member in tf.getmembers():
                        if member.isfile():
                            uncompressed_size += member.size
                            file_count += 1

            return ArchiveInfo(
                path=archive_path,
                format=format,
                compressed_size=compressed_size,
                uncompressed_size=uncompressed_size,
                file_count=file_count,
                created_date=time.ctime(archive_path.stat().st_ctime)
            )

        except Exception as e:
            raise ArchiveError(archive_path, "info", str(e), e)

    def _detect_archive_format(self, archive_path: Path) -> Optional[ArchiveFormat]:
        """Detect archive format from file extension and magic bytes"""
        # First try by extension
        path_str = str(archive_path).lower()

        for ext, format in self.extension_map.items():
            if path_str.endswith(ext):
                return format

        # Try by magic bytes
        try:
            with open(archive_path, 'rb') as f:
                magic = f.read(10)

                # ZIP magic bytes
                if magic.startswith(b'PK'):
                    return ArchiveFormat.ZIP

                # TAR magic bytes (at offset 257)
                f.seek(257)
                tar_magic = f.read(5)
                if tar_magic == b'ustar':
                    return ArchiveFormat.TAR

                # GZIP magic bytes
                if magic.startswith(b'\x1f\x8b'):
                    return ArchiveFormat.TAR_GZ

                # BZIP2 magic bytes
                if magic.startswith(b'BZ'):
                    return ArchiveFormat.TAR_BZ2

                # XZ magic bytes
                if magic.startswith(b'\xfd7zXZ'):
                    return ArchiveFormat.TAR_XZ

                # 7z magic bytes
                if magic.startswith(b'7z\xbc\xaf\x27\x1c'):
                    return ArchiveFormat.SEVEN_ZIP

                # RAR magic bytes
                if magic.startswith(b'Rar!'):
                    return ArchiveFormat.RAR

        except Exception:
            pass

        return None

    async def _handle_zip(self, operation: str, files: List[Path], target: Path,
                         compression_level: int, progress_callback: Optional[Callable],
                         total_size: int, total_files: int) -> OperationResult:
        """Handle ZIP archive operations"""
        try:
            if operation == 'create':
                return await self._create_zip(files, target, compression_level,
                                            progress_callback, total_size, total_files)
            elif operation == 'extract':
                return await self._extract_zip(files[0], target, progress_callback,
                                             total_size, total_files)
        except Exception as e:
            raise ArchiveError(target, operation, str(e), e)

    async def _create_zip(self, files: List[Path], archive_path: Path,
                         compression_level: int, progress_callback: Optional[Callable],
                         total_size: int, total_files: int) -> OperationResult:
        """Create ZIP archive"""
        processed_size = 0
        processed_files = 0
        created_files = []

        # Map compression level to zipfile constants
        compression_map = {
            0: zipfile.ZIP_STORED,
            1: zipfile.ZIP_DEFLATED,
            3: zipfile.ZIP_DEFLATED,
            6: zipfile.ZIP_DEFLATED,
            9: zipfile.ZIP_DEFLATED
        }

        compression = compression_map.get(compression_level, zipfile.ZIP_DEFLATED)

        with zipfile.ZipFile(archive_path, 'w', compression=compression,
                           compresslevel=compression_level) as zf:

            for file_path in files:
                if file_path.is_file():
                    # Add single file
                    zf.write(file_path, file_path.name)
                    processed_size += file_path.stat().st_size
                    processed_files += 1
                    created_files.append(file_path)

                    # Update progress
                    if progress_callback:
                        progress = (processed_size / total_size) * 100 if total_size > 0 else 0
                        await progress_callback(progress, f"Adding {file_path.name}")

                elif file_path.is_dir():
                    # Add directory recursively
                    for item in file_path.rglob('*'):
                        if item.is_file():
                            # Calculate relative path
                            rel_path = item.relative_to(file_path.parent)
                            zf.write(item, str(rel_path))

                            processed_size += item.stat().st_size
                            processed_files += 1
                            created_files.append(item)

                            # Update progress
                            if progress_callback:
                                progress = (processed_size / total_size) * 100 if total_size > 0 else 0
                                await progress_callback(progress, f"Adding {item.name}")

                            # Allow other tasks to run
                            await asyncio.sleep(0)

        return OperationResult(
            success=True,
            message=f"Created ZIP archive with {processed_files} files",
            affected_files=[archive_path],
            progress=100.0,
            bytes_processed=processed_size
        )

    async def _extract_zip(self, archive_path: Path, destination: Path,
                          progress_callback: Optional[Callable],
                          total_size: int, total_files: int) -> OperationResult:
        """Extract ZIP archive"""
        processed_size = 0
        processed_files = 0
        extracted_files = []

        with zipfile.ZipFile(archive_path, 'r') as zf:
            for info in zf.infolist():
                if not info.is_dir():
                    # Extract file
                    extracted_path = destination / info.filename
                    extracted_path.parent.mkdir(parents=True, exist_ok=True)

                    with zf.open(info) as source, open(extracted_path, 'wb') as target:
                        while True:
                            chunk = source.read(self.chunk_size)
                            if not chunk:
                                break
                            target.write(chunk)
                            processed_size += len(chunk)

                            # Update progress
                            if progress_callback:
                                progress = (processed_size / total_size) * 100 if total_size > 0 else 0
                                await progress_callback(progress, f"Extracting {info.filename}")

                            # Allow other tasks to run
                            await asyncio.sleep(0)

                    processed_files += 1
                    extracted_files.append(extracted_path)

        return OperationResult(
            success=True,
            message=f"Extracted {processed_files} files from ZIP archive",
            affected_files=extracted_files,
            progress=100.0,
            bytes_processed=processed_size
        )

    async def _handle_tar(self, operation: str, files: List[Path], target: Path,
                         compression_level: int, progress_callback: Optional[Callable],
                         total_size: int, total_files: int) -> OperationResult:
        """Handle TAR archive operations"""
        try:
            format = self._detect_archive_format(target if operation == 'create' else files[0])

            if operation == 'create':
                return await self._create_tar(files, target, format, compression_level,
                                            progress_callback, total_size, total_files)
            elif operation == 'extract':
                return await self._extract_tar(files[0], target, format, progress_callback,
                                             total_size, total_files)
        except Exception as e:
            raise ArchiveError(target, operation, str(e), e)

    # Alias methods for different TAR formats
    async def _handle_tar_gz(self, *args, **kwargs):
        return await self._handle_tar(*args, **kwargs)

    async def _handle_tar_bz2(self, *args, **kwargs):
        return await self._handle_tar(*args, **kwargs)

    async def _handle_tar_xz(self, *args, **kwargs):
        return await self._handle_tar(*args, **kwargs)

    async def _create_tar(self, files: List[Path], archive_path: Path, format: ArchiveFormat,
                         compression_level: int, progress_callback: Optional[Callable],
                         total_size: int, total_files: int) -> OperationResult:
        """Create TAR archive"""
        processed_size = 0
        processed_files = 0
        created_files = []

        mode = self._get_tar_mode(format, 'w', compression_level)

        with tarfile.open(archive_path, mode) as tf:
            for file_path in files:
                if file_path.is_file():
                    tf.add(file_path, file_path.name)
                    processed_size += file_path.stat().st_size
                    processed_files += 1
                    created_files.append(file_path)

                    if progress_callback:
                        progress = (processed_size / total_size) * 100 if total_size > 0 else 0
                        await progress_callback(progress, f"Adding {file_path.name}")

                elif file_path.is_dir():
                    tf.add(file_path, file_path.name)

                    for item in file_path.rglob('*'):
                        if item.is_file():
                            rel_path = item.relative_to(file_path.parent)
                            processed_size += item.stat().st_size
                            processed_files += 1
                            created_files.append(item)

                            if progress_callback:
                                progress = (processed_size / total_size) * 100 if total_size > 0 else 0
                                await progress_callback(progress, f"Adding {item.name}")

                            await asyncio.sleep(0)

        return OperationResult(
            success=True,
            message=f"Created TAR archive with {processed_files} files",
            affected_files=[archive_path],
            progress=100.0,
            bytes_processed=processed_size
        )

    async def _extract_tar(self, archive_path: Path, destination: Path, format: ArchiveFormat,
                          progress_callback: Optional[Callable],
                          total_size: int, total_files: int) -> OperationResult:
        """Extract TAR archive"""
        processed_size = 0
        processed_files = 0
        extracted_files = []

        mode = self._get_tar_mode(format, 'r')

        with tarfile.open(archive_path, mode) as tf:
            for member in tf.getmembers():
                if member.isfile():
                    tf.extract(member, destination)
                    extracted_path = destination / member.name
                    extracted_files.append(extracted_path)

                    processed_size += member.size
                    processed_files += 1

                    if progress_callback:
                        progress = (processed_size / total_size) * 100 if total_size > 0 else 0
                        await progress_callback(progress, f"Extracting {member.name}")

                    await asyncio.sleep(0)

        return OperationResult(
            success=True,
            message=f"Extracted {processed_files} files from TAR archive",
            affected_files=extracted_files,
            progress=100.0,
            bytes_processed=processed_size
        )

    def _get_tar_mode(self, format: ArchiveFormat, operation: str,
                     compression_level: int = 6) -> str:
        """Get TAR mode string based on format and operation"""
        base_mode = operation  # 'r' or 'w'

        if format == ArchiveFormat.TAR:
            return base_mode
        elif format == ArchiveFormat.TAR_GZ:
            return f"{base_mode}:gz"
        elif format == ArchiveFormat.TAR_BZ2:
            return f"{base_mode}:bz2"
        elif format == ArchiveFormat.TAR_XZ:
            return f"{base_mode}:xz"

        return base_mode

    async def _handle_7z(self, operation: str, files: List[Path], target: Path,
                        compression_level: int, progress_callback: Optional[Callable],
                        total_size: int, total_files: int) -> OperationResult:
        """Handle 7-Zip archive operations (requires py7zr)"""
        try:
            import py7zr

            if operation == 'create':
                return await self._create_7z(files, target, compression_level,
                                           progress_callback, total_size, total_files)
            elif operation == 'extract':
                return await self._extract_7z(files[0], target, progress_callback,
                                            total_size, total_files)
        except ImportError:
            raise ArchiveError(target, operation, "py7zr library not installed")
        except Exception as e:
            raise ArchiveError(target, operation, str(e), e)

    async def _handle_rar(self, operation: str, files: List[Path], target: Path,
                         compression_level: int, progress_callback: Optional[Callable],
                         total_size: int, total_files: int) -> OperationResult:
        """Handle RAR archive operations (requires rarfile)"""
        try:
            import rarfile

            if operation == 'extract':
                return await self._extract_rar(files[0], target, progress_callback,
                                             total_size, total_files)
            else:
                raise ArchiveError(target, operation, "RAR creation not supported")
        except ImportError:
            raise ArchiveError(target, operation, "rarfile library not installed")
        except Exception as e:
            raise ArchiveError(target, operation, str(e), e)

    def _list_7z_contents(self, archive_path: Path) -> List[str]:
        """List 7z archive contents"""
        try:
            import py7zr
            with py7zr.SevenZipFile(archive_path, 'r') as archive:
                return archive.getnames()
        except ImportError:
            return ["7z support not available (py7zr not installed)"]

    def _list_rar_contents(self, archive_path: Path) -> List[str]:
        """List RAR archive contents"""
        try:
            import rarfile
            with rarfile.RarFile(archive_path, 'r') as archive:
                return archive.namelist()
        except ImportError:
            return ["RAR support not available (rarfile not installed)"]

    async def _verify_archive(self, archive_path: Path, format: ArchiveFormat) -> None:
        """Verify archive integrity"""
        try:
            if format == ArchiveFormat.ZIP:
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    bad_file = zf.testzip()
                    if bad_file:
                        raise CorruptedArchiveError(archive_path)

            elif format in [ArchiveFormat.TAR, ArchiveFormat.TAR_GZ,
                           ArchiveFormat.TAR_BZ2, ArchiveFormat.TAR_XZ]:
                mode = self._get_tar_mode(format, 'r')
                with tarfile.open(archive_path, mode) as tf:
                    # TAR files don't have built-in integrity check
                    # Just try to read the member list
                    tf.getnames()

            # For other formats, basic existence check is sufficient

        except Exception as e:
            raise CorruptedArchiveError(archive_path)