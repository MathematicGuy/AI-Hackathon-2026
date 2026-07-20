"""Validated runtime access to the representative-image mapping."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from backend.app.catalog_images.representative import (
    IMAGE_TYPE,
    assign_representative_image,
    group_key,
    normalize_image_url,
    validate_source_url,
)

DEFAULT_MAPPING_PATH = (
    Path(__file__).resolve().parent / "data" / "representative_images.v1.json"
)
PLACEHOLDER_IMAGE_URL = "/images/products/representative-placeholder.svg"


class ProductIdentity(Protocol):
    category_code: str
    brand_id: str | None
    brand: str | None
    sku: str | None


@dataclass(frozen=True, slots=True)
class RepresentativeImageMapping:
    mapping_version: int
    generated_at: str
    groups: dict[str, dict]

    @classmethod
    def from_payload(cls, payload: dict) -> "RepresentativeImageMapping":
        version = payload.get("mapping_version")
        generated_at = payload.get("generated_at")
        groups = payload.get("groups")
        if not isinstance(version, int) or version < 1:
            raise ValueError("mapping_version must be a positive integer")
        if not isinstance(generated_at, str) or not generated_at.strip():
            raise ValueError("generated_at is required")
        if not isinstance(groups, dict):
            raise ValueError("groups must be an object keyed by group_key")

        validated: dict[str, dict] = {}
        for key, raw in groups.items():
            if not isinstance(raw, dict):
                raise ValueError(f"group {key!r} must be an object")
            category_code = str(raw.get("category_code", "")).strip()
            brand_id_value = raw.get("brand_id")
            brand_id = (
                str(brand_id_value).strip() if brand_id_value is not None else None
            )
            brand = str(raw.get("brand", "")).strip()
            if not category_code or not brand:
                raise ValueError(f"group {key} category_code and brand are required")
            if key != group_key(category_code, brand_id, brand):
                raise ValueError(f"group key does not match its fields: {key}")
            if raw.get("image_type") != IMAGE_TYPE:
                raise ValueError(f"group {key} must use image_type={IMAGE_TYPE!r}")
            source_url = raw.get("source_url")
            if not isinstance(source_url, str):
                raise ValueError(f"group {key} source_url is required")
            validate_source_url(source_url)
            images = raw.get("images")
            if not isinstance(images, list) or not 1 <= len(images) <= 3:
                raise ValueError(f"group {key} must contain one to three images")
            for image_url in images:
                if not isinstance(image_url, str):
                    raise ValueError(f"group {key} image URLs must be strings")
                if normalize_image_url(image_url, source_url) != image_url:
                    raise ValueError(f"group {key} contains a non-allowlisted image")
            if len(images) != len(set(images)):
                raise ValueError(f"group {key} contains duplicate images")
            validated[key] = {
                "category_code": category_code,
                "brand_id": brand_id,
                "brand": brand,
                "image_type": IMAGE_TYPE,
                "images": list(images),
                "source_url": source_url,
            }
        return cls(version, generated_at, validated)

    @classmethod
    def load(cls, path: Path | str = DEFAULT_MAPPING_PATH) -> "RepresentativeImageMapping":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_payload(payload)

    def projection_for(self, product: ProductIdentity) -> dict[str, str | int]:
        """Return a representative URL or the common placeholder."""
        try:
            key = group_key(
                product.category_code,
                product.brand_id,
                product.brand or "",
            )
        except ValueError:
            key = ""
        group = self.groups.get(key)
        assigned = None
        if group is not None and product.sku:
            assigned = assign_representative_image(
                product.sku,
                {
                    **group,
                    "group_key": key,
                    "mapping_version": self.mapping_version,
                },
            )
        return {
            "image_url": (
                assigned["image_url"] if assigned else PLACEHOLDER_IMAGE_URL
            ),
            "image_type": IMAGE_TYPE,
            "mapping_version": self.mapping_version,
        }


@lru_cache(maxsize=1)
def load_default_mapping() -> RepresentativeImageMapping:
    return RepresentativeImageMapping.load(DEFAULT_MAPPING_PATH)


__all__ = [
    "DEFAULT_MAPPING_PATH",
    "PLACEHOLDER_IMAGE_URL",
    "RepresentativeImageMapping",
    "load_default_mapping",
]
