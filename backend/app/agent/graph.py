"""Agent turn pipeline: guard → understand → remember → route → respond.

The node order and responsibility boundaries follow
`docs/product/architecture/multi-category-agent.md`. This is the
deterministic single-agent core; LangGraph checkpointer wrapping (durable
session persistence) is deferred to the persistence story and noted in the
US-206 record — the in-memory `AgentState` carries the session today.
"""

import re
from dataclasses import dataclass, field

from backend.app.agent.catalog.dataset_adapter import GenericProduct
from backend.app.agent.catalog.dimensions import (
    better_of,
    dimension_display,
    dimension_value,
    dimensions_for,
    metric_explanation,
    rankable,
)
from backend.app.agent.catalog.registry import CategoryRegistry
from backend.app.agent.contracts import AgentState
from backend.app.agent.conversation import coldstart, memory
from backend.app.agent.conversation.domain_rules import apply_domain_filters
from backend.app.agent.conversation.understand import (
    UnderstandingExtractor,
    understand_turn,
)
from backend.app.agent.policies.answer import (
    build_policy_answer,
    degradation_response,
    display_source,
)
from backend.app.agent.policies.corpus import PolicyCorpus
from backend.app.agent.respond import format_trieu, format_vnd, render_suggestions
from backend.app.agent.tools.aggregate import category_overview
from backend.app.agent.tools.compare import compare_products
from backend.app.agent.tools.search import search_products
from backend.app.agent.tools.suggest import suggest_products
from backend.app.agent.validate import degrade_to_facts, validate_response
from backend.app.guardrails.input_rules import evaluate_input
from backend.app.observability import AgentObserver, noop_agent_observer

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

# Products people ask for that the catalog does not carry, with the closest
# in-catalog alternatives. An honest "bên em chưa kinh doanh X" beats a menu
# dump (Cường's live-test 2: "có laptop không?").
_UNAVAILABLE_PRODUCTS: dict[str, tuple[str, ...]] = {
    "laptop": ("Máy tính để bàn", "Máy tính bảng", "Màn hình máy tính"),
    "máy tính xách tay": ("Máy tính để bàn", "Máy tính bảng"),
    "điện thoại": ("Máy tính bảng", "Đồng hồ thông minh"),
    "tivi": ("Màn hình máy tính",),
    "ti vi": ("Màn hình máy tính",),
    "tv": ("Màn hình máy tính",),
    "loa": ("Micro karaoke",),
    "tai nghe": ("Micro thu âm điện thoại",),
    "quạt": ("Máy lạnh",),
    "nồi chiên": ("Máy rửa chén",),
    "lò vi sóng": ("Máy rửa chén",),
}

# The customer is asking ABOUT the bot's pending question, not answering it
# ("mục đích sử dụng tủ lạnh á?").
_ECHO_MARKERS = ("á?", "á ?", " hả", "là sao", "nghĩa là", "ý em", "ý là gì")

# Deep questions about the products/metrics just presented ("cái nào tốt hơn
# về mặt hiệu năng?", "thang đo là gì?", "màn nào nét hơn?").
_PRODUCT_QA_MARKERS = (
    "thang đo", "tốt hơn về", "hơn về mặt", "nào tốt hơn", "nào nét hơn",
    "nào êm hơn", "nào mạnh hơn", "nào bền hơn", "nào tiết kiệm",
    "khác nhau chỗ nào", "khác gì nhau", "hiệu năng ở đây", "đo bằng gì",
    "dựa vào đâu", "chấm theo",
)
_QA_COMPARATIVE = re.compile(r"nào\s+\w+\s+hơn|cái nào .{0,24}hơn")

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
    observer: AgentObserver | None = None

    @classmethod
    def from_default_paths(cls, *, with_llm: bool = True) -> "AgentDependencies":
        from backend.app.agent.catalog.dataset_adapter import default_adapter
        from backend.app.observability import default_agent_observer

        observer = default_agent_observer()
        extractor = None
        polisher = None
        if with_llm:
            from backend.app.agent.llm.client import default_extractor, default_polisher

            extractor = default_extractor(observer=observer)
            polisher = default_polisher(observer=observer)
        return cls(
            products=default_adapter().load(),
            extractor=extractor,
            polisher=polisher,
            observer=observer,
        )


@dataclass(frozen=True, slots=True)
class AgentReply:
    text: str
    intent: str
    flags: list[str] = field(default_factory=list)
    presented_ids: list[str] = field(default_factory=list)


def _observer(deps: AgentDependencies) -> AgentObserver:
    observer = deps.observer
    if observer is None or not callable(getattr(observer, "span", None)):
        return noop_agent_observer()
    return observer


def _state_snapshot(state: AgentState) -> dict[str, object]:
    return {
        "turn_number": state.turn_number,
        "current_intent": state.current_intent,
        "need": state.need.model_dump(),
        "previous_needs": {
            category: need.model_dump()
            for category, need in state.previous_needs.items()
        },
        "pending_question_key": state.pending_question_key,
        "shown_product_ids": dict(state.shown_product_ids),
        "last_presented_ids": list(state.last_presented_ids),
        "guardrail_flags": list(state.guardrail_flags),
    }


