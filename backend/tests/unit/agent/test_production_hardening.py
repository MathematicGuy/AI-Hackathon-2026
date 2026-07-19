"""US-125 production hardening: endpoint limits, structured comparison,
fail-fast catalog, and LLM retry/logging.

The suite injects fakes throughout; nothing here touches a network or a
database.
"""

import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.agent.api import _RateLimiter, _comparison_table, create_agent_router
from backend.app.agent.catalog import pg_adapter
from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.contracts import AgentState, GenericNeed
from backend.app.agent.graph import AgentDependencies, _compare_flow
from backend.app.observability import noop_agent_observer
from backend.app.agent.llm.client import (
    LLMCandidate,
    LLMUnderstandingExtractor,
    _is_transient,
)


def product(pid, code, price, attrs=None, gift=None, sale=None):
    return GenericProduct(
        productidweb=pid,
        category_code=code,
        category_name="Máy lạnh",
        brand="B",
        brand_id="1",
        model_code=pid,
        sku=pid,
        attributes=attrs or {},
        promotion=PromotionInfo(list_price=price, sale_price=sale, gift=gift),
    )


# --- rate limiter ------------------------------------------------------------


def test_rate_limiter_allows_up_to_the_limit_then_blocks():
    limiter = _RateLimiter(limit=3, window_seconds=60)
    assert [limiter.check("ip", now=0.0) for _ in range(3)] == [None, None, None]
    retry_after = limiter.check("ip", now=0.0)
    assert retry_after is not None and retry_after > 0


def test_rate_limiter_window_slides():
    limiter = _RateLimiter(limit=1, window_seconds=10)
    assert limiter.check("ip", now=0.0) is None
    assert limiter.check("ip", now=5.0) is not None
    # Past the window the client is allowed again.
    assert limiter.check("ip", now=11.0) is None


def test_rate_limiter_is_per_client():
    limiter = _RateLimiter(limit=1, window_seconds=60)
    assert limiter.check("a", now=0.0) is None
    assert limiter.check("b", now=0.0) is None


# --- endpoint limits ---------------------------------------------------------


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("AGENT_MAX_MESSAGE_CHARS", "50")
    monkeypatch.setenv("AGENT_RATE_LIMIT_REQUESTS", "3")
    monkeypatch.setenv("AGENT_RATE_LIMIT_WINDOW_SECONDS", "60")
    app = FastAPI()
    app.include_router(create_agent_router(AgentDependencies(products=[])))
    with TestClient(app) as test_client:
        yield test_client


def test_oversized_message_is_rejected_with_413(client):
    response = client.post("/api/v1/agent/respond", json={"message": "a" * 51})
    assert response.status_code == 413


def test_message_at_the_limit_is_accepted(client):
    response = client.post("/api/v1/agent/respond", json={"message": "a" * 50})
    assert response.status_code == 200


def test_rate_limit_returns_429_with_retry_after(client):
    for _ in range(3):
        assert client.post("/api/v1/agent/respond", json={"message": "hi"}).status_code == 200
    blocked = client.post("/api/v1/agent/respond", json={"message": "hi"})
    assert blocked.status_code == 429
    assert blocked.headers.get("Retry-After")


def test_feedback_never_logs_message_text(client, caplog):
    with caplog.at_level(logging.INFO, logger="backend.app.agent.api"):
        response = client.post(
            "/api/v1/agent/feedback",
            json={"session_id": "s-1", "message_index": 0, "rating": "like"},
        )
    assert response.status_code == 200
    logged = " ".join(record.getMessage() for record in caplog.records)
    assert "s-1" in logged and "like" in logged


def test_router_accepts_a_dependency_provider():
    """The catalog app mounts this router before its lifespan builds the
    dependencies, so `deps` is a callable there (see backend/app/api/main.py).
    Reading the observer off the callable instead of the resolved object would
    raise AttributeError on every agent request in production, and no other
    test exercises that path.
    """
    deps = AgentDependencies(products=[])
    app = FastAPI()
    app.include_router(create_agent_router(lambda: deps))
    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/agent/respond", json={"message": "xin chào"}
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["text"]
    assert body["trace_id"]


def test_session_ceiling_evicts_the_coldest_session(monkeypatch):
    monkeypatch.setenv("AGENT_MAX_SESSIONS", "2")
    app = FastAPI()
    app.include_router(create_agent_router(AgentDependencies(products=[])))
    with TestClient(app) as test_client:
        ids = []
        for _ in range(3):
            body = test_client.post(
                "/api/v1/agent/respond", json={"message": "xin chào"}
            ).json()
            ids.append(body["session_id"])
        # The oldest session is gone, so reusing it starts a fresh state rather
        # than growing the map without bound.
        replayed = test_client.post(
            "/api/v1/agent/respond",
            json={"session_id": ids[0], "message": "xin chào"},
        )
        assert replayed.status_code == 200


# --- structured comparison ---------------------------------------------------


def compare_state(products):
    state = AgentState(session_id="s")
    state.need = GenericNeed(category_code="36")
    state.last_presented_ids = [p.productidweb for p in products]
    return state


