"""
Comprehensive Logging System for LaxyFile

This module provides a centralized logging system with multiple log levels,
categories, and output formats for comprehensive application monitoring.
"""

import logging
import logging.handlers
import sys
import threading
from pathlib import Path
from typing import Dict, Optional, Any, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import json


class LogLevel(Enum):
    """Log levels for different types of messages"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Categories for organizing log messages"""
    SYSTEM = "system"
    FILE_OPS = "file_ops"
    UI = "ui"
    AI = "ai"
    PLUGIN = "plugin"
    PERFORMANCE = "performance"
    SECURITY = "security"
    INTEGRATION = "integration"


@dataclass
class LogEntry:
    """Represents a single log entry"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    logger_name: str
    message: str
    extra_data: Dict[str, Any] = field(default_factory=dict)
    exception_info: Optional[str] = None


@dataclass
class LogStatistics:
    """Statistics about logging activity"""
    total_entries: int = 0
    entries_by_level: Dict[LogLevel, int] = field(default_factory=dict)
    entries_by_category: Dict[LogCategory, int] = field(default_factory=dict)
    recent_errors: List[LogEntry] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)


class LogFormatter(logging.Formatter):
    """Custom formatter for LaxyFile logs"""

    def __init__(self, include_category: bool = True):
        self.include_category = include_category
        super().__init__()

    def format(self, record):
        # Create timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        # Get category if available
        category = getattr(record, 'category', 'UNKNOWN')

        # Format message
        if self.include_category:
            formatted = f"[{timestamp}] [{record.levelname:8}] [{category:12}] {record.name}: {record.getMessage()}"
        else:
            formatted = f"[{timestamp}] [{record.levelname:8}] {record.name}: {record.getMessage()}"

        # Add exception info if present
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


class CategoryLogger:
    """Logger wrapper that adds category information"""

    def __init__(self, logger: logging.Logger, category: LogCategory):
        self.logger = logger
        self.category = category

    def debug(self, message: str, **kwargs):
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, exc_info=None, **kwargs):
        self._log(LogLevel.ERROR, message, exc_info=exc_info, **kwargs)

    def critical(self, message: str, exc_info=None, **kwargs):
        self._log(LogLevel.CRITICAL, message, exc_info=exc_info, **kwargs)

    def _log(self, level: LogLevel, message: str, exc_info=None, **kwargs):
        # Add category to extra data
        extra = {'category': self.category.value}
        extra.update(kwargs)

        # Log with appropriate level
        log_func = getattr(self.logger, level.value.lower())
        log_func(message, extra=extra, exc_info=exc_info)


class LoggingSystem:
    """Main logging system for LaxyFile"""

    def __init__(self, config):
        self.config = config
        self.loggers: Dict[str, CategoryLogger] = {}
        self.statistics = LogStatistics()
        self.log_entries: List[LogEntry] = []
        self.max_entries = config.get('logging.max_entries', 10000)
        self.lock = threading.Lock()

        # Setup root logger
        self.root_logger = logging.getLogger('laxyfile')
        self.root_logger.setLevel(logging.DEBUG)

        # Clear any existing handlers
        self.root_logger.handlers.clear()

        # Setup handlers
        self._setup_handlers()

        # Setup log capture
        self._setup_log_capture()

    def _setup_handlers(self):
        """Setup log handlers based on configuration"""
        log_config = self.config.get('logging', {})

        # Console handler
        if log_config.get('console_enabled', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_level = getattr(logging, log_config.get('console_level', 'INFO'))
            console_handler.setLevel(console_level)
            console_handler.setFormatter(LogFormatter(include_category=True))
            self.root_logger.addHandler(console_handler)

        # File handler
        if log_config.get('file_enabled', True):
            log_dir = Path(log_config.get('log_directory', '~/.laxyfile/logs')).expanduser()
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / 'laxyfile.log'
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=log_config.get('max_file_size', 10 * 1024 * 1024),  # 10MB
                backupCount=log_config.get('backup_count', 5)
            )

            file_level = getattr(logging, log_config.get('file_level', 'DEBUG'))
            file_handler.setLevel(file_level)
            file_handler.setFormatter(LogFormatter(include_category=True))
            self.root_logger.addHandler(file_handler)

        # JSON handler for structured logging
        if log_config.get('json_enabled', False):
            log_dir = Path(log_config.get('log_directory', '~/.laxyfile/logs')).expanduser()
            json_file = log_dir / 'laxyfile.json'
            json_handler = logging.FileHandler(json_file)
            json_handler.setLevel(logging.DEBUG)
            json_handler.setFormatter(self._create_json_formatter())
            self.root_logger.addHandler(json_handler)

    def _create_json_formatter(self):
        """Create JSON formatter for structured logging"""
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                    'level': record.levelname,
                    'category': getattr(record, 'category', 'UNKNOWN'),
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }

                if record.exc_info:
                    log_entry['exception'] = self.formatException(record.exc_info)

                return json.dumps(log_entry)

        return JSONFormatter()

    def _setup_log_capture(self):
        """Setup log capture for statistics and monitoring"""
        class StatisticsHandler(logging.Handler):
            def __init__(self, logging_system):
                super().__init__()
                self.logging_system = logging_system

            def emit(self, record):
                self.logging_system._capture_log_entry(record)

        stats_handler = StatisticsHandler(self)
        stats_handler.setLevel(logging.DEBUG)
        self.root_logger.addHandler(stats_handler)

    def _format_exception(self, exc_info):
        """Format exception information"""
        if exc_info:
            import traceback
            return ''.join(traceback.format_exception(*exc_info))
        return None

    def _capture_log_entry(self, record):
        """Capture log entry for statistics"""
        with self.lock:
            # Create log entry
            level = LogLevel(record.levelname)
            category = LogCategory(getattr(record, 'category', 'system'))

            entry = LogEntry(
                timestamp=datetime.fromtimestamp(record.created),
                level=level,
                category=category,
                logger_name=record.name,
                message=record.getMessage(),
                exception_info=self._format_exception(record.exc_info) if record.exc_info else None
            )

            # Add to entries list
            self.log_entries.append(entry)

            # Maintain max entries limit
            if len(self.log_entries) > self.max_entries:
                self.log_entries = self.log_entries[-self.max_entries:]

            # Update statistics
            self.statistics.total_entries += 1

            if level not in self.statistics.entries_by_level:
                self.statistics.entries_by_level[level] = 0
            self.statistics.entries_by_level[level] += 1

            if category not in self.statistics.entries_by_category:
                self.statistics.entries_by_category[category] = 0
            self.statistics.entries_by_category[category] += 1

            # Track recent errors
            if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                self.statistics.recent_errors.append(entry)
                # Keep only last 50 errors
                if len(self.statistics.recent_errors) > 50:
                    self.statistics.recent_errors = self.statistics.recent_errors[-50:]

    def get_logger(self, name: str, category: LogCategory) -> CategoryLogger:
        """Get a logger for a specific component and category"""
        logger_key = f"{name}_{category.value}"

        if logger_key not in self.loggers:
            base_logger = logging.getLogger(f"laxyfile.{name}")
            self.loggers[logger_key] = CategoryLogger(base_logger, category)

        return self.loggers[logger_key]

    def get_log_statistics(self) -> LogStatistics:
        """Get current logging statistics"""
        with self.lock:
            return LogStatistics(
                total_entries=self.statistics.total_entries,
                entries_by_level=self.statistics.entries_by_level.copy(),
                entries_by_category=self.statistics.entries_by_category.copy(),
                recent_errors=self.statistics.recent_errors.copy(),
                start_time=self.statistics.start_time
            )

    def get_recent_logs(self, count: int = 100, level: Optional[LogLevel] = None,
                       category: Optional[LogCategory] = None) -> List[LogEntry]:
        """Get recent log entries with optional filtering"""
        with self.lock:
            entries = self.log_entries.copy()

        # Apply filters
        if level:
            entries = [e for e in entries if e.level == level]

        if category:
            entries = [e for e in entries if e.category == category]

        # Return most recent entries
        return entries[-count:]

    def clear_logs(self):
        """Clear all stored log entries"""
        with self.lock:
            self.log_entries.clear()
            self.statistics = LogStatistics()

    def set_log_level(self, level: LogLevel):
        """Set the global log level"""
        log_level = getattr(logging, level.value)
        self.root_logger.setLevel(log_level)

        # Update all handlers
        for handler in self.root_logger.handlers:
            handler.setLevel(log_level)

    def shutdown(self):
        """Shutdown the logging system"""
        logging.shutdown()


# Global logging system instance
_logging_system: Optional[LoggingSystem] = None


def initialize_logging(config) -> LoggingSystem:
    """Initialize the global logging system"""
    global _logging_system
    _logging_system = LoggingSystem(config)
    return _logging_system


def get_logging_system() -> Optional[LoggingSystem]:
    """Get the global logging system instance"""
    return _logging_system


def get_logger(name: str, category: LogCategory) -> CategoryLogger:
    """Get a logger for a specific component and category"""
    if _logging_system is None:
        raise RuntimeError("Logging system not initialized")
    return _logging_system.get_logger(name, category)