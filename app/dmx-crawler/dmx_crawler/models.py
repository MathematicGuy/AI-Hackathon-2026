from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class CategoryConfig:
    code: str
    name: str
    url: str
    path_prefix: str
    active: bool = True


@dataclass(frozen=True)
class LocationConfig:
    """A verified DMX province + representative ward/address.

    DMX currently requires a ward and a street address before it renders a
    delivery estimate.  The address in config is a public representative
    address, not a customer address.  Operators should replace it with an
    address appropriate for their own test/fulfilment area.
    """

    code: str
    name: str
    province_id: int
    province_name: str
    ward_id: int
    ward_name: str
    address: str
    aliases: tuple[str, ...] = ()
    active: bool = True


@dataclass
class ProductLink:
    url: str
    category_code: str
    source_product_key: Optional[str] = None
    product_code: Optional[str] = None
    lastmod: Optional[str] = None
    source: str = "sitemap"
    title_hint: Optional[str] = None
    brand_hint: Optional[str] = None
    sale_price_hint: Optional[int] = None
    list_price_hint: Optional[int] = None
    sold_hint: Optional[int] = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductContent:
    canonical_url: str
    category_code: str
    name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    source_product_key: Optional[str] = None
    product_code: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    sold_count: Optional[int] = None
    specs: list[dict[str, Any]] = field(default_factory=list)
    # Ordered, lossless specification snapshot. A list is intentional: using
    # a label-keyed mapping would discard group membership, display order and
    # duplicate labels/values.
    specs_raw: list[dict[str, Any]] = field(default_factory=list)
    specs_diagnostics: dict[str, Any] = field(default_factory=dict)
    images: list[str] = field(default_factory=list)
    stock_status: str = "unknown"
    stock_raw: Optional[str] = None
    source_location: dict[str, Any] = field(default_factory=dict)
    observed_at: Optional[str] = None


@dataclass
class DeliveryInfo:
    status: str = "unknown"
    address: Optional[str] = None
    method: Optional[str] = None
    eta: Optional[str] = None
    raw_text: Optional[str] = None
    returned_location: dict[str, Any] = field(default_factory=dict)


@dataclass
class LocationSnapshot:
    sale_price: Optional[int] = None
    list_price: Optional[int] = None
    promotion: dict[str, Any] = field(default_factory=dict)
    stock_status: str = "unknown"
    stock_raw: Optional[str] = None
    delivery: DeliveryInfo = field(default_factory=DeliveryInfo)
    returned_location: dict[str, Any] = field(default_factory=dict)
    observed_at: Optional[str] = None


@dataclass
class ParsedPage:
    content: ProductContent
    location_snapshot: Optional[LocationSnapshot] = None


@dataclass
class SpecificationParseResult:
    """Complete specification parse plus evidence about its completeness.

    ``groups`` is the canonical snapshot persisted in ``specs_raw_json``.
    ``items`` is a flattened view of the same objects for EAV persistence.
    The item dictionaries deliberately remain schema-less so a newly observed
    website attribute does not require a Python or database schema change.
    """

    groups: list[dict[str, Any]] = field(default_factory=list)
    items: list[dict[str, Any]] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)
