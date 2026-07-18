"""Deterministic content hashing for idempotent upserts."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def content_hash(payload: Any) -> str:
    """Stable sha256 over a JSON-serializable payload.

    Keys are sorted so the same logical record always hashes identically,
    regardless of column order.
    """
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
