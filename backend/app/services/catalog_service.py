"""Catalog business logic. Validates input and orchestrates the repository.

Contains no SQL: all data access goes through CatalogRepository.
"""

from __future__ import annotations

from backend.app.api.errors import (
    InvalidAttributeFilterError,
    NotFoundError,
    ValidationAppError,
)
from backend.app.api.schemas.common import SORT_COLUMNS
from backend.app.repositories.catalog_repository import CatalogRepository


class CatalogService:
    def __init__(self, repo: CatalogRepository):
        self.repo = repo

    def list_categories(self) -> list[dict]:
        return self.repo.list_categories()

    def get_category_attributes(self, category_code: str) -> tuple[dict, list[dict]]:
        category = self.repo.get_category(category_code)
        if category is None:
            raise NotFoundError(f"category '{category_code}' not found")
        return category, self.repo.category_attributes(category_code)

    def list_brands(self, category_code: str | None) -> list[dict]:
        if category_code is not None and self.repo.get_category(category_code) is None:
            raise NotFoundError(f"category '{category_code}' not found")
        return self.repo.list_brands(category_code)

    def get_product(self, sku: str) -> dict:
        product = self.repo.get_product(sku)
        if product is None:
            raise NotFoundError(f"product '{sku}' not found")
        return product

    def _attribute_keys(self, category_code: str) -> set[str]:
        return {row["key"] for row in self.repo.category_attributes(category_code)}

    def search(self, request) -> tuple[list[dict], int, int]:
        if request.attribute_filters and not request.category_code:
            raise InvalidAttributeFilterError(
                "attribute_filters require category_code"
            )

        valid_keys: set[str] | None = None
        if request.category_code is not None:
            if self.repo.get_category(request.category_code) is None:
                raise NotFoundError(f"category '{request.category_code}' not found")

        if request.attribute_filters:
            valid_keys = self._attribute_keys(request.category_code)
            unknown = [
                f.key for f in request.attribute_filters if f.key not in valid_keys
            ]
            if unknown:
                raise InvalidAttributeFilterError(
                    f"unknown attribute keys for category {request.category_code}",
                    details=unknown,
                )

        for spec in request.sort:
            if spec.field in SORT_COLUMNS:
                continue
            if request.category_code is None:
                raise ValidationAppError(
                    f"sort by attribute '{spec.field}' requires category_code"
                )
            if valid_keys is None:
                valid_keys = self._attribute_keys(request.category_code)
            if spec.field not in valid_keys:
                raise ValidationAppError(
                    f"unknown sort attribute '{spec.field}' "
                    f"for category {request.category_code}"
                )

        attribute_filters = [
            (f.key, f.op, f.value) for f in request.attribute_filters
        ]
        sort = [(s.field, s.direction, s.numeric) for s in request.sort]
        rows, total = self.repo.search(
            query=request.query,
            category_code=request.category_code,
            brands=request.brands,
            attribute_filters=attribute_filters,
            sort=sort,
            page=request.page,
            page_size=request.page_size,
        )
        total_pages = (total + request.page_size - 1) // request.page_size if total else 0
        return rows, total, total_pages

    def batch(self, skus: list[str]) -> tuple[list[dict], list[str]]:
        unique = list(dict.fromkeys(skus))
        rows = self.repo.get_products_by_skus(unique)
        found = {row["sku"] for row in rows}
        missing = [sku for sku in unique if sku not in found]
        return rows, missing

    def compare(
        self, skus: list[str]
    ) -> tuple[list[dict], bool, str | None, list[dict], list[str]]:
        unique = list(dict.fromkeys(skus))
        rows = self.repo.get_products_by_skus(unique)
        by_sku = {row["sku"]: row for row in rows}
        ordered = [by_sku[sku] for sku in unique if sku in by_sku]
        missing = [sku for sku in unique if sku not in by_sku]

        warnings: list[str] = []
        if missing:
            warnings.append(f"skus not found: {', '.join(missing)}")

        categories = {row["category_code"] for row in ordered}
        same_category = len(categories) <= 1
        category_code = next(iter(categories)) if same_category and categories else None
        if not same_category:
            warnings.append(
                "products span multiple categories; comparison may be less meaningful"
            )

        # Union of attribute keys, preserving first-seen order.
        keys: list[str] = []
        seen: set[str] = set()
        for row in ordered:
            for key in row["attributes"].keys():
                if key not in seen:
                    seen.add(key)
                    keys.append(key)
        matrix = [
            {
                "key": key,
                "values": {row["sku"]: row["attributes"].get(key) for row in ordered},
            }
            for key in keys
        ]
        return ordered, same_category, category_code, matrix, warnings
