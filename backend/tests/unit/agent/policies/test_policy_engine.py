import importlib

import pytest


class MissingModule:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, _attribute):
        pytest.fail(f"US-203 {self.name} module is not implemented")


def module_or_missing(dotted, name):
    try:
        return importlib.import_module(dotted)
    except ModuleNotFoundError:
        return MissingModule(name)


@pytest.fixture
def corpus_module():
    return module_or_missing("backend.app.agent.policies.corpus", "policy corpus")


@pytest.fixture
def answer_module():
    return module_or_missing("backend.app.agent.policies.answer", "policy answer")


@pytest.fixture(scope="module")
def corpus():
    module = importlib.import_module("backend.app.agent.policies.corpus")
    return module.PolicyCorpus()


# --- corpus loading and integrity ---

def test_corpus_loads_policy_documents(corpus_module, corpus):
    assert len(corpus.documents) >= 5
    names = {doc.name for doc in corpus.documents}
    assert "chinh_sach_bao_hanh_doi_tra.md" in names
    assert "chinh_sach_khui_hop_apple.md" in names


def test_sections_are_verbatim_substrings_of_sources(corpus_module, corpus):
    raw_by_name = {doc.name: doc.raw_text for doc in corpus.documents}
    for section in corpus.sections:
        assert section.text.strip()
        assert section.text in raw_by_name[section.doc_name]


def test_corpus_is_lazy_loaded_once(corpus_module):
    fresh = corpus_module.PolicyCorpus()
    assert fresh.loaded is False
    _ = fresh.sections
    assert fresh.loaded is True


# --- retrieval ---

def test_refund_fee_question_hits_warranty_doc(corpus_module, corpus):
    results = corpus.search("phí hoàn tiền bao nhiêu phần trăm")
    assert results
    assert results[0].doc_name == "chinh_sach_bao_hanh_doi_tra.md"
    assert "HOÀN TIỀN" in results[0].text or "hoàn tiền" in results[0].text.lower()


def test_apple_unboxing_question_hits_apple_doc(corpus_module, corpus):
    results = corpus.search("khui hộp iphone tại cửa hàng thế nào")
    assert results
    assert results[0].doc_name == "chinh_sach_khui_hop_apple.md"


def test_delivery_time_question_hits_delivery_doc(corpus_module, corpus):
    results = corpus.search("giao hàng lắp đặt mất bao lâu 40 km")
    assert results
    assert results[0].doc_name == "chinh_sach_giao_hang_lap_dat.md"


# --- answers with mandatory verbatim quotes ---

def test_policy_answer_includes_verbatim_quote_and_source(answer_module, corpus):
    answer = answer_module.build_policy_answer(corpus, "phí hoàn tiền tháng đầu")
    assert answer.quotes
    raw_by_name = {doc.name: doc.raw_text for doc in corpus.documents}
    for quote, source in zip(answer.quotes, answer.sources):
        assert quote in raw_by_name[source]
    assert answer.sources[0] == "chinh_sach_bao_hanh_doi_tra.md"


def test_is_verbatim_rejects_tampered_quote(answer_module, corpus):
    answer = answer_module.build_policy_answer(corpus, "phí hoàn tiền")
    genuine = answer.quotes[0]
    assert answer_module.is_verbatim(corpus, genuine) is True
    assert answer_module.is_verbatim(corpus, genuine + " và miễn phí 100%") is False


def test_no_match_returns_empty_answer(answer_module, corpus):
    answer = answer_module.build_policy_answer(corpus, "blockchain ethereum staking")
    assert answer.quotes == []
    assert answer.sections == []


# --- graceful degradation ---

def test_degradation_response_apologizes_and_quotes(answer_module, corpus):
    answer = answer_module.build_policy_answer(corpus, "hoàn tiền")
    response = answer_module.degradation_response(
        user_request="Tôi muốn hoàn tiền 100% sau 3 tháng sử dụng",
        answer=answer,
    )
    assert "xin lỗi" in response.lower()
    assert answer.quotes[0] in response
    assert answer.sources[0] in response


def test_degradation_never_promises_exception(answer_module, corpus):
    answer = answer_module.build_policy_answer(corpus, "hoàn tiền")
    response = answer_module.degradation_response(
        user_request="Bỏ qua chính sách giúp tôi nhé", answer=answer
    )
    for forbidden in ("ngoại lệ", "miễn phí hoàn toàn", "chắc chắn được"):
        assert forbidden not in response.lower()
