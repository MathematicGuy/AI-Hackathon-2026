"""Agent turn pipeline: guard → understand → remember → route → respond.

The node order and responsibility boundaries follow
`docs/product/architecture/multi-category-agent.md`. This is the
deterministic single-agent core; LangGraph checkpointer wrapping (durable
session persistence) is deferred to the persistence story and noted in the
US-206 record — the in-memory `AgentState` carries the session today.
"""

from dataclasses import dataclass, field

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.registry import CategoryRegistry
from backend.app.agent.contracts import AgentState, DEFAULT_ROLES
from backend.app.agent.conversation import coldstart, memory
from backend.app.agent.conversation.domain_rules import apply_domain_filters
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
    # Polite conversation control is always in-scope (stop/thanks must reach
    # the intent layer, not die at the degraded fail-closed gate).
    "dừng", "cảm ơn", "tạm biệt", "thôi", "quay lại",
)

_POLICY_VIOLATION_MARKERS = (
    "bỏ qua chính sách", "ngoại lệ", "dù quá hạn", "quá hạn vẫn",
    "không chịu phí", "miễn phí 100%", "bỏ qua điều khoản",
)

# Attempts to extract benefits the data does not grant: demanding extra
# discounts/gifts, claiming the bot promised something, or asking the bot to
# commit a private deal. The bot only reports promotions that exist in data.
_EXPLOIT_MARKERS = (
    "cam kết giảm", "hứa giảm", "giảm thêm cho", "bớt cho mình", "bớt thêm",
    "tặng thêm cho", "áp mã", "ghi nhận khuyến mãi", "bạn vừa hứa",
    "bạn đã hứa", "em vừa hứa", "chốt giá rẻ hơn", "deal riêng",
    "miễn phí cho mình", "free cho mình", "giảm 50% cho mình",
)

EXPLOIT_REPLY = (
    "Dạ em rất tiếc là em không thể tự tạo hay cam kết thêm ưu đãi ngoài "
    "chương trình chính thức ạ. Mọi khuyến mãi, quà tặng em tư vấn đều theo "
    "đúng dữ liệu hệ thống của Điện Máy XANH. Anh/chị muốn em kiểm tra các "
    "khuyến mãi đang có cho sản phẩm mình quan tâm để tận dụng tốt nhất không ạ?"
)

# Explicit cues that the user really wants to change product category.
_SWITCH_CUES = ("thôi", "chuyển", "đổi sang", "sang xem", "quay lại", "xem giúp")

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
    polisher: object | None = None  # LLMPolisher; optional rephrasing pass

    @classmethod
    def from_default_paths(cls, *, with_llm: bool = True) -> "AgentDependencies":
        from backend.app.agent.catalog.dataset_adapter import default_adapter

        extractor = None
        polisher = None
        if with_llm:
            from backend.app.agent.llm.client import default_extractor, default_polisher

            extractor = default_extractor()
            polisher = default_polisher()
        return cls(
            products=default_adapter().load(),
            extractor=extractor,
            polisher=polisher,
        )


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
    # 1. Benefit-exploit guard first: the bot never grants or commits
    # promotions. The reply is a fixed refusal that processes no content, so
    # checking before the input guard is safe.
    low = message.lower()
    if any(marker in low for marker in _EXPLOIT_MARKERS):
        state.guardrail_flags.append("promotion_exploit_blocked")
        return AgentReply(
            text=EXPLOIT_REPLY,
            intent="unsupported",
            flags=["promotion_exploit_blocked"],
        )

    # 2. Input guard (word count, payload, injection; agent scope = all
    # categories). A plain answer to the pending cold-start question is
    # in-scope by construction — never fail closed on it.
    guard = evaluate_input(
        message,
        in_scope_markers=_agent_scope_markers(deps.registry),
        other_category_markers=(),
    )
    state.guardrail_flags.extend(guard.flags)
    expecting_answer = state.pending_question_key is not None
    if guard.blocked and not (
        expecting_answer and guard.reason == "degraded_fail_closed"
    ):
        state.guardrail_flags.append("guardrail_block")
        text = guard.message or GUARDRAIL_REPLY
        return AgentReply(text=text, intent="unsupported", flags=list(guard.flags))

    # 2. Understand (LLM route when configured, deterministic fallback always).
    understanding, flags = await understand_turn(
        message,
        extractor=deps.extractor,
        state_summary=_state_summary(state),
        registry=deps.registry,
    )
    state.guardrail_flags.extend(flags)

    # 2b. A low-confidence (fallback) category switch mid-conversation needs an
    # explicit switch cue — merely mentioning another appliance ("mình chưa có
    # màn hình" while buying a PC) must not reroute the whole consultation.
    if (
        understanding.confidence <= 0.35
        and state.need.category_code is not None
        and understanding.need_patch.category_code
        not in (None, state.need.category_code)
        and not any(cue in low for cue in _SWITCH_CUES)
    ):
        patch = understanding.need_patch.model_copy(update={"category_code": None})
        understanding = understanding.model_copy(update={"need_patch": patch})

    # 2c. Capture the pending cold-start answer when the reply carried no
    # structured signal (keeps per-category filter memory complete).
    understanding = _capture_pending_answer(state, message, understanding)

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

    return await _product_flow(state, deps, intent, flags)


