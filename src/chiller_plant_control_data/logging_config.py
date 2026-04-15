"""Centralized logging setup for the project."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024
DEFAULT_BACKUP_COUNT = 5


def setup_logger(
    log_level: str = "INFO",
    *,
    log_dir: str | Path = "log",
    log_file_name: str = "app.log",
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> logging.Logger:
    """Configure root logger with console and rotating file handlers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if root_logger.handlers:
        return root_logger

    target_dir = Path(log_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=target_dir / log_file_name,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Return a named logger using the shared logging setup."""
    return logging.getLogger(name)

