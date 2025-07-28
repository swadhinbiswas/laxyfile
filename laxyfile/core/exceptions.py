"""
Exception Classes

This module defines all custom exception classes used throughout LaxyFile
for consistent error handling and reporting.
"""

from pathlib import Path
from typing import Optional, List, Any


class LaxyFileError(Exception):
    """Base exception class for all LaxyFile errors"""

    def __init__(self, message: str, details: Optional[str] = None,
                 error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.details = details
        self.error_code = error_code

    def __str__(self) -> str:
        result = self.message
        if self.details:
            result += f"\nDetails: {self.details}"
        if self.error_code:
            result += f"\nError Code: {self.error_code}"
        return result


class FileOperationError(LaxyFileError):
    """Exception raised during file operations"""

    def __init__(self, operation: str, path: Path, message: str,
                 original_error: Optional[Exception] = None):
        super(__init__(message))
        self.operation = operation
        self.path = path
        self.original_error = original_error

    def __str__(self) -> str:
        result = f"File operation '{self.operation}' failed for '{self.path}': {self.message}"
        if self.original_error:
            result += f"\nOriginal error: {self.original_error}"
        return result


class PermissionError(FileOperationError):
    """Exception raised when permission is denied"""


class APIError(LaxyFileError):
    """Exception raised during API operations"""

    def __init__(self, api_name: str, operation: str, message: str,
                 status_code: Optional[int] = None):
        super().__init__(message)
        self.api_name = api_name
        self.operation = operation
        self.status_code = status_code

    def __str__(self) -> str:
        result = f"API '{self.api_name}' operation '{self.operation}' failed: {self.message}"
        if self.status_code:
            result += f" (Status: {self.status_code})"
        return result

    def __init__(self, path: Path, operation: str = "access"):
        super().__init__(
            operation=operation,
            path=path,
            message=f"Permission denied for {operation} operation",
            original_error=None
        )


class FileNotFoundError(FileOperationError):
    """Exception raised when file is not found"""

    def __init__(self, path: Path, operation: str = "access"):
        super().__init__(
            operation=operation,
            path=path,
            message="File or directory not found",
            original_error=None
        )


class DirectoryNotEmptyError(FileOperationError):
    """Exception raised when trying to delete non-empty directory"""

    def __init__(self, path: Path):
        super().__init__(
            operation="delete",
            path=path,
            message="Directory is not empty",
            original_error=None
        )


class DiskSpaceError(FileOperationError):
    """Exception raised when insufficient disk space"""

    def __init__(self, path: Path, required_space: int, available_space: int):
        super().__init__(
            operation="write",
            path=path,
            message=f"Insufficient disk space. Required: {required_space}, Available: {available_space}",
            original_error=None
        )
        self.required_space = required_space
        self.available_space = available_space


class ArchiveError(LaxyFileError):
    """Exception raised during archive operations"""

    def __init__(self, archive_path: Path, operation: str, message: str,
                 original_error: Optional[Exception] = None):
        super().__init__(message)
        self.archive_path = archive_path
        self.operation = operation
        self.original_error = original_error

    def __str__(self) -> str:
        result = f"Archive operation '{self.operation}' failed for '{self.archive_path}': {self.message}"
        if self.original_error:
            result += f"\nOriginal error: {self.original_error}"
        return result


class UnsupportedArchiveFormatError(ArchiveError):
    """Exception raised for unsupported archive formats"""

    def __init__(self, archive_path: Path, format_name: str):
        super().__init__(
            archive_path=archive_path,
            operation="format_detection",
            message=f"Unsupported archive format: {format_name}",
            original_error=None
        )
        self.format_name = format_name


class CorruptedArchiveError(ArchiveError):
    """Exception raised for corrupted archives"""

    def __init__(self, archive_path: Path):
        super().__init__(
            archive_path=archive_path,
            operation="read",
            message="Archive file is corrupted or invalid",
            original_error=None
        )


class ConfigurationError(LaxyFileError):
    """Exception raised for configuration-related errors"""

    def __init__(self, config_key: str, message: str,
                 config_file: Optional[Path] = None):
        super().__init__(message)
        self.config_key = config_key
        self.config_file = config_file

    def __str__(self) -> str:
        result = f"Configuration error for '{self.config_key}': {self.message}"
        if self.config_file:
            result += f"\nConfig file: {self.config_file}"
        return result


class InvalidConfigValueError(ConfigurationError):
    """Exception raised for invalid configuration values"""

    def __init__(self, config_key: str, value: Any, expected_type: str,
                 config_file: Optional[Path] = None):
        super().__init__(
            config_key=config_key,
            message=f"Invalid value '{value}' for configuration key. Expected: {expected_type}",
            config_file=config_file
        )
        self.value = value
        self.expected_type = expected_type


class MissingConfigError(ConfigurationError):
    """Exception raised for missing required configuration"""

    def __init__(self, config_key: str, config_file: Optional[Path] = None):
        super().__init__(
            config_key=config_key,
            message=f"Required configuration key is missing",
            config_file=config_file
        )


class InputError(LaxyFileError):
    """Exception raised for invalid user input"""

    def __init__(self, input_value: str, message: str,
                 expected_format: Optional[str] = None):
        super().__init__(message)
        self.input_value = input_value
        self.expected_format = expected_format

    def __str__(self) -> str:
        result = f"Invalid input '{self.input_value}': {self.message}"
        if self.expected_format:
            result += f"\nExpected format: {self.expected_format}"
        return result


class AIError(LaxyFileError):
    """Exception raised during AI operations"""

    def __init__(self, operation: str, message: str,
                 model: Optional[str] = None, query: Optional[str] = None,
                 original_error: Optional[Exception] = None):
        super().__init__(message)
        self.operation = operation
        self.model = model
        self.query = query
        self.original_error = original_error

    def __str__(self) -> str:
        result = f"AI operation '{self.operation}' failed: {self.message}"
        if self.model:
            result += f"\nModel: {self.model}"
        if self.query:
            result += f"\nQuery: {self.query[:100]}..."
        if self.original_error:
            result += f"\nOriginal error: {self.original_error}"
        return result


class AINotConfiguredError(AIError):
    """Exception raised when AI is not properly configured"""

    def __init__(self, missing_config: List[str]):
        super().__init__(
            operation="initialization",
            message=f"AI not configured. Missing: {', '.join(missing_config)}",
            original_error=None
        )
        self.missing_config = missing_config


class AIQuotaExceededError(AIError):
    """Exception raised when AI quota is exceeded"""

    def __init__(self, model: str, reset_time: Optional[str] = None):
        message = f"AI quota exceeded for model '{model}'"
        if reset_time:
            message += f". Quota resets at: {reset_time}"

        super().__init__(
            operation="query",
            message=message,
            model=model,
            original_error=None
        )
        self.reset_time = reset_time


class PreviewError(LaxyFileError):
    """Exception raised during preview generation"""

    def __init__(self, file_path: Path, preview_type: str, message: str,
                 original_error: Optional[Exception] = None):
        super().__init__(message)
        self.file_path = file_path
        self.preview_type = preview_type
        self.original_error = original_error

    def __str__(self) -> str:
        result = f"Preview generation failed for '{self.file_path}' (type: {self.preview_type}): {self.message}"
        if self.original_error:
            result += f"\nOriginal error: {self.original_error}"
        return result


class UnsupportedPreviewFormatError(PreviewError):
    """Exception raised for unsupported preview formats"""

    def __init__(self, file_path: Path, file_type: str):
        super().__init__(
            file_path=file_path,
            preview_type=file_type,
            message=f"Preview not supported for file type: {file_type}",
            original_error=None
        )


class ThemeError(LaxyFileError):
    """Exception raised during theme operations"""

    def __init__(self, theme_name: str, operation: str, message: str,
                 original_error: Optional[Exception] = None):
        super().__init__(message)
        self.theme_name = theme_name
        self.operation = operation
        self.original_error = original_error

    def __str__(self) -> str:
        result = f"Theme operation '{self.operation}' failed for theme '{self.theme_name}': {self.message}"
        if self.original_error:
            result += f"\nOriginal error: {self.original_error}"
        return result


class ThemeNotFoundError(ThemeError):
    """Exception raised when theme is not found"""

    def __init__(self, theme_name: str):
        super().__init__(
            theme_name=theme_name,
            operation="load",
            message="Theme not found",
            original_error=None
        )


class InvalidThemeError(ThemeError):
    """Exception raised for invalid theme configuration"""

    def __init__(self, theme_name: str, validation_errors: List[str]):
        super().__init__(
            theme_name=theme_name,
            operation="validation",
            message=f"Invalid theme configuration: {', '.join(validation_errors)}",
            original_error=None
        )
        self.validation_errors = validation_errors


class PluginError(LaxyFileError):
    """Exception raised during plugin operations"""

    def __init__(self, plugin_name: str, operation: str, message: str,
                 original_error: Optional[Exception] = None):
        super().__init__(message)
        self.plugin_name = plugin_name
        self.operation = operation
        self.original_error = original_error

    def __str__(self) -> str:
        result = f"Plugin operation '{self.operation}' failed for plugin '{self.plugin_name}': {self.message}"
        if self.original_error:
            result += f"\nOriginal error: {self.original_error}"
        return result


class PluginNotFoundError(PluginError):
    """Exception raised when plugin is not found"""

    def __init__(self, plugin_name: str):
        super().__init__(
            plugin_name=plugin_name,
            operation="load",
            message="Plugin not found",
            original_error=None
        )


class PluginDependencyError(PluginError):
    """Exception raised for plugin dependency issues"""

    def __init__(self, plugin_name: str, missing_dependencies: List[str]):
        super().__init__(
            plugin_name=plugin_name,
            operation="dependency_check",
            message=f"Missing dependencies: {', '.join(missing_dependencies)}",
            original_error=None
        )
        self.missing_dependencies = missing_dependencies


class PlatformError(LaxyFileError):
    """Exception raised for platform-specific operations"""

    def __init__(self, platform: str, operation: str, message: str,
                 original_error: Optional[Exception] = None):
        super().__init__(message)
        self.platform = platform
        self.operation = operation
        self.original_error = original_error

    def __str__(self) -> str:
        result = f"Platform operation '{self.operation}' failed on {self.platform}: {self.message}"
        if self.original_error:
            result += f"\nOriginal error: {self.original_error}"
        return result


class UnsupportedPlatformError(PlatformError):
    """Exception raised for unsupported platform operations"""

    def __init__(self, platform: str, operation: str):
        super().__init__(
            platform=platform,
            operation=operation,
            message=f"Operation not supported on this platform",
            original_error=None
        )


class CacheError(LaxyFileError):
    """Exception raised during cache operations"""

    def __init__(self, operation: str, key: str, message: str,
                 original_error: Optional[Exception] = None):
        super().__init__(message)
        self.operation = operation
        self.key = key
        self.original_error = original_error

    def __str__(self) -> str:
        result = f"Cache operation '{self.operation}' failed for key '{self.key}': {self.message}"
        if self.original_error:
            result += f"\nOriginal error: {self.original_error}"
        return result


class CacheFullError(CacheError):
    """Exception raised when cache is full"""

    def __init__(self, key: str, cache_size: int, max_size: int):
        super().__init__(
            operation="set",
            key=key,
            message=f"Cache is full. Current size: {cache_size}, Max size: {max_size}",
            original_error=None
        )
        self.cache_size = cache_size
        self.max_size = max_size


class PerformanceError(LaxyFileError):
    """Exception raised during performance operations"""

    def __init__(self, operation: str, message: str,
                 original_error: Optional[Exception] = None):
        super().__init__(message)
        self.operation = operation
        self.original_error = original_error

    def __str__(self) -> str:
        result = f"Performance operation '{self.operation}' failed: {self.message}"
        if self.original_error:
            result += f"\nOriginal error: {self.original_error}"
        return result