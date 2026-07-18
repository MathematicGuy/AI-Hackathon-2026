"""Policy answers with mandatory verbatim quotes and graceful degradation.

Every answer carries quotes that are exact substrings of the source markdown
(mechanically validated) plus the source document names. Requests that
conflict with policy get a sincere, employee-style apology that quotes the
governing clause and never promises an exception (ADR-0016)."""

from dataclasses import dataclass, field

from backend.app.agent.policies.corpus import PolicyCorpus, PolicySection

MAX_QUOTE_CHARS = 600

# Customer-facing policy names. Filenames must never reach the end user.
DISPLAY_NAMES = {
    "chinh_sach_bao_hanh_doi_tra.md": "Chính sách bảo hành & đổi trả",
    "chinh_sach_giao_hang_lap_dat.md": "Chính sách giao hàng & lắp đặt",
    "chinh_sach_khui_hop_apple.md": "Chính sách khui hộp sản phẩm Apple",
    "chinh_sach_xu_ly_du_lieu_ca_nhan.md": "Chính sách xử lý dữ liệu cá nhân",
    "dieu-khoang-su-dung (1).md": "Điều khoản sử dụng",
    "chat_luong_phuc_vu.md": "Chính sách chất lượng phục vụ",
}


def display_source(doc_name: str) -> str:
    if doc_name in DISPLAY_NAMES:
        return DISPLAY_NAMES[doc_name]
    cleaned = doc_name.removesuffix(".md").replace("_", " ").replace("-", " ")
    return cleaned.capitalize()


@dataclass(frozen=True, slots=True)
class PolicyAnswer:
    question: str
    sections: list[PolicySection] = field(default_factory=list)
    quotes: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


def _quote_from(section: PolicySection) -> str:
    text = section.text.strip()
    if len(text) <= MAX_QUOTE_CHARS:
        return text
    # Cut on a paragraph boundary so the quote stays a verbatim substring.
    head = text[:MAX_QUOTE_CHARS]
    boundary = max(head.rfind("\n\n"), head.rfind("\n"), head.rfind(". "))
    return head[: boundary + 1].strip() if boundary > 100 else head.strip()


def build_policy_answer(
    corpus: PolicyCorpus, question: str, *, top: int = 2, min_score: float = 1.0
) -> PolicyAnswer:
    # Below the relevance floor a graceful no-info answer beats an off-topic
    # quote (Cường's live-test finding).
    sections = corpus.search(question, top=top, min_score=min_score)
    quotes = [_quote_from(section) for section in sections]
    sources = [section.doc_name for section in sections]
    return PolicyAnswer(
        question=question, sections=sections, quotes=quotes, sources=sources
    )


def is_verbatim(corpus: PolicyCorpus, quote: str) -> bool:
    cleaned = quote.strip()
    if not cleaned:
        return False
    return any(cleaned in document.raw_text for document in corpus.documents)


def degradation_response(*, user_request: str, answer: PolicyAnswer) -> str:
    """Polite, sincere refusal for a request that conflicts with policy."""
    lines = [
        "Dạ em thành thật xin lỗi anh/chị, em rất tiếc là em không thể hỗ trợ "
        "yêu cầu này vì chính sách hiện hành của cửa hàng ạ.",
    ]
    if answer.quotes:
        lines.append("")
        lines.append(f"Theo {display_source(answer.sources[0])} của bên em:")
        lines.append(answer.quotes[0])
        lines.append("")
        lines.append(
            "Trong phạm vi chính sách trên, em rất sẵn lòng hỗ trợ anh/chị "
            "phương án phù hợp nhất — anh/chị cho em biết thêm tình trạng sản "
            "phẩm và thời điểm mua để em tư vấn hướng xử lý đúng quyền lợi ạ."
        )
    else:
        lines.append(
            "Em chưa tìm thấy điều khoản phù hợp; anh/chị vui lòng liên hệ tổng "
            "đài 1900 232 461 để được hỗ trợ chính xác nhất ạ."
        )
    return "\n".join(lines)
