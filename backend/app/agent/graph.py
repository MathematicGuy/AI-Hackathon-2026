"""Agent turn pipeline: guard → understand → remember → route → respond.

The node order and responsibility boundaries follow
`docs/product/architecture/multi-category-agent.md`. This is the
deterministic single-agent core; LangGraph checkpointer wrapping (durable
session persistence) is deferred to the persistence story and noted in the
US-206 record — the in-memory `AgentState` carries the session today.
"""

from dataclasses import dataclass, field

from backend.app.agent.catalog.dataset_adapter import ExcelDatasetAdapter, GenericProduct
from backend.app.agent.catalog.registry import CategoryRegistry
from backend.app.agent.contracts import AgentState, DEFAULT_ROLES
from backend.app.agent.conversation import coldstart, memory
from backend.app.agent.conversation.understand import (
    UnderstandingExtractor,
    understand_turn,
)
from backend.app.agent.policies.answer import (
    build_policy_answer,
    degradation_response,
)
from backend.app.agent.policies.corpus import PolicyCorpus
from backend.app.agent.respond import format_vnd, render_suggestions
from backend.app.agent.tools.compare import compare_products
from backend.app.agent.tools.search import search_products
from backend.app.agent.tools.suggest import suggest_products
from backend.app.agent.validate import degrade_to_facts, validate_response
from backend.app.guardrails.input_rules import evaluate_input

_SHOPPING_MARKERS = (
    "mua", "tư vấn", "sản phẩm", "giá", "khuyến mãi", "so sánh", "gợi ý",
    "chính sách", "bảo hành", "giao hàng", "đổi trả", "hoàn tiền", "xem thêm",
    "chi tiết", "còn hàng", "ngân sách", "triệu",
)

_POLICY_VIOLATION_MARKERS = (
    "bỏ qua chính sách", "ngoại lệ", "dù quá hạn", "quá hạn vẫn",
    "không chịu phí", "miễn phí 100%", "bỏ qua điều khoản",
)

GUARDRAIL_REPLY = (
    "Dạ em xin phép không xử lý nội dung này ạ. Em là trợ lý tư vấn sản phẩm "
    "của Điện Máy XANH — anh/chị cần tìm sản phẩm nào để em hỗ trợ ạ?"
)

STOP_REPLY = (
    "Dạ vâng ạ. Cảm ơn anh/chị đã ghé Điện Máy XANH, khi nào cần tư vấn thêm "
    "anh/chị cứ nhắn em nhé ạ!"
)


@dataclass
class AgentDependencies:
    products: list[GenericProduct]
    registry: CategoryRegistry = field(default_factory=CategoryRegistry)
    corpus: PolicyCorpus = field(default_factory=PolicyCorpus)
    extractor: UnderstandingExtractor | None = None

    @classmethod
    def from_default_paths(cls) -> "AgentDependencies":
        return cls(products=ExcelDatasetAdapter().load())


@dataclass(frozen=True, slots=True)
class AgentReply:
    text: str
    intent: str
    flags: list[str] = field(default_factory=list)
    presented_ids: list[str] = field(default_factory=list)


def _agent_scope_markers(registry: CategoryRegistry) -> tuple[str, ...]:
    return registry.all_markers() + _SHOPPING_MARKERS


def _category_menu(registry: CategoryRegistry) -> str:
    names = ", ".join(category.sheet_name for category in registry.all())
    return (
        "Dạ hiện em tư vấn được các ngành hàng: "
        + names
        + ". Anh/chị đang quan tâm sản phẩm nào để em hỗ trợ ngay ạ?"
    )


async def run_turn(state: AgentState, message: str, deps: AgentDependencies) -> AgentReply:
    # 1. Guard (word count, payload, injection; agent scope = all categories).
    guard = evaluate_input(
        message,
        in_scope_markers=_agent_scope_markers(deps.registry),
        other_category_markers=(),
    )
    state.guardrail_flags.extend(guard.flags)
    if guard.blocked:
        state.guardrail_flags.append("guardrail_block")
        text = guard.message or GUARDRAIL_REPLY
        return AgentReply(text=text, intent="unsupported", flags=list(guard.flags))

    # 2. Understand (LLM route when configured, deterministic fallback always).
    understanding, flags = await understand_turn(
        message, extractor=deps.extractor, registry=deps.registry
    )
    state.guardrail_flags.extend(flags)

    # 3. Remember (fixed-format need; patch / correction / category switch).
    memory.apply_turn(state, understanding)
    intent = understanding.intent

    # 4. Route.
    if intent == "stop":
        return AgentReply(text=STOP_REPLY, intent=intent, flags=flags)

    if intent == "policy_question":
        return _policy_flow(message, deps, flags)

    if intent == "unsupported":
        return AgentReply(text=_category_menu(deps.registry), intent=intent, flags=flags)

    return _product_flow(state, deps, intent, flags)


