"""
Comprehensive File Operations

This module provides robust file operations with progress tracking,
error handling, and recovery options, inspired by SuperFile's reliability.
"""

import os
import shutil
import asyncio
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, AsyncIterator, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import threading

from ..core.interfaces import OperationInterface
from ..core.types import OperationResult, OperationStatus
from ..core.exceptions import (
    FileOperationError, PermissionError as LaxyPermissionError,
    DiskSpaceError, DirectoryNotEmptyError
)
from ..utils.logger import Logger


class OperationType(Enum):
    """File operation types"""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    CREATE_DIR = "create_directory"
    CREATE_FILE = "create_file"


@dataclass
class OperationProgress:
    """Progress tracking for file operations"""
    operation_id: str
    operation_type: OperationType
    total_files: int = 0
    processed_files: int = 0
    total_bytes: int = 0
    processed_bytes: int = 0
    current_file: str = ""
    speed_bps: float = 0.0
    eta_seconds: float = 0.0
    status: OperationStatus = OperationStatus.PENDING
    error_count: int = 0
    errors: List[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)

    @property
    def progress_percent(self) -> float:
        """Get progress percentage"""
        if self.total_bytes > 0:
            return (self.processed_bytes / self.total_bytes) * 100
        elif self.total_files > 0:
            return (self.processed_files / self.total_files) * 100
        return 0.0

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return time.time() - self.start_time


class ProgressTracker:
    """Tracks progress for file operations"""

    def __init__(self):
        self.operations: Dict[str, OperationProgress] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def create_operation(self, operation_id: str, operation_type: OperationType,
                        total_files: int = 0, total_bytes: int = 0) -> OperationProgress:
        """Create a new operation progress tracker"""
        with self._lock:
            progress = OperationProgress(
                operation_id=operation_id,
                operation_type=operation_type,
                total_files=total_files,
                total_bytes=total_bytes
            )
            self.operations[operation_id] = progress
            return progress

    def update_progress(self, operation_id: str, **kwargs) -> None:
        """Update operation progress"""
        with self._lock:
            if operation_id in self.operations:
                progress = self.operations[operation_id]

                for key, value in kwargs.items():
                    if hasattr(progress, key):
                        setattr(progress, key, value)

                # Calculate speed and ETA
                elapsed = progress.elapsed_time
                if elapsed > 0 and progress.processed_bytes > 0:
                    progress.speed_bps = progress.processed_bytes / elapsed

                    if progress.speed_bps > 0:
                        remaining_bytes = progress.total_bytes - progress.processed_bytes
                        progress.eta_seconds = remaining_bytes / progress.speed_bps

                # Notify callbacks
                self._notify_callbacks(operation_id, progress)

    def add_callback(self, operation_id: str, callback: Callable) -> None:
        """Add progress callback"""
        with self._lock:
            if operation_id not in self.callbacks:
                self.callbacks[operation_id] = []
            self.callbacks[operation_id].append(callback)

    def _notify_callbacks(self, operation_id: str, progress: OperationProgress) -> None:
        """Notify all callbacks for an operation"""
        if operation_id in self.callbacks:
            for callback in self.callbacks[operation_id]:
                try:
                    callback(progress)
                except Exception as e:
                    # Don't let callback errors break the operation
                    pass

    def get_progress(self, operation_id: str) -> Optional[OperationProgress]:
        """Get operation progress"""
        with self._lock:
            return self.operations.get(operation_id)

    def complete_operation(self, operation_id: str, success: bool = True) -> None:
        """Mark operation as complete"""
        with self._lock:
            if operation_id in self.operations:
                progress = self.operations[operation_id]
                progress.status = OperationStatus.COMPLETED if success else OperationStatus.FAILED
                self._notify_callbacks(operation_id, progress)

    def cancel_operation(self, operation_id: str) -> None:
        """Cancel an operation"""
        with self._lock:
            if operation_id in self.operations:
                progress = self.operations[operation_id]
                progress.status = OperationStatus.CANCELLED
                self._notify_callbacks(operation_id, progress)


