from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.promotions import PromotionInfo
from backend.app.agent.policies.answer import build_policy_answer
from backend.app.agent.policies.corpus import PolicyCorpus
from backend.app.agent.respond import render_suggestions
from backend.app.agent.tools.suggest import suggest_products
from backend.app.agent.validate import degrade_to_facts, validate_response


def product(pid, *, list_price=None, sale_price=None, gift=None):
    return GenericProduct(
        productidweb=pid,
        category_code="115",
        category_name="Máy giặt",
        brand="LG",
        brand_id="1",
        model_code=f"M-{pid}",
        sku=f"S-{pid}",
        attributes={"productidweb": pid, "Khối lượng giặt": "9 kg"},
        promotion=PromotionInfo(list_price=list_price, sale_price=sale_price, gift=gift),
    )


def test_rendered_suggestions_pass_validation():
    products = [
        product("w1", list_price=8_000_000),
        product("w2", list_price=12_000_000, sale_price=9_000_000,
                gift="Phiếu mua hàng 500.000đ"),
    ]
    suggestions = suggest_products(products, category_code="115")
    response = render_suggestions(suggestions, category_name="máy giặt")
    result = validate_response(
        response.text, allowed_products=response.allowed_products
    )
    assert result.ok, result.violations


def test_fabricated_price_is_caught():
    products = [product("w1", list_price=8_000_000)]
    text = "Dạ mẫu này đang giảm còn 5.990.000đ thôi ạ, anh chị lấy không ạ?"
    result = validate_response(text, allowed_products=products)
    assert not result.ok
    assert any(v.startswith("unverified_amount") for v in result.violations)


def test_price_delta_between_records_is_allowed():
    products = [
        product("w1", list_price=8_000_000),
        product("w2", list_price=12_000_000),
    ]
    text = "Dạ mẫu 12.000.000đ cao hơn mẫu 8.000.000đ đúng 4.000.000đ nhưng giặt được nhiều hơn ạ?"
    result = validate_response(text, allowed_products=products)
    assert result.ok, result.violations


def test_gift_amount_from_record_is_allowed():
    products = [
        product("w2", list_price=12_000_000, gift="Phiếu mua hàng 500.000đ"),
    ]
    text = "Dạ mua mẫu này anh/chị được kèm phiếu 500.000đ ạ?"
    result = validate_response(text, allowed_products=products)
    assert result.ok, result.violations


def test_tampered_policy_quote_is_caught():
    corpus = PolicyCorpus()
    answer = build_policy_answer(corpus, "phí hoàn tiền")
    genuine = answer.quotes[0]
    result = validate_response(
        "Dạ theo chính sách ạ.",
        allowed_products=[],
        policy_quotes=[genuine + " và được miễn phí"],
        corpus=corpus,
    )
    assert not result.ok
    assert "non_verbatim_quote" in result.violations


def test_multiple_questions_rejected():
    result = validate_response(
        "Anh thích màu gì? Ngân sách bao nhiêu?", allowed_products=[]
    )
    assert not result.ok
    assert "multiple_questions" in result.violations


def test_degrade_to_facts_contains_only_verified_prices():
    products = [product("w1", list_price=8_000_000)]
    text = degrade_to_facts(products)
    result = validate_response(text, allowed_products=products)
    assert result.ok, result.violations
    assert "8.000.000đ" in text
