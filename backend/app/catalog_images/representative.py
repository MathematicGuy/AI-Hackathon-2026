"""Collect and assign representative images for category-brand groups.

This module deliberately does not resolve individual products. It reads an
explicit first-party Điện Máy Xanh category-brand page, keeps at most three
product-card image URLs, and deterministically assigns one frozen URL to a SKU.
"""

from __future__ import annotations

import hashlib
import html.parser
import re
import time
import unicodedata
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urljoin, urlparse

import httpx

IMAGE_TYPE = "representative"
_SOURCE_HOSTS = {"dienmayxanh.com", "www.dienmayxanh.com"}
_IMAGE_HOSTS = {"cdn.tgdd.vn", "cdnv2.tgdd.vn"}
_VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


@dataclass(frozen=True)
class GroupSource:
    category_code: str
    brand_id: str | None
    brand: str
    source_url: str | None
    match_brand: str | None = None

    @property
    def key(self) -> str:
        return group_key(self.category_code, self.brand_id, self.brand)


PILOT_GROUPS = (
    GroupSource(
        category_code="38",
        brand_id="2",
        brand="Samsung",
        source_url="https://www.dienmayxanh.com/tu-lanh-samsung",
    ),
    GroupSource(
        category_code="36",
        brand_id="7",
        brand="Panasonic",
        source_url="https://www.dienmayxanh.com/may-lanh-panasonic/",
    ),
    GroupSource(
        category_code="115",
        brand_id="315",
        brand="Electrolux",
        source_url="https://www.dienmayxanh.com/may-giat-electrolux",
    ),
    GroupSource(
        category_code="39",
        brand_id="133",
        brand="Bosch",
        source_url="https://www.dienmayxanh.com/may-rua-chen-bosch",
    ),
    GroupSource(
        category_code="41",
        brand_id="355",
        brand="Stiebel Eltron",
        source_url="https://www.dienmayxanh.com/may-nuoc-nong-stiebel-eltron/",
    ),
)


def normalized_brand_slug(brand: str) -> str:
    value = brand.strip().casefold().replace("đ", "d")
    value = "".join(
        character
        for character in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def group_key(category_code: str, brand_id: str | None, brand: str) -> str:
    category = str(category_code).strip()
    brand_identifier = str(brand_id).strip() if brand_id is not None else ""
    if brand_identifier:
        return f"{category}:{brand_identifier}"
    normalized = normalized_brand_slug(brand)
    if not normalized:
        raise ValueError("brand is required when brand_id is missing")
    return f"{category}:brand:{normalized}"


def validate_source_url(source_url: str) -> None:
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in _SOURCE_HOSTS:
        raise ValueError("source_url must be an HTTPS dienmayxanh.com URL")


def normalize_image_url(value: str, source_url: str) -> str | None:
    candidate = urljoin(source_url, value.strip())
    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or host not in _IMAGE_HOSTS:
        return None
    path = parsed.path.casefold()
    if "/products/images/" not in path and "/timerseo/" not in path:
        return None
    return parsed._replace(scheme="https", fragment="").geturl()


class _ProductCardImageParser(html.parser.HTMLParser):
    def __init__(self, source_url: str, expected_brand: str, limit: int) -> None:
        super().__init__(convert_charrefs=True)
        self.source_url = source_url
        self.expected_brand = normalized_brand_slug(expected_brand)
        self.limit = limit
        self.images: list[str] = []
        self._seen: set[str] = set()
        self._stack: list[tuple[str, bool, bool, bool, bool]] = []
        self._list_depth = 0
        self._image_depth = 0
        self._card_depth = 0
        self._brand_depth = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = {key: value or "" for key, value in attrs}
        classes = set(values.get("class", "").split())
        starts_list = "listproduct" in classes
        starts_image = self._list_depth > 0 and "item-img" in classes
        starts_card = (
            self._list_depth > 0
            and tag == "li"
            and "item" in classes
            and bool(values.get("data-id"))
        )
        starts_brand = (
            self._card_depth > 0
            and tag == "a"
            and normalized_brand_slug(values.get("data-brand", ""))
            == self.expected_brand
        )

        if starts_list:
            self._list_depth += 1
        if starts_image:
            self._image_depth += 1
        if starts_card:
            self._card_depth += 1
        if starts_brand:
            self._brand_depth += 1

        if (
            tag == "img"
            and self._list_depth > 0
            and self._image_depth > 0
            and self._card_depth > 0
            and self._brand_depth > 0
        ):
            self._add_image(values)

        if tag not in _VOID_TAGS:
            self._stack.append(
                (tag, starts_list, starts_image, starts_card, starts_brand)
            )

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] != tag:
                continue
            closing = self._stack[index:]
            del self._stack[index:]
            self._list_depth -= sum(1 for _, starts, _, _, _ in closing if starts)
            self._image_depth -= sum(1 for _, _, starts, _, _ in closing if starts)
            self._card_depth -= sum(1 for _, _, _, starts, _ in closing if starts)
            self._brand_depth -= sum(1 for _, _, _, _, starts in closing if starts)
            break

    def _add_image(self, attrs: dict[str, str]) -> None:
        if len(self.images) >= self.limit:
            return
        raw = attrs.get("data-src") or attrs.get("data-lazy-src") or attrs.get("src")
        if not raw:
            return
        normalized = normalize_image_url(raw, self.source_url)
        if normalized is None or normalized in self._seen:
            return
        self._seen.add(normalized)
        self.images.append(normalized)