def _observed_response(
    observer: AgentObserver,
    reply: AgentReply,
    *,
    outcome: str,
    response_source: str = "deterministic",
    polish_accepted: bool | None = None,
) -> AgentReply:
    metadata: dict[str, object] = {
        "outcome": outcome,
        "response_source": response_source,
    }
    if polish_accepted is not None:
        metadata["polish_accepted"] = polish_accepted
    with observer.span(
        "response_generation",
        input={"intent": reply.intent},
        metadata={"outcome": outcome},
    ) as observation:
        observation.update(
            output={
                "text": reply.text,
                "intent": reply.intent,
                "flags": reply.flags,
                "presented_ids": reply.presented_ids,
            },
            metadata=metadata,
        )
    return reply


def _observe_output_validation(
    observer: AgentObserver,
    *,
    text: str,
    allowed_product_ids: list[str],
    ok: bool,
    violations: list[str],
) -> None:
    outcome = "accepted" if ok else "degraded"
    with observer.span(
        "output_validation",
        input={
            "text": text,
            "allowed_product_ids": allowed_product_ids,
        },
        metadata={"outcome": outcome},
    ) as observation:
        observation.update(
            output={"ok": ok, "violations": violations},
            metadata={"outcome": outcome},
        )


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
    observer = _observer(deps)
    try:
        reply = await _run_turn_core(state, message, deps, observer)
        # Conversation context for the LLM extractor (trimmed, last 3 exchanges).
        state.recent_turns.append((message[:200], reply.text[:200]))
        del state.recent_turns[:-3]
        return reply
    finally:
        with observer.span(
            "final_state",
            input={"session_id": state.session_id},
            metadata={"turn_number": state.turn_number},
        ) as observation:
            observation.update(
                output=_state_snapshot(state),
                metadata={"intent": state.current_intent},
            )


async def _run_turn_core(
    state: AgentState, message: str, deps: AgentDependencies, observer: AgentObserver
) -> AgentReply:
    # 1. Benefit-exploit guard first: the bot never grants or commits
    # promotions. The reply is a fixed refusal that processes no content, so
    # checking before the input guard is safe.
    low = message.lower()
    if any(marker in low for marker in _EXPLOIT_MARKERS):
        state.guardrail_flags.append("promotion_exploit_blocked")
        with observer.span(
            "input_guardrail",
            input={"message": message},
            metadata={"subtype": "promotion_exploit"},
        ) as observation:
            observation.update(
                output={"blocked": True, "flags": ["promotion_exploit_blocked"]},
                metadata={"subtype": "promotion_exploit"},
            )
        return _observed_response(
            observer,
            AgentReply(
                text=EXPLOIT_REPLY,
                intent="unsupported",
                flags=["promotion_exploit_blocked"],
            ),
            outcome="guardrail_block",
        )

    # 2. Input guard — deliberate abuse only (Cường's rebalance): word limit,
    # payload/injection/credential rules, and a real NeMo block. Ordinary text
    # without shopping markers is NOT refused; friendliness is handled by the
    # understanding layer, so degraded fail-closed never fires here.
    with observer.span(
        "input_guardrail",
        input={"message": message},
    ) as observation:
        guard = evaluate_input(
            message,
            in_scope_markers=_agent_scope_markers(deps.registry),
            other_category_markers=(),
        )
        observation.update(
            output={
                "blocked": guard.blocked,
                "stage": guard.stage,
                "reason": guard.reason,
                "flags": list(guard.flags),
            },
            metadata={
                "subtype": guard.stage or "passed",
                "reason": guard.reason,
            },
        )
    state.guardrail_flags.extend(guard.flags)
    if guard.blocked and guard.reason != "degraded_fail_closed":
        state.guardrail_flags.append("guardrail_block")
        text = guard.message or GUARDRAIL_REPLY
        return _observed_response(
            observer,
            AgentReply(text=text, intent="unsupported", flags=list(guard.flags)),
            outcome="guardrail_block",
        )

    # 2a-pre0. Deep question about the products/metrics just presented takes
    # precedence over everything conversational — the echo flow must never
    # swallow "cái nào tốt hơn về mặt hiệu năng? thang đo là gì?" (live-test
    # 3 failure).
    if _is_product_qa(state, low):
        return _observed_response(
            observer,
            await _product_qa_flow(state, low, deps, []),
            outcome="product_qa",
        )

    # 2a-pre. The customer is asking ABOUT the bot's own question, not
    # answering it ("mục đích sử dụng tủ lạnh á?") — explain with a concrete
    # example instead of capturing the echo or routing anywhere else.
    if _is_question_echo(state, low):
        return _observed_response(
            observer,
            _question_clarification_flow(state, low, deps),
            outcome="question_clarification",
        )

    # 2a-pre2. Honest no-stock answer for products the catalog does not carry
    # ("có laptop không?") — never a bare menu dump.
    if deps.registry.detect(message) is None:
        unavailable = _unavailable_reply(low, deps.registry)
        if unavailable is not None:
            return _observed_response(
                observer,
                AgentReply(text=unavailable, intent="unsupported", flags=[]),
                outcome="unsupported",
            )

    # 2. Understand (LLM route when configured, deterministic fallback always).
    understanding, flags = await understand_turn(
        message,
        extractor=deps.extractor,
        state_summary=_state_summary(state),
        registry=deps.registry,
        active_category=state.need.category_code,
        observer=observer,
    )
    state.guardrail_flags.extend(flags)

    before_state = _state_snapshot(state)
    with observer.span(
        "state_update",
        input={"state": before_state},
    ) as state_observation:
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
        after_state = _state_snapshot(state)
        delta = {
            key: {"before": before_state[key], "after": after_state[key]}
            for key in before_state
            if before_state[key] != after_state[key]
        }
        state_observation.update(
            output={"state": after_state},
            metadata={"memory_delta": delta},
        )
    intent = understanding.intent

    # 4. Route.
    route = {
        "stop": "stop",
        "policy_question": "policy_flow",
        "unsupported": "unsupported",
    }.get(intent, "product_flow")
    with observer.span(
        "route_decision",
        input={"intent": intent},
        metadata={"route": route},
    ) as route_observation:
        route_observation.update(
            output={"intent": intent},
            metadata={
                "route": route,
                "branch": (
                    "policy"
                    if intent == "policy_question"
                    else route.removesuffix("_flow")
                ),
            },
        )
    if intent == "stop":
        return _observed_response(
            observer,
            AgentReply(text=STOP_REPLY, intent=intent, flags=flags),
            outcome="stop",
        )

    if intent == "policy_question":
        return _policy_flow(message, deps, flags, observer)

    if intent == "smalltalk":
        return _observed_response(
            observer,
            await _smalltalk_flow(state, message, deps, flags, observer),
            outcome="smalltalk",
        )

    if intent == "question_clarification":
        return _observed_response(
            observer,
            _question_clarification_flow(state, low, deps),
            outcome="question_clarification",
        )

    if intent == "product_qa":
        return _observed_response(
            observer,
            await _product_qa_flow(state, low, deps, flags),
            outcome="product_qa",
        )

    if intent == "catalog_overview":
        return _observed_response(
            observer,
            _catalog_overview_flow(state, deps, flags),
            outcome="catalog_overview",
        )

    if intent == "price_range_query":
        return _observed_response(
            observer,
            _price_range_flow(state, deps, flags),
            outcome="price_range",
        )

    if intent == "promotion_inquiry":
        return _observed_response(
            observer,
            _promotion_flow(state, deps, flags),
            outcome="promotion",
        )

    if intent == "unsupported":
        return _observed_response(
            observer,
            AgentReply(text=_category_menu(deps.registry), intent=intent, flags=flags),
            outcome="unsupported",
        )

    return await _product_flow(state, deps, intent, flags, observer, low)


