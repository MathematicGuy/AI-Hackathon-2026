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
from backend.app.agent.tools.suggest import Suggestions

ROLE_LABELS = {
    "best_price": "Giá tốt nhất",
    "best_value": "Đáng tiền nhất (khuyến mãi sâu)",
    "best_performance": "Hiệu năng/công suất tốt nhất",
}


def format_vnd(amount: int) -> str:
    return f"{amount:,}".replace(",", ".") + "đ"


@dataclass(frozen=True, slots=True)
class ProposedResponse:
    text: str
    allowed_products: list[GenericProduct] = field(default_factory=list)
    policy_quotes: list[str] = field(default_factory=list)
    question: str | None = None


def _product_line(product: GenericProduct, roles: list[str]) -> str:
    badges = " + ".join(ROLE_LABELS.get(role, role) for role in roles)
    parts = [f"• [{badges}] {product.name}"]
    if product.sale_price is not None and product.list_price is not None:
        discount = product.promotion.discount_percent
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


def render_suggestions(
    suggestions: Suggestions,
    *,
    category_name: str,
    next_question: str | None = None,
) -> ProposedResponse:
    lines = [
        f"Dạ em gợi ý anh/chị mấy mẫu {category_name} đang có ưu đãi tốt ạ:",
        "",
    ]
    for product in suggestions.distinct_products:
        roles = suggestions.roles_for(product.productidweb)
        lines.append(_product_line(product, roles))
        lines.append("")
    if suggestions.skipped_roles:
        lines.append(
            "(Em chưa đủ dữ liệu để chấm mục: "
            + ", ".join(ROLE_LABELS.get(r, r) for r in suggestions.skipped_roles)
            + " ạ.)"
        )
        lines.append("")
    question = next_question or (
        "Anh/chị muốn em so sánh chi tiết hai mẫu nào, hay xem thêm lựa chọn khác ạ?"
    )
    lines.append(question)
    return ProposedResponse(
        text="\n".join(lines).strip(),
        allowed_products=suggestions.distinct_products,
        question=question,
    )
