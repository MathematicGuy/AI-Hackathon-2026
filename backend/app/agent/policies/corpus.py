"""Policy corpus: loads the retailer's markdown policies lazily and splits them
into sections whose text is always a verbatim substring of the source file, so
quotes can be validated mechanically (ADR-0016). Keyword-scored retrieval; no
vector store (ADR-014)."""

import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

DEFAULT_POLICY_DIR = Path("data") / "dataset"

_HEADING = re.compile(
    r"^\s*(\d+(\.\d+)*[\)\.]\s+\S|#{1,6}\s+\S|\d+[A-ZĐÀ-Ỵ])"
)
MAX_SECTION_CHARS = 1800
_WORD = re.compile(r"[\wÀ-ỹ]+", re.UNICODE)

# Folded synonym hints: query word -> extra folded words searched on its behalf.
_SYNONYMS = {
    "ship": ("giao",),
    "iphone": ("apple",),
    "tra": ("doi",),
}

# Folded Vietnamese function words that carry no policy signal.
_STOPWORDS = {
    "chinh", "sach", "cua", "cho", "tai", "the", "nao", "bao", "nhieu", "khi",
    "va", "la", "den", "tu", "ve", "khong", "nhu", "nay", "gi", "o", "co",
    "cac", "mot", "nhung", "duoc", "bang", "toi", "em", "anh", "chi", "xin",
    "vui", "long", "muon", "can", "hoi", "biet", "them", "giup", "minh",
    # Retail-generic words that appear in every document and carry no signal.
    "hang", "nhom", "san", "pham", "khach",
    # Conversation-generic words: "mục đích sử dụng tủ lạnh á?" must not match
    # the data-privacy heading "Chúng tôi sử dụng ... vì mục đích gì?" on these
    # alone (Cường's live-test 2 misroute).
    "muc", "dich", "su", "dung",
}

# A line that is only an enumeration marker ("b.", "a)", "2.1") — quoting a
# section that ends on one of these reads as a broken chunk.
_ORPHAN_ENUM = re.compile(r"^\s*(?:[a-zđ]|[0-9]+(?:\.[0-9]+)*)[\.\)]\s*$")

# Topic bigrams (folded): when the query names a policy TOPIC, sections from
# the document carrying that topic in its NAME get a decisive bonus — an
# incidental "Bảo hành Thợ" mention in the delivery doc must not outrank the
# warranty policy (live-test 6). Single-word scoring cannot express this
# because topic words like "bảo" fold into stopwords.
_TOPIC_BIGRAMS = (
    "bao hanh", "doi tra", "hoan tien", "giao hang", "lap dat",
    "khui hop", "du lieu ca nhan", "tra gop", "dieu khoan",
)
_TOPIC_BONUS = 6.0


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if _HEADING.match(stripped):
        return True
    letters = [ch for ch in stripped if ch.isalpha()]
    if len(letters) >= 8:
        upper_ratio = sum(1 for ch in letters if ch.isupper()) / len(letters)
        return upper_ratio > 0.7
    return False


def _tokens(text: str) -> list[str]:
    return [match.group(0).lower() for match in _WORD.finditer(text)]


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


@dataclass(frozen=True, slots=True)
class PolicyDocument:
    name: str
    path: Path
    raw_text: str


@dataclass(frozen=True, slots=True)
class PolicySection:
    doc_name: str
    heading: str
    text: str


