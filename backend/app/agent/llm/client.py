"""Tolerant LLM route resolution + structured understanding extractor.

Prefers the strict environment-owned model settings (Thành's contract); when
that contract is incomplete, falls back to whatever provider keys exist in the
local `.env` (OpenRouter primary, Mistral fallback) so the real agent can run
today. API keys are never logged. Tests inject a fake transport; no network in
the test suite.
"""

import json
import os
import re
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from backend.app.agent.catalog.registry import CategoryRegistry
from backend.app.agent.contracts import AgentUnderstanding
from backend.app.agent.conversation.understand import ExtractorError
from backend.app.observability import AgentObserver, noop_agent_observer

DEFAULT_OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MISTRAL_BASE = "https://api.mistral.ai/v1"
DEFAULT_MAIN_MODEL = "deepseek/deepseek-v4-flash"
DEFAULT_FALLBACK_MODEL = "mistral-medium-latest"


@dataclass(frozen=True, slots=True)
class LLMCandidate:
    base_url: str
    api_key: str = field(repr=False)
    model: str


def load_env_file(path: str | Path = ".env") -> dict[str, str]:
    values: dict[str, str] = {}
    env_path = Path(path)
    if not env_path.exists():
        return values
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def resolve_llm_candidates(env: dict[str, str] | None = None) -> list[LLMCandidate]:
    values = dict(load_env_file())
    values.update(os.environ)
    if env is not None:
        values.update(env)

    candidates: list[LLMCandidate] = []
    openrouter_key = values.get("OPENROUTER_API_KEY", "")
    if openrouter_key:
        candidates.append(
            LLMCandidate(
                base_url=values.get("OPENROUTER_BASE_URL") or DEFAULT_OPENROUTER_BASE,
                api_key=openrouter_key,
                model=values.get("MAIN_LLM_MODEL")
                or values.get("DEFAULT_MODEL")
                or DEFAULT_MAIN_MODEL,
            )
        )
    mistral_key = values.get("MISTRAL_API_KEY", "")
    if mistral_key:
        candidates.append(
            LLMCandidate(
                base_url=values.get("MISTRAL_BASE_URL") or DEFAULT_MISTRAL_BASE,
                api_key=mistral_key,
                model=values.get("FALLBACK_LLM_MODEL") or DEFAULT_FALLBACK_MODEL,
            )
        )
    return candidates


_SYSTEM_TEMPLATE = """Bạn là bộ phân tích hội thoại cho trợ lý bán hàng Điện Máy XANH.
Nhiệm vụ: đọc tin nhắn khách và trả về DUY NHẤT một JSON object đúng schema, không giải thích thêm.

Schema:
{{
  "intent": một trong ["new_search","change_constraints","more_recommendations","compare_products","product_detail","check_availability","policy_question","stop","unsupported"],
  "confidence": số 0..1,
  "need_patch": {{
    "category_code": mã ngành trong bảng dưới hoặc null,
    "usage_purpose": mục đích sử dụng khách nêu hoặc null,
    "budget_min": số VND hoặc null,
    "budget_max": số VND hoặc null,
    "brand_prefs": [thương hiệu khách nêu],
    "priorities": [ưu tiên khách nêu, vd "tiết kiệm điện"],
    "attribute_constraints": {{"tên tiêu chí": "giá trị khách nêu"}},
    "location": khu vực hoặc null,
    "requested_roles": [] hoặc ["best_price"] nếu khách chỉ muốn rẻ nhất
  }},
  "product_refs": []
}}

Bảng mã ngành: {categories}

QUY TẮC:
- KHÔNG bịa số: chỉ điền budget khi khách nêu con số (quy đổi "triệu" -> VND).
- Trường không có thông tin để null/rỗng.
- Câu hỏi về chính sách/bảo hành/đổi trả/giao hàng/trả góp/khui hộp -> intent "policy_question".
- Khách chào tạm biệt/dừng -> "stop". Ngoài phạm vi mua sắm điện máy -> "unsupported".
{state_summary}"""


def _category_table(registry: CategoryRegistry) -> str:
    return "; ".join(
        f"{category.code}={category.sheet_name}" for category in registry.all()
    )


