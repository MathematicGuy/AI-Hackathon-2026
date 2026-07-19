"""Contract: POST /api/v1/agent/respond as ChatbotAssistant.tsx calls it.

The frontend posts {session_id, message} — session_id is null on the first
turn — and reads {session_id, text} off the response. No database required:
the router is mounted over an in-memory dependency set.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.app.agent.api import create_agent_router
from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.graph import AgentDependencies


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(create_agent_router(AgentDependencies(products=[])))
    with TestClient(app) as test_client:
        yield test_client


def test_route_is_mounted(client):
    response = client.post(
        "/api/v1/agent/respond", json={"session_id": None, "message": "xin chào"}
    )
    assert response.status_code == 200, response.text


def test_null_session_id_gets_a_generated_one(client):
    body = client.post(
        "/api/v1/agent/respond", json={"session_id": None, "message": "xin chào"}
    ).json()
    assert body["session_id"]
    assert isinstance(body["text"], str) and body["text"]


def test_response_carries_the_fields_the_frontend_reads(client):
    body = client.post(
        "/api/v1/agent/respond", json={"message": "tôi muốn mua tủ lạnh"}
    ).json()
    assert {
        "session_id",
        "request_id",
        "intent",
        "text",
        "flags",
        "presented_ids",
        "presentation",
    } <= set(body)
    assert set(body["presentation"]) == {
        "type",
        "products",
        "comparison_rows",
        "follow_up_questions",
        "warnings",
    }


def test_first_turn_comparison_is_text_only_without_selected_products(client):
    body = client.post(
        "/api/v1/agent/respond",
        json={"message": "so sánh hai mẫu tủ lạnh"},
    ).json()

    assert body["intent"] == "compare_products"
    assert body["presentation"]["type"] == "text"
    assert body["presentation"]["products"] == []
    assert body["presentation"]["comparison_rows"] == []


def _catalog_product(pid: str, sku: str, price: int) -> GenericProduct:
    return GenericProduct(
        productidweb=pid,
        category_code="38",
        category_name="Tủ Lạnh",
        brand="LG",
        brand_id="1",
        model_code=f"M-{pid}",
        sku=sku,
        attributes={
            "productidweb": pid,
            "category_code": "38",
            "brand": "LG",
            "Dung tích sử dụng": "300 lít",
        },
        promotion=PromotionInfo(list_price=price, sale_price=None, gift=None),
    )


def test_recommendation_presentation_is_render_ready_and_grounded():
    app = FastAPI()
    products = [
        _catalog_product("web-1", "SKU-1", 8_000_000),
        _catalog_product("web-2", "SKU-2", 10_000_000),
    ]
    app.include_router(create_agent_router(AgentDependencies(products=products)))

    with TestClient(app) as test_client:
        body = test_client.post(
            "/api/v1/agent/respond",
            json={"message": "mua tủ lạnh tầm 15 triệu"},
        ).json()

    assert body["presentation"]["type"] == "recommendation"
    assert body["presentation"]["products"]
    assert {item["sku"] for item in body["presentation"]["products"]} <= {
        "SKU-1",
        "SKU-2",
    }
    assert {
        item["productidweb"] for item in body["presentation"]["products"]
    } <= {"web-1", "web-2"}
    assert all(item["image_url"] is None for item in body["presentation"]["products"])
    assert all(
        item["product_url"] is not None
        and item["product_url"].startswith("https://www.dienmayxanh.com/p/")
        for item in body["presentation"]["products"]
    )


def test_follow_up_comparison_uses_the_same_grounded_session_products():
    app = FastAPI()
    products = [
        _catalog_product("web-1", "SKU-1", 8_000_000),
        _catalog_product("web-2", "SKU-2", 10_000_000),
    ]
    app.include_router(create_agent_router(AgentDependencies(products=products)))

    with TestClient(app) as test_client:
        recommendation = test_client.post(
            "/api/v1/agent/respond",
            json={"message": "mua tủ lạnh tầm 15 triệu"},
        ).json()
        comparison = test_client.post(
            "/api/v1/agent/respond",
            json={
                "session_id": recommendation["session_id"],
                "message": "so sánh hai mẫu",
            },
        ).json()

    assert comparison["presentation"]["type"] == "comparison"
    assert comparison["session_id"] == recommendation["session_id"]
    skus = [
        item["sku"] for item in comparison["presentation"]["products"]
    ]
    assert skus == ["SKU-1", "SKU-2"]
    assert len(skus) >= 2 and len(skus) == len(set(skus))
    for row in comparison["presentation"]["comparison_rows"]:
        row_skus = [value["sku"] for value in row["values"]]
        assert len(row_skus) == len(skus)
        assert set(row_skus) == set(skus)
    price_row = next(
        row
        for row in comparison["presentation"]["comparison_rows"]
        if row["label"] == "Giá hiện tại"
    )
    assert [value["value"] for value in price_row["values"]] == [
        "8.000.000đ",
        "10.000.000đ",
    ]
    assert comparison["presented_ids"] == ["web-1", "web-2"]


def test_session_id_round_trips(client):
    first = client.post(
        "/api/v1/agent/respond", json={"message": "tôi muốn mua tủ lạnh"}
    ).json()
    second = client.post(
        "/api/v1/agent/respond",
        json={"session_id": first["session_id"], "message": "cho 2 người"},
    ).json()
    assert second["session_id"] == first["session_id"]


def test_empty_message_is_rejected(client):
    response = client.post("/api/v1/agent/respond", json={"message": ""})
    assert response.status_code == 422
