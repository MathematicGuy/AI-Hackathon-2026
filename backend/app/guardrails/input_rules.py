"""Layered deterministic input guardrail for the M1 advisor.

Stages run in the frozen ``INPUT_GUARD_ORDER`` and short-circuit at the first
block. Precision is a first-class goal: the rules must never overfire on a
legitimate máy lạnh shopping request, while still keeping unrelated categories
and unsafe actions out of the recommendation flow.
"""

import re
from dataclasses import dataclass

from backend.app.graph.node_names import INPUT_GUARD_ORDER
from backend.app.guardrails.nemo.input import NemoInputRail, default_input_rail

STAGE_WORD_COUNT, STAGE_REGEX, STAGE_NEMO, STAGE_SCOPE, _STAGE_INTENT = INPUT_GUARD_ORDER

WORD_LIMIT = 150
MAX_URL_LENGTH = 2000
REPEATED_CHAR_RUN = 20

BLOCK_MESSAGE_OVERSIZED = (
    "Yêu cầu đang dài hơn giới hạn 150 từ. Hãy gửi ngắn gọn bốn thông tin: "
    "diện tích phòng, ngân sách, ưu tiên chính và khu vực sử dụng."
)

# Tight markers — chosen so a normal Vietnamese máy lạnh shopper never trips them.
_INJECTION_MARKERS = (
    "ignore previous",
    "ignore all previous",
    "previous instructions",
    "disregard previous",
    "bỏ qua hướng dẫn",
    "bỏ qua chỉ dẫn",
)
_ENCODED_MARKERS = ("data:text", ";base64", "base64,", "\\x00", "\x00")
_UNSAFE_EXEC_MARKERS = (
    "os.system",
    "import os",
    "rm -rf",
    "subprocess",
    "exec(",
    "eval(",
    "system(",
    "chạy lệnh",
)
_CREDENTIAL_MARKERS = (
    "api key",
    "api-key",
    "apikey",
    "system prompt",
    "hidden prompt",
    "internal prompt",
    "prompt hệ thống",
    "mật khẩu",
    "credential",
)

# Other DMX categories. Only block on these when there is no máy lạnh signal.
_OTHER_CATEGORY_MARKERS = (
    "tủ lạnh",
    "tu lanh",
    "điện thoại",
    "dien thoai",
    "laptop",
    "máy tính",
    "tivi",
    "tai nghe",
    "robot hút",
    "máy giặt",
    "máy lọc",
    "nồi chiên",
)
# Actions that are always out of scope regardless of category signal.
_DISALLOWED_ACTION_MARKERS = (
    "tự động đặt",
    "tự động mua",
    "tự đặt mua",
    "đặt mua giúp",
    "auto mua",
    "sửa catalog",
    "thay đổi giá",
    "chỉnh giá",
    "cập nhật kho",
)
_IN_SCOPE_MARKERS = ("máy lạnh", "may lanh", "điều hòa", "điều hoà", "dieu hoa")


@dataclass(frozen=True, slots=True)
class InputGuardResult:
    blocked: bool
    stage: str | None = None
    reason: str | None = None
    message: str | None = None
    flags: tuple[str, ...] = ()


def _regex_payload_reason(message: str) -> str | None:
    if not message.strip():
        return "empty"
    # Non-whitespace run only: never overfire on pasted spacing or separators.
    if re.search(r"(\S)\1{%d,}" % (REPEATED_CHAR_RUN - 1), message):
        return "repeated_char"
    low = message.lower()
    if any(marker in low for marker in _INJECTION_MARKERS):
        return "injection"
    if any(marker in low for marker in _ENCODED_MARKERS):
        return "encoded_payload"
    if _has_over_long_url(message):
        return "long_url"
    if any(marker in low for marker in _UNSAFE_EXEC_MARKERS):
        return "unsafe_exec"
    if any(marker in low for marker in _CREDENTIAL_MARKERS):
        return "credential"
    return None


def _has_over_long_url(message: str) -> bool:
    return any(
        token.startswith(("http://", "https://")) and len(token) > MAX_URL_LENGTH
        for token in message.split()
    )


def _is_disallowed_action(low: str) -> bool:
    return any(marker in low for marker in _DISALLOWED_ACTION_MARKERS)


def evaluate_input(
    message: str,
    *,
    nemo: NemoInputRail | None = None,
    in_scope_markers: tuple[str, ...] | None = None,
    other_category_markers: tuple[str, ...] | None = None,
) -> InputGuardResult:
    nemo = nemo or default_input_rail()
    scope_markers = (
        in_scope_markers if in_scope_markers is not None else _IN_SCOPE_MARKERS
    )
    category_markers = (
        other_category_markers
        if other_category_markers is not None
        else _OTHER_CATEGORY_MARKERS
    )
    flags: list[str] = []

    # 1. Word count.
    if len(message.split()) >= WORD_LIMIT:
        return InputGuardResult(
            blocked=True,
            stage=STAGE_WORD_COUNT,
            reason="word_limit",
            message=BLOCK_MESSAGE_OVERSIZED,
        )

    # 2. Deterministic regex / payload rules.
    reason = _regex_payload_reason(message)
    if reason is not None:
        return InputGuardResult(blocked=True, stage=STAGE_REGEX, reason=reason)

    # 3. NeMo input rail (injected).
    verdict = nemo.check(message)
    degraded = not verdict.available
    if degraded:
        flags.append("guardrail_degraded")
    elif not verdict.allowed:
        return InputGuardResult(
            blocked=True,
            stage=STAGE_NEMO,
            reason="nemo_block",
            flags=tuple(flags),
        )

    # 4. Scope. Precision-first: unsafe/auto actions always block; another
    #    category blocks only when there is no máy lạnh signal, so a legitimate
    #    request that merely references another appliance is not overfired.
    low = message.lower()
    in_scope = any(marker in low for marker in scope_markers)
    if _is_disallowed_action(low):
        return InputGuardResult(
            blocked=True, stage=STAGE_SCOPE, reason="out_of_scope", flags=tuple(flags)
        )
    if any(marker in low for marker in category_markers) and not in_scope:
        return InputGuardResult(
            blocked=True, stage=STAGE_SCOPE, reason="out_of_scope", flags=tuple(flags)
        )
    if degraded and not in_scope:
        return InputGuardResult(
            blocked=True,
            stage=STAGE_SCOPE,
            reason="degraded_fail_closed",
            flags=tuple(flags),
        )

    return InputGuardResult(blocked=False, flags=tuple(flags))