def _policy_flow(message: str, deps: AgentDependencies, flags: list[str]) -> AgentReply:
    answer = build_policy_answer(deps.corpus, message)
    low = message.lower()
    if any(marker in low for marker in _POLICY_VIOLATION_MARKERS):
        text = degradation_response(user_request=message, answer=answer)
        return AgentReply(text=text, intent="policy_question", flags=flags)
    if not answer.quotes:
        return AgentReply(
            text=(
                "Dạ em chưa tìm thấy điều khoản phù hợp với câu hỏi này ạ. "
                "Anh/chị có thể hỏi rõ hơn, hoặc gọi tổng đài 1900 232 461 để "
                "được hỗ trợ chính xác nhất ạ."
            ),
            intent="policy_question",
            flags=flags,
        )
    lines = [
        f"Dạ theo {answer.sources[0]}, chính sách quy định nguyên văn ạ:",
        f'"{answer.quotes[0]}"',
        "",
        "Anh/chị cần em giải thích thêm điểm nào trong chính sách này không ạ?",
    ]
    text = "\n".join(lines)
    result = validate_response(
        text, allowed_products=[], policy_quotes=[answer.quotes[0]], corpus=deps.corpus
    )
    if not result.ok:
        text = degradation_response(user_request=message, answer=answer)
    return AgentReply(text=text, intent="policy_question", flags=flags)


def _product_flow(
    state: AgentState, deps: AgentDependencies, intent: str, flags: list[str]
) -> AgentReply:
    need = state.need
    category = need.category_code

    if category is None:
        return AgentReply(text=_category_menu(deps.registry), intent=intent, flags=flags)

    registry_category = deps.registry.by_code(category)

    if intent == "compare_products":
        return _compare_flow(state, deps, flags)

    if intent == "check_availability":
        return AgentReply(
            text=(
                "Dạ hiện em chưa có dữ liệu tồn kho theo thời gian thực ạ. "
                "Anh/chị để lại khu vực của mình, em sẽ nhờ cửa hàng gần nhất "
                "kiểm tra và báo lại ngay ạ?"
            ),
            intent=intent,
            flags=flags,
        )

    # Cold-start: ask the most material missing question first.
    if not coldstart.has_material_minimum(need):
        question = coldstart.next_question(state)
        if question is not None:
            coldstart.record_asked(state, question)
            return AgentReply(text=question.ask, intent=intent, flags=flags)

    # Enough to act: search, suggest by roles, sell.
    shown = state.shown_for(category)
    exclude = tuple(shown) if intent == "more_recommendations" else ()
    result = search_products(
        deps.products,
        category_code=category,
        budget_min=need.budget_min,
        budget_max=need.budget_max,
        brands=tuple(need.brand_prefs),
        limit=10,
        exclude_ids=exclude,
    )
    if not result.items:
        budget_note = (
            f" trong tầm giá {format_vnd(need.budget_max)}" if need.budget_max else ""
        )
        return AgentReply(
            text=(
                f"Dạ em chưa tìm được mẫu {registry_category.sheet_name}"
                f"{budget_note} phù hợp ạ. Anh/chị có thể nới ngân sách một chút "
                "hoặc bỏ bớt một tiêu chí để em tìm thêm lựa chọn tốt không ạ?"
            ),
            intent=intent,
            flags=flags,
        )

    roles = tuple(need.requested_roles) or DEFAULT_ROLES
    suggestions = suggest_products(
        result.items, category_code=category, roles=roles
    )
    follow_up = coldstart.next_question(state)
    question_text = None
    if follow_up is not None:
        coldstart.record_asked(state, follow_up)
        question_text = follow_up.ask
    response = render_suggestions(
        suggestions,
        category_name=registry_category.sheet_name,
        next_question=question_text,
    )
    validation = validate_response(
        response.text, allowed_products=response.allowed_products
    )
    text = response.text if validation.ok else degrade_to_facts(response.allowed_products)

    presented = [p.productidweb for p in response.allowed_products]
    state.last_presented_ids = presented
    for pid in presented:
        if pid not in shown:
            shown.append(pid)
    return AgentReply(text=text, intent=intent, flags=flags, presented_ids=presented)


def _compare_flow(
    state: AgentState, deps: AgentDependencies, flags: list[str]
) -> AgentReply:
    ids = tuple(state.last_presented_ids[:2])
    if len(ids) < 2:
        return AgentReply(
            text=(
                "Dạ anh/chị muốn so sánh hai mẫu nào ạ? Em có thể gợi ý vài mẫu "
                "trước rồi mình so sánh chi tiết nhé ạ?"
            ),
            intent="compare_products",
            flags=flags,
        )
    comparison = compare_products(deps.products, ids)
    lines = ["Dạ em so sánh nhanh hai mẫu anh/chị đang xem ạ:", ""]
    for item in comparison.items:
        price = format_vnd(item.effective_price) if item.effective_price else "giá đang cập nhật"
        line = f"• {item.name}: {price}"
        if item.discount_percent:
            line += f" (đang giảm {item.discount_percent:.0f}%)"
        if item.gift:
            line += " — có quà tặng kèm"
        lines.append(line)
    if comparison.price_delta:
        lines.append(
            f"Chênh lệch giá giữa hai mẫu là {format_vnd(comparison.price_delta)} ạ."
        )
    shared_preview = list(comparison.shared_attributes.items())[:3]
    for key, values in shared_preview:
        rendered = " / ".join(values[pid] for pid in ids if pid in values)
        lines.append(f"• {key}: {rendered}")
    lines.append("")
    lines.append("Anh/chị nghiêng về mẫu nào hơn để em tư vấn sâu thêm ạ?")
    text = "\n".join(lines)
    allowed = [p for p in deps.products if p.productidweb in ids]
    validation = validate_response(text, allowed_products=allowed)
    if not validation.ok:
        text = degrade_to_facts(allowed)
    return AgentReply(text=text, intent="compare_products", flags=flags)
