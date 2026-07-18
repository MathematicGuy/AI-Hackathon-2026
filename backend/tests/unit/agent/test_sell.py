import pytest

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.respond import format_vnd, render_suggestions
from backend.app.agent.tools.suggest import suggest_products


def product(pid, *, code="115", brand="LG", list_price=None, sale_price=None,
            gift=None, attrs=None):
    attributes = {"productidweb": pid, "category_code": code, "brand": brand}
    attributes.update(attrs or {})
    return GenericProduct(
        productidweb=pid,
        category_code=code,
        category_name="Máy giặt",
        brand=brand,
        brand_id="1",
        model_code=f"M-{pid}",
        sku=f"S-{pid}",
        attributes=attributes,
        promotion=PromotionInfo(list_price=list_price, sale_price=sale_price, gift=gift),
    )


@pytest.fixture
def candidates():
    return [
        product("w1", list_price=8_000_000, attrs={"Khối lượng giặt": "8 kg"}),
        product("w2", list_price=12_000_000, sale_price=9_000_000,
                gift="Phiếu mua hàng 500.000đ", attrs={"Khối lượng giặt": "10 kg"}),
        product("w3", list_price=15_000_000, attrs={"Khối lượng giặt": "12 kg"}),
        product("w4", list_price=7_000_000, attrs={"Khối lượng giặt": "7 kg"}),
    ]


def test_default_roles_price_value_performance(candidates):
    suggestions = suggest_products(candidates, category_code="115")
    assert suggestions.winners["best_price"].productidweb == "w4"
    assert suggestions.winners["best_value"].productidweb == "w2"  # 25% off + gift
    assert suggestions.winners["best_performance"].productidweb == "w3"  # 12 kg
    assert suggestions.skipped_roles == []


def test_requested_roles_override(candidates):
    suggestions = suggest_products(
        candidates, category_code="115", roles=["best_price"]
    )
    assert list(suggestions.winners) == ["best_price"]


def test_performance_skipped_with_disclosure_when_attribute_missing(candidates):
    stripped = [
        product("x1", list_price=5_000_000),
        product("x2", list_price=6_000_000),
    ]
    suggestions = suggest_products(stripped, category_code="115")
    assert "best_performance" in suggestions.skipped_roles


def test_duplicate_winner_renders_once_with_merged_roles(candidates):
    cheap_and_valuable = [
        product("y1", list_price=10_000_000, sale_price=6_000_000, gift="Quà"),
        product("y2", list_price=9_000_000, attrs={"Khối lượng giặt": "9 kg"}),
    ]
    suggestions = suggest_products(cheap_and_valuable, category_code="115")
    assert suggestions.winners["best_price"].productidweb == "y1"
    assert suggestions.winners["best_value"].productidweb == "y1"
    assert len(suggestions.distinct_products) == 2
    assert set(suggestions.roles_for("y1")) == {"best_price", "best_value"}


def test_render_leads_with_promotion_and_ends_with_one_question(candidates):
    suggestions = suggest_products(candidates, category_code="115")
    response = render_suggestions(suggestions, category_name="máy giặt")
    assert "Giá khuyến mãi " + format_vnd(9_000_000) in response.text
    assert "giảm 25%" in response.text
    assert "Quà tặng kèm: Phiếu mua hàng 500.000đ" in response.text
    assert response.text.count("?") == 1
    assert response.text.strip().endswith("?")
