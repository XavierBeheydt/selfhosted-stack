"""Logger setup for dnszoner."""

from __future__ import annotations

import logging
import sys


def setup_logger(level: str = "INFO") -> logging.Logger:
    """Configure and return the ``dnszoner`` logger."""
    log_level = getattr(logging, level.upper(), None)
    if not isinstance(log_level, int):
        log_level = logging.INFO

    logger = logging.getLogger("dnszoner")
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
