"""Process-wide logging setup.

Entrypoints call `configure_logging()` once at start. Without it, module
loggers inherit the root logger's default, which drops INFO entirely — so
migration and ingestion output would silently vanish when those `print` calls
became log records.

Level comes from LOG_LEVEL (default INFO). Records go to stdout so the
container runtime collects them.
"""

import logging
import os
import sys

DEFAULT_LEVEL = "INFO"
_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(level: str | None = None) -> None:
    resolved = (level or os.environ.get("LOG_LEVEL") or DEFAULT_LEVEL).upper()
    if not hasattr(logging, resolved):
        resolved = DEFAULT_LEVEL
    logging.basicConfig(
        level=getattr(logging, resolved),
        format=_FORMAT,
        stream=sys.stdout,
        force=True,
    )
