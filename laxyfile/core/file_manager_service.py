"""
FileManagerService - Thread-safe singleton service for file management

This module provides a centralized, thread-safe file manager service that ensures
the file manager is always available when needed and handles initialization errors gracefully.
"""

import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from .file_manager import FileManager
from .advanced_file_manager import AdvancedFileManager
from .config import Config
from ..utils.logger import Logger


class FileManagerService:
    """Thread-safe singleton service for file management"""

    _instance: Optional['FileManagerService'] = None
    _lock = threading.Lock()
    _initialized = False

    def __init__(self):
        """Private constructor - use get_instance() instead"""
        if FileManagerService._instance is not None:
            raise RuntimeError("Use FileManagerService.get_instance() instead of direct instantiation")

        self.logger = Logger()
        self._file_manager: Optional[FileManager] = None
        self._advanced_file_manager: Optional[AdvancedFileManager] = None
        self._config: Optional[Config] = None
        self._initialization_lock = threading.Lock()
        self._initialization_attempts = 0
        self._last_initialization_attempt: Optional[datetime] = None
        self._initialization_error: Optional[str] = None
        self._use_advanced = False

    @classmethod
    def get_instance(cls) -> 'FileManagerService':
        """Get the singleton instance with thread-safe lazy initialization"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def initialize(self, config: Optional[Config] = None, use_advanced: bool = False) -> bool:
        """Initialize the file manager service

        Args:
            config: Configuration object (optional)
            use_advanced: Whether to use AdvancedFileManager (default: False)

        Returns:
            bool: True if initialization successful, False otherwise
        """
        with self._initialization_lock:
            try:
                self._config = config or Config()
                self._use_advanced = use_advanced
                self._initialization_attempts += 1
                self._last_initialization_attempt = datetime.now()

                if use_advanced:
                    self._advanced_file_manager = AdvancedFileManager(self._config)
                    # Initialize async components if available
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Schedule initialization in the background
                            asyncio.create_task(self._advanced_file_manager.initialize())
                        else:
                            # Run initialization synchronously
                            loop.run_until_complete(self._advanced_file_manager.initialize())
                    except RuntimeError:
                        # No event loop, skip async initialization
                        self.logger.warning("No event loop available for advanced file manager initialization")
                else:
                    self._file_manager = FileManager()

                FileManagerService._initialized = True
                self._initialization_error = None
                self.logger.info(f"FileManagerService initialized successfully (advanced={use_advanced})")
                return True

            except Exception as e:
                self._initialization_error = str(e)
                self.logger.error(f"Failed to initialize FileManagerService: {e}")
                return False

    def ensure_initialized(self) -> bool:
        """Ensure the file manager is properly initialized

        Returns:
            bool: True if file manager is available, False otherwise
        """
        if not FileManagerService._initialized or (not self._file_manager and not self._advanced_file_manager):
            return self.initialize()
        return True

    def reinitialize(self, force: bool = False) -> bool:
        """Attempt to reinitialize the file manager

        Args:
            force: Force reinitialization even if already initialized

        Returns:
            bool: True if reinitialization successful, False otherwise
        """
        if not force and self.is_healthy():
            return True

        with self._initialization_lock:
            try:
                # Reset state
                FileManagerService._initialized = False
                self._file_manager = None
                self._advanced_file_manager = None

                # Attempt reinitialization
                return self.initialize(self._config, self._use_advanced)

            except Exception as e:
                self.logger.error(f"Failed to reinitialize FileManagerService: {e}")
                return False

    def get_file_manager(self) -> Optional[FileManager]:
        """Get the file manager instance with automatic initialization

        Returns:
            FileManager instance or None if initialization failed
        """
        if not self.ensure_initialized():
            return None

        if self._use_advanced:
            return self._advanced_file_manager
        else:
            return self._file_manager

    def is_healthy(self) -> bool:
        """Check if the file manager service is healthy

        Returns:
            bool: True if service is healthy and ready to use
        """
        try:
            if not FileManagerService._initialized:
                return False

            file_manager = self._advanced_file_manager if self._use_advanced else self._file_manager
            if file_manager is None:
                return False

            # Test basic functionality
            if hasattr(file_manager, 'list_directory'):
                # Try to list current directory as a health check
                test_path = Path.cwd()
                if self._use_advanced:
                    # For advanced file manager, we need to handle async
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Can't test async in running loop, assume healthy
                            return True
                        else:
                            loop.run_until_complete(file_manager.list_directory(test_path))
                    except RuntimeError:
                        # No event loop, assume healthy if object exists
                        return True
                else:
                    file_manager.list_directory(test_path)
                return True

            return False

        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get detailed status information about the service

        Returns:
            Dict containing status information
        """
        return {
            'initialized': FileManagerService._initialized,
            'healthy': self.is_healthy(),
            'use_advanced': self._use_advanced,
            'initialization_attempts': self._initialization_attempts,
            'last_initialization_attempt': self._last_initialization_attempt,
            'initialization_error': self._initialization_error,
            'has_file_manager': self._file_manager is not None,
            'has_advanced_file_manager': self._advanced_file_manager is not None
        }

    def list_directory(self, path: Path, show_hidden: bool = False, **kwargs):
        """Safe wrapper for list_directory operation

        Args:
            path: Directory path to list
            show_hidden: Whether to show hidden files
            **kwargs: Additional arguments for advanced file manager

        Returns:
            List of file information or empty list on error
        """
        try:
            file_manager = self.get_file_manager()
            if file_manager is None:
                self.logger.error("File manager not available for list_directory")
                return []

            if self._use_advanced:
                # Handle async call for advanced file manager
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Create a task for async execution
                        task = asyncio.create_task(
                            file_manager.list_directory(path, show_hidden, **kwargs)
                        )
                        # For now, return empty list and log warning
                        # In a real implementation, this would need proper async handling
                        self.logger.warning("Async list_directory called from sync context")
                        return []
                    else:
                        return loop.run_until_complete(
                            file_manager.list_directory(path, show_hidden, **kwargs)
                        )
                except RuntimeError:
                    # Fallback to basic file manager
                    if self._file_manager is None:
                        self._file_manager = FileManager()
                    return self._file_manager.list_directory(path, show_hidden)
            else:
                return file_manager.list_directory(path, show_hidden)

        except Exception as e:
            self.logger.error(f"Error in list_directory: {e}")
            return []

    def safe_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """Execute a file operation safely with error handling

        Args:
            operation_name: Name of the operation for logging
            operation_func: Function to execute
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            Operation result or None on error
        """
        try:
            file_manager = self.get_file_manager()
            if file_manager is None:
                self.logger.error(f"File manager not available for {operation_name}")
                return None

            if not hasattr(file_manager, operation_func.__name__):
                self.logger.error(f"Operation {operation_func.__name__} not available on file manager")
                return None

            return operation_func(*args, **kwargs)

        except Exception as e:
            self.logger.error(f"Error in {operation_name}: {e}")

            # Attempt recovery
            if self.reinitialize():
                try:
                    file_manager = self.get_file_manager()
                    if file_manager and hasattr(file_manager, operation_func.__name__):
                        return operation_func(*args, **kwargs)
                except Exception as recovery_error:
                    self.logger.error(f"Recovery attempt failed for {operation_name}: {recovery_error}")

            return None

    @classmethod
    def reset(cls):
        """Reset the singleton instance (mainly for testing)"""
        with cls._lock:
            cls._instance = None
            cls._initialized = False


# Convenience functions for common operations
def get_file_manager_service() -> FileManagerService:
    """Get the file manager service instance"""
    return FileManagerService.get_instance()


def safe_list_directory(path: Path, show_hidden: bool = False, **kwargs):
    """Safely list directory contents"""
    service = get_file_manager_service()
    return service.list_directory(path, show_hidden, **kwargs)


def ensure_file_manager_available() -> bool:
    """Ensure file manager is available and healthy"""
    service = get_file_manager_service()
    return service.ensure_initialized() and service.is_healthy()