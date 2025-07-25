"""
Logging utility for LaxyFile
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

class Logger:
    """Centralized logging for LaxyFile"""

    def __init__(self, name: str = "LaxyFile", log_file: Optional[Path] = None):
        self.logger = logging.getLogger(name)

        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)

            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # File handler (if specified or default)
            if log_file is None:
                log_dir = Path.home() / ".config" / "laxyfile" / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file = log_dir / f"laxyfile_{datetime.now().strftime('%Y%m%d')}.log"

            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                self.logger.warning(f"Could not create file handler: {e}")

    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)

    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)

    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)

    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)