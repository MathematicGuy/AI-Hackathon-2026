"""Postgres dataset adapter over Duy's data platform.

Reads the `products` table (backend/migrations/0002_catalog.sql) through the
platform's own connection helper and yields the exact same `GenericProduct`
shape as the Excel adapter — the rest of the agent cannot tell the backends
apart. `sku` is the platform's unique business key; `productidweb` may be
shared by variants, so the agent-level id falls back to sku when the web id is
missing. Credentials are never logged.
"""

from typing import Any, Callable

from backend.app.agent.catalog.dataset_adapter import GenericProduct, _as_text
from backend.app.agent.catalog.promotions import extract_promotion

_PRODUCTS_QUERY = """
    SELECT sku, productidweb, model_code, category_code, brand, brand_id,
           sheet_name, attributes
    FROM products
"""

RowFetcher = Callable[[], list[tuple]]


def _default_fetcher() -> list[tuple]:
    from backend.app.db.connection import connect

    with connect() as conn:
        return conn.execute(_PRODUCTS_QUERY).fetchall()


class PostgresDatasetAdapter:
    def __init__(self, fetch_rows: RowFetcher | None = None) -> None:
        self._fetch_rows = fetch_rows or _default_fetcher
        self._cache: list[GenericProduct] | None = None

    def load(self) -> list[GenericProduct]:
        if self._cache is not None:
            return self._cache
        products: list[GenericProduct] = []
        for row in self._fetch_rows():
            sku, productidweb, model_code, category_code, brand, brand_id, \
                sheet_name, attributes = row
            record: dict[str, Any] = dict(attributes or {})
            identity = _as_text(productidweb) or _as_text(sku)
            if identity is None:
                continue
            products.append(
                GenericProduct(
                    productidweb=identity,
                    category_code=_as_text(category_code) or "",
                    category_name=_as_text(sheet_name) or "",
                    brand=_as_text(brand),
                    brand_id=_as_text(brand_id),
                    model_code=_as_text(model_code),
                    sku=_as_text(sku),
                    attributes=record,
                    promotion=extract_promotion(record),
                )
            )
        self._cache = products
        return products


def postgres_available() -> bool:
    """Cheap availability probe: settings loadable and one row reachable.
    Any failure (missing config, container down) means unavailable."""
    try:
        from backend.app.db.connection import connect

        with connect() as conn:
            conn.execute("SELECT 1 FROM products LIMIT 1").fetchone()
        return True
    except Exception:
        return False
