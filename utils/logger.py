"""
Centralized logging configuration for the Career Copilot application
Provides structured logging with different levels and formatters
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    Outputs logs in JSON format for easier parsing and analysis
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add any extra fields
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability during development
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        # Format the message
        formatted = super().format(record)

        # Reset levelname for future uses
        record.levelname = levelname

        return formatted


def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    use_json: bool = False,
    use_colors: bool = True
) -> logging.Logger:
    """
    Set up a logger with both file and console handlers

    Args:
        name: Logger name (typically __name__ of the module)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files (if None, only console logging)
        use_json: Whether to use JSON formatting for file logs
        use_colors: Whether to use colored output for console (dev mode)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, log_level.upper()))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if use_colors:
        console_format = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (if log_dir is specified)
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Create separate log files for different levels
        # Main log file
        file_handler = logging.FileHandler(
            log_path / f"career_copilot_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.DEBUG)

        # Error log file
        error_handler = logging.FileHandler(
            log_path / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        )
        error_handler.setLevel(logging.ERROR)

        # Choose formatter
        if use_json:
            file_format = JSONFormatter()
        else:
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        file_handler.setFormatter(file_format)
        error_handler.setFormatter(file_format)

        logger.addHandler(file_handler)
        logger.addHandler(error_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with default configuration

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    # Check if logger already exists
    logger = logging.getLogger(name)

    if not logger.handlers:
        # Set up with default configuration
        import os
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_dir = os.getenv('LOG_DIR', './logs')
        use_json = os.getenv('LOG_FORMAT', 'text').lower() == 'json'

        return setup_logger(
            name=name,
            log_level=log_level,
            log_dir=log_dir,
            use_json=use_json,
            use_colors=True
        )

    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """
    Custom logger adapter for adding contextual information to logs
    """

    def process(self, msg, kwargs):
        # Add extra context to the log record
        if 'extra' not in kwargs:
            kwargs['extra'] = {}

        # Merge adapter's extra with log call's extra
        kwargs['extra'].update(self.extra)

        return msg, kwargs


def log_execution_time(logger: logging.Logger):
    """
    Decorator to log function execution time

    Usage:
        @log_execution_time(logger)
        def my_function():
            pass
    """
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.debug(f"Starting {func.__name__}")

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    f"{func.__name__} completed in {execution_time:.2f}s",
                    extra={'execution_time': execution_time, 'function': func.__name__}
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed after {execution_time:.2f}s: {str(e)}",
                    extra={'execution_time': execution_time, 'function': func.__name__},
                    exc_info=True
                )
                raise

        return wrapper
    return decorator


# Example usage functions
if __name__ == "__main__":
    # Example 1: Basic logger
    logger = get_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Example 2: Logger with context
    adapter = LoggerAdapter(logger, {'user_id': 'user123', 'request_id': 'req456'})
    adapter.info("User performed action")

    # Example 3: Log execution time
    @log_execution_time(logger)
    def slow_function():
        import time
        time.sleep(1)
        return "Done"

    slow_function()