def _extract_json(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object in model output")
    return json.loads(cleaned[start : end + 1])


def _provider_name(base_url: str) -> str:
    host = urlparse(base_url).netloc.lower() or base_url.lower()
    if "openrouter" in host:
        return "openrouter"
    if "mistral" in host:
        return "mistral"
    return host


class _SilentObservation:
    def update(self, **kwargs: object) -> None:
        return None


def _safe_update(handle: object, **kwargs: object) -> None:
    try:
        handle.update(**kwargs)  # type: ignore[attr-defined]
    except Exception:
        return None


@contextmanager
def _generation_span(observer: AgentObserver, name: str, **kwargs: object):
    """Open an observation without allowing tracing failures to affect calls."""
    try:
        context = observer.span(name, **kwargs)
        handle = context.__enter__()
    except Exception:
        yield _SilentObservation()
        return

    error_info: tuple[object, object, object] = (None, None, None)
    try:
        yield handle
    except BaseException as exc:
        error_info = (type(exc), exc, exc.__traceback__)
        raise
    finally:
        try:
            context.__exit__(*error_info)
        except Exception:
            pass


class LLMUnderstandingExtractor:
    def __init__(
        self,
        candidates: list[LLMCandidate],
        *,
        registry: CategoryRegistry | None = None,
        transport=None,
        timeout: float = 25.0,
        observer: AgentObserver | None = None,
    ) -> None:
        if not candidates:
            raise ValueError("no LLM candidates configured")
        self.candidates = candidates
        self.registry = registry or CategoryRegistry()
        self.timeout = timeout
        self._transport = transport
        self.observer = observer or noop_agent_observer()

    async def _call(self, candidate: LLMCandidate, system: str, user: str) -> str:
        if self._transport is not None:
            return await self._transport(candidate, system, user)
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            base_url=candidate.base_url,
            api_key=candidate.api_key,
            timeout=self.timeout,
        )
        response = await client.chat.completions.create(
            model=candidate.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
        )
        return response.choices[0].message.content or ""

    async def extract(self, message: str, *, state_summary: str = "") -> AgentUnderstanding:
        summary_note = (
            f"\nBối cảnh phiên hiện tại: {state_summary}" if state_summary else ""
        )
        system = _SYSTEM_TEMPLATE.format(
            categories=_category_table(self.registry), state_summary=summary_note
        )
        last_error: Exception | None = None
        for index, candidate in enumerate(self.candidates):
            generation = _SilentObservation()
            try:
                with _generation_span(
                    self.observer,
                    "understanding_model_call",
                    kind="generation",
                    model=candidate.model,
                    model_parameters={"temperature": 0},
                    input={"system": system, "user": message},
                    metadata={
                        "candidate_index": index,
                        "provider": _provider_name(candidate.base_url),
                        "role": "understanding",
                    },
                ) as generation:
                    raw = await self._call(candidate, system, message)
                    _safe_update(generation, output=raw)
                return AgentUnderstanding.model_validate(_extract_json(raw))
            except Exception as exc:  # provider, parse, or validation failure
                last_error = exc
                _safe_update(
                    generation,
                    error={"type": type(exc).__name__},
                    output={"fallback": True},
                )
        raise ExtractorError(str(last_error))


def default_extractor(*, observer: AgentObserver | None = None) -> LLMUnderstandingExtractor | None:
    candidates = resolve_llm_candidates()
    if not candidates:
        return None
    return LLMUnderstandingExtractor(candidates, observer=observer)


_POLISH_SYSTEM = """Bạn là nhân viên tư vấn bán hàng Điện Máy XANH (xưng em, gọi khách anh/chị, mở đầu Dạ, giọng gần gũi).
Viết lại đoạn tư vấn dưới đây cho tự nhiên, ấm áp và chủ động bán hàng hơn.

QUY TẮC BẮT BUỘC:
- GIỮ NGUYÊN 100% mọi con số (giá, %, dung tích...), tên sản phẩm, quà tặng — không thêm, không bớt, không làm tròn.
- Không thêm bất kỳ khuyến mãi/cam kết/thông tin nào không có trong bản gốc.
- Giữ đúng MỘT câu hỏi ở cuối.
- Trả về DUY NHẤT phần văn bản đã viết lại."""


class LLMPolisher:
    """Optional rephrasing pass. The grounding validator re-checks the
    polished text against the same records; any violation falls back to the
    deterministic version."""

    def __init__(
        self,
        candidates: list[LLMCandidate],
        *,
        transport=None,
        timeout: float = 25.0,
        observer: AgentObserver | None = None,
    ) -> None:
        if not candidates:
            raise ValueError("no LLM candidates configured")
        self.candidates = candidates
        self.timeout = timeout
        self._transport = transport
        self.observer = observer or noop_agent_observer()

    async def _call(self, candidate: LLMCandidate, system: str, user: str) -> str:
        if self._transport is not None:
            return await self._transport(candidate, system, user)
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            base_url=candidate.base_url,
            api_key=candidate.api_key,
            timeout=self.timeout,
        )
        response = await client.chat.completions.create(
            model=candidate.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content or ""

    async def polish(self, text: str) -> str:
        for index, candidate in enumerate(self.candidates):
            generation = _SilentObservation()
            try:
                with _generation_span(
                    self.observer,
                    "response_polish_model_call",
                    kind="generation",
                    model=candidate.model,
                    model_parameters={"temperature": 0.4},
                    input={"system": _POLISH_SYSTEM, "user": text},
                    metadata={
                        "candidate_index": index,
                        "provider": _provider_name(candidate.base_url),
                        "role": "response_polish",
                    },
                ) as generation:
                    raw = await self._call(candidate, _POLISH_SYSTEM, text)
                    _safe_update(generation, output=raw)
                polished = raw.strip()
                if polished:
                    return polished
                _safe_update(generation, output={"fallback": True, "reason": "empty"})
            except Exception as exc:
                _safe_update(
                    generation,
                    error={"type": type(exc).__name__},
                    output={"fallback": True},
                )
                continue
        return text


def default_polisher(*, observer: AgentObserver | None = None) -> LLMPolisher | None:
    if os.environ.get("AGENT_LLM_POLISH", "").lower() not in ("1", "true", "yes"):
        return None
    candidates = resolve_llm_candidates()
    if not candidates:
        return None
    return LLMPolisher(candidates, observer=observer)
