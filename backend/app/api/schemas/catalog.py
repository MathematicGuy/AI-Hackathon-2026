"""Product Catalog API request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field

from backend.app.api.schemas.common import APIModel, AttributeFilter, SortSpec


class HealthResponse(APIModel):
    status: str
    database: str


class ProductRecord(APIModel):
    """A product. ``attributes`` is the original spreadsheet row, verbatim."""

    sku: str
    productidweb: str | None = None
    model_code: str | None = None
    category_code: str | None = None
    category_name: str | None = None
    brand: str | None = None
    brand_id: str | None = None
    sheet_name: str
    attributes: dict[str, Any]
    source_file: str
    updated_at: datetime


class Category(APIModel):
    category_code: str
    name: str
    product_count: int


class CategoryList(APIModel):
    items: list[Category]
    total: int


class CategoryAttribute(APIModel):
    key: str
    non_null_count: int
    total: int


class CategoryAttributes(APIModel):
    category_code: str
    name: str
    attributes: list[CategoryAttribute]


class Brand(APIModel):
    brand: str
    brand_id: str | None = None
    product_count: int


class BrandList(APIModel):
    items: list[Brand]
    total: int


class SearchRequest(APIModel):
    query: str | None = Field(
        default=None, description="ILIKE over sku, productidweb, model_code, brand"
    )
    category_code: str | None = None
    brands: list[str] | None = None
    attribute_filters: list[AttributeFilter] = Field(default_factory=list)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort: list[SortSpec] = Field(default_factory=list)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "query": "panasonic",
                    "category_code": "36",
                    "brands": ["Panasonic", "Daikin"],
                    "attribute_filters": [
                        {"key": "Loại Gas", "op": "eq", "value": "R-32"},
                        {"key": "giá khuyến mãi", "op": "lte", "value": 15000000},
                    ],
                    "page": 1,
                    "page_size": 20,
                    "sort": [
                        {"field": "giá khuyến mãi", "direction": "asc", "numeric": True}
                    ],
                }
            ]
        },
    )


class SearchResponse(APIModel):
    items: list[ProductRecord]
    page: int
    page_size: int
    total: int
    total_pages: int


class BatchRequest(APIModel):
    skus: list[str] = Field(min_length=1, max_length=100)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"skus": ["1751098000210", "1751098000128"]}]
        },
    )


class BatchResponse(APIModel):
    items: list[ProductRecord]
    missing_skus: list[str]


class CompareRequest(APIModel):
    skus: list[str] = Field(min_length=2, max_length=5)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"skus": ["1751098000210", "1751098000128"]}]
        },
    )


class CompareAttributeRow(APIModel):
    key: str
    values: dict[str, Any]


class CompareResponse(APIModel):
    products: list[ProductRecord]
    same_category: bool
    category_code: str | None = None
    attributes: list[CompareAttributeRow]
    warnings: list[str]
