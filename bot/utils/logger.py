"""Structured logging configuration using structlog.

Provides:
- JSON logging for production (machine-readable)
- Rich console logging for development (human-readable)
- Automatic context binding (timestamp, logger name, log level)
- Thread-safe, async-compatible logging

Usage:
    from bot.utils.logger import get_logger, setup_logging

    # Call once at startup:
    setup_logging(level="INFO", log_format="console")

    # Then in any module:
    logger = get_logger(__name__)
    logger.info("user.joined", user_id=12345, guild="My Server")
"""

from __future__ import annotations

import logging
import sys

import structlog


def setup_logging(
    level: str = "INFO",
    log_format: str = "console",
) -> None:
    """Configure structured logging for the entire application.

    Must be called once at application startup, before any logging occurs.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Output format — 'json' for production, 'console' for dev.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Shared processors for all outputs
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "json":
        # Production: JSON output for log aggregation
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
        shared_processors.append(
            structlog.processors.format_exc_info,
        )
    else:
        # Development: colored, human-readable output
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.plain_traceback,
        )

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure the root Python logger
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Silence noisy third-party loggers
    for noisy_logger in [
        "discord",
        "discord.http",
        "discord.gateway",
        "discord.client",
        "sqlalchemy.engine",
        "aiohttp.access",
        "urllib3",
        "httpx",
        "httpcore",
    ]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    # Allow discord.py errors through
    logging.getLogger("discord.errors").setLevel(logging.ERROR)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger bound to a specific module name.

    Args:
        name: Usually __name__ of the calling module.

    Returns:
        A structlog BoundLogger instance with the logger name bound.
    """
    return structlog.get_logger(name)
