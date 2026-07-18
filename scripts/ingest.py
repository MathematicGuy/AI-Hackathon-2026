#!/usr/bin/env python
"""Thin CLI wrapper. Business logic lives in backend.app.ingestion.run.

Usage:
    python scripts/ingest.py --source data/dataset
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from backend.app.ingestion.run import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