def parse_representative_images(
    page_html: str, source_url: str, expected_brand: str, *, limit: int = 3
) -> list[str]:
    validate_source_url(source_url)
    if not 1 <= limit <= 3:
        raise ValueError("limit must be between 1 and 3")
    if not normalized_brand_slug(expected_brand):
        raise ValueError("expected_brand is required")
    parser = _ProductCardImageParser(source_url, expected_brand, limit)
    parser.feed(page_html)
    parser.close()
    return parser.images


def collect_group(
    group: GroupSource,
    client: httpx.Client,
    *,
    max_attempts: int = 3,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    """Fetch one source page; failures remain isolated to this group."""
    if not 1 <= max_attempts <= 5:
        raise ValueError("max_attempts must be between 1 and 5")
    if group.source_url is None:
        return {
            "group_key": group.key,
            "category_code": group.category_code,
            "brand_id": group.brand_id,
            "brand": group.brand,
            "image_type": IMAGE_TYPE,
            "source_url": None,
            "status": "skipped",
            "failure_reason": "missing_first_party_source",
            "images": [],
        }
    validate_source_url(group.source_url)

    failure_reason: str | None = None
    for attempt in range(max_attempts):
        try:
            response = client.get(group.source_url)
            if response.status_code == 404:
                return {
                    "group_key": group.key,
                    "category_code": group.category_code,
                    "brand_id": group.brand_id,
                    "brand": group.brand,
                    "image_type": IMAGE_TYPE,
                    "source_url": str(response.url),
                    "status": "not_found",
                    "failure_reason": "http_404",
                    "images": [],
                }
            if response.status_code == 429 or response.status_code >= 500:
                failure_reason = f"http_{response.status_code}"
                if attempt + 1 < max_attempts:
                    retry_after = response.headers.get("Retry-After", "")
                    delay = float(retry_after) if retry_after.isdigit() else 2**attempt
                    sleep(delay)
                    continue
            response.raise_for_status()
            images = parse_representative_images(
                response.text,
                str(response.url),
                group.match_brand or group.brand,
                limit=3,
            )
            status = "ready" if images else "not_found"
            return {
                "group_key": group.key,
                "category_code": group.category_code,
                "brand_id": group.brand_id,
                "brand": group.brand,
                "image_type": IMAGE_TYPE,
                "source_url": str(response.url),
                "status": status,
                "failure_reason": None if images else "no_product_card_images",
                "images": [
                    {"position": index, "url": url, "source_url": str(response.url)}
                    for index, url in enumerate(images)
                ],
            }
        except (httpx.HTTPError, ValueError) as exc:
            failure_reason = type(exc).__name__
            if attempt + 1 < max_attempts:
                sleep(2**attempt)

    return {
        "group_key": group.key,
        "category_code": group.category_code,
        "brand_id": group.brand_id,
        "brand": group.brand,
        "image_type": IMAGE_TYPE,
        "source_url": group.source_url,
        "status": "error",
        "failure_reason": failure_reason or "unknown_error",
        "images": [],
    }


def assign_representative_image(sku: str, mapping_group: dict) -> dict | None:
    """Return the same group image for the same SKU and frozen mapping."""
    images = mapping_group.get("images") or []
    if not images:
        return None
    key = str(mapping_group["group_key"])
    sku_value = str(sku).strip()
    if not sku_value:
        raise ValueError("sku is required")
    digest = hashlib.sha256(f"{key}\0{sku_value}".encode()).digest()
    index = int.from_bytes(digest[:8], "big") % len(images)
    selected = images[index]
    image_url = selected if isinstance(selected, str) else selected["url"]
    return {
        "sku": sku_value,
        "group_key": key,
        "image_url": image_url,
        "image_type": IMAGE_TYPE,
        "mapping_version": mapping_group.get("mapping_version", 1),
    }