def _state_summary(state: AgentState) -> str:
    need = state.need
    parts: list[str] = []
    if need.category_code is not None:
        parts.append(f"ngành đang tư vấn: {need.category_code}")
        if need.usage_purpose:
            parts.append(f"mục đích: {need.usage_purpose}")
        if need.budget_min:
            parts.append(f"ngân sách tối thiểu: {need.budget_min}")
        if need.budget_max:
            parts.append(f"ngân sách tối đa: {need.budget_max}")
        asked = state.asked_questions.get(need.category_code) or []
        if asked:
            parts.append(f"đã hỏi các câu: {', '.join(asked)}")
    if state.pending_question_text:
        parts.append(
            f'bot vừa hỏi và đang chờ trả lời: "{state.pending_question_text}"'
        )
    if state.recent_turns:
        history = " | ".join(
            f"Khách: {user} → Bot: {bot}" for user, bot in state.recent_turns
        )
        parts.append(f"3 lượt gần nhất: {history}")
    return "; ".join(parts)


def _is_question_echo(state: AgentState, low: str) -> bool:
    if state.pending_question_key is None and state.need.category_code is None:
        return False
    if not any(marker in low for marker in _ECHO_MARKERS):
        return False
    if "mục đích" in low:
        return True
    pending = (state.pending_question_text or "").lower()
    if not pending:
        return False
    pending_words = {w for w in re.findall(r"[\wÀ-ỹ]+", pending) if len(w) >= 3}
    message_words = {w for w in re.findall(r"[\wÀ-ỹ]+", low) if len(w) >= 3}
    return len(pending_words & message_words) >= 2


def _question_clarification_flow(
    state: AgentState, low: str, deps: AgentDependencies
) -> AgentReply:
    category = state.need.category_code
    category_name = (
        deps.registry.by_code(category).sheet_name if category else "sản phẩm"
    )
    if "mục đích" in low:
        example = coldstart.purpose_example(category) or (
            "dùng hằng ngày hay có nhu cầu đặc biệt"
        )
        text = (
            f"Dạ ý em là anh/chị định dùng {category_name} cho nhu cầu nào ạ — "
            f"ví dụ: {example}. Anh/chị cứ mô tả thoải mái, em sẽ lọc đúng mẫu "
            "phù hợp ạ."
        )
        return AgentReply(text=text, intent="question_clarification", flags=[])
    example = coldstart.question_example(category, state.pending_question_key)
    question = state.pending_question_text or (
        "anh/chị cho em xin thêm thông tin về nhu cầu của mình ạ"
    )
    lines = [f"Dạ em xin hỏi lại cho rõ ạ: {question}"]
    if example:
        lines.append(f"(Ví dụ: {example} ạ.)")
    return AgentReply(
        text="\n".join(lines), intent="question_clarification", flags=[]
    )


def _is_product_qa(state: AgentState, low: str) -> bool:
    if not state.last_presented_ids:
        return False
    if any(marker in low for marker in _PRODUCT_QA_MARKERS):
        return True
    if _QA_COMPARATIVE.search(low):
        return True
    # A dimension the category knows, asked with a comparative/question form.
    dims = dimensions_for(state.need.category_code)
    mentions_dim = any(
        marker in low for dim in dims for marker in dim.pref_markers
    )
    return mentions_dim and ("hơn" in low or "là gì" in low or "bao nhiêu" in low)


