"""Deterministic salesman rendering over verified records.

Every fact in the rendered text comes from retrieved records (prices, gifts,
discounts) or the policy corpus (verbatim quotes). The proactive-salesman
framing — leading with promotions and benefits, ending with one consultative
question — is deterministic here; optional LLM polish (Part G) may rephrase
but the validator re-checks any polished text against the same records.
"""

import re
from dataclasses import dataclass, field

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.contracts import GenericNeed
from backend.app.agent.tools.suggest import Suggestions

ROLE_LABELS = {
    "best_price": "Giá tốt nhất",
    "best_value": "Đáng tiền nhất (khuyến mãi sâu)",
    "best_performance": "Hiệu năng/công suất tốt nhất",
    "most_expensive": "Cao cấp nhất",
}


def format_vnd(amount: int) -> str:
    return f"{amount:,}".replace(",", ".") + "đ"


def format_trieu(amount: int) -> str:
    """User-need amounts render as '12 triệu' — natural Vietnamese, and never
    mistaken for a product-price claim by the grounding validator."""
    millions = amount / 1_000_000
    if millions >= 1:
        text = f"{millions:.1f}".rstrip("0").rstrip(".")
        return f"{text} triệu"
    return f"{amount // 1000}k"


@dataclass(frozen=True, slots=True)
class ProposedResponse:
    text: str
    allowed_products: list[GenericProduct] = field(default_factory=list)
    policy_quotes: list[str] = field(default_factory=list)
    question: str | None = None


def _product_line(product: GenericProduct, roles: list[str]) -> str:
    badges = " + ".join(ROLE_LABELS.get(role, role) for role in roles)
    parts = [f"• [{badges}] {product.name}"]
    discount = product.promotion.discount_percent
    # Real data contains rows where sale price equals list price — there is a
    # promotion field but no actual discount, so guard on the percent itself.
    if discount is not None and product.sale_price is not None:
        parts.append(
            f"  Giá khuyến mãi {format_vnd(product.sale_price)} "
            f"(giá gốc {format_vnd(product.list_price)}, giảm {discount:.0f}%)"
        )
    elif product.effective_price is not None:
        parts.append(f"  Giá {format_vnd(product.effective_price)}")
    else:
        parts.append("  Giá đang cập nhật")
    if product.gift_promotion:
        gift = product.gift_promotion
        if len(gift) > 160:
            # Never cut in the middle of a number — a truncated amount would
            # look like an invented price claim.
            gift = re.sub(r"[\d.,]*$", "", gift[:157]).rstrip() + "…"
        parts.append(f"  Quà tặng kèm: {gift}")
    return "\n".join(parts)


def _need_summary(need: GenericNeed | None) -> str | None:
    if need is None:
        return None
    parts: list[str] = []
    if need.usage_purpose:
        parts.append(f"mục đích {need.usage_purpose}")
    if need.budget_min and need.budget_max:
        parts.append(
            f"tầm giá {format_trieu(need.budget_min)}–{format_trieu(need.budget_max)}"
        )
    elif need.budget_max:
        parts.append(f"ngân sách khoảng {format_trieu(need.budget_max)}")
    if need.brand_prefs:
        parts.append(f"ưu tiên hãng {', '.join(need.brand_prefs)}")
    if need.priorities:
        parts.append(", ".join(need.priorities))
    return " và ".join(parts) if parts else None


def _fit_reason(
    product: GenericProduct, roles: list[str], need: GenericNeed | None
) -> str:
    reasons: list[str] = []
    if "best_price" in roles:
        reasons.append("giá tốt nhất trong các mẫu phù hợp")
    if "best_value" in roles and product.promotion.discount_percent:
        reasons.append(
            f"đang giảm sâu {product.promotion.discount_percent:.0f}% nên rất đáng tiền"
        )
    if "best_performance" in roles:
        reasons.append("thông số thuộc nhóm mạnh nhất trong tầm này")
    if "most_expensive" in roles:
        reasons.append("là mẫu cao cấp nhất bên em đang có theo yêu cầu của mình")
    if product.gift_promotion and "best_value" not in roles:
        reasons.append("có quà tặng kèm")
    if need is not None and need.budget_max and product.effective_price:
        if product.effective_price <= need.budget_max:
            reasons.append("nằm gọn trong ngân sách của mình")
        else:
            reasons.append(
                "nhỉnh hơn ngân sách một chút nhưng đáng cân nhắc vì ưu đãi"
            )
    return "  → Phù hợp vì " + ", ".join(reasons) + "." if reasons else ""


