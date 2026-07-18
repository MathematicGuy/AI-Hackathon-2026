"""Tests for the data-platform round: Postgres adapter, backend selection,
domain rules, and LLM polish."""

import pytest

from backend.app.agent.catalog.dataset_adapter import (
    ExcelDatasetAdapter,
    GenericProduct,
    default_adapter,
)
from backend.app.agent.catalog.pg_adapter import PostgresDatasetAdapter
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.contracts import AgentState, GenericNeed
from backend.app.agent.conversation.domain_rules import apply_domain_filters
from backend.app.agent.graph import AgentDependencies, run_turn
from backend.app.agent.llm.client import LLMCandidate, LLMPolisher


# --- Postgres adapter ---

def pg_row(sku, pidw, code, sheet, attrs):
    return (sku, pidw, f"M-{sku}", code, "Samsung", "1", sheet, attrs)


def test_pg_adapter_yields_same_shape_as_excel():
    rows = [
        pg_row("sku1", "111", "38", "Tủ Lạnh",
               {"productidweb": "111", "Dung tích sử dụng": "300 lít",
                "giá gốc": "10000000", "giá khuyến mãi": "9000000",
                "khuyến mãi quà": "Quà 500.000đ"}),
        pg_row("sku2", None, "36", "Máy lạnh", {"giá gốc": "8000000"}),
    ]
    adapter = PostgresDatasetAdapter(fetch_rows=lambda: rows)
    products = adapter.load()
    assert len(products) == 2
    first = products[0]
    assert isinstance(first, GenericProduct)
    assert first.productidweb == "111"
    assert first.category_name == "Tủ Lạnh"
    assert first.attributes["Dung tích sử dụng"] == "300 lít"
    assert first.sale_price == 9_000_000
    assert first.gift_promotion == "Quà 500.000đ"
    # Missing productidweb falls back to the unique sku.
    assert products[1].productidweb == "sku2"


def test_pg_adapter_caches(monkeypatch):
    calls = []

    def fetch():
        calls.append(1)
        return []

    adapter = PostgresDatasetAdapter(fetch_rows=fetch)
    adapter.load()
    adapter.load()
    assert len(calls) == 1


# --- backend selection ---

def test_forced_excel_backend(monkeypatch):
    monkeypatch.setenv("AGENT_DATA_BACKEND", "excel")
    assert isinstance(default_adapter(), ExcelDatasetAdapter)


def test_forced_postgres_backend(monkeypatch):
    monkeypatch.setenv("AGENT_DATA_BACKEND", "postgres")
    assert isinstance(default_adapter(), PostgresDatasetAdapter)


def test_auto_selection_falls_back_to_excel_when_pg_unavailable(monkeypatch):
    monkeypatch.delenv("AGENT_DATA_BACKEND", raising=False)
    monkeypatch.setattr(
        "backend.app.agent.catalog.pg_adapter.postgres_available", lambda: False
    )
    assert isinstance(default_adapter(), ExcelDatasetAdapter)


# --- domain rules ---

def product(pid, code, attrs):
    return GenericProduct(
        productidweb=pid,
        category_code=code,
        category_name="x",
        brand="B",
        brand_id="1",
        model_code=pid,
        sku=pid,
        attributes=attrs,
        promotion=PromotionInfo(list_price=10_000_000, sale_price=None, gift=None),
    )


def test_fridge_household_band_filters_capacity():
    products = [
        product("small", "38", {"Dung tích sử dụng": "150 lít"}),
        product("mid", "38", {"Dung tích sử dụng": "320 lít"}),
        product("big", "38", {"Dung tích sử dụng": "550 lít"}),
        product("nodata", "38", {}),
    ]
    need = GenericNeed(
        category_code="38", attribute_constraints={"household": "nhà 4 người"}
    )
    kept = {p.productidweb for p in apply_domain_filters(products, need)}
    assert kept == {"mid", "nodata"}  # band 200-450; missing data never excluded


def test_aircon_room_area_must_be_covered():
    products = [
        product("s", "36", {"Phạm vi sử dụng": "Từ 10 - 15m²"}),
        product("m", "36", {"Phạm vi sử dụng": "Từ 15 - 20m²"}),
        product("norange", "36", {"Phạm vi sử dụng": "20m²"}),
    ]
    need = GenericNeed(
        category_code="36", attribute_constraints={"room_area": "phòng 18m2"}
    )
    kept = {p.productidweb for p in apply_domain_filters(products, need)}
    assert kept == {"m", "norange"}


def test_monitor_size_within_two_inches():
    products = [
        product("m24", "73", {"Kích thước màn hình": "24 inch"}),
        product("m32", "73", {"Kích thước màn hình": "32 inch"}),
    ]
    need = GenericNeed(category_code="73", attribute_constraints={"size": "30 inch"})
    kept = {p.productidweb for p in apply_domain_filters(products, need)}
    assert kept == {"m32"}  # 32 within +-2 of 30; 24 is six inches away


def test_domain_rules_never_empty_the_pool():
    products = [product("far", "73", {"Kích thước màn hình": "70 inch"})]
    need = GenericNeed(category_code="73", attribute_constraints={"size": "24 inch"})
    assert apply_domain_filters(products, need) == products


# --- LLM polish ---

async def test_polish_applied_when_grounded(monkeypatch):
    fridge = product("f1", "38", {"Dung tích sử dụng": "300 lít",
                                  "giá gốc": "10000000"})

    async def transport(candidate, system, user):
        return user.replace("Dạ em gợi ý", "Dạ em rất vui được gợi ý")

    deps = AgentDependencies(
        products=[fridge],
        polisher=LLMPolisher(
            [LLMCandidate(base_url="https://x", api_key="k", model="m")],
            transport=transport,
        ),
    )
    state = AgentState(need=GenericNeed(category_code="38", budget_max=12_000_000))
    reply = await run_turn(state, "tư vấn tủ lạnh tầm 12 triệu", deps)
    assert "rất vui được gợi ý" in reply.text


async def test_polish_with_invented_price_is_rejected(monkeypatch):
    fridge = product("f1", "38", {"giá gốc": "10000000"})

    async def transport(candidate, system, user):
        return user + "\nĐặc biệt giảm còn 5.990.000đ hôm nay!"

    deps = AgentDependencies(
        products=[fridge],
        polisher=LLMPolisher(
            [LLMCandidate(base_url="https://x", api_key="k", model="m")],
            transport=transport,
        ),
    )
    state = AgentState(need=GenericNeed(category_code="38", budget_max=12_000_000))
    reply = await run_turn(state, "tư vấn tủ lạnh tầm 12 triệu", deps)
    assert "5.990.000" not in reply.text
    assert "polish_rejected" in reply.flags
