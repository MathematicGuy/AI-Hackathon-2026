import pytest

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.contracts import AgentState, GenericNeed
from backend.app.agent.graph import AgentDependencies, run_turn
from backend.app.agent.presentation import (
    build_comparison_presentation,
    build_recommendation_presentation,
)
from backend.app.agent.tools.compare import compare_products
from backend.app.agent.tools.suggest import Suggestions


def product(
    productidweb: str,
    *,
    sku: str | None,
    brand: str = "LG",
    list_price: int | None = None,
    sale_price: int | None = None,
    gift: str | None = None,
    attrs: dict | None = None,
    code: str = "38",
    include_productidweb_attribute: bool = True,
) -> GenericProduct:
    attributes = {"category_code": code, "brand": brand}
    if include_productidweb_attribute:
        attributes["productidweb"] = productidweb
    attributes.update(attrs or {})
    return GenericProduct(
        productidweb=productidweb,
        category_code=code,
        category_name="Tủ Lạnh",
        brand=brand,
        brand_id="1",
        model_code=f"M-{productidweb}",
        sku=sku,
        attributes=attributes,
        promotion=PromotionInfo(
            list_price=list_price,
            sale_price=sale_price,
            gift=gift,
        ),
    )


def test_recommendation_uses_stable_sku_and_merges_server_badges():
    winner = product(
        "web-1",
        sku="SKU-1",
        list_price=10_000_000,
        sale_price=8_000_000,
        gift="Phiếu mua hàng 500.000đ",
        attrs={"Dung tích": "300 lít"},
    )
    extra = product(
        "web-2",
        sku="SKU-2",
        brand="Samsung",
        list_price=12_000_000,
        attrs={"Dung tích": "400 lít"},
    )
    suggestions = Suggestions(
        winners={"best_price": winner, "best_value": winner},
    )

    presentation = build_recommendation_presentation(
        suggestions,
        also_consider=[winner, extra],
        follow_up_question="Anh/chị muốn so sánh hai mẫu nào ạ?",
    )

    assert presentation.type == "recommendation"
    assert [item.sku for item in presentation.products] == ["SKU-1", "SKU-2"]
    assert [badge.code for badge in presentation.products[0].badges] == [
        "best_price",
        "best_value",
    ]
    assert presentation.products[0].effective_price_vnd == 8_000_000
    assert presentation.products[0].list_price_vnd == 10_000_000
    assert presentation.products[0].promotion_text == "Phiếu mua hàng 500.000đ"
    assert presentation.products[0].highlights[0].model_dump() == {
        "label": "Dung tích",
        "value": "300 lít",
    }
    assert presentation.products[0].productidweb == "web-1"
    assert presentation.products[0].image_url is None
    assert presentation.products[0].product_url == "https://www.dienmayxanh.com/p/web-1"
    assert presentation.products[0].rating is None
    assert presentation.products[0].sold_count is None
    assert presentation.comparison_rows == []
    assert presentation.follow_up_questions == [
        "Anh/chị muốn so sánh hai mẫu nào ạ?"
    ]


def test_missing_authoritative_web_id_stays_null():
    item = product(
        "SKU-1",
        sku="SKU-1",
        list_price=8_000_000,
        include_productidweb_attribute=False,
    )
    presentation = build_recommendation_presentation(
        Suggestions(winners={"best_price": item})
    )

    assert presentation.products[0].productidweb is None


def test_overlong_authoritative_web_id_is_omitted_not_truncated():
    raw_web_id = "web-" + "1" * 200
    item = product(raw_web_id, sku="SKU-1", list_price=8_000_000)

    presentation = build_recommendation_presentation(
        Suggestions(winners={"best_price": item})
    )

    assert presentation.products[0].productidweb is None


@pytest.mark.parametrize(
    "products",
    [
        [product("web-1", sku=None, list_price=8_000_000)],
        [
            product("web-1", sku="SKU-DUP", list_price=8_000_000),
            product("web-2", sku="SKU-DUP", list_price=9_000_000),
        ],
    ],
)
def test_recommendation_falls_back_to_text_without_nonempty_unique_skus(products):
    suggestions = Suggestions(
        winners={f"role-{index}": item for index, item in enumerate(products)}
    )

    presentation = build_recommendation_presentation(suggestions)

    assert presentation.type == "text"
    assert presentation.products == []
    assert presentation.comparison_rows == []
    assert presentation.warnings