def _missing_info_hint(
    need: GenericNeed | None, *, purpose_example: str | None = None
) -> str | None:
    """Only fields the customer has NOT answered yet — re-mentioning an
    answered one reads as not listening (Cường's live-test 2). Abstract asks
    carry a concrete example."""
    if need is None:
        return None
    missing: list[str] = []
    if not need.usage_purpose:
        ask = "mục đích sử dụng"
        if purpose_example:
            ask += f" (ví dụ: {purpose_example})"
        missing.append(ask)
    if not need.budget_max and not need.budget_min:
        missing.append("khoảng giá mong muốn")
    if not need.priorities:
        missing.append("điều anh/chị ưu tiên nhất")
    if not missing:
        return None
    return (
        "Em có thể chọn chính xác hơn nữa nếu anh/chị cho em biết thêm về "
        + ", ".join(missing[:2])
        + " ạ."
    )


def _debate_line(suggestions: Suggestions) -> str | None:
    priced = [
        p for p in suggestions.distinct_products if p.effective_price is not None
    ]
    if len(priced) < 2:
        return None
    cheapest = min(priced, key=lambda p: p.effective_price)
    priciest = max(priced, key=lambda p: p.effective_price)
    if cheapest.productidweb == priciest.productidweb:
        return None
    delta = priciest.effective_price - cheapest.effective_price
    if delta <= 0:
        return None
    pricier_roles = suggestions.roles_for(priciest.productidweb)
    if "best_performance" in pricier_roles:
        perk = "mạnh hơn hẳn về thông số"
    elif (priciest.promotion.discount_percent or 0) > (
        cheapest.promotion.discount_percent or 0
    ):
        perk = "đang được giảm sâu hơn"
    elif priciest.gift_promotion and not cheapest.gift_promotion:
        perk = "kèm quà tặng mà mẫu kia không có"
    else:
        perk = "thuộc phân khúc cao cấp hơn"
    return (
        f"So nhanh: {cheapest.name} rẻ hơn {priciest.name} "
        f"{format_vnd(delta)}; đổi lại {priciest.name} {perk} ạ."
    )


def render_suggestions(
    suggestions: Suggestions,
    *,
    category_name: str,
    next_question: str | None = None,
    also_consider: list[GenericProduct] | None = None,
    need: GenericNeed | None = None,
    purpose_example: str | None = None,
) -> ProposedResponse:
    # The three ranked roles always lead the answer; extra worthwhile options
    # follow in a "tham khảo thêm" section. Reasoning is context-driven
    # (Cường: focus on intention/context, explain WHY each pick fits).
    summary = _need_summary(need)
    opener = (
        f"Dạ dựa trên yêu cầu của anh/chị về {summary}, em gợi ý mấy mẫu "
        f"{category_name} phù hợp nhất ạ:"
        if summary
        else f"Dạ em gợi ý anh/chị mấy mẫu {category_name} đang có ưu đãi tốt ạ:"
    )
    lines = [opener, ""]
    for product in suggestions.distinct_products:
        roles = suggestions.roles_for(product.productidweb)
        lines.append(_product_line(product, roles))
        reason = _fit_reason(product, roles, need)
        if reason:
            lines.append(reason)
        lines.append("")
    # Quick debate between the picks: benefit vs drawback, deterministic from
    # the records (price delta is validator-allowed).
    debate = _debate_line(suggestions)
    if debate:
        lines.append(debate)
        lines.append("")
    # Roles the data cannot support are skipped silently — never shown to the
    # end user (Cường's live-test finding).
    extras = list(also_consider or [])
    if extras:
        lines.append("Ngoài ra anh/chị có thể tham khảo thêm:")
        for product in extras:
            price = (
                format_vnd(product.effective_price)
                if product.effective_price is not None
                else "giá đang cập nhật"
            )
            note = ""
            if product.promotion.discount_percent:
                note = f", đang giảm {product.promotion.discount_percent:.0f}%"
            if product.gift_promotion:
                note += ", có quà tặng"
            lines.append(f"• {product.name} — {price}{note}")
        lines.append("")
    hint = _missing_info_hint(need, purpose_example=purpose_example)
    if hint and next_question is None:
        lines.append(hint)
    question = next_question or (
        "Anh/chị muốn em so sánh chi tiết hai mẫu nào, hay xem thêm lựa chọn khác ạ?"
    )
    lines.append(question)
    return ProposedResponse(
        text="\n".join(lines).strip(),
        allowed_products=suggestions.distinct_products + extras,
        question=question,
    )