class ComprehensiveFileOperations(OperationInterface):
    """Comprehensive file operations with SuperFile-inspired reliability"""

    def __init__(self, config: Any = None):
        self.config = config
        self.logger = Logger()
        self.progress_tracker = ProgressTracker()
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Operation settings
        self.chunk_size = 64 * 1024  # 64KB chunks for copying
        self.verify_copies = True
        self.use_fast_move = True  # Use rename when possible
        self.backup_on_overwrite = False

        # Cancellation support
        self.cancelled_operations: set = set()

        # Callback registration
        self.progress_callbacks: List[Callable] = []
        self.completion_callbacks: List[Callable] = []

    def register_progress_callback(self, callback: Callable) -> None:
        """Register a callback for operation progress updates"""
        self.progress_callbacks.append(callback)

    def register_completion_callback(self, callback: Callable) -> None:
        """Register a callback for operation completion"""
        self.completion_callbacks.append(callback)

    def _notify_progress_callbacks(self, operation_data: Dict[str, Any]) -> None:
        """Notify all progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(operation_data)
            except Exception as e:
                self.logger.error(f"Error in progress callback: {e}")

    def _notify_completion_callbacks(self, operation_data: Dict[str, Any]) -> None:
        """Notify all completion callbacks"""
        for callback in self.completion_callbacks:
            try:
                callback(operation_data)
            except Exception as e:
                self.logger.error(f"Error in completion callback: {e}")

    async def copy_files(self, sources: List[Path], destination: Path,
                        progress_callback: Optional[Callable] = None) -> OperationResult:
        """Copy files with comprehensive progress tracking and error handling"""
        operation_id = f"copy_{int(time.time() * 1000)}"

        try:
            # Validate inputs
            if not sources:
                raise FileOperationError("copy", destination, "No source files specified")

            if not destination.exists():
                destination.mkdir(parents=True, exist_ok=True)

            if not destination.is_dir():
                raise FileOperationError("copy", destination, "Destination must be a directory")

            # Calculate total size and file count
            total_files, total_bytes = await self._calculate_operation_size(sources)

            # Create progress tracker
            progress = self.progress_tracker.create_operation(
                operation_id, OperationType.COPY, total_files, total_bytes
            )

            if progress_callback:
                self.progress_tracker.add_callback(operation_id, progress_callback)

            progress.status = OperationStatus.IN_PROGRESS

            # Perform copy operation
            copied_files = []
            errors = []

            for source in sources:
                if operation_id in self.cancelled_operations:
                    break

                try:
                    if source.is_file():
                        dest_file = destination / source.name
                        await self._copy_file_with_progress(
                            source, dest_file, operation_id
                        )
                        copied_files.append(dest_file)
                    elif source.is_dir():
                        dest_dir = destination / source.name
                        copied_dir_files = await self._copy_directory_with_progress(
                            source, dest_dir, operation_id
                        )
                        copied_files.extend(copied_dir_files)

                except Exception as e:
                    error_msg = f"Failed to copy {source}: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

                    # Update error count
                    self.progress_tracker.update_progress(
                        operation_id, error_count=progress.error_count + 1
                    )

            # Complete operation
            success = len(errors) == 0 and operation_id not in self.cancelled_operations
            self.progress_tracker.complete_operation(operation_id, success)

            return OperationResult(
                success=success,
                message=f"Copied {len(copied_files)} files" if success else f"Copy completed with {len(errors)} errors",
                affected_files=copied_files,
                errors=errors,
                progress=progress.progress_percent,
                duration=progress.elapsed_time,
                bytes_processed=progress.processed_bytes
            )

        except Exception as e:
            self.progress_tracker.complete_operation(operation_id, False)
            raise FileOperationError("copy", destination, str(e), e)
        finally:
            # Cleanup
            self.cancelled_operations.discard(operation_id)

    async def move_files(self, sources: List[Path], destination: Path,
                        progress_callback: Optional[Callable] = None) -> OperationResult:
        """Move files with optimization for same-filesystem operations"""
        operation_id = f"move_{int(time.time() * 1000)}"

        try:
            # Validate inputs
            if not sources:
                raise FileOperationError("move", destination, "No source files specified")

            if not destination.exists():
                destination.mkdir(parents=True, exist_ok=True)

            # Check if we can use fast move (rename)
            can_fast_move = self.use_fast_move and self._can_use_fast_move(sources[0], destination)

            # Calculate operation size
            total_files, total_bytes = await self._calculate_operation_size(sources)

            # Create progress tracker
            progress = self.progress_tracker.create_operation(
                operation_id, OperationType.MOVE, total_files, total_bytes
            )

            if progress_callback:
                self.progress_tracker.add_callback(operation_id, progress_callback)

            progress.status = OperationStatus.IN_PROGRESS

            moved_files = []
            errors = []

            for source in sources:
                if operation_id in self.cancelled_operations:
                    break

                try:
                    dest_path = destination / source.name

                    if can_fast_move:
                        # Fast move using rename
                        source.rename(dest_path)
                        moved_files.append(dest_path)

                        # Update progress
                        self.progress_tracker.update_progress(
                            operation_id,
                            processed_files=progress.processed_files + 1,
                            processed_bytes=progress.processed_bytes + (source.stat().st_size if source.is_file() else 0),
                            current_file=str(source)
                        )
                    else:
                        # Copy then delete
                        if source.is_file():
                            await self._copy_file_with_progress(source, dest_path, operation_id)
                            source.unlink()
                            moved_files.append(dest_path)
                        elif source.is_dir():
                            copied_files = await self._copy_directory_with_progress(source, dest_path, operation_id)
                            shutil.rmtree(source)
                            moved_files.extend(copied_files)

                except Exception as e:
                    error_msg = f"Failed to move {source}: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            # Complete operation
            success = len(errors) == 0 and operation_id not in self.cancelled_operations
            self.progress_tracker.complete_operation(operation_id, success)

            return OperationResult(
                success=success,
                message=f"Moved {len(moved_files)} files" if success else f"Move completed with {len(errors)} errors",
                affected_files=moved_files,
                errors=errors,
                progress=progress.progress_percent,
                duration=progress.elapsed_time,
                bytes_processed=progress.processed_bytes
            )

        except Exception as e:
            self.progress_tracker.complete_operation(operation_id, False)
            raise FileOperationError("move", destination, str(e), e)
        finally:
            self.cancelled_operations.discard(operation_id)

    async def delete_files(self, files: List[Path], use_trash: bool = True,
                          progress_callback: Optional[Callable] = None) -> OperationResult:
        """Delete files with optional trash support"""
        operation_id = f"delete_{int(time.time() * 1000)}"

        try:
            if not files:
                raise FileOperationError("delete", Path(), "No files specified for deletion")

            # Calculate operation size
            total_files, total_bytes = await self._calculate_operation_size(files)

            # Create progress tracker
            progress = self.progress_tracker.create_operation(
                operation_id, OperationType.DELETE, total_files, total_bytes
            )

            if progress_callback:
                self.progress_tracker.add_callback(operation_id, progress_callback)

            progress.status = OperationStatus.IN_PROGRESS

            deleted_files = []
            errors = []

            for file_path in files:
                if operation_id in self.cancelled_operations:
                    break

                try:
                    if use_trash:
                        await self._move_to_trash(file_path)
                    else:
                        if file_path.is_file():
                            file_path.unlink()
                        elif file_path.is_dir():
                            shutil.rmtree(file_path)

                    deleted_files.append(file_path)

                    # Update progress
                    self.progress_tracker.update_progress(
                        operation_id,
                        processed_files=progress.processed_files + 1,
                        current_file=str(file_path)
                    )

                except Exception as e:
                    error_msg = f"Failed to delete {file_path}: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            # Complete operation
            success = len(errors) == 0 and operation_id not in self.cancelled_operations
            self.progress_tracker.complete_operation(operation_id, success)

            action = "moved to trash" if use_trash else "deleted"
            return OperationResult(
                success=success,
                message=f"{action.title()} {len(deleted_files)} files" if success else f"Delete completed with {len(errors)} errors",
                affected_files=deleted_files,
                errors=errors,
                progress=progress.progress_percent,
                duration=progress.elapsed_time
            )

        except Exception as e:
            self.progress_tracker.complete_operation(operation_id, False)
            raise FileOperationError("delete", Path(), str(e), e)
        finally:
            self.cancelled_operations.discard(operation_id)

    def rename_file(self, old_path: Path, new_name: str) -> OperationResult:
        """Rename a file or directory"""
        try:
            if not old_path.exists():
                raise FileOperationError("rename", old_path, "File does not exist")

            # Validate new name
            if not new_name or '/' in new_name or '\\' in new_name:
                raise FileOperationError("rename", old_path, "Invalid filename")

            new_path = old_path.parent / new_name

            if new_path.exists():
                raise FileOperationError("rename", old_path, f"File '{new_name}' already exists")

            # Perform rename
            old_path.rename(new_path)

            return OperationResult(
                success=True,
                message=f"Renamed '{old_path.name}' to '{new_name}'",
                affected_files=[new_path],
                progress=100.0,
                duration=0.0
            )

        except Exception as e:
            raise FileOperationError("rename", old_path, str(e), e)

    async def _copy_file_with_progress(self, source: Path, destination: Path,
                                     operation_id: str) -> None:
        """Copy a single file with progress tracking"""
        if destination.exists() and not self._should_overwrite(source, destination):
            raise FileOperationError("copy", source, f"Destination exists: {destination}")

        # Create destination directory if needed
        destination.parent.mkdir(parents=True, exist_ok=True)

        file_size = source.stat().st_size
        copied_bytes = 0

        with open(source, 'rb') as src_file, open(destination, 'wb') as dst_file:
            while True:
                if operation_id in self.cancelled_operations:
                    # Clean up partial file
                    destination.unlink(missing_ok=True)
                    raise FileOperationError("copy", source, "Operation cancelled")

                chunk = src_file.read(self.chunk_size)
                if not chunk:
                    break

                dst_file.write(chunk)
                copied_bytes += len(chunk)

                # Update progress
                progress = self.progress_tracker.get_progress(operation_id)
                if progress:
                    self.progress_tracker.update_progress(
                        operation_id,
                        processed_bytes=progress.processed_bytes + len(chunk),
                        current_file=str(source)
                    )

                # Allow other tasks to run
                await asyncio.sleep(0)

        # Verify copy if enabled
        if self.verify_copies:
            if not await self._verify_file_copy(source, destination):
                destination.unlink(missing_ok=True)
                raise FileOperationError("copy", source, "File verification failed")

        # Copy metadata
        shutil.copystat(source, destination)

        # Update file count
        progress = self.progress_tracker.get_progress(operation_id)
        if progress:
            self.progress_tracker.update_progress(
                operation_id,
                processed_files=progress.processed_files + 1
            )

    async def _copy_directory_with_progress(self, source: Path, destination: Path,
                                          operation_id: str) -> List[Path]:
        """Copy a directory recursively with progress tracking"""
        copied_files = []

        # Create destination directory
        destination.mkdir(parents=True, exist_ok=True)

        # Copy all files and subdirectories
        for item in source.rglob('*'):
            if operation_id in self.cancelled_operations:
                break

            relative_path = item.relative_to(source)
            dest_item = destination / relative_path

            try:
                if item.is_file():
                    await self._copy_file_with_progress(item, dest_item, operation_id)
                    copied_files.append(dest_item)
                elif item.is_dir():
                    dest_item.mkdir(parents=True, exist_ok=True)

            except Exception as e:
                self.logger.error(f"Error copying {item}: {e}")

        return copied_files

    async def _calculate_operation_size(self, paths: List[Path]) -> Tuple[int, int]:
        """Calculate total files and bytes for operation"""
        total_files = 0
        total_bytes = 0

        for path in paths:
            if path.is_file():
                total_files += 1
                total_bytes += path.stat().st_size
            elif path.is_dir():
                for item in path.rglob('*'):
                    if item.is_file():
                        total_files += 1
                        total_bytes += item.stat().st_size

        return total_files, total_bytes

    def _can_use_fast_move(self, source: Path, destination: Path) -> bool:
        """Check if we can use fast move (rename) operation"""
        try:
            # Check if both paths are on the same filesystem
            source_stat = source.stat()
            dest_stat = destination.stat()

            # On Unix systems, compare device IDs
            if hasattr(source_stat, 'st_dev') and hasattr(dest_stat, 'st_dev'):
                return source_stat.st_dev == dest_stat.st_dev

            # On Windows, compare drive letters
            source_drive = str(source).split(':')[0] if ':' in str(source) else ''
            dest_drive = str(destination).split(':')[0] if ':' in str(destination) else ''

            return source_drive.lower() == dest_drive.lower()

        except:
            return False

    def _should_overwrite(self, source: Path, destination: Path) -> bool:
        """Determine if file should be overwritten"""
        # For now, always ask user or use config setting
        # In a real implementation, this would show a dialog
        return self.config.get('file_operations.overwrite_existing', False) if self.config else False

    async def _verify_file_copy(self, source: Path, destination: Path) -> bool:
        """Verify that file was copied correctly"""
        try:
            # Quick size check
            if source.stat().st_size != destination.stat().st_size:
                return False

            # For small files, do checksum verification
            if source.stat().st_size < 10 * 1024 * 1024:  # 10MB
                source_hash = await self._calculate_file_hash(source)
                dest_hash = await self._calculate_file_hash(destination)
                return source_hash == dest_hash

            return True
        except:
            return False

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(self.chunk_size), b""):
                hash_sha256.update(chunk)
                await asyncio.sleep(0)  # Allow other tasks to run

        return hash_sha256.hexdigest()

    async def _move_to_trash(self, file_path: Path) -> None:
        """Move file to system trash"""
        try:
            # Try to use system trash
            import send2trash
            send2trash.send2trash(str(file_path))
        except ImportError:
            # Fallback: move to a trash directory
            trash_dir = Path.home() / '.local' / 'share' / 'Trash' / 'files'
            trash_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique name if file exists in trash
            trash_path = trash_dir / file_path.name
            counter = 1
            while trash_path.exists():
                name_parts = file_path.name.rsplit('.', 1)
                if len(name_parts) == 2:
                    trash_path = trash_dir / f"{name_parts[0]}_{counter}.{name_parts[1]}"
                else:
                    trash_path = trash_dir / f"{file_path.name}_{counter}"
                counter += 1

            # Move to trash
            file_path.rename(trash_path)

    def cancel_operation(self, operation_id: str) -> None:
        """Cancel an ongoing operation"""
        self.cancelled_operations.add(operation_id)
        self.progress_tracker.cancel_operation(operation_id)

    def get_operation_progress(self, operation_id: str) -> Optional[OperationProgress]:
        """Get progress for an operation"""
        return self.progress_tracker.get_progress(operation_id)

    def cleanup(self) -> None:
        """Cleanup resources"""
        self.executor.shutdown(wait=True)