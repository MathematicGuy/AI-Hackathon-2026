"""Data access for the product catalog. All SQL lives here and is parameterized.

Attribute keys and values are always passed as bound parameters, never
interpolated into SQL text. Sort directions and column names come from a
code-controlled whitelist.
"""

from __future__ import annotations

from typing import Any

from backend.app.api.schemas.common import SORT_COLUMNS

# Only digits with an optional sign and one decimal part are treated as numeric.
_NUMERIC_RE = r"^-?[0-9]+(\.[0-9]+)?$"

_PRODUCT_SELECT = """
    SELECT p.sku, p.productidweb, p.model_code, p.category_code,
           c.sheet_name AS category_name, p.brand, p.brand_id, p.sheet_name,
           p.attributes, p.source_file, p.updated_at
    FROM products p
    LEFT JOIN categories c ON c.category_code = p.category_code
"""


def build_attribute_condition(key: str, op: str, value: Any) -> tuple[str, list[Any]]:
    """Return a parameterized SQL condition and its params for one filter."""
    if op == "eq":
        return "p.attributes ->> %s = %s", [key, _as_text(value)]
    if op == "neq":
        return "p.attributes ->> %s IS DISTINCT FROM %s", [key, _as_text(value)]
    if op == "contains":
        return "p.attributes ->> %s ILIKE %s", [key, f"%{value}%"]
    if op == "in":
        return "p.attributes ->> %s = ANY(%s)", [key, [_as_text(v) for v in value]]
    if op == "gte":
        return (
            "(CASE WHEN p.attributes ->> %s ~ %s "
            "THEN (p.attributes ->> %s)::numeric END) >= %s",
            [key, _NUMERIC_RE, key, value],
        )
    if op == "lte":
        return (
            "(CASE WHEN p.attributes ->> %s ~ %s "
            "THEN (p.attributes ->> %s)::numeric END) <= %s",
            [key, _NUMERIC_RE, key, value],
        )
    if op == "exists":
        if value is False:
            return "p.attributes ->> %s IS NULL", [key]
        return "p.attributes ->> %s IS NOT NULL", [key]
    raise ValueError(f"unsupported operator: {op}")


def build_order_by(sort: list[tuple[str, str, bool]]) -> tuple[str, list[Any]]:
    """Build a safe ORDER BY. ``sort`` is a list of (field, direction, numeric)."""
    if not sort:
        return " ORDER BY p.sku ASC", []
    clauses: list[str] = []
    params: list[Any] = []
    for field, direction, numeric in sort:
        sql_dir = "DESC" if direction == "desc" else "ASC"
        if field in SORT_COLUMNS:
            clauses.append(f"p.{field} {sql_dir} NULLS LAST")
        elif numeric:
            clauses.append(
                f"(CASE WHEN p.attributes ->> %s ~ %s "
                f"THEN (p.attributes ->> %s)::numeric END) {sql_dir} NULLS LAST"
            )
            params += [field, _NUMERIC_RE, field]
        else:
            clauses.append(f"p.attributes ->> %s {sql_dir} NULLS LAST")
            params.append(field)
    clauses.append("p.sku ASC")  # stable tie-breaker
    return " ORDER BY " + ", ".join(clauses), params


def _as_text(value: Any) -> str:
    return value if isinstance(value, str) else str(value)


class CatalogRepository:
    def __init__(self, conn):
        self.conn = conn

    def list_categories(self) -> list[dict]:
        return self.conn.execute(
            """
            SELECT c.category_code, c.sheet_name AS name,
                   count(p.sku) AS product_count
            FROM categories c
            LEFT JOIN products p ON p.category_code = c.category_code
            GROUP BY c.category_code, c.sheet_name
            ORDER BY product_count DESC, c.category_code
            """
        ).fetchall()

    def get_category(self, category_code: str) -> dict | None:
        return self.conn.execute(
            "SELECT category_code, sheet_name AS name FROM categories "
            "WHERE category_code = %s",
            [category_code],
        ).fetchone()

    def category_attributes(self, category_code: str) -> list[dict]:
        return self.conn.execute(
            """
            SELECT k.key,
                   count(*) FILTER (WHERE p.attributes ->> k.key IS NOT NULL)
                       AS non_null_count,
                   count(*) AS total
            FROM products p, LATERAL jsonb_object_keys(p.attributes) AS k(key)
            WHERE p.category_code = %s
            GROUP BY k.key
            ORDER BY non_null_count DESC, k.key
            """,
            [category_code],
        ).fetchall()

    def list_brands(self, category_code: str | None) -> list[dict]:
        return self.conn.execute(
            """
            SELECT p.brand, max(p.brand_id) AS brand_id, count(*) AS product_count
            FROM products p
            WHERE p.brand IS NOT NULL
              AND (%(category_code)s::text IS NULL
                   OR p.category_code = %(category_code)s)
            GROUP BY p.brand
            ORDER BY product_count DESC, p.brand
            """,
            {"category_code": category_code},
        ).fetchall()

    def get_product(self, sku: str) -> dict | None:
        return self.conn.execute(
            _PRODUCT_SELECT + " WHERE p.sku = %s", [sku]
        ).fetchone()

    def get_products_by_skus(self, skus: list[str]) -> list[dict]:
        return self.conn.execute(
            _PRODUCT_SELECT + " WHERE p.sku = ANY(%s)", [list(skus)]
        ).fetchall()

    def search(
        self,
        *,
        query: str | None,
        category_code: str | None,
        brands: list[str] | None,
        attribute_filters: list[tuple[str, str, Any]],
        sort: list[tuple[str, str, bool]],
        page: int,
        page_size: int,
    ) -> tuple[list[dict], int]:
        where: list[str] = []
        params: list[Any] = []

        if category_code:
            where.append("p.category_code = %s")
            params.append(category_code)
        if brands:
            where.append("p.brand = ANY(%s)")
            params.append(list(brands))
        if query:
            where.append(
                "(p.sku ILIKE %s OR p.productidweb ILIKE %s "
                "OR p.model_code ILIKE %s OR p.brand ILIKE %s)"
            )
            like = f"%{query}%"
            params += [like, like, like, like]
        for key, op, value in attribute_filters:
            condition, condition_params = build_attribute_condition(key, op, value)
            where.append(condition)
            params += condition_params

        where_sql = (" WHERE " + " AND ".join(where)) if where else ""

        total = self.conn.execute(
            "SELECT count(*) AS n FROM products p" + where_sql, params
        ).fetchone()["n"]

        order_sql, order_params = build_order_by(sort)
        offset = (page - 1) * page_size
        rows = self.conn.execute(
            _PRODUCT_SELECT + where_sql + order_sql + " LIMIT %s OFFSET %s",
            params + order_params + [page_size, offset],
        ).fetchall()
        return rows, total
