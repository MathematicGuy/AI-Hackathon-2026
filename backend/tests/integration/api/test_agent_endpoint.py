"""Integration: the sales agent answers on the catalog app itself.

The agent used to run only as a separate app (agent.api.create_agent_app) that
nothing served, so the frontend's POST /api/v1/agent/respond hit a 404 on the
deployed API. These tests pin the route to the app that actually ships.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.api.main import app
from backend.app.db.connection import connect


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


def test_agent_respond_is_served_by_the_catalog_app(client):
    response = client.post(
        "/api/v1/agent/respond",
        json={"session_id": None, "message": "tôi muốn mua tủ lạnh"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["text"].strip()
    assert body["session_id"]


def test_agent_conversation_reaches_grounded_products(client):
    first = client.post(
        "/api/v1/agent/respond",
        json={"session_id": None, "message": "tôi muốn mua tủ lạnh"},
    ).json()
    second = client.post(
        "/api/v1/agent/respond",
        json={
            "session_id": first["session_id"],
            "message": "nhà 4 người, tầm 15 triệu",
        },
    ).json()
    assert second["presented_ids"], second["text"]
    # Every suggested product must exist in the catalog the API serves.
    for productidweb in second["presented_ids"]:
        with connect() as conn:
            found = conn.execute(
                "SELECT count(*) FROM products WHERE productidweb = %s",
                [productidweb],
            ).fetchone()[0]
        assert found > 0, productidweb
