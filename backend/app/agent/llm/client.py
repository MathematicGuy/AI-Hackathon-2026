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
from dataclasses import dataclass, field
from pathlib import Path

from backend.app.agent.catalog.registry import CategoryRegistry
from backend.app.agent.contracts import AgentUnderstanding
from backend.app.agent.conversation.understand import ExtractorError

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


class LLMUnderstandingExtractor:
    def __init__(
        self,
        candidates: list[LLMCandidate],
        *,
        registry: CategoryRegistry | None = None,
        transport=None,
        timeout: float = 25.0,
    ) -> None:
        if not candidates:
            raise ValueError("no LLM candidates configured")
        self.candidates = candidates
        self.registry = registry or CategoryRegistry()
        self.timeout = timeout
        self._transport = transport

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
        for candidate in self.candidates:
            try:
                raw = await self._call(candidate, system, message)
                return AgentUnderstanding.model_validate(_extract_json(raw))
            except Exception as exc:  # provider, parse, or validation failure
                last_error = exc
        raise ExtractorError(str(last_error))


def default_extractor() -> LLMUnderstandingExtractor | None:
    candidates = resolve_llm_candidates()
    if not candidates:
        return None
    return LLMUnderstandingExtractor(candidates)