def _question_dimensions(state: AgentState, low: str) -> list:
    dims = dimensions_for(state.need.category_code)
    matched = [
        dim
        for dim in dims
        if dim.label.lower() in low
        or any(marker in low for marker in dim.pref_markers)
    ]
    if matched:
        return matched
    # Generic "hiệu năng/tốt hơn" → the rankable dimensions, strongest first.
    return [dim for dim in dims if rankable(dim)][:3]


async def _product_qa_flow(
    state: AgentState, low: str, deps: AgentDependencies, flags: list[str]
) -> AgentReply:
    category = state.need.category_code
    presented = [
        p
        for pid in state.last_presented_ids[:3]
        for p in deps.products
        if p.productidweb == pid
    ]
    if not presented or not dimensions_for(category):
        return AgentReply(
            text=(
                "Dạ anh/chị hỏi về mẫu nào ạ? Em gợi ý vài mẫu trước rồi mình "
                "đi sâu từng thông số nhé ạ?"
            ),
            intent="product_qa",
            flags=flags,
        )
    lines: list[str] = []
    wants_metric = any(
        marker in low
        for marker in ("là gì", "thang đo", "đo bằng", "dựa vào đâu", "chấm theo")
    )
    category_name = deps.registry.by_code(category).sheet_name if category else ""
    if wants_metric:
        explanation = metric_explanation(category)
        if explanation:
            lines.append(
                f"Dạ với {category_name}, em đánh giá dựa trên các thang đo: "
                f"{explanation} ạ."
            )
        lines.append("")
    dims = _question_dimensions(state, low)
    lines.append("Em so trực tiếp các mẫu vừa gợi ý theo dữ liệu hãng công bố ạ:")
    for dim in dims[:4]:
        values: list[str] = []
        for product in presented:
            shown = dimension_display(product, dim)
            values.append(
                f"{product.name}: {shown if shown else 'hãng không công bố'}"
            )
        lines.append(f"• {dim.label} — " + " | ".join(values))
        if rankable(dim) and len(presented) >= 2:
            first_value = dimension_value(presented[0], dim)
            second_value = dimension_value(presented[1], dim)
            verdict = better_of(first_value, second_value, dim)
            if verdict != 0:
                winner = presented[0] if verdict == -1 else presented[1]
                lines.append(f"  → {winner.name} nhỉnh hơn ở mục này ạ.")
    lines.append("")
    lines.append(
        "Anh/chị nghiêng về tiêu chí nào nhất để em chốt mẫu phù hợp ạ?"
    )
    text = "\n".join(lines)
    validation = validate_response(text, allowed_products=presented)
    if not validation.ok:
        text = degrade_to_facts(presented)
    if deps.polisher is not None:
        polished = await deps.polisher.polish(text)
        if polished and polished != text:
            recheck = validate_response(polished, allowed_products=presented)
            if recheck.ok:
                text = polished
    return AgentReply(text=text, intent="product_qa", flags=flags)


def _unavailable_reply(low: str, registry: CategoryRegistry) -> str | None:
    for term, alternatives in _UNAVAILABLE_PRODUCTS.items():
        if term in low:
            alt = ", ".join(alternatives)
            return (
                f"Dạ bên em hiện chưa kinh doanh {term} ạ. Gần nhất bên em có "
                f"{alt} — anh/chị có muốn em tư vấn thử không ạ?"
            )
    return None


def _capture_pending_answer(state, message: str, understanding):
    key = state.pending_question_key
    if not key:
        return understanding
    patch = understanding.need_patch
    switching = patch.category_code not in (None, state.need.category_code)
    if switching:
        state.pending_question_key = None
        state.pending_question_text = None
        return understanding
    # A redundant category_code equal to the active category is not new
    # information — it must not suppress the pending-answer capture ("nhà 4
    # người" while the household question is pending).
    explicit = patch.model_fields_set - {"requested_roles", "category_code"}
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
    state.pending_question_text = None
    return understanding


_COOLING_MARKERS = ("nóng", "oi bức", "nóng bức")
_THANKS_MARKERS = ("cảm ơn", "cám ơn")
_AGREE_MARKERS = ("đồng ý", "ok", "oke", "được đó", "ừ")


async def _smalltalk_flow(
    state: AgentState,
    message: str,
    deps: AgentDependencies,
    flags: list[str],
    observer: AgentObserver,
) -> AgentReply:
    """Friendly retail small talk with a gentle sales pivot — never a refusal."""
    low = message.lower()
    if any(marker in low for marker in _COOLING_MARKERS):
        text = (
            "Dạ em hiểu anh/chị đang cảm thấy thời tiết nóng bức ạ. Nếu cần tư "
            "vấn sản phẩm hỗ trợ làm mát như máy lạnh hay quạt điều hòa, "
            "anh/chị cho em biết diện tích phòng và tầm giá để em hỗ trợ nhanh "
            "chóng ạ."
        )
    elif any(marker in low for marker in _THANKS_MARKERS):
        text = (
            "Dạ em cảm ơn anh/chị ạ! Rất vui được hỗ trợ mình. Anh/chị cần em "
            "tư vấn thêm sản phẩm nào nữa không ạ?"
        )
    elif any(marker in low for marker in _AGREE_MARKERS):
        # Confirmation mid-flow: continue the product conversation.
        if state.need.category_code is not None:
            return await _product_flow(state, deps, "new_search", flags, observer)
        text = (
            "Dạ vâng ạ! Anh/chị đang quan tâm sản phẩm nào để em tư vấn ngay ạ?"
        )
    else:
        text = (
            "Dạ em chào anh/chị ạ! Em là trợ lý tư vấn của Điện Máy XANH. "
            "Anh/chị đang cần tìm sản phẩm nào để em hỗ trợ mình ạ?"
        )
    if deps.polisher is not None:
        polished = await deps.polisher.polish(text)
        if polished and validate_response(polished, allowed_products=[]).ok:
            text = polished
    return AgentReply(text=text, intent="smalltalk", flags=flags)


