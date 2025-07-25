"""
Batch Operations and Conflict Resolution

This module provides batch processing capabilities and intelligent
conflict resolution for file operations in LaxyFile.
"""

import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

from ..core.types import OperationResult, OperationStatus
from ..core.exceptions import FileOperationError
from .file_ops import ComprehensiveFileOperations, OperationType, OperationProgress
from ..utils.logger import Logger


class ConflictAction(Enum):
    """Actions for handling file conflicts"""
    SKIP = "skip"
    OVERWRITE = "overwrite"
    RENAME = "rename"
    MERGE = "merge"
    ASK_USER = "ask_user"
    BACKUP = "backup"


class BatchStrategy(Enum):
    """Strategies for batch processing"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ADAPTIVE = "adaptive"


@dataclass
class ConflictInfo:
    """Information about a file conflict"""
    source_path: Path
    destination_path: Path
    conflict_type: str  # "exists", "permission", "size_mismatch", etc.
    source_size: int = 0
    dest_size: int = 0
    source_modified: Optional[str] = None
    dest_modified: Optional[str] = None
    suggested_action: ConflictAction = ConflictAction.ASK_USER

    def __post_init__(self):
        # Auto-suggest actions based on conflict type and file properties
        if self.conflict_type == "exists":
            if self.source_size > self.dest_size:
                self.suggested_action = ConflictAction.OVERWRITE
            elif self.source_modified and self.dest_modified:
                if self.source_modified > self.dest_modified:
                    self.suggested_action = ConflictAction.OVERWRITE
                else:
                    self.suggested_action = ConflictAction.SKIP
            else:
                self.suggested_action = ConflictAction.RENAME


@dataclass
class BatchOperation:
    """Represents a batch operation"""
    operation_id: str
    operation_type: OperationType
    items: List[Tuple[Path, Path]]  # (source, destination) pairs
    options: Dict[str, Any] = field(default_factory=dict)
    strategy: BatchStrategy = BatchStrategy.ADAPTIVE
    conflict_resolution: Dict[str, ConflictAction] = field(default_factory=dict)
    max_parallel: int = 4

    # Progress tracking
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    conflicts: List[ConflictInfo] = field(default_factory=list)

    def __post_init__(self):
        self.total_items = len(self.items)


class ConflictResolver:
    """Handles file operation conflicts intelligently"""

    def __init__(self, config: Any = None):
        self.config = config
        self.logger = Logger()

        # Default conflict resolution rules
        self.default_rules = {
            "overwrite_newer": True,
            "overwrite_larger": False,
            "backup_on_overwrite": True,
            "auto_rename_pattern": "{name}_{counter}{ext}",
            "max_rename_attempts": 100
        }

        # User-defined rules (can be loaded from config)
        self.user_rules = {}
        if config:
            self.user_rules = config.get('conflict_resolution', {})

    async def resolve_conflict(self, conflict: ConflictInfo,
                             user_callback: Optional[Callable] = None) -> ConflictAction:
        """Resolve a file conflict using rules or user input"""
        try:
            # Check if we have a pre-defined action for this specific file
            conflict_key = f"{conflict.source_path}:{conflict.destination_path}"
            if conflict_key in self.user_rules:
                return ConflictAction(self.user_rules[conflict_key])

            # Apply automatic rules
            action = self._apply_automatic_rules(conflict)
            if action != ConflictAction.ASK_USER:
                return action

            # Ask user if callback is provided
            if user_callback:
                try:
                    user_action = await user_callback(conflict)
                    if isinstance(user_action, ConflictAction):
                        return user_action
                    elif isinstance(user_action, str):
                        return ConflictAction(user_action)
                except Exception as e:
                    self.logger.error(f"Error in user conflict callback: {e}")

            # Default fallback
            return ConflictAction.SKIP

        except Exception as e:
            self.logger.error(f"Error resolving conflict: {e}")
            return ConflictAction.SKIP

    def _apply_automatic_rules(self, conflict: ConflictInfo) -> ConflictAction:
        """Apply automatic conflict resolution rules"""
        if conflict.conflict_type == "exists":
            # Rule: Overwrite if source is newer
            if (self.default_rules.get("overwrite_newer", True) and
                conflict.source_modified and conflict.dest_modified):
                if conflict.source_modified > conflict.dest_modified:
                    return ConflictAction.OVERWRITE

            # Rule: Overwrite if source is larger
            if (self.default_rules.get("overwrite_larger", False) and
                conflict.source_size > conflict.dest_size):
                return ConflictAction.OVERWRITE

            # Rule: Backup and overwrite
            if self.default_rules.get("backup_on_overwrite", True):
                return ConflictAction.BACKUP

            # Default: Rename
            return ConflictAction.RENAME

        elif conflict.conflict_type == "permission":
            return ConflictAction.SKIP

        return ConflictAction.ASK_USER

    def generate_backup_name(self, original_path: Path) -> Path:
        """Generate a backup filename"""
        timestamp = int(time.time())
        stem = original_path.stem
        suffix = original_path.suffix

        backup_name = f"{stem}.backup.{timestamp}{suffix}"
        return original_path.parent / backup_name

    def generate_renamed_path(self, original_path: Path, counter: int = 1) -> Path:
        """Generate a renamed path to avoid conflicts"""
        pattern = self.default_rules.get("auto_rename_pattern", "{name}_{counter}{ext}")

        stem = original_path.stem
        suffix = original_path.suffix

        new_name = pattern.format(
            name=stem,
            counter=counter,
            ext=suffix
        )

        return original_path.parent / new_name

    def find_available_name(self, base_path: Path) -> Path:
        """Find an available filename by incrementing counter"""
        if not base_path.exists():
            return base_path

        max_attempts = self.default_rules.get("max_rename_attempts", 100)

        for counter in range(1, max_attempts + 1):
            candidate = self.generate_renamed_path(base_path, counter)
            if not candidate.exists():
                return candidate

        # If we can't find an available name, use timestamp
        timestamp = int(time.time())
        return self.generate_renamed_path(base_path, timestamp)


class BatchOperationManager:
    """Manages batch file operations with intelligent processing"""

    def __init__(self, file_ops: ComprehensiveFileOperations, config: Any = None):
        self.file_ops = file_ops
        self.config = config
        self.logger = Logger()
        self.conflict_resolver = ConflictResolver(config)

        # Batch processing settings
        self.max_parallel_operations = 4
        self.adaptive_threshold = 100  # Switch to parallel for > 100 items
        self.chunk_size = 10  # Process items in chunks

        # Active operations
        self.active_operations: Dict[str, BatchOperation] = {}
        self.operation_callbacks: Dict[str, List[Callable]] = {}

    async def execute_batch_operation(self, batch_op: BatchOperation,
                                    progress_callback: Optional[Callable] = None,
                                    conflict_callback: Optional[Callable] = None) -> OperationResult:
        """Execute a batch operation with intelligent processing"""
        try:
            # Store operation
            self.active_operations[batch_op.operation_id] = batch_op

            if progress_callback:
                if batch_op.operation_id not in self.operation_callbacks:
                    self.operation_callbacks[batch_op.operation_id] = []
                self.operation_callbacks[batch_op.operation_id].append(progress_callback)

            # Choose processing strategy
            strategy = self._choose_strategy(batch_op)

            # Execute based on strategy
            if strategy == BatchStrategy.SEQUENTIAL:
                result = await self._execute_sequential(batch_op, conflict_callback)
            elif strategy == BatchStrategy.PARALLEL:
                result = await self._execute_parallel(batch_op, conflict_callback)
            else:  # ADAPTIVE
                result = await self._execute_adaptive(batch_op, conflict_callback)

            return result

        except Exception as e:
            self.logger.error(f"Error in batch operation {batch_op.operation_id}: {e}")
            return OperationResult(
                success=False,
                message=f"Batch operation failed: {e}",
                errors=[str(e)]
            )
        finally:
            # Cleanup
            self.active_operations.pop(batch_op.operation_id, None)
            self.operation_callbacks.pop(batch_op.operation_id, None)

    def _choose_strategy(self, batch_op: BatchOperation) -> BatchStrategy:
        """Choose optimal processing strategy based on operation characteristics"""
        if batch_op.strategy != BatchStrategy.ADAPTIVE:
            return batch_op.strategy

        # Adaptive strategy selection
        item_count = len(batch_op.items)

        # For small batches, use sequential
        if item_count < 10:
            return BatchStrategy.SEQUENTIAL

        # For large batches with simple operations, use parallel
        if item_count > self.adaptive_threshold:
            if batch_op.operation_type in [OperationType.COPY, OperationType.MOVE]:
                return BatchStrategy.PARALLEL

        # Default to sequential for complex operations
        return BatchStrategy.SEQUENTIAL

    async def _execute_sequential(self, batch_op: BatchOperation,
                                conflict_callback: Optional[Callable] = None) -> OperationResult:
        """Execute batch operation sequentially"""
        results = []
        errors = []
        processed_files = []

        for i, (source, destination) in enumerate(batch_op.items):
            try:
                # Check for conflicts
                conflict = await self._check_conflict(source, destination, batch_op.operation_type)
                if conflict:
                    action = await self.conflict_resolver.resolve_conflict(conflict, conflict_callback)

                    if action == ConflictAction.SKIP:
                        batch_op.skipped_items += 1
                        continue
                    elif action == ConflictAction.RENAME:
                        destination = self.conflict_resolver.find_available_name(destination)
                    elif action == ConflictAction.BACKUP:
                        backup_path = self.conflict_resolver.generate_backup_name(destination)
                        if destination.exists():
                            destination.rename(backup_path)

                # Execute operation
                result = await self._execute_single_operation(
                    batch_op.operation_type, source, destination
                )

                if result.success:
                    batch_op.completed_items += 1
                    processed_files.extend(result.affected_files)
                else:
                    batch_op.failed_items += 1
                    errors.extend(result.errors)

                results.append(result)

                # Update progress
                await self._update_progress(batch_op, i + 1)

            except Exception as e:
                batch_op.failed_items += 1
                error_msg = f"Failed to process {source}: {e}"
                errors.append(error_msg)
                self.logger.error(error_msg)

        success = batch_op.failed_items == 0
        return OperationResult(
            success=success,
            message=f"Batch operation completed: {batch_op.completed_items} succeeded, {batch_op.failed_items} failed, {batch_op.skipped_items} skipped",
            affected_files=processed_files,
            errors=errors,
            progress=100.0
        )

    async def _execute_parallel(self, batch_op: BatchOperation,
                              conflict_callback: Optional[Callable] = None) -> OperationResult:
        """Execute batch operation in parallel"""
        semaphore = asyncio.Semaphore(batch_op.max_parallel)
        tasks = []

        async def process_item(source: Path, destination: Path, index: int):
            async with semaphore:
                try:
                    # Check for conflicts
                    conflict = await self._check_conflict(source, destination, batch_op.operation_type)
                    if conflict:
                        action = await self.conflict_resolver.resolve_conflict(conflict, conflict_callback)

                        if action == ConflictAction.SKIP:
                            batch_op.skipped_items += 1
                            return None
                        elif action == ConflictAction.RENAME:
                            destination = self.conflict_resolver.find_available_name(destination)
                        elif action == ConflictAction.BACKUP:
                            backup_path = self.conflict_resolver.generate_backup_name(destination)
                            if destination.exists():
                                destination.rename(backup_path)

                    # Execute operation
                    result = await self._execute_single_operation(
                        batch_op.operation_type, source, destination
                    )

                    if result.success:
                        batch_op.completed_items += 1
                    else:
                        batch_op.failed_items += 1

                    # Update progress
                    await self._update_progress(batch_op, batch_op.completed_items + batch_op.failed_items)

                    return result

                except Exception as e:
                    batch_op.failed_items += 1
                    self.logger.error(f"Failed to process {source}: {e}")
                    return OperationResult(
                        success=False,
                        message=str(e),
                        errors=[str(e)]
                    )

        # Create tasks for all items
        for i, (source, destination) in enumerate(batch_op.items):
            task = asyncio.create_task(process_item(source, destination, i))
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_files = []
        errors = []

        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            elif result and result.success:
                processed_files.extend(result.affected_files)
            elif result and not result.success:
                errors.extend(result.errors)

        success = batch_op.failed_items == 0
        return OperationResult(
            success=success,
            message=f"Parallel batch operation completed: {batch_op.completed_items} succeeded, {batch_op.failed_items} failed, {batch_op.skipped_items} skipped",
            affected_files=processed_files,
            errors=errors,
            progress=100.0
        )

    async def _execute_adaptive(self, batch_op: BatchOperation,
                              conflict_callback: Optional[Callable] = None) -> OperationResult:
        """Execute batch operation using adaptive strategy"""
        # Start with small parallel batch to test performance
        test_batch_size = min(5, len(batch_op.items))
        test_items = batch_op.items[:test_batch_size]
        remaining_items = batch_op.items[test_batch_size:]

        # Create test batch
        test_batch = BatchOperation(
            operation_id=f"{batch_op.operation_id}_test",
            operation_type=batch_op.operation_type,
            items=test_items,
            strategy=BatchStrategy.PARALLEL,
            max_parallel=2
        )

        start_time = time.time()
        test_result = await self._execute_parallel(test_batch, conflict_callback)
        test_duration = time.time() - start_time

        # Update main batch progress
        batch_op.completed_items += test_batch.completed_items
        batch_op.failed_items += test_batch.failed_items
        batch_op.skipped_items += test_batch.skipped_items

        if not remaining_items:
            return test_result

        # Decide strategy for remaining items based on test performance
        avg_time_per_item = test_duration / max(1, len(test_items))

        if avg_time_per_item < 0.1:  # Fast operations, use parallel
            remaining_batch = BatchOperation(
                operation_id=f"{batch_op.operation_id}_remaining",
                operation_type=batch_op.operation_type,
                items=remaining_items,
                strategy=BatchStrategy.PARALLEL,
                max_parallel=batch_op.max_parallel
            )
            remaining_result = await self._execute_parallel(remaining_batch, conflict_callback)
        else:  # Slow operations, use sequential
            remaining_batch = BatchOperation(
                operation_id=f"{batch_op.operation_id}_remaining",
                operation_type=batch_op.operation_type,
                items=remaining_items,
                strategy=BatchStrategy.SEQUENTIAL
            )
            remaining_result = await self._execute_sequential(remaining_batch, conflict_callback)

        # Update main batch progress
        batch_op.completed_items += remaining_batch.completed_items
        batch_op.failed_items += remaining_batch.failed_items
        batch_op.skipped_items += remaining_batch.skipped_items

        # Combine results
        all_files = test_result.affected_files + remaining_result.affected_files
        all_errors = test_result.errors + remaining_result.errors

        success = batch_op.failed_items == 0
        return OperationResult(
            success=success,
            message=f"Adaptive batch operation completed: {batch_op.completed_items} succeeded, {batch_op.failed_items} failed, {batch_op.skipped_items} skipped",
            affected_files=all_files,
            errors=all_errors,
            progress=100.0
        )

    async def _check_conflict(self, source: Path, destination: Path,
                            operation_type: OperationType) -> Optional[ConflictInfo]:
        """Check for potential conflicts"""
        try:
            if operation_type in [OperationType.COPY, OperationType.MOVE]:
                if destination.exists():
                    source_stat = source.stat()
                    dest_stat = destination.stat()

                    return ConflictInfo(
                        source_path=source,
                        destination_path=destination,
                        conflict_type="exists",
                        source_size=source_stat.st_size,
                        dest_size=dest_stat.st_size,
                        source_modified=time.ctime(source_stat.st_mtime),
                        dest_modified=time.ctime(dest_stat.st_mtime)
                    )

            return None

        except Exception as e:
            self.logger.error(f"Error checking conflict: {e}")
            return None

    async def _execute_single_operation(self, operation_type: OperationType,
                                      source: Path, destination: Path) -> OperationResult:
        """Execute a single file operation"""
        try:
            if operation_type == OperationType.COPY:
                return await self.file_ops.copy_files([source], destination.parent)
            elif operation_type == OperationType.MOVE:
                return await self.file_ops.move_files([source], destination.parent)
            elif operation_type == OperationType.DELETE:
                return await self.file_ops.delete_files([source])
            else:
                raise FileOperationError(operation_type.value, source, "Unsupported operation type")

        except Exception as e:
            return OperationResult(
                success=False,
                message=str(e),
                errors=[str(e)]
            )

    async def _update_progress(self, batch_op: BatchOperation, completed: int) -> None:
        """Update batch operation progress"""
        progress = (completed / batch_op.total_items) * 100 if batch_op.total_items > 0 else 0

        # Notify callbacks
        if batch_op.operation_id in self.operation_callbacks:
            for callback in self.operation_callbacks[batch_op.operation_id]:
                try:
                    await callback(progress, f"Processed {completed}/{batch_op.total_items} items")
                except Exception as e:
                    self.logger.error(f"Error in progress callback: {e}")

    def create_batch_copy(self, sources: List[Path], destination: Path,
                         options: Dict[str, Any] = None) -> BatchOperation:
        """Create a batch copy operation"""
        items = [(source, destination / source.name) for source in sources]

        return BatchOperation(
            operation_id=f"batch_copy_{int(time.time() * 1000)}",
            operation_type=OperationType.COPY,
            items=items,
            options=options or {}
        )

    def create_batch_move(self, sources: List[Path], destination: Path,
                         options: Dict[str, Any] = None) -> BatchOperation:
        """Create a batch move operation"""
        items = [(source, destination / source.name) for source in sources]

        return BatchOperation(
            operation_id=f"batch_move_{int(time.time() * 1000)}",
            operation_type=OperationType.MOVE,
            items=items,
            options=options or {}
        )

    def create_batch_delete(self, sources: List[Path],
                           options: Dict[str, Any] = None) -> BatchOperation:
        """Create a batch delete operation"""
        items = [(source, source) for source in sources]  # Destination not used for delete

        return BatchOperation(
            operation_id=f"batch_delete_{int(time.time() * 1000)}",
            operation_type=OperationType.DELETE,
            items=items,
            options=options or {}
        )

    def cancel_batch_operation(self, operation_id: str) -> bool:
        """Cancel a running batch operation"""
        if operation_id in self.active_operations:
            # In a real implementation, this would set a cancellation flag
            # that would be checked during operation execution
            self.logger.info(f"Cancelling batch operation {operation_id}")
            return True
        return False

    def get_batch_progress(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get progress information for a batch operation"""
        if operation_id in self.active_operations:
            batch_op = self.active_operations[operation_id]
            return {
                "operation_id": batch_op.operation_id,
                "operation_type": batch_op.operation_type.value,
                "total_items": batch_op.total_items,
                "completed_items": batch_op.completed_items,
                "failed_items": batch_op.failed_items,
                "skipped_items": batch_op.skipped_items,
                "progress_percent": (batch_op.completed_items / batch_op.total_items) * 100 if batch_op.total_items > 0 else 0,
                "conflicts": len(batch_op.conflicts)
            }
        return None