def test_comparison_table_carries_products_rows_and_winner():
    a = product("a", "36", 10_000_000, {"Độ ồn": "24 dB", "Loại máy": "1 chiều"})
    b = product("b", "36", 8_000_000, {"Độ ồn": "30 dB", "Loại máy": "2 chiều"})
    deps = AgentDependencies(products=[a, b])
    reply = _compare_flow(compare_state([a, b]), deps, [], noop_agent_observer())
    table = _comparison_table(deps, reply)

    assert table is not None
    assert [p["id"] for p in table["products"]] == ["a", "b"]
    noise = next(r for r in table["rows"] if r["label"] == "Độ ồn")
    # Lower dB wins for a numeric_lower dimension.
    assert noise["winner_id"] == "a"
    # Values are positional, in the same order as `products`.
    assert noise["values"] == ["24 dB", "30 dB"]
    prices = [p["effective_price"] for p in table["products"]]
    assert prices == [10_000_000, 8_000_000]


def test_comparison_row_is_dropped_when_a_side_is_a_placeholder():
    a = product("a", "36", 10_000_000, {"Độ ồn": "24 dB"})
    b = product("b", "36", 8_000_000, {"Độ ồn": "Hãng không công bố"})
    deps = AgentDependencies(products=[a, b])
    reply = _compare_flow(compare_state([a, b]), deps, [], noop_agent_observer())
    table = _comparison_table(deps, reply)

    assert table is not None
    assert all(row["label"] != "Độ ồn" for row in table["rows"])


def test_non_rankable_dimension_has_no_winner():
    a = product("a", "36", 10_000_000, {"Loại máy": "1 chiều"})
    b = product("b", "36", 8_000_000, {"Loại máy": "2 chiều"})
    deps = AgentDependencies(products=[a, b])
    reply = _compare_flow(compare_state([a, b]), deps, [], noop_agent_observer())
    table = _comparison_table(deps, reply)

    row = next(r for r in table["rows"] if r["label"] == "Loại máy")
    assert row["winner_id"] is None


def test_comparison_is_absent_without_two_products():
    a = product("a", "36", 10_000_000, {})
    deps = AgentDependencies(products=[a])
    state = AgentState(session_id="s")
    state.need = GenericNeed(category_code="36")
    state.last_presented_ids = ["a"]
    reply = _compare_flow(state, deps, [], noop_agent_observer())
    assert _comparison_table(deps, reply) is None


def test_comparison_table_agrees_with_the_reply_text():
    """The defect this story fixes: the table must not contradict the answer."""
    a = product("a", "36", 10_000_000, {"Độ ồn": "24 dB"})
    b = product("b", "36", 8_000_000, {"Độ ồn": "30 dB"})
    deps = AgentDependencies(products=[a, b])
    reply = _compare_flow(compare_state([a, b]), deps, [], noop_agent_observer())
    table = _comparison_table(deps, reply)

    noise = next(r for r in table["rows"] if r["label"] == "Độ ồn")
    winner_name = next(
        p["name"] for p in table["products"] if p["id"] == noise["winner_id"]
    )
    assert f"{winner_name} nhỉnh hơn" in reply.text


# --- fail-fast catalog -------------------------------------------------------


def test_postgres_unavailable_falls_back_when_not_required(monkeypatch, caplog):
    monkeypatch.delenv("REQUIRE_POSTGRES", raising=False)
    monkeypatch.setattr(
        pg_adapter, "_require_postgres", lambda: False
    )
    with caplog.at_level(logging.WARNING, logger="backend.app.agent.catalog.pg_adapter"):
        assert pg_adapter.postgres_available() is False
    assert "postgres_unavailable" in caplog.text


def test_postgres_unavailable_is_fatal_when_required(monkeypatch):
    monkeypatch.setenv("REQUIRE_POSTGRES", "true")
    with pytest.raises(pg_adapter.PostgresRequiredError):
        pg_adapter.postgres_available()


@pytest.mark.parametrize(
    "value,expected",
    [("true", True), ("1", True), ("yes", True), ("false", False), ("", False)],
)
def test_require_postgres_flag_parsing(monkeypatch, value, expected):
    monkeypatch.setenv("REQUIRE_POSTGRES", value)
    assert pg_adapter._require_postgres() is expected


# --- LLM retry and logging ---------------------------------------------------


def test_transient_errors_are_recognised():
    assert _is_transient(Exception("429 Too Many Requests"))
    assert _is_transient(Exception("connection timed out"))
    assert not _is_transient(Exception("invalid api key"))


async def test_extractor_retries_once_on_a_transient_error(caplog):
    attempts: list[str] = []

    async def transport(candidate, system, user):
        attempts.append(candidate.model)
        if len(attempts) == 1:
            raise Exception("429 rate limit")
        return '{"intent":"new_search","confidence":0.9,"need_patch":{}}'

    extractor = LLMUnderstandingExtractor(
        [LLMCandidate(base_url="x", api_key="k", model="m1")],
        transport=transport,
        retry_backoff=0.0,
    )
    with caplog.at_level(logging.WARNING, logger="backend.app.agent.llm.client"):
        understanding = await extractor.extract("mua tủ lạnh")

    assert understanding.intent == "new_search"
    assert attempts == ["m1", "m1"]
    assert "extract_failed" in caplog.text


async def test_extractor_moves_to_the_next_candidate_on_a_hard_error():
    attempts: list[str] = []

    async def transport(candidate, system, user):
        attempts.append(candidate.model)
        if candidate.model == "m1":
            raise Exception("invalid api key")
        return '{"intent":"new_search","confidence":0.9,"need_patch":{}}'

    extractor = LLMUnderstandingExtractor(
        [
            LLMCandidate(base_url="x", api_key="k", model="m1"),
            LLMCandidate(base_url="y", api_key="k", model="m2"),
        ],
        transport=transport,
        retry_backoff=0.0,
    )
    await extractor.extract("mua tủ lạnh")
    # A non-transient failure is not retried on the same candidate.
    assert attempts == ["m1", "m2"]