def test_comparison_rows_are_keyed_by_each_unique_product_sku():
    first = product(
        "web-1",
        sku="SKU-1",
        list_price=10_000_000,
        sale_price=8_000_000,
        gift="Quà tặng A",
        attrs={"Dung tích": "300 lít", "Công nghệ": "Inverter"},
    )
    second = product(
        "web-2",
        sku="SKU-2",
        brand="Samsung",
        list_price=12_000_000,
        attrs={"Dung tích": "400 lít"},
    )
    comparison = compare_products([first, second], ("web-1", "web-2"))

    presentation = build_comparison_presentation(
        [first, second],
        comparison,
        follow_up_question="Anh/chị nghiêng về mẫu nào hơn ạ?",
    )

    assert presentation.type == "comparison"
    assert [item.sku for item in presentation.products] == ["SKU-1", "SKU-2"]
    assert len(presentation.products) == 2
    assert presentation.follow_up_questions == [
        "Anh/chị nghiêng về mẫu nào hơn ạ?"
    ]
    for row in presentation.comparison_rows:
        assert [cell.sku for cell in row.values] == ["SKU-1", "SKU-2"]
        assert len(row.values) == len(presentation.products)
    capacity = next(
        row for row in presentation.comparison_rows if row.label == "Dung tích"
    )
    assert [cell.value for cell in capacity.values] == ["300 lít", "400 lít"]
    technology = next(
        row for row in presentation.comparison_rows if row.label == "Công nghệ"
    )
    assert [cell.value for cell in technology.values] == ["Inverter", None]


def test_comparison_needs_two_unique_skus_or_falls_back_to_text():
    only = product("web-1", sku="SKU-1", list_price=8_000_000)
    comparison = compare_products([only], ("web-1",))

    presentation = build_comparison_presentation([only], comparison)

    assert presentation.type == "text"
    assert presentation.products == []
    assert presentation.comparison_rows == []
    assert presentation.warnings


def test_comparison_caps_shared_attribute_rows_at_three():
    attributes = {f"Thuộc tính {index}": f"Giá trị {index}" for index in range(5)}
    first = product("web-1", sku="SKU-1", attrs=attributes)
    second = product("web-2", sku="SKU-2", attrs=attributes)
    comparison = compare_products([first, second], ("web-1", "web-2"))

    presentation = build_comparison_presentation([first, second], comparison)

    assert len(presentation.comparison_rows) == 7
    assert [row.label for row in presentation.comparison_rows[-3:]] == [
        "Thuộc tính 0",
        "Thuộc tính 1",
        "Thuộc tính 2",
    ]


def test_presentation_bounds_catalog_strings_and_highlights():
    item = product(
        "web-1",
        sku="SKU-1",
        gift="Ưu đãi " + "G" * 500 + " 5.000.000đ",
        attrs={
            f"Nhãn {index}" + "L" * 200: f"Giá trị {index}"
            for index in range(5)
        },
    )

    presentation = build_recommendation_presentation(
        Suggestions(winners={"best_price": item})
    )
    rendered = presentation.products[0]

    assert rendered.promotion_text is None
    assert len(rendered.highlights) == 3
    assert all(len(highlight.label) <= 120 for highlight in rendered.highlights)
    assert all(len(highlight.value or "") <= 500 for highlight in rendered.highlights)


def test_overlong_skipped_roles_cannot_overflow_warning_contract():
    item = product("web-1", sku="SKU-1")
    skipped = [f"role-{index}-" + "R" * 800 for index in range(20)]

    presentation = build_recommendation_presentation(
        Suggestions(winners={"best_price": item}, skipped_roles=skipped)
    )

    assert len(presentation.warnings) <= 10
    assert all(len(warning) <= 500 for warning in presentation.warnings)


@pytest.mark.parametrize(
    ("last_ids", "products", "current_category"),
    [
        (
            ["stale", "web-2"],
            [product("web-2", sku="SKU-2")],
            "38",
        ),
        (
            ["web-1", "web-2"],
            [
                product("web-1", sku="SKU-1", code="38"),
                product("web-2", sku="SKU-2", code="38"),
                product("pc-1", sku="PC-1", code="72"),
            ],
            "72",
        ),
        (
            ["shared", "web-2"],
            [
                product("shared", sku="SKU-1"),
                product("shared", sku="SKU-1-VARIANT"),
                product("web-2", sku="SKU-2"),
            ],
            "38",
        ),
    ],
)
async def test_compare_with_stale_cross_category_or_ambiguous_ids_is_text_only(
    last_ids, products, current_category
):
    state = AgentState(
        need=GenericNeed(category_code=current_category),
        last_presented_ids=last_ids,
    )

    reply = await run_turn(
        state,
        "so sánh hai mẫu",
        AgentDependencies(products=products),
    )

    assert reply.intent == "compare_products"
    assert reply.presentation.type == "text"
    assert reply.presentation.products == []
    assert reply.presentation.comparison_rows == []


async def test_recommendation_with_variant_winners_sharing_web_id_fails_closed():
    products = [
        product(
            "shared-web",
            sku="SKU-LOW",
            list_price=8_000_000,
            attrs={"Dung tích sử dụng": "200 lít"},
        ),
        product(
            "shared-web",
            sku="SKU-HIGH",
            list_price=15_000_000,
            sale_price=12_000_000,
            attrs={"Dung tích sử dụng": "500 lít"},
        ),
    ]

    state = AgentState(last_presented_ids=["old-web-1", "old-web-2"])
    reply = await run_turn(
        state,
        "mua tủ lạnh tầm 20 triệu",
        AgentDependencies(products=products),
    )

    assert "ambiguous_product_identity" in reply.flags
    assert state.last_presented_ids == []
    assert reply.presented_ids == []
    assert reply.presentation.type == "text"
    assert reply.presentation.products == []
    assert reply.presentation.comparison_rows == []
    assert reply.presentation.warnings
