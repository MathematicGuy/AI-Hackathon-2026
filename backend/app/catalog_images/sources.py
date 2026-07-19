"""Derive deterministic first-party category-brand source pages."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol
from urllib.parse import urlencode

from backend.app.catalog_images.representative import (
    GroupSource,
    group_key,
    normalized_brand_slug,
)

_CATEGORY_SLUGS = {
    "38": "tu-lanh",
    "36": "may-lanh",
    "115": "may-giat",
    "116": "may-say-quan-ao",
    "39": "may-rua-chen",
    "40": "tu-dong",
    "41": "may-nuoc-nong",
    "139": "micro",
    "137": "micro-thu-am",
    "49": "dong-ho-thong-minh",
    "72": "may-tinh-nguyen-bo",
    "73": "man-hinh-may-tinh",
    "75": "may-in",
    "30": "may-tinh-bang",
}

_CATEGORY_MATCH_NAMES = {
    "30": "Máy tính bảng",
    "36": "Máy lạnh",
    "38": "Tủ lạnh",
    "39": "Máy rửa chén",
    "40": "Tủ đông, tủ mát",
    "41": "Máy nước nóng",
    "49": "Đồng hồ thông minh",
    "72": "Máy tính để bàn",
    "73": "Màn hình máy tính",
    "75": "Máy in",
    "115": "Máy giặt",
    "116": "Máy sấy quần áo",
    "137": "Micro thu âm điện thoại",
    "139": "Micro karaoke",
}
_INVALID_BRANDS = {"", "n-a", "khac"}
_BRAND_URL_SLUGS = {
    "ipad-apple": "apple",
    "hp-hyperx": "hyperx",
}
_BRAND_MATCH_NAMES = {
    "hp-hyperx": "HP HyperX",
}
_SOURCE_PATH_OVERRIDES = {
    ("30", "ipad-apple"): "may-tinh-bang-apple-ipad",
}


class CatalogProduct(Protocol):
    category_code: str
    brand_id: str | None
    brand: str | None


def source_for_group(
    category_code: str, brand_id: str | None, brand: str
) -> GroupSource:
    """Build first-party listing and DMX group-search source URLs."""
    category = str(category_code).strip()
    normalized_brand = normalized_brand_slug(brand)
    category_slug = _CATEGORY_SLUGS.get(category)
    if category_slug is None or normalized_brand in _INVALID_BRANDS:
        source_url = None
        fallback_url = None
    else:
        brand_slug = _BRAND_URL_SLUGS.get(normalized_brand, normalized_brand)
        source_path = _SOURCE_PATH_OVERRIDES.get(
            (category, normalized_brand), f"{category_slug}-{brand_slug}"
        )
        source_url = f"https://www.dienmayxanh.com/{source_path}"
        query = f"{category_slug.replace('-', ' ')} {brand.strip()}"
        fallback_url = (
            "https://www.dienmayxanh.com/search?"
            + urlencode({"key": query, "sc": "new"})
        )
    return GroupSource(
        category_code=category,
        brand_id=str(brand_id).strip() if brand_id is not None else None,
        brand=brand.strip(),
        source_url=source_url,
        match_brand=_BRAND_MATCH_NAMES.get(normalized_brand),
        fallback_url=fallback_url,
        match_category=_CATEGORY_MATCH_NAMES.get(category),
    )


def catalog_group_sources(products: Iterable[CatalogProduct]) -> tuple[GroupSource, ...]:
    """Return every unique catalog group in a stable, reviewable order."""
    groups: dict[str, GroupSource] = {}
    for product in products:
        brand = (product.brand or "").strip()
        if not brand:
            continue
        source = source_for_group(product.category_code, product.brand_id, brand)
        groups.setdefault(group_key(source.category_code, source.brand_id, brand), source)

    def sort_key(source: GroupSource) -> tuple[int, str, str]:
        try:
            category_order = int(source.category_code)
        except ValueError:
            category_order = 10**9
        return category_order, normalized_brand_slug(source.brand), source.key

    return tuple(sorted(groups.values(), key=sort_key))


__all__ = ["catalog_group_sources", "source_for_group"]
