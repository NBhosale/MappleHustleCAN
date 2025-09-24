import logging
import sys
from logging.config import dictConfig

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
        "default": {
            "format": "[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO"},
}


def setup_logging():
    """Call this once in main.py at startup."""
    dictConfig(LOGGING_CONFIG)
    logging.info("✅ Logging configured")