def _state_summary(state: AgentState) -> str:
    need = state.need
    if need.category_code is None:
        return ""
    parts = [f"ngành đang tư vấn: {need.category_code}"]
    if need.usage_purpose:
        parts.append(f"mục đích: {need.usage_purpose}")
    if need.budget_max:
        parts.append(f"ngân sách tối đa: {need.budget_max}")
    if state.pending_question_key:
        parts.append(f"đang chờ khách trả lời câu hỏi: {state.pending_question_key}")
    return "; ".join(parts)


def _capture_pending_answer(state, message: str, understanding):
    key = state.pending_question_key
    if not key:
        return understanding
    patch = understanding.need_patch
    switching = patch.category_code not in (None, state.need.category_code)
    if switching:
        state.pending_question_key = None
        return understanding
    explicit = patch.model_fields_set - {"requested_roles"}
    has_signal = any(
        getattr(patch, name) not in (None, [], {}) for name in explicit
    )
    if understanding.intent == "unsupported" or not has_signal:
        answer = message.strip()[:120]
        if key == "purpose" and state.need.usage_purpose is None:
            state.need = state.need.model_copy(update={"usage_purpose": answer})
        else:
            constraints = dict(state.need.attribute_constraints)
            constraints[key] = answer
            state.need = state.need.model_copy(
                update={"attribute_constraints": constraints}
            )
        if understanding.intent == "unsupported":
            understanding = understanding.model_copy(update={"intent": "new_search"})
    state.pending_question_key = None
    return understanding


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


async def _product_flow(
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
            state.pending_question_key = question.key
            return AgentReply(text=question.ask, intent=intent, flags=flags)

    # Enough to act: search, suggest by roles, sell.
    shown = state.shown_for(category)
    exclude = tuple(shown) if intent == "more_recommendations" else ()
    # Pool of 20 (search maximum) so the value/performance roles see more than
    # the cheapest page (audit finding: a pool of 10 price-sorted items biased
    # every role toward cheap products).
    result = search_products(
        deps.products,
        category_code=category,
        budget_min=need.budget_min,
        budget_max=need.budget_max,
        brands=tuple(need.brand_prefs),
        limit=20,
        exclude_ids=exclude,
    )
    if not result.items:
        budget_note = (
            f" trong tầm giá {format_vnd(need.budget_max)}" if need.budget_max else ""
        )
        unpriced_note = ""
        if need.budget_max is not None or need.budget_min is not None:
            unpriced = sum(
                1
                for p in deps.products
                if p.category_code == category and p.effective_price is None
            )
            if unpriced:
                unpriced_note = (
                    f" (Ngoài ra có {unpriced} mẫu chưa niêm yết giá trên hệ "
                    "thống — anh/chị có thể để lại nhu cầu, em nhờ cửa hàng "
                    "báo giá chính xác ạ.)"
                )
        return AgentReply(
            text=(
                f"Dạ em chưa tìm được mẫu {registry_category.sheet_name}"
                f"{budget_note} phù hợp ạ. Anh/chị có thể nới ngân sách một chút "
                "hoặc bỏ bớt một tiêu chí để em tìm thêm lựa chọn tốt không ạ?"
                + unpriced_note
            ),
            intent=intent,
            flags=flags,
        )

    # Per-category domain rules narrow the pool from captured answers
    # (household → capacity band, room area → coverage, screen size → inches).
    pool = apply_domain_filters(result.items, need)
    roles = tuple(need.requested_roles) or DEFAULT_ROLES
    suggestions = suggest_products(pool, category_code=category, roles=roles)
    winner_ids = {p.productidweb for p in suggestions.distinct_products}
    also_consider = [
        p for p in pool if p.productidweb not in winner_ids
    ][:3]
    follow_up = coldstart.next_question(state)
    question_text = None
    if follow_up is not None:
        coldstart.record_asked(state, follow_up)
        state.pending_question_key = follow_up.key
        question_text = follow_up.ask
    response = render_suggestions(
        suggestions,
        category_name=registry_category.sheet_name,
        next_question=question_text,
        also_consider=also_consider,
    )
    validation = validate_response(
        response.text, allowed_products=response.allowed_products
    )
    text = response.text if validation.ok else degrade_to_facts(response.allowed_products)

    # Optional LLM polish: rephrase, then re-validate against the same
    # records; any violation keeps the deterministic text.
    if validation.ok and deps.polisher is not None:
        polished = await deps.polisher.polish(text)
        if polished and polished != text:
            recheck = validate_response(
                polished, allowed_products=response.allowed_products
            )
            if recheck.ok:
                text = polished
            else:
                flags = flags + ["polish_rejected"]

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