def _catalog_overview_flow(
    state: AgentState, deps: AgentDependencies, flags: list[str]
) -> AgentReply:
    category = state.need.category_code
    if category is None:
        return AgentReply(
            text=_category_menu(deps.registry), intent="catalog_overview", flags=flags
        )
    overview = category_overview(deps.products, category_code=category)
    registry_category = deps.registry.by_code(category)
    top_brands = sorted(
        overview.brand_counts.items(), key=lambda kv: -kv[1]
    )[:5]
    lines = [
        f"Dạ ngành {registry_category.sheet_name} bên em hiện có "
        f"{overview.product_count} mẫu ạ.",
    ]
    if top_brands:
        lines.append(
            "Các thương hiệu nổi bật: "
            + ", ".join(name for name, _ in top_brands) + "."
        )
    if overview.price_min is not None and overview.price_max is not None:
        lines.append(
            f"Giá niêm yết từ {format_vnd(overview.price_min)} đến "
            f"{format_vnd(overview.price_max)}."
        )
    lines.append(
        "Anh/chị cho em biết nhu cầu và tầm giá để em gợi ý đúng mẫu phù hợp ạ?"
    )
    return AgentReply(
        text="\n".join(lines), intent="catalog_overview", flags=flags
    )


def _price_range_flow(
    state: AgentState, deps: AgentDependencies, flags: list[str]
) -> AgentReply:
    category = state.need.category_code
    if category is None:
        return AgentReply(
            text=(
                "Dạ anh/chị muốn xem vùng giá của ngành hàng nào ạ (tủ lạnh, "
                "máy giặt, máy lạnh...) để em tra chính xác giúp mình ạ?"
            ),
            intent="price_range_query",
            flags=flags,
        )
    overview = category_overview(deps.products, category_code=category)
    registry_category = deps.registry.by_code(category)
    if overview.price_min is None or overview.price_max is None:
        return AgentReply(
            text=(
                f"Dạ hiện các mẫu {registry_category.sheet_name} bên em chưa "
                "niêm yết giá trên hệ thống ạ. Anh/chị để lại nhu cầu, em nhờ "
                "cửa hàng gần nhất báo giá chính xác giúp mình nhé ạ?"
            ),
            intent="price_range_query",
            flags=flags,
        )
    text = (
        f"Dạ {registry_category.sheet_name} bên em đang có "
        f"{overview.product_count} mẫu, giá niêm yết dao động từ "
        f"{format_vnd(overview.price_min)} đến {format_vnd(overview.price_max)} ạ.\n"
        "Anh/chị dự định trong tầm nào để em lọc đúng những mẫu đáng tiền nhất "
        "cho mình ạ?"
    )
    return AgentReply(text=text, intent="price_range_query", flags=flags)


def _promotion_flow(
    state: AgentState, deps: AgentDependencies, flags: list[str]
) -> AgentReply:
    category = state.need.category_code
    pool = [
        p
        for p in deps.products
        if category is None or p.category_code == category
    ]
    discounted = [p for p in pool if p.promotion.discount_percent is not None]
    gifted = [p for p in pool if p.gift_promotion]
    if not discounted and not gifted:
        return AgentReply(
            text=(
                "Dạ hiện em chưa có thông tin cụ thể về chương trình khuyến "
                "mãi đang diễn ra ạ. Anh/chị vui lòng truy cập website Điện "
                "Máy XANH hoặc đến cửa hàng gần nhất để được cập nhật khuyến "
                "mãi mới nhất giúp em ạ."
            ),
            intent="promotion_inquiry",
            flags=flags,
        )
    scope_note = (
        f"ngành {deps.registry.by_code(category).sheet_name}"
        if category
        else "toàn hệ thống"
    )
    lines = [
        f"Dạ {scope_note} bên em đang có {len(discounted)} mẫu giảm giá và "
        f"{len(gifted)} mẫu kèm quà tặng ạ.",
    ]
    top = sorted(
        discounted, key=lambda p: -(p.promotion.discount_percent or 0)
    )[:3]
    if top:
        lines.append("Một vài ưu đãi nổi bật:")
        for product in top:
            lines.append(
                f"• {product.name}: giảm {product.promotion.discount_percent:.0f}%"
                f", còn {format_vnd(product.effective_price)}"
            )
    lines.append(
        "Anh/chị quan tâm ngành hàng nào để em nêu ưu đãi chi tiết và chọn "
        "mẫu hời nhất ạ?"
    )
    text = "\n".join(lines)
    validation = validate_response(text, allowed_products=top)
    if not validation.ok:
        text = degrade_to_facts(top)
    return AgentReply(text=text, intent="promotion_inquiry", flags=flags)


