"""Contract: POST /api/v1/agent/respond as ChatbotAssistant.tsx calls it.

The frontend posts {session_id, message} — session_id is null on the first
turn — and reads {session_id, text} off the response. No database required:
the router is mounted over an in-memory dependency set.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

import json

from backend.app.agent.api import create_agent_router
from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.graph import AgentDependencies, AgentReply
from backend.app.catalog_images.mapping import (
    PLACEHOLDER_IMAGE_URL,
    RepresentativeImageMapping,
)


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
    assert set(body) == {
        "session_id",
        "request_id",
        "trace_id",
        "intent",
        "text",
        "flags",
        "presented_ids",
        "comparison",
        "image_url",
        "image_type",
        "mapping_version",
    }


def test_comparison_is_null_off_a_comparison_turn(client):
    """The structured table is additive: absent unless the turn compares."""
    body = client.post(
        "/api/v1/agent/respond", json={"message": "tôi muốn mua tủ lạnh"}
    ).json()
    assert body["comparison"] is None


def test_image_fields_are_null_off_a_product_turn(client):
    body = client.post(
        "/api/v1/agent/respond", json={"message": "xin chào"}
    ).json()
    assert body["image_url"] is None
    assert body["image_type"] is None
    assert body["mapping_version"] is None


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


def _product(*, category_code="38", brand_id="2", brand="Samsung"):
    return GenericProduct(
        productidweb="p1",
        category_code=category_code,
        category_name="Tủ lạnh",
        brand=brand,
        brand_id=brand_id,
        model_code="MODEL",
        sku="sku-1",
        attributes={},
        promotion=PromotionInfo(list_price=None, sale_price=None, gift=None),
    )


def _mapping():
    return RepresentativeImageMapping.from_payload(
        {
            "mapping_version": 7,
            "generated_at": "2026-07-19T00:00:00+00:00",
            "groups": {
                "38:2": {
                    "category_code": "38",
                    "brand_id": "2",
                    "brand": "Samsung",
                    "image_type": "representative",
                    "images": [
                        "https://cdn.tgdd.vn/Products/Images/1/p1.jpg"
                    ],
                    "source_url": "https://www.dienmayxanh.com/tu-lanh-samsung",
                }
            },
        }
    )


@pytest.mark.parametrize(
    "stream,path",
    [
        (False, "/api/v1/agent/respond"),
        (True, "/api/v1/agent/respond/stream"),
    ],
)
def test_product_response_projects_the_same_representative_fields(
    monkeypatch, stream, path
):
    async def fake_run_turn(state, message, deps):
        return AgentReply(text="Sản phẩm phù hợp", intent="new_search", presented_ids=["p1"])

    monkeypatch.setattr("backend.app.agent.api.run_turn", fake_run_turn)
    app = FastAPI()
    app.include_router(
        create_agent_router(
            AgentDependencies(products=[_product()]), image_mapping=_mapping()
        )
    )
    with TestClient(app) as product_client:
        response = product_client.post(path, json={"message": "tư vấn tủ lạnh"})
    assert response.status_code == 200
    if stream:
        events = [json.loads(line) for line in response.text.splitlines()]
        body = next(event for event in events if event["type"] == "done")
    else:
        body = response.json()
    assert body["image_url"] == "https://cdn.tgdd.vn/Products/Images/1/p1.jpg"
    assert body["image_type"] == "representative"
    assert body["mapping_version"] == 7


def test_product_without_mapping_uses_common_placeholder(monkeypatch):
    async def fake_run_turn(state, message, deps):
        return AgentReply(text="Sản phẩm phù hợp", intent="new_search", presented_ids=["p1"])

    monkeypatch.setattr("backend.app.agent.api.run_turn", fake_run_turn)
    app = FastAPI()
    app.include_router(
        create_agent_router(
            AgentDependencies(
                products=[_product(category_code="36", brand_id="8", brand="LG")]
            ),
            image_mapping=_mapping(),
        )
    )
    with TestClient(app) as product_client:
        body = product_client.post(
            "/api/v1/agent/respond", json={"message": "tư vấn máy lạnh"}
        ).json()
    assert body["image_url"] == PLACEHOLDER_IMAGE_URL
    assert body["image_type"] == "representative"
    assert body["mapping_version"] == 7
