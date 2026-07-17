from __future__ import annotations

import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import CategoryConfig, LocationConfig


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///data/dmx.db"
    site_base_url: str = "https://www.dienmayxanh.com"
    user_agent: str = "DMXCrawler/0.1 (+respectful research)"
    min_request_interval_seconds: float = 5.0
    request_timeout_seconds: float = 30.0
    max_attempts: int = 3
    locations_file: str = "config/locations.yaml"
    categories_file: str = "config/categories.yaml"
    sitemap_index_path: str = "/newsitemap/sitemap-product"

    @classmethod
    def from_env(cls) -> "Settings":
        def value(name: str, default: Any) -> Any:
            return os.getenv(name, default)

        return cls(
            database_url=value("DMX_DATABASE_URL", cls.database_url),
            site_base_url=value("DMX_SITE_BASE_URL", cls.site_base_url).rstrip("/"),
            user_agent=value("DMX_USER_AGENT", cls.user_agent),
            min_request_interval_seconds=float(value("DMX_MIN_REQUEST_INTERVAL_SECONDS", cls.min_request_interval_seconds)),
            request_timeout_seconds=float(value("DMX_REQUEST_TIMEOUT_SECONDS", cls.request_timeout_seconds)),
            max_attempts=int(value("DMX_MAX_ATTEMPTS", cls.max_attempts)),
            locations_file=value("DMX_LOCATIONS_FILE", cls.locations_file),
            categories_file=value("DMX_CATEGORIES_FILE", cls.categories_file),
        )


def _scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value.startswith(("\"", "'")) and value.endswith(value[0]):
        return value[1:-1]
    if value.lower() in {"true", "yes"}:
        return True
    if value.lower() in {"false", "no"}:
        return False
    if value.lower() in {"null", "none", "~"}:
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [str(_scalar(part)) for part in inner.split(",") if part.strip()] if inner else []
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def _simple_yaml(path: str | Path) -> dict[str, Any]:
    """Parse the intentionally small config YAML used by this project.

    PyYAML is optional.  This fallback handles mappings, a top-level list and
    scalar/list values, which keeps the CLI runnable without downloading a
    dependency in an air-gapped environment.
    """

    try:
        import yaml  # type: ignore

        with open(path, "r", encoding="utf-8") as handle:
            result = yaml.safe_load(handle)
        return result or {}
    except ImportError:
        pass
    result: dict[str, Any] = {}
    current_list: list[dict[str, Any]] | None = None
    current_key: str | None = None
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.split("#", 1)[0].rstrip()
            if not line.strip():
                continue
            stripped = line.strip()
            if stripped.endswith(":") and not stripped.startswith("-"):
                current_key = stripped[:-1].strip()
                current_list = []
                result[current_key] = current_list
                continue
            if stripped.startswith("-"):
                if current_list is None:
                    continue
                item: dict[str, Any] = {}
                current_list.append(item)
                remainder = stripped[1:].strip()
                if ":" in remainder:
                    key, val = remainder.split(":", 1)
                    item[key.strip()] = _scalar(val)
                continue
            if ":" not in stripped:
                continue
            key, val = stripped.split(":", 1)
            key = key.strip()
            if current_list and raw.startswith((" ", "\t")):
                current_list[-1][key] = _scalar(val)
            else:
                result[key] = _scalar(val)
    return result


def load_locations(path: str | Path) -> list[LocationConfig]:
    data = _simple_yaml(path).get("locations", [])
    locations: list[LocationConfig] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        locations.append(
            LocationConfig(
                code=str(item["code"]),
                name=str(item.get("name", item["code"])),
                province_id=int(item["province_id"]),
                province_name=str(item.get("province_name", item.get("name", ""))),
                ward_id=int(item.get("ward_id", 0)),
                ward_name=str(item.get("ward_name", "")),
                address=str(item.get("address") or ""),
                aliases=tuple(str(x) for x in item.get("aliases", []) or []),
                active=bool(item.get("active", True)),
            )
        )
    return locations


def load_categories(path: str | Path, base_url: str = "https://www.dienmayxanh.com") -> list[CategoryConfig]:
    data = _simple_yaml(path).get("categories", [])
    categories: list[CategoryConfig] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        code = str(item["code"])
        categories.append(
            CategoryConfig(
                code=code,
                name=str(item.get("name", code)),
                url=str(item.get("url", f"{base_url}/{code}")),
                path_prefix=str(item.get("path_prefix", f"/{code}/")),
                active=bool(item.get("active", True)),
            )
        )
    return categories
