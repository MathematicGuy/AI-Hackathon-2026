import importlib

import pytest

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.promotions import PromotionInfo


class MissingModule:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, _attribute):
        pytest.fail(f"US-202 {self.name} module is not implemented")


def module_or_missing(dotted, name):
    try:
        return importlib.import_module(dotted)
    except ModuleNotFoundError:
        return MissingModule(name)


@pytest.fixture
def search():
    return module_or_missing("backend.app.agent.tools.search", "search tool")


@pytest.fixture
def aggregate():
    return module_or_missing("backend.app.agent.tools.aggregate", "aggregate tool")


@pytest.fixture
def compare():
    return module_or_missing("backend.app.agent.tools.compare", "compare tool")


@pytest.fixture
def detail():
    return module_or_missing("backend.app.agent.tools.detail", "detail tool")


def product(pid, *, code="38", brand="Samsung", list_price=None, sale_price=None,
            gift=None, attrs=None):
    attributes = {"productidweb": pid, "category_code": code, "brand": brand}
    attributes.update(attrs or {})
    return GenericProduct(
        productidweb=pid,
        category_code=code,
        category_name="Tủ Lạnh",
        brand=brand,
        brand_id="1",
        model_code=f"M-{pid}",
        sku=f"S-{pid}",
        attributes=attributes,
        promotion=PromotionInfo(list_price=list_price, sale_price=sale_price, gift=gift),
    )


@pytest.fixture
def catalog():
    return [
        product("p1", brand="Samsung", list_price=10_000_000, sale_price=8_000_000,
                gift="Phiếu mua hàng 500k", attrs={"Dung tích": "300 lít"}),
        product("p2", brand="LG", list_price=12_000_000,
                attrs={"Dung tích": "400 lít"}),
        product("p3", brand="Samsung", list_price=7_000_000, sale_price=6_500_000,
                attrs={"Dung tích": "250 lít"}),
        product("p4", brand="Toshiba", list_price=None,
                attrs={"Dung tích": "180 lít"}),
        product("p5", code="36", brand="Daikin", list_price=15_000_000,
                attrs={"Loại máy": "1 chiều"}),
    ]


# --- search ---

def test_search_filters_by_category(search, catalog):
    result = search.search_products(catalog, category_code="38")
    assert {p.productidweb for p in result.items} <= {"p1", "p2", "p3", "p4"}
    assert result.total_candidates == 4


def test_search_budget_filter_uses_effective_price(search, catalog):
    result = search.search_products(catalog, category_code="38", budget_max=8_000_000)
    ids = {p.productidweb for p in result.items}
    # p1 qualifies via sale price 8tr; p3 via 6.5tr; p2 too expensive;
    # p4 has no price -> excluded from budget-constrained search.
    assert ids == {"p1", "p3"}


def test_search_brand_filter_case_insensitive(search, catalog):
    result = search.search_products(catalog, category_code="38", brands=("samsung",))
    assert {p.productidweb for p in result.items} == {"p1", "p3"}


def test_search_attribute_contains(search, catalog):
    result = search.search_products(
        catalog, category_code="38", attribute_contains={"Dung tích": "300"}
    )
    assert [p.productidweb for p in result.items] == ["p1"]


def test_search_sorts_deterministically_price_ascending(search, catalog):
    result = search.search_products(catalog, category_code="38")
    ids = [p.productidweb for p in result.items]
    # effective prices: p3=6.5tr, p1=8tr, p2=12tr, p4=None (last)
    assert ids == ["p3", "p1", "p2", "p4"]


def test_search_cursor_and_exclusions(search, catalog):
    first = search.search_products(catalog, category_code="38", limit=2)
    assert [p.productidweb for p in first.items] == ["p3", "p1"]
    assert first.has_more is True
    rest = search.search_products(
        catalog, category_code="38", limit=10, cursor=first.next_cursor,
        exclude_ids=("p2",),
    )
    assert [p.productidweb for p in rest.items] == ["p4"]


# --- aggregate ---

def test_category_overview_counts_prices_promotions(aggregate, catalog):
    overview = aggregate.category_overview(catalog, category_code="38")
    assert overview.product_count == 4
    assert overview.brand_counts["Samsung"] == 2
    assert overview.price_min == 6_500_000
    assert overview.price_max == 12_000_000
    assert overview.discounted_count == 2
    assert overview.gift_count == 1


# --- compare ---

def test_compare_promotion_forward(compare, catalog):
    result = compare.compare_products(catalog, ("p1", "p2"))
    assert [item.productidweb for item in result.items] == ["p1", "p2"]
    p1 = result.items[0]
    assert p1.sale_price == 8_000_000
    assert p1.discount_percent == pytest.approx(20.0)
    assert p1.gift == "Phiếu mua hàng 500k"
    # Promotion delta must be part of the comparison, not just specs.
    assert result.price_delta == 4_000_000
    assert "Dung tích" in result.shared_attributes
    assert result.shared_attributes["Dung tích"]["p1"] == "300 lít"


def test_compare_unknown_id_rejected(compare, catalog):
    with pytest.raises(KeyError):
        compare.compare_products(catalog, ("p1", "ghost"))


# --- detail ---

def test_detail_returns_nonnull_attributes(detail, catalog):
    info = detail.product_detail(catalog, "p1")
    assert info.product.productidweb == "p1"
    assert info.attributes["Dung tích"] == "300 lít"
    assert all(value not in (None, "") for value in info.attributes.values())


def test_detail_unknown_id_returns_none(detail, catalog):
    assert detail.product_detail(catalog, "ghost") is None
