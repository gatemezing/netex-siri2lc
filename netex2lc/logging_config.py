"""Logging configuration for netex2lc and siri2lc."""
from __future__ import annotations

import logging
import sys
from typing import Optional


class ParsingError(Exception):
    """Raised when parsing fails in strict mode."""

    pass


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def setup_logging(verbose: bool = False, quiet: bool = False) -> logging.Logger:
    """Configure and return logger for the application."""
    logger = logging.getLogger("netex2lc")

    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.WARNING

    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        formatter = logging.Formatter(
            "%(levelname)s: %(message)s" if not verbose else "%(levelname)s [%(name)s] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_logger() -> logging.Logger:
    """Get the application logger."""
    return logging.getLogger("netex2lc")


class ParsingContext:
    """Context for tracking parsing statistics and errors."""

    def __init__(self, strict: bool = False):
        self.strict = strict
        self.logger = get_logger()
        self.skipped_count = 0
        self.processed_count = 0
        self.errors: list[str] = []

    def skip(self, reason: str, element_id: Optional[str] = None):
        """Record a skipped element."""
        self.skipped_count += 1
        msg = f"Skipped: {reason}"
        if element_id:
            msg = f"Skipped [{element_id}]: {reason}"
        self.logger.debug(msg)
        self.errors.append(msg)

        if self.strict:
            raise ParsingError(msg)

    def success(self, element_id: Optional[str] = None):
        """Record a successfully processed element."""
        self.processed_count += 1
        if element_id:
            self.logger.debug(f"Processed: {element_id}")

    def report(self):
        """Log a summary of parsing results."""
        self.logger.info(
            f"Parsing complete: {self.processed_count} processed, {self.skipped_count} skipped"
        )
        if self.skipped_count > 0 and self.logger.level > logging.DEBUG:
            self.logger.warning(
                f"{self.skipped_count} elements skipped. Use --verbose for details."
            )
