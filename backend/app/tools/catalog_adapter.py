"""Read-only access to a JSON product catalog."""

import json
from pathlib import Path
from typing import Any


class CatalogAdapter:
    def __init__(self, catalog_path: Path):
        self.catalog_path = catalog_path

    def load(self) -> list[dict[str, Any]]:
        records = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise ValueError("catalog must be a list")
        return records
