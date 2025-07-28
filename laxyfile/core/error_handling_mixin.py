"""
ErrorHandlingMixin - Provides consistent error handling across all components

This mixin provides standardized error handling, recovery mechanisms, and fallback
behaviors for components that interact with the file manager.
"""

import time
import functools
from typing import Any, Optional, Callable, Dict, List, Union
from pathlib import Path
from datetime import datetime, timedelta

from .file_manager_service import FileManagerService
from ..utils.logger import Logger


class ErrorHandlingMixin:
    """Mixin providing consistent error handling across all components"""

    def __init__(self):
        """Initialize error handling mixin"""
        if not hasattr(self, 'logger'):
            self.logger = Logger()

        # Error tracking
        self._error_count = 0
        self._last_error_time: Optional[datetime] = None
        self._error_history: List[Dict[str, Any]] = []
        self._max_error_history = 50

        # Recovery settings
        self._max_retry_attempts = 3
        self._retry_delay_base = 1.0  # Base delay in seconds
        self._recovery_timeout = 30.0  # Max time to spend on recovery
        self._exponential_backoff_max = 10.0  # Max backoff delay

        # Automatic recovery settings
        self._auto_recovery_enabled = True
        self._recovery_attempts = 0
        self._max_recovery_attempts = 5
        self._last_recovery_attempt: Optional[datetime] = None
        self._recovery_cooldown = timedelta(minutes=1)  # Wait between recovery attempts

        # User notification callbacks
        self._notification_callbacks: List[Callable] = []
        self._recovery_status_callbacks: List[Callable] = []

        # Fallback cache
        self._fallback_cache: Dict[str, Any] = {}
        self._cache_ttl = timedelta(minutes=5)

    def safe_file_operation(self, operation: Callable, *args,
                           fallback_value: Any = None,
                           cache_key: Optional[str] = None,
                           max_retries: Optional[int] = None,
                           **kwargs) -> Optional[Any]:
        """Execute file operations with comprehensive error handling

        Args:
            operation: The operation function to execute
            *args: Arguments for the operation
            fallback_value: Value to return if operation fails
            cache_key: Key for caching results/fallbacks
    max_retries: Maximum retry attempts (overrides default)
            **kwargs: Keyword arguments for the operation

        Returns:
            Operation result or fallback value on error
        """
        operation_name = getattr(operation, '__name__', str(operation))
        max_retries = max_retries or self._max_retry_attempts

        # Check cache first if cache_key provided
        if cache_key:
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result

        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()

                # Execute the operation
                result = operation(*args, **kwargs)

                # Cache successful result
                if cache_key and result is not None:
                    self._cache_result(cache_key, result)

                # Log successful recovery if this was a retry
                if attempt > 0:
                    self.logger.info(f"Operation {operation_name} succeeded on attempt {attempt + 1}")

                return result

            except Exception as e:
                error_info = {
                    'operation': operation_name,
                    'attempt': attempt + 1,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'timestamp': datetime.now(),
                    'args': str(args)[:100],  # Truncate for logging
                    'kwargs': str(kwargs)[:100]
                }

                self._record_error(error_info)

                # If this is the last attempt, handle final failure
                if attempt >= max_retries:
                    return self._handle_final_failure(
                        operation_name, e, fallback_value, cache_key
                    )

                # Attempt recovery before retry
                if not self._attempt_recovery(operation_name, e, attempt):
                    # Recovery failed, try fallback
                    return self._handle_final_failure(
                        operation_name, e, fallback_value, cache_key
                    )

                # Wait before retry with exponential backoff
                retry_delay = self._retry_delay_base * (2 ** attempt)
                time.sleep(min(retry_delay, 5.0))  # Cap at 5 seconds

        return fallback_value

    def handle_file_manager_error(self, error: Exception, context: str = "") -> None:
        """Standardized file manager error handling

        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
        """
        error_type = type(error).__name__
        error_msg = str(error)

        # Log the error with context
        if context:
            self.logger.error(f"File manager error in {context}: {error_type}: {error_msg}")
        else:
            self.logger.error(f"File manager error: {error_type}: {error_msg}")

        # Check if this is a critical file manager error
        critical_errors = [
            'AttributeError',  # Usually 'NoneType' object has no attribute
            'TypeError',       # File manager is None
            'ImportError',     # Module loading issues
        ]

        if error_type in critical_errors and 'NoneType' in error_msg:
            self.logger.critical("Critical file manager error detected - attempting recovery")
            self._attempt_file_manager_recovery()

        # Update error statistics
        self._error_count += 1
        self._last_error_time = datetime.now()

    def get_fallback_behavior(self, operation_type: str, **kwargs) -> Any:
        """Provide fallback behavior when file manager is unavailable

        Args:
            operation_type: Type of operation that failed
            **kwargs: Additional context for fallback behavior

        Returns:
            Appropriate fallback value or behavior
        """
        fallback_behaviors = {
            'list_directory': self._fallback_list_directory,
            'get_file_info': self._fallback_get_file_info,
            'file_operations': self._fallback_file_operations,
            'preview': self._fallback_preview,
            'search': self._fallback_search
        }

        fallback_func = fallback_behaviors.get(operation_type)
        if fallback_func:
            try:
                return fallback_func(**kwargs)
            except Exception as e:
                self.logger.error(f"Fallback behavior failed for {operation_type}: {e}")

        return self._get_generic_fallback(operation_type)

    def is_file_manager_available(self) -> bool:
        """Check if file manager is available and healthy

        Returns:
            bool: True if file manager is available and working
        """
        try:
            service = FileManagerService.get_instance()
            return service.is_healthy()
        except Exception as e:
            self.logger.error(f"Error checking file manager availability: {e}")
            return False

    def ensure_file_manager_available(self) -> bool:
        """Ensure file manager is available, attempt recovery if needed

        Returns:
            bool: True if file manager is now available
        """
        if self.is_file_manager_available():
            return True

        self.logger.warning("File manager not available, attempting recovery")
        return self._attempt_file_manager_recovery()

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring and debugging

        Returns:
            Dict containing error statistics
        """
        return {
            'total_errors': self._error_count,
            'last_error_time': self._last_error_time,
            'recent_errors': self._error_history[-10:],  # Last 10 errors
            'error_rate': self._calculate_error_rate(),
            'file_manager_available': self.is_file_manager_available()
        }

    def clear_error_history(self) -> None:
        """Clear error history and reset statistics"""
        self._error_count = 0
        self._last_error_time = None
        self._error_history.clear()
        self._fallback_cache.clear()
        self._recovery_attempts = 0
        self._last_recovery_attempt = None
        self.logger.info("Error history cleared")

    def register_notification_callback(self, callback: Callable[[str, str], None]) -> None:
        """Register a callback for user notifications

        Args:
            callback: Function that takes (message, level) parameters
        """
        if callback not in self._notification_callbacks:
            self._notification_callbacks.append(callback)

    def register_recovery_status_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback for recovery status updates

        Args:
            callback: Function that takes recovery status dict
        """
        if callback not in self._recovery_status_callbacks:
            self._recovery_status_callbacks.append(callback)

    def enable_auto_recovery(self, enabled: bool = True) -> None:
        """Enable or disable automatic recovery

        Args:
            enabled: Whether to enable automatic recovery
        """
        self._auto_recovery_enabled = enabled
        self.logger.info(f"Automatic recovery {'enabled' if enabled else 'disabled'}")

    def trigger_manual_recovery(self) -> bool:
        """Manually trigger recovery process

        Returns:
            bool: True if recovery was successful
        """
        self.logger.info("Manual recovery triggered")
        self._notify_users("Attempting manual recovery...", "info")

        success = self._attempt_file_manager_recovery_with_backoff()

        if success:
            self._notify_users("Recovery successful!", "success")
        else:
            self._notify_users("Recovery failed. Please restart the application.", "error")

        return success

    def _record_error(self, error_info: Dict[str, Any]) -> None:
        """Record error information for tracking and analysis"""
        self._error_history.append(error_info)

        # Limit history size
        if len(self._error_history) > self._max_error_history:
            self._error_history = self._error_history[-self._max_error_history:]

        self._error_count += 1
        self._last_error_time = error_info['timestamp']

    def _attempt_recovery(self, operation_name: str, error: Exception, attempt: int) -> bool:
        """Attempt to recover from an error

        Args:
            operation_name: Name of the failed operation
            error: The exception that occurred
            attempt: Current attempt number

        Returns:
            bool: True if recovery was successful
        """
        try:
            self.logger.info(f"Attempting recovery for {operation_name} (attempt {attempt + 1})")

            # Check if this is a file manager related error
            if self._is_file_manager_error(error):
                return self._attempt_file_manager_recovery()

            # Generic recovery attempts
            time.sleep(0.1)  # Brief pause
            return True

        except Exception as recovery_error:
            self.logger.error(f"Recovery attempt failed: {recovery_error}")
            return False

    def _attempt_file_manager_recovery(self) -> bool:
        """Attempt to recover the file manager service

        Returns:
            bool: True if recovery was successful
        """
        try:
            self.logger.info("Attempting file manager recovery")

            service = FileManagerService.get_instance()

            # Try reinitialization
            if service.reinitialize(force=True):
                self.logger.info("File manager recovery successful")
                return True

            # If reinitialize failed, try getting a new instance
            FileManagerService.reset()
            new_service = FileManagerService.get_instance()

            if new_service.ensure_initialized():
                self.logger.info("File manager recovery successful with new instance")
                return True

            self.logger.error("File manager recovery failed")
            return False

        except Exception as e:
            self.logger.error(f"File manager recovery error: {e}")
            return False

    def _handle_final_failure(self, operation_name: str, error: Exception,
                            fallback_value: Any, cache_key: Optional[str]) -> Any:
        """Handle final failure after all retries exhausted

        Args:
            operation_name: Name of the failed operation
            error: The final exception
            fallback_value: Fallback value to return
            cache_key: Cache key for storing fallback

        Returns:
            Fallback value or cached result
        """
        self.handle_file_manager_error(error, operation_name)

        # Try to get a cached fallback
        if cache_key:
            cached_fallback = self._get_cached_fallback(cache_key)
            if cached_fallback is not None:
                self.logger.info(f"Using cached fallback for {operation_name}")
                return cached_fallback

        # Use provided fallback or generate one
        if fallback_value is not None:
            result = fallback_value
        else:
            result = self.get_fallback_behavior(operation_name)

        # Cache the fallback for future use
        if cache_key and result is not None:
            self._cache_fallback(cache_key, result)

        return result

    def _is_file_manager_error(self, error: Exception) -> bool:
        """Check if an error is related to file manager issues"""
        error_msg = str(error).lower()
        error_type = type(error).__name__

        file_manager_indicators = [
            'nonetype',
            'file_manager',
            'list_directory',
            'has no attribute',
            'not initialized'
        ]

        return (error_type in ['AttributeError', 'TypeError'] or
                any(indicator in error_msg for indicator in file_manager_indicators))

    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if available and not expired"""
        if cache_key not in self._fallback_cache:
            return None

        cached_data = self._fallback_cache[cache_key]
        if datetime.now() - cached_data['timestamp'] > self._cache_ttl:
            del self._fallback_cache[cache_key]
            return None

        return cached_data['value']

    def _cache_result(self, cache_key: str, result: Any) -> None:
        """Cache a successful result"""
        self._fallback_cache[cache_key] = {
            'value': result,
            'timestamp': datetime.now(),
            'type': 'result'
        }

    def _get_cached_fallback(self, cache_key: str) -> Optional[Any]:
        """Get cached fallback if available"""
        fallback_key = f"fallback_{cache_key}"
        return self._get_cached_result(fallback_key)

    def _cache_fallback(self, cache_key: str, fallback: Any) -> None:
        """Cache a fallback value"""
        fallback_key = f"fallback_{cache_key}"
        self._fallback_cache[fallback_key] = {
            'value': fallback,
            'timestamp': datetime.now(),
            'type': 'fallback'
        }

    def _calculate_error_rate(self) -> float:
        """Calculate recent error rate"""
        if not self._error_history:
            return 0.0

        # Calculate errors in the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_errors = [
            error for error in self._error_history
            if error['timestamp'] > one_hour_ago
        ]

        return len(recent_errors) / 60.0  # Errors per minute

    # Fallback behavior implementations

    def _fallback_list_directory(self, path: Optional[Path] = None, **kwargs) -> List[Any]:
        """Fallback behavior for directory listing"""
        if path is None:
            path = Path.cwd()

        try:
            # Try basic Python directory listing as fallback
            items = []
            if path.exists() and path.is_dir():
                for item in path.iterdir():
                    # Create minimal file info
                    items.append({
                        'name': item.name,
                        'path': item,
                        'is_dir': item.is_dir(),
                        'is_file': item.is_file(),
                        'size': item.stat().st_size if item.is_file() else 0,
                        'modified': item.stat().st_mtime
                    })
            return items
        except Exception as e:
            self.logger.error(f"Fallback directory listing failed: {e}")
            return []

    def _fallback_get_file_info(self, path: Optional[Path] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Fallback behavior for getting file information"""
        if path is None:
            return None

        try:
            if path.exists():
                stat_info = path.stat()
                return {
                    'name': path.name,
                    'path': path,
                    'is_dir': path.is_dir(),
                    'is_file': path.is_file(),
                    'size': stat_info.st_size,
                    'modified': stat_info.st_mtime,
                    'file_type': 'directory' if path.is_dir() else 'file'
                }
        except Exception as e:
            self.logger.error(f"Fallback file info failed: {e}")

        return None

    def _fallback_file_operations(self, **kwargs) -> bool:
        """Fallback behavior for file operations"""
        self.logger.warning("File operations not available - file manager unavailable")
        return False

    def _fallback_preview(self, **kwargs) -> str:
        """Fallback behavior for file preview"""
        return "Preview not available - file manager unavailable"

    def _fallback_search(self, **kwargs) -> List[Any]:
        """Fallback behavior for file search"""
        return []

    def _get_generic_fallback(self, operation_type: str) -> Any:
        """Get generic fallback for unknown operation types"""
        fallback_map = {
            'list': [],
            'get': None,
            'search': [],
            'operation': False,
            'preview': "Not available",
            'info': None
        }

        # Try to match operation type to fallback
        for key, value in fallback_map.items():
            if key in operation_type.lower():
                return value

        return None


def safe_file_operation(fallback_value: Any = None, cache_key: Optional[str] = None,
                       max_retries: int = 3):
    """Decorator for safe file operations with error handling

    Args:
        fallback_value: Value to return on failure
        cache_key: Key for caching results
        max_retries: Maximum retry attempts
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if not isinstance(self, ErrorHandlingMixin):
                # If not using mixin, create temporary error handler
                error_handler = ErrorHandlingMixin()
                return error_handler.safe_file_operation(
                    func, self, *args,
                    fallback_value=fallback_value,
                    cache_key=cache_key,
                    max_retries=max_retries,
                    **kwargs
                )
            else:
                return self.safe_file_operation(
                    func, self, *args,
                    fallback_value=fallback_value,
                    cache_key=cache_key,
                    max_retries=max_retries,
                    **kwargs
                )
        return wrapper
    return decorator