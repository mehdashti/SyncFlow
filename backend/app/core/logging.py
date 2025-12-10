"""
Logging Configuration

Uses Loguru for structured logging with rotation and retention.
"""

import sys
from pathlib import Path
from loguru import logger

from app.core.config import settings


def configure_logging() -> None:
    """Configure application logging with Loguru."""

    # Remove default handler
    logger.remove()

    # Console handler with colors
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # File handler with rotation
    log_file = Path(settings.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file,
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=settings.LOG_MAX_BYTES,
        retention=settings.LOG_BACKUP_COUNT,
        compression="zip",
        serialize=False,
    )

    logger.info(f"Logging configured: level={settings.LOG_LEVEL}, file={log_file}")
