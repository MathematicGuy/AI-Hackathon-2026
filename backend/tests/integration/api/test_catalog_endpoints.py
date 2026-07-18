"""Integration tests: HTTP -> service -> repository -> PostgreSQL (8,746 products).

Skipped automatically when a populated database is not reachable.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.api.main import app
from backend.app.db.connection import connect

MAYLANH = "36"  # category_code for "Máy lạnh"


def _product_count() -> int:
    try:
        with connect() as conn:
            return conn.execute("SELECT count(*) FROM products").fetchone()[0]
    except Exception:
        return 0


PRODUCT_COUNT = _product_count()

pytestmark = pytest.mark.skipif(
    PRODUCT_COUNT == 0, reason="PostgreSQL with catalog data is not reachable"
)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_reports_database_up(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


def test_categories_cover_all_products(client):
    body = client.get("/api/v1/categories").json()
    assert body["total"] == 14
    assert sum(item["product_count"] for item in body["items"]) == 8746


def test_category_attributes_expose_original_headers(client):
    body = client.get(f"/api/v1/categories/{MAYLANH}/attributes").json()
    keys = {attr["key"] for attr in body["attributes"]}
    assert "Phạm vi sử dụng" in keys
    assert "giá khuyến mãi" in keys


def test_unknown_category_returns_unified_404(client):
    response = client.get("/api/v1/categories/__nope__/attributes")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_brands_scoped_to_category(client):
    body = client.get("/api/v1/brands", params={"category_code": MAYLANH}).json()
    assert body["total"] > 0
    assert all(brand["product_count"] > 0 for brand in body["items"])


def test_search_without_filters_returns_full_catalog(client):
    body = client.post("/api/v1/products/search", json={"page_size": 1}).json()
    assert body["total"] == 8746
    assert body["total_pages"] == 8746


def test_search_attribute_filter_then_detail_preserves_attributes(client):
    search = client.post(
        "/api/v1/products/search",
        json={
            "category_code": MAYLANH,
            "attribute_filters": [{"key": "Loại Gas", "op": "eq", "value": "R-32"}],
            "page_size": 5,
        },
    ).json()
    assert search["total"] > 0
    item = search["items"][0]
    assert isinstance(item["attributes"], dict)
    assert item["attributes"].get("Loại Gas") == "R-32"

    detail = client.get(f"/api/v1/products/{item['sku']}")
    assert detail.status_code == 200
    assert detail.json()["sku"] == item["sku"]
    assert detail.json()["attributes"].get("Loại Gas") == "R-32"


def test_search_numeric_filter_respects_bound(client):
    body = client.post(
        "/api/v1/products/search",
        json={
            "category_code": MAYLANH,
            "attribute_filters": [
                {"key": "giá khuyến mãi", "op": "lte", "value": 12000000}
            ],
            "page_size": 20,
        },
    ).json()
    assert body["total"] > 0
    for item in body["items"]:
        price = item["attributes"].get("giá khuyến mãi")
        if price not in (None, ""):
            assert float(price) <= 12000000


def test_search_unknown_attribute_key_is_rejected(client):
    response = client.post(
        "/api/v1/products/search",
        json={
            "category_code": MAYLANH,
            "attribute_filters": [{"key": "__nope__", "op": "eq", "value": "x"}],
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_attribute_filter"


def test_attribute_filter_without_category_is_rejected(client):
    response = client.post(
        "/api/v1/products/search",
        json={"attribute_filters": [{"key": "Loại Gas", "op": "eq", "value": "R-32"}]},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_attribute_filter"


def test_page_size_over_max_is_rejected(client):
    response = client.post("/api/v1/products/search", json={"page_size": 101})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_batch_returns_found_and_missing(client):
    search = client.post(
        "/api/v1/products/search", json={"category_code": MAYLANH, "page_size": 2}
    ).json()
    skus = [item["sku"] for item in search["items"]]
    body = client.post(
        "/api/v1/products/batch", json={"skus": skus + ["__missing__"]}
    ).json()
    assert len(body["items"]) == 2
    assert body["missing_skus"] == ["__missing__"]


def test_compare_same_category(client):
    search = client.post(
        "/api/v1/products/search", json={"category_code": MAYLANH, "page_size": 3}
    ).json()
    skus = [item["sku"] for item in search["items"]]
    body = client.post("/api/v1/products/compare", json={"skus": skus}).json()
    assert body["same_category"] is True
    assert body["category_code"] == MAYLANH
    assert len(body["products"]) == len(skus)
    assert len(body["attributes"]) > 0
