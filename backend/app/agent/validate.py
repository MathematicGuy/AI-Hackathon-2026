"""Deterministic grounding validation — the last gate before responding.

Checks that every large number (a price-like claim) in the outgoing text
exists among the allowed records' prices or their pairwise differences, that
every policy quote is a verbatim substring of the corpus, and that the
response asks at most one question. A failed check degrades the response to
the deterministic facts instead of letting an invented claim through.
"""

import re
from dataclasses import dataclass, field

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.policies.corpus import PolicyCorpus

_PRICE_LIKE = re.compile(r"\d{1,3}(?:[.,]\d{3}){2,}|\d{7,}")


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ok: bool
    violations: list[str] = field(default_factory=list)


def _allowed_amounts(products: list[GenericProduct]) -> set[int]:
    prices: set[int] = set()
    record_numbers: set[int] = set()
    for product in products:
        for amount in (product.list_price, product.sale_price):
            if amount is not None:
                prices.add(amount)
        # Numbers appearing verbatim inside record text (gift promotions,
        # spec values) are grounded claims too.
        for value in (product.gift_promotion, *product.attributes.values()):
            if value in (None, ""):
                continue
            for match in _PRICE_LIKE.finditer(str(value)):
                record_numbers.add(int(re.sub(r"[.,]", "", match.group(0))))
    deltas = {abs(a - b) for a in prices for b in prices if a != b}
    return prices | deltas | record_numbers


def validate_response(
    text: str,
    *,
    allowed_products: list[GenericProduct],
    policy_quotes: list[str] = (),
    corpus: PolicyCorpus | None = None,
) -> ValidationResult:
    violations: list[str] = []

    allowed = _allowed_amounts(allowed_products)
    for match in _PRICE_LIKE.finditer(text):
        amount = int(re.sub(r"[.,]", "", match.group(0)))
        if amount >= 100_000 and amount not in allowed:
            violations.append(f"unverified_amount:{match.group(0)}")

    if policy_quotes:
        if corpus is None:
            violations.append("quotes_without_corpus")
        else:
            raw_texts = [document.raw_text for document in corpus.documents]
            for quote in policy_quotes:
                if not any(quote.strip() in raw for raw in raw_texts):
                    violations.append("non_verbatim_quote")

    if text.count("?") > 1:
        violations.append("multiple_questions")

    return ValidationResult(ok=not violations, violations=violations)


def degrade_to_facts(products: list[GenericProduct]) -> str:
    from backend.app.agent.respond import format_vnd

    lines = [
        "Dạ để đảm bảo thông tin chính xác, em gửi anh/chị thông tin đã "
        "kiểm chứng ạ:",
    ]
    for product in products:
        price = (
            format_vnd(product.effective_price)
            if product.effective_price is not None
            else "giá đang cập nhật"
        )
        lines.append(f"• {product.name} — {price}")
    lines.append("Anh/chị cần em kiểm tra thêm thông tin nào không ạ?")
    return "\n".join(lines)