class PolicyCorpus:
    def __init__(self, directory: Path | str | None = None) -> None:
        configured = (
            directory or os.environ.get("AGENT_POLICY_DIR") or DEFAULT_POLICY_DIR
        )
        self.directory = Path(configured)
        self._documents: list[PolicyDocument] | None = None
        self._sections: list[PolicySection] | None = None
        self._index: list[tuple[dict[str, int], set[str]]] | None = None

    @property
    def loaded(self) -> bool:
        return self._documents is not None

    @property
    def documents(self) -> list[PolicyDocument]:
        if self._documents is None:
            self._documents = [
                PolicyDocument(
                    name=path.name,
                    path=path,
                    raw_text=path.read_text(encoding="utf-8"),
                )
                for path in sorted(self.directory.glob("*.md"))
            ]
        return self._documents

    @property
    def sections(self) -> list[PolicySection]:
        if self._sections is None:
            self._sections = [
                section
                for document in self.documents
                for section in _split_sections(document)
            ]
        return self._sections

    def search(
        self, query: str, *, top: int = 3, min_score: float = 0.0
    ) -> list[PolicySection]:
        query_words = {
            word
            for word in _tokens(_fold(query))
            if len(word) >= 2 and word not in _STOPWORDS
        }
        for word in list(query_words):
            query_words.update(_SYNONYMS.get(word, ()))
        if not query_words:
            return []

        folded_query = _fold(query)
        query_topics = tuple(
            bigram for bigram in _TOPIC_BIGRAMS if bigram in folded_query
        )

        scored: list[tuple[float, int, PolicySection]] = []
        for index, section in enumerate(self.sections):
            # Heading-only stubs carry nothing quotable.
            if len(section.text.strip()) < 80:
                continue
            body_counts, heading_words = self._section_index()[index]
            matched = {word for word in query_words if body_counts.get(word)}
            if not matched:
                continue
            # Cap per-word frequency so long sections cannot win on repetition,
            # then normalize by section length.
            score = float(sum(min(body_counts[word], 3) for word in matched))
            score += 3.0 * len(matched & heading_words)
            score /= 1.0 + len(section.text) / 1500.0
            # The document NAME is the strongest topical signal: "bảo hành"
            # must prefer chinh_sach_bao_hanh_doi_tra over an incidental
            # "Bảo hành Thợ" mention in the delivery doc (live-test 6).
            doc_words = set(_tokens(_fold(section.doc_name)))
            score += 2.0 * len(query_words & doc_words)
            folded_doc_name = _fold(section.doc_name).replace("_", " ").replace("-", " ")
            score += _TOPIC_BONUS * sum(
                1 for topic in query_topics if topic in folded_doc_name
            )
            if (len(matched) >= 2 or score >= 2.0) and score >= min_score:
                scored.append((score, index, section))
        scored.sort(key=lambda entry: (-entry[0], entry[1]))
        return [section for _, _, section in scored[:top]]

    def _section_index(self) -> list[tuple[dict[str, int], set[str]]]:
        if self._index is None:
            from collections import Counter

            self._index = [
                (
                    dict(Counter(_tokens(_fold(section.text)))),
                    set(_tokens(_fold(section.heading))),
                )
                for section in self.sections
            ]
        return self._index


def _split_sections(document: PolicyDocument) -> list[PolicySection]:
    lines = document.raw_text.splitlines(keepends=True)
    sections: list[PolicySection] = []
    current_heading = document.name
    buffer: list[str] = []

    def flush() -> None:
        text = "".join(buffer).strip("\n")
        if not text.strip():
            return
        for chunk in _window(text):
            chunk = _trim_orphan_tail(chunk)
            if not chunk:
                continue
            sections.append(
                PolicySection(
                    doc_name=document.name,
                    heading=current_heading.strip(),
                    text=chunk,
                )
            )

    for line in lines:
        if _is_heading(line):
            flush()
            buffer = [line]
            current_heading = line.strip()
        else:
            buffer.append(line)
    flush()
    return sections


def _trim_orphan_tail(chunk: str) -> str:
    """Drop trailing lines that are bare enumeration markers so a windowed
    chunk never ends on 'b.' with no content. Trimming whole trailing lines
    keeps the chunk a verbatim substring of the source."""
    lines = chunk.split("\n")
    while lines and (
        not lines[-1].strip() or _ORPHAN_ENUM.match(lines[-1])
    ):
        lines.pop()
    return "\n".join(lines).strip("\n")


def _window(text: str) -> list[str]:
    """Split an oversized section on paragraph boundaries. Each chunk stays a
    verbatim substring of the source document."""
    if len(text) <= MAX_SECTION_CHARS:
        return [text]
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for paragraph in text.split("\n\n"):
        length = len(paragraph) + 2
        if current and current_length + length > MAX_SECTION_CHARS:
            chunks.append("\n\n".join(current).strip("\n"))
            current, current_length = [], 0
        current.append(paragraph)
        current_length += length
    if current:
        chunks.append("\n\n".join(current).strip("\n"))
    return [chunk for chunk in chunks if chunk.strip()]