def _policy_flow(
    message: str,
    deps: AgentDependencies,
    flags: list[str],
    observer: AgentObserver,
) -> AgentReply:
    with observer.span(
        "policy_retrieval",
        input={"message": message},
    ) as retrieval_observation:
        answer = build_policy_answer(deps.corpus, message)
        retrieval_outcome = "matches" if answer.quotes else "no_match"
        retrieval_observation.update(
            output={
                "sources": list(answer.sources),
                "quotes": list(answer.quotes),
                "count": len(answer.quotes),
            },
            metadata={"outcome": retrieval_outcome},
        )
    low = message.lower()
    if any(marker in low for marker in _POLICY_VIOLATION_MARKERS):
        text = degradation_response(user_request=message, answer=answer)
        return _observed_response(
            observer,
            AgentReply(text=text, intent="policy_question", flags=flags),
            outcome="policy_conflict",
        )
    if not answer.quotes:
        return _observed_response(
            observer,
            AgentReply(
                text=(
                    "Dạ em chưa tìm thấy điều khoản phù hợp với câu hỏi này ạ. "
                    "Anh/chị có thể hỏi rõ hơn, hoặc gọi tổng đài 1900 232 461 để "
                    "được hỗ trợ chính xác nhất ạ."
                ),
                intent="policy_question",
                flags=flags,
            ),
            outcome="policy_no_match",
        )
    # Natural presentation: customer-facing policy name, quote rendered as
    # normal text. The literal-quote framing appears only when the user asked
    # for it ("nguyên văn"/"trích"). Verbatim validation still runs below.
    source_name = display_source(answer.sources[0])
    wants_literal = "nguyên văn" in low or "trích" in low
    if wants_literal:
        lines = [
            f"Dạ theo {source_name} của bên em, trích nguyên văn ạ:",
            f'"{answer.quotes[0]}"',
        ]
    else:
        lines = [
            f"Dạ theo {source_name} của bên em ạ:",
            answer.quotes[0],
        ]
    lines += [
        "",
        "Anh/chị cần em giải thích thêm điểm nào trong chính sách này không ạ?",
    ]
    text = "\n".join(lines)
    validation_input = text
    result = validate_response(
        text, allowed_products=[], policy_quotes=[answer.quotes[0]], corpus=deps.corpus
    )
    if not result.ok:
        # A failed quote check means WE could not ground the answer — that is
        # a retrieval problem, never the customer violating policy, so the
        # violation apology would be the wrong frame (live-test 2 finding).
        text = (
            "Dạ em chưa tìm thấy điều khoản phù hợp với câu hỏi này ạ. "
            "Anh/chị có thể hỏi rõ hơn, hoặc gọi tổng đài 1900 232 461 để "
            "được hỗ trợ chính xác nhất ạ."
        )
    reply = _observed_response(
        observer,
        AgentReply(text=text, intent="policy_question", flags=flags),
        outcome="policy_answer" if result.ok else "policy_degraded",
    )
    _observe_output_validation(
        observer,
        text=validation_input,
        allowed_product_ids=[],
        ok=result.ok,
        violations=list(result.violations),
    )
    return reply


