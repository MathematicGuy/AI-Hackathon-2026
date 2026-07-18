from backend.app.ingestion.hashing import content_hash


def test_content_hash_is_order_independent():
    assert content_hash({"a": 1, "b": 2}) == content_hash({"b": 2, "a": 1})


def test_content_hash_changes_with_value():
    assert content_hash({"a": 1}) != content_hash({"a": 2})


def test_content_hash_handles_none_and_unicode():
    digest = content_hash({"Phạm vi sử dụng": "Từ 30 - 40m²", "x": None})
    assert isinstance(digest, str)
    assert len(digest) == 64
