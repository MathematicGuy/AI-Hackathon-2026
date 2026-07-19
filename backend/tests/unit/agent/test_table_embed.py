"""Round 7 (scoped): the EXISTING comparison embedded as a table payload —
present only on compare replies, built from the same tools as the text."""

from fastapi.testclient import TestClient

from backend.app.agent.api import _comparison_table, create_agent_app
from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.graph import AgentDependencies, AgentReply


def product(pid, code, price, sale=None, attrs=None):
    return GenericProduct(
        productidweb=pid,
        category_code=code,
        category_name="x",
        brand="B",
        brand_id="1",
        model_code=pid,
        sku=pid,
        attributes=attrs or {},
        promotion=PromotionInfo(list_price=price, sale_price=sale, gift=None),
    )


def _deps():
    return AgentDependencies(
        products=[
            product("a", "36", 8_000_000, sale=6_000_000,
                    attrs={"Độ ồn": "29 dB", "Loại Inverter": "Máy lạnh Inverter"}),
            product("b", "36", 9_000_000,
                    attrs={"Độ ồn": "33 dB", "Loại Inverter": "Máy lạnh Inverter"}),
        ]
    )


def test_table_only_on_compare_intent():
    deps = _deps()
    compare = AgentReply(text="x", intent="compare_products", presented_ids=["a", "b"])
    other = AgentReply(text="x", intent="new_search", presented_ids=["a", "b"])
    assert _comparison_table(deps, compare) is not None
    assert _comparison_table(deps, other) is None


def test_table_matches_records_and_winner():
    deps = _deps()
    reply = AgentReply(text="x", intent="compare_products", presented_ids=["a", "b"])
    table = _comparison_table(deps, reply)
    assert [p["id"] for p in table["products"]] == ["a", "b"]
    assert table["products"][0]["effective_price"] == 6_000_000
    assert table["products"][0]["discount_percent"] == 25.0
    noise = next(r for r in table["rows"] if r["label"] == "Độ ồn")
    assert noise["values"] == ["29 dB", "33 dB"]
    assert noise["winner_id"] == "a"  # lower dB wins
    inverter = next(r for r in table["rows"] if r["label"] == "Inverter")
    assert inverter["winner_id"] is None  # tie


def test_table_requires_two_products():
    deps = _deps()
    reply = AgentReply(text="x", intent="compare_products", presented_ids=["a"])
    assert _comparison_table(deps, reply) is None


def test_respond_endpoint_carries_table():
    client = TestClient(create_agent_app(_deps()))
    client.post(
        "/api/v1/agent/respond",
        json={"session_id": "t1", "message": "tư vấn máy lạnh"},
    )
    response = client.post(
        "/api/v1/agent/respond",
        json={"session_id": "t1", "message": "so sánh 2 mẫu rẻ nhất đi"},
    )
    body = response.json()
    assert body["intent"] == "compare_products"
    assert body["table"] is not None
    assert len(body["table"]["products"]) == 2