async def _product_flow(
    state: AgentState,
    deps: AgentDependencies,
    intent: str,
    flags: list[str],
    observer: AgentObserver,
    low: str = "",
) -> AgentReply:
    need = state.need
    category = need.category_code

    if category is None:
        return _observed_response(
            observer,
            AgentReply(text=_category_menu(deps.registry), intent=intent, flags=flags),
            outcome="clarification",
        )

    registry_category = deps.registry.by_code(category)

    if intent == "compare_products":
        return _compare_flow(state, deps, flags, observer, low)

    if intent == "check_availability":
        return _observed_response(
            observer,
            AgentReply(
                text=(
                    "Dạ hiện em chưa có dữ liệu tồn kho theo thời gian thực ạ. "
                    "Anh/chị để lại khu vực của mình, em sẽ nhờ cửa hàng gần nhất "
                    "kiểm tra và báo lại ngay ạ?"
                ),
                intent=intent,
                flags=flags,
            ),
            outcome="availability_unavailable",
        )

    # Cold-start: bundle the top 2-3 missing questions into one opener
    # message; later gaps are asked one at a time as follow-ups.
    if not coldstart.has_material_minimum(need):
        questions = coldstart.opening_questions(state, limit=3)
        if questions:
            text = coldstart.render_opening(
                questions, registry_category.sheet_name
            )
            return _observed_response(
                observer,
                AgentReply(text=text, intent=intent, flags=flags),
                outcome="clarification",
            )

    # Enough to act: search, suggest by roles, sell.
    shown = state.shown_for(category)
    # "Show more" excludes what the customer already saw — but an explicit
    # role ask ("máy đắt nhất") is a selection over the WHOLE pool: the
    # answer may legitimately be a model already shown.
    exclude = (
        tuple(shown)
        if intent == "more_recommendations" and not need.requested_roles
        else ()
    )
    # Pool of 20 (search maximum) so the value/performance roles see more than
    # the cheapest page (audit finding: a pool of 10 price-sorted items biased
    # every role toward cheap products).
    search_input = {
        "category_code": category,
        "budget_min": need.budget_min,
        "budget_max": need.budget_max,
        "brands": tuple(need.brand_prefs),
        "limit": 20,
        "exclude_ids": exclude,
    }
    with observer.span("product_search", input=search_input) as search_observation:
        result = search_products(
            deps.products,
            category_code=category,
            budget_min=need.budget_min,
            budget_max=need.budget_max,
            brands=tuple(need.brand_prefs),
            limit=20,
            exclude_ids=exclude,
            budget_slack=0.08,
        )
        search_outcome = "matches" if result.items else "no_match"
        search_observation.update(
            output={
                "product_ids": [p.productidweb for p in result.items],
                "count": len(result.items),
                "total_candidates": result.total_candidates,
                "has_more": result.has_more,
            },
            metadata={"outcome": search_outcome},
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
        return _observed_response(
            observer,
            AgentReply(
                text=(
                    f"Dạ em chưa tìm được mẫu {registry_category.sheet_name}"
                    f"{budget_note} phù hợp ạ. Anh/chị có thể nới ngân sách một chút "
                    "hoặc bỏ bớt một tiêu chí để em tìm thêm lựa chọn tốt không ạ?"
                    + unpriced_note
                ),
                intent=intent,
                flags=flags,
            ),
            outcome="no_match",
        )

    # Per-category domain rules narrow the pool from captured answers
    # (household → capacity band, room area → coverage, screen size → inches).
    roles = tuple(need.requested_roles) or None
    with observer.span(
        "filter_and_rank",
        input={
            "product_ids": [p.productidweb for p in result.items],
            "need": need.model_dump(),
            "roles": list(need.requested_roles),
        },
    ) as rank_observation:
        pool = apply_domain_filters(result.items, need)
        # Explicit customer roles win; otherwise suggest_products derives
        # preference-driven dimension roles from the need (classic trio when the
        # need carries no dimension signal — additive, never regressive).
        suggestions = suggest_products(
            pool, category_code=category, roles=roles, need=need
        )
        rank_observation.update(
            output={
                "eligible_ids": [p.productidweb for p in pool],
                "winners": {
                    role: product.productidweb
                    for role, product in suggestions.winners.items()
                },
                "skipped_roles": list(suggestions.skipped_roles),
            },
            metadata={"skipped_roles": list(suggestions.skipped_roles)},
        )
    winner_ids = {p.productidweb for p in suggestions.distinct_products}
    also_consider = [
        p for p in pool if p.productidweb not in winner_ids
    ][:3]
    follow_up = coldstart.next_question(state)
    question_text = None
    if follow_up is not None:
        coldstart.record_asked(state, follow_up)
        state.pending_question_key = follow_up.key
        state.pending_question_text = follow_up.ask
        question_text = follow_up.ask
    response = render_suggestions(
        suggestions,
        category_name=registry_category.sheet_name,
        next_question=question_text,
        also_consider=also_consider,
        need=need,
        purpose_example=coldstart.purpose_example(category),
    )
    validation = validate_response(
        response.text, allowed_products=response.allowed_products
    )
    validation_input = response.text
    text = response.text if validation.ok else degrade_to_facts(response.allowed_products)

    # Optional LLM polish: rephrase, then re-validate against the same
    # records; any violation keeps the deterministic text.
    polish_accepted: bool | None = None
    response_source = "deterministic"
    if validation.ok and deps.polisher is not None:
        polish_accepted = False
        polished = await deps.polisher.polish(text)
        if polished and polished != text:
            recheck = validate_response(
                polished, allowed_products=response.allowed_products
            )
            if recheck.ok:
                text = polished
                validation = recheck
                validation_input = polished
                polish_accepted = True
                response_source = "polished"
            else:
                flags = flags + ["polish_rejected"]
                validation = recheck
                validation_input = polished

    presented = [p.productidweb for p in response.allowed_products]
    state.last_presented_ids = presented
    for pid in presented:
        if pid not in shown:
            shown.append(pid)
    reply = _observed_response(
        observer,
        AgentReply(text=text, intent=intent, flags=flags, presented_ids=presented),
        outcome={
            "more_recommendations": "more_products",
            "product_detail": "product_detail",
        }.get(intent, "recommendation"),
        response_source=response_source,
        polish_accepted=polish_accepted,
    )
    _observe_output_validation(
        observer,
        text=validation_input,
        allowed_product_ids=[p.productidweb for p in response.allowed_products],
        ok=validation.ok,
        violations=list(validation.violations),
    )
    return reply


def _pick_comparison_pair(
    state: AgentState, deps: AgentDependencies, low: str
) -> tuple[str, ...]:
    """No products presented yet: the compare tools ARE available — fetch two
    candidates matching the ask ("2 mẫu rẻ nhất", "nổi bật") instead of
    bouncing the question back (live-test 4 finding)."""
    category = state.need.category_code
    if category is None:
        return ()
    result = search_products(
        deps.products,
        category_code=category,
        budget_min=state.need.budget_min,
        budget_max=state.need.budget_max,
        limit=20,
        budget_slack=0.08,
    )
    priced = [p for p in result.items if p.effective_price is not None]
    if len(priced) < 2:
        return ()
    if any(k in low for k in ("rẻ nhất", "giá thấp", "rẻ")):
        pair = priced[:2]  # search sorts price-ascending
    elif any(k in low for k in ("đắt nhất", "cao cấp", "xịn")):
        pair = sorted(
            priced, key=lambda p: (-p.effective_price, p.productidweb)
        )[:2]
    else:  # "nổi bật"/default: deepest promotions, cheapest as fallback
        discounted = sorted(
            (p for p in priced if p.promotion.discount_percent),
            key=lambda p: (-p.promotion.discount_percent, p.productidweb),
        )
        pair = discounted[:2] if len(discounted) >= 2 else priced[:2]
    return tuple(p.productidweb for p in pair)


def _compare_flow(
    state: AgentState,
    deps: AgentDependencies,
    flags: list[str],
    observer: AgentObserver,
    low: str = "",
) -> AgentReply:
    ids = tuple(state.last_presented_ids[:2])
    if len(ids) < 2:
        ids = _pick_comparison_pair(state, deps, low)
    if len(ids) < 2:
        return _observed_response(
            observer,
            AgentReply(
                text=(
                    "Dạ anh/chị muốn so sánh sản phẩm thuộc ngành hàng nào ạ "
                    "(máy lạnh, tủ lạnh, màn hình...)? Em chọn các mẫu đáng "
                    "chú ý nhất rồi so sánh chi tiết ngay ạ."
                ),
                intent="compare_products",
                flags=flags,
            ),
            outcome="comparison_clarification",
        )
    state.last_presented_ids = list(ids)
    comparison = compare_products(deps.products, ids)
    lines = ["Dạ em so sánh hai mẫu anh/chị đang xem ạ:", ""]
    for item in comparison.items:
        price = format_vnd(item.effective_price) if item.effective_price else "giá đang cập nhật"
        line = f"• {item.name}: {price}"
        if item.discount_percent:
            line += f" (đang giảm {item.discount_percent:.0f}%)"
        if item.gift:
            line += " — có quà tặng kèm"
        lines.append(line)

    # Dimension table: the category's registered dimensions with real data on
    # both sides, each with a verdict where rankable — the comparison explains
    # itself on the axes that matter for this product type (live-test 3).
    selected = [p for pid in ids for p in deps.products if p.productidweb == pid]
    dim_lines: list[str] = []
    if len(selected) == 2:
        first, second = selected
        for dim in dimensions_for(state.need.category_code):
            shown_a = dimension_display(first, dim)
            shown_b = dimension_display(second, dim)
            if shown_a is None or shown_b is None or shown_a == shown_b:
                continue
            line = f"• {dim.label}: {shown_a} vs {shown_b}"
            if rankable(dim):
                verdict = better_of(
                    dimension_value(first, dim), dimension_value(second, dim), dim
                )
                if verdict == -1:
                    line += f" → {first.name} nhỉnh hơn"
                elif verdict == 1:
                    line += f" → {second.name} nhỉnh hơn"
            dim_lines.append(line)
    if dim_lines:
        lines.append("")
        lines.append("Về thông số:")
        lines.extend(dim_lines[:5])
    else:
        shared_preview = list(comparison.shared_attributes.items())[:3]
        for key, values in shared_preview:
            rendered = " / ".join(values[pid] for pid in ids if pid in values)
            lines.append(f"• {key}: {rendered}")
    lines.append("")

    # Reasoning: benefit/drawback per model plus a context-based lean
    # (Cường: comparison must explain WHY, not just list).
    first, second = comparison.items[0], comparison.items[1]
    if (
        first.effective_price is not None
        and second.effective_price is not None
        and comparison.price_delta
    ):
        cheaper, pricier = (
            (first, second)
            if first.effective_price <= second.effective_price
            else (second, first)
        )
        lines.append(
            f"{cheaper.name} lợi hơn về giá — tiết kiệm được "
            f"{format_vnd(comparison.price_delta)} so với {pricier.name}."
        )
        pricier_perks = []
        if pricier.discount_percent and (
            not cheaper.discount_percent
            or pricier.discount_percent > cheaper.discount_percent
        ):
            pricier_perks.append(
                f"đang giảm {pricier.discount_percent:.0f}% sâu hơn"
            )
        if pricier.gift and not cheaper.gift:
            pricier_perks.append("có quà tặng kèm mà mẫu kia không có")
        if pricier_perks:
            lines.append(
                f"Đổi lại, {pricier.name} {' và '.join(pricier_perks)}."
            )
        need = state.need
        anchor = need.usage_purpose or (
            need.priorities[0] if need.priorities else None
        )
        if need.budget_max and pricier.effective_price > need.budget_max:
            lines.append(
                f"Dựa trên ngân sách khoảng {format_trieu(need.budget_max)} của "
                f"anh/chị, em nghiêng về {cheaper.name} vì vừa túi tiền hơn ạ."
            )
        elif anchor:
            lines.append(
                f"Dựa trên yêu cầu về {anchor} của anh/chị, em nghĩ mình nên "
                "cân giữa mức chênh giá và ưu đãi kèm theo ở trên ạ."
            )
    lines.append("")
    lines.append("Anh/chị nghiêng về mẫu nào hơn để em tư vấn sâu thêm ạ?")
    text = "\n".join(lines)
    allowed = [p for p in deps.products if p.productidweb in ids]
    validation_input = text
    validation = validate_response(text, allowed_products=allowed)
    if not validation.ok:
        text = degrade_to_facts(allowed)
    reply = _observed_response(
        observer,
        AgentReply(
            text=text,
            intent="compare_products",
            flags=flags,
            presented_ids=list(ids),
        ),
        outcome="comparison",
    )
    _observe_output_validation(
        observer,
        text=validation_input,
        allowed_product_ids=[p.productidweb for p in allowed],
        ok=validation.ok,
        violations=list(validation.violations),
    )
    return reply
