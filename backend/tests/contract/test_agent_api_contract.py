"""Contract: POST /api/v1/agent/respond as ChatbotAssistant.tsx calls it.

The frontend posts {session_id, message} — session_id is null on the first
turn — and reads {session_id, text} off the response. No database required:
the router is mounted over an in-memory dependency set.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.app.agent.api import create_agent_router
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
    assert set(body) == {
        "session_id",
        "request_id",
        "intent",
        "text",
        "flags",
        "presented_ids",
        "comparison",
    }


def test_comparison_is_null_off_a_comparison_turn(client):
    """The structured table is additive: absent unless the turn compares."""
    body = client.post(
        "/api/v1/agent/respond", json={"message": "tôi muốn mua tủ lạnh"}
    ).json()
    assert body["comparison"] is None


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
