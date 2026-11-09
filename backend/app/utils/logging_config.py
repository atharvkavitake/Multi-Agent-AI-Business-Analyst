"""
Enterprise Logging Configuration Module.

Provides formatted and structured console logging for the FastAPI application,
background agents, and analytical services.
"""

import logging
import sys
from typing import Optional


def setup_logging(level: Optional[str] = "INFO") -> None:
    """
    Configure global logging format for standard output.
    """
    log_level = getattr(logging, level.upper(), logging.INFO) if level else logging.INFO

    # Custom log format with timestamp, level, module name and message
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    # Suppress overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a pre-configured logger for a specific module.

    Usage:
        logger = get_logger(__name__)
        logger.info("Message")
    """
    return logging.getLogger(name)

