# Copyright (c) 2025 TOON Format Organization
# SPDX-License-Identifier: MIT
"""Centralized logging configuration for toon_format.

This module provides consistent logging infrastructure across all toon_format
modules with support for the TOON_FORMAT_DEBUG environment variable for
enabling debug-level logging.
"""

import logging
import os
from functools import lru_cache
from typing import Optional

# Constants
TOON_FORMAT_DEBUG_ENV_VAR = "TOON_FORMAT_DEBUG"
DEFAULT_LOG_LEVEL = logging.WARNING
DEBUG_LOG_LEVEL = logging.DEBUG


@lru_cache(maxsize=1)
def is_debug_enabled() -> bool:
    """Check if TOON_FORMAT_DEBUG environment variable is set to truthy value.

    Accepts: "1", "true", "True", "TRUE", "yes", "Yes", "YES"

    Returns:
        bool: True if debug mode is enabled, False otherwise.

    Note:
        Result is cached for performance.
    """
    value = os.environ.get(TOON_FORMAT_DEBUG_ENV_VAR, "").lower()
    return value in ("1", "true", "yes")


def get_logger(name: str) -> logging.Logger:
    """Create or retrieve logger for given module name.

    Configures logger with appropriate level based on environment variable
    and adds a StreamHandler with consistent formatting.

    Args:
        name: Module name (typically __name__).

    Returns:
        logging.Logger: Configured logger instance.

    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.debug("Debug message")  # Only shown if TOON_FORMAT_DEBUG=1
    """
    logger = logging.getLogger(name)

    # Set log level based on debug mode
    level = DEBUG_LOG_LEVEL if is_debug_enabled() else DEFAULT_LOG_LEVEL
    logger.setLevel(level)

    # Add StreamHandler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def configure_logging(level: Optional[int] = None) -> None:
    """Configure log level programmatically for all toon_format loggers.

    Useful for testing and programmatic control of logging.

    Args:
        level: Log level (e.g., logging.DEBUG, logging.INFO).
               If None, uses environment variable or default.

    Examples:
        >>> configure_logging(logging.DEBUG)  # Enable debug logging
        >>> configure_logging(logging.WARNING)  # Reset to default
    """
    if level is None:
        level = DEBUG_LOG_LEVEL if is_debug_enabled() else DEFAULT_LOG_LEVEL

    # Update all existing toon_format loggers
    for name in list(logging.Logger.manager.loggerDict.keys()):
        if name.startswith("toon_format"):
            logger = logging.getLogger(name)
            logger.setLevel(level)
            for handler in logger.handlers:
                handler.setLevel(level)
