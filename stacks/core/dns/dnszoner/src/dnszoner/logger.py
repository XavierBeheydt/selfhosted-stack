# Copyright © 2026 Xavier Beheydt <xavier.beheydt@gmail.com> - All Rights Reserved

"""
Logger setup for DNSZoner.
"""

import logging
import sys


def setup_logger(level: str = "INFO") -> logging.Logger:
    """Setup and return the DNSZoner logger."""
    logger = logging.getLogger("dnszoner")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
