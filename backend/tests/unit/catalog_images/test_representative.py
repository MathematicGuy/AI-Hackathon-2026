from pathlib import Path

import httpx
import pytest

from backend.app.catalog_images.representative import (
    GroupSource,
    assign_representative_image,
    collect_group,
    group_key,
    parse_representative_images,
)


LISTING_HTML = """
<img data-src="https://cdnv2.tgdd.vn/mwg-static/dmx/Common/menu.png">
<ul class="listsearch listproduct">
  <li class="item" data-id="9">
    <a data-brand="Other"><div class="item-img"><img data-src="//cdn.tgdd.vn/Products/Images/1/9/wrong.jpg"></div></a>
  </li>
  <li class="item" data-id="10">
    <a data-brand="Samsung"><div class="item-img"><img data-src="//cdn.tgdd.vn/Products/Images/1/10/a.jpg"></div></a>
  </li>
  <li class="item" data-id="11">
    <a data-brand="Samsung"><div class="item-img"><img src="https://cdnv2.tgdd.vn/Products/Images/1/11/b.jpg"></div></a>
  </li>
  <li class="item" data-id="10">
    <a data-brand="Samsung"><div class="item-img"><img data-src="https://cdn.tgdd.vn/Products/Images/1/10/a.jpg"></div></a>
  </li>
  <li class="item" data-id="12">
    <a data-brand="Samsung"><div class="item-img"><img data-lazy-src="https://cdn.tgdd.vn/2026/07/timerseo/12-600x600-1.png"></div></a>
  </li>
  <li class="item" data-id="13">
    <a data-brand="Samsung"><div class="item-img"><img src="https://cdn.tgdd.vn/Products/Images/1/13/d.jpg"></div></a>
  </li>
</ul>
"""


def test_parser_keeps_three_unique_product_card_images():
    images = parse_representative_images(
        LISTING_HTML, "https://www.dienmayxanh.com/tu-lanh-samsung", "Samsung"
    )
    assert images == [
        "https://cdn.tgdd.vn/Products/Images/1/10/a.jpg",
        "https://cdnv2.tgdd.vn/Products/Images/1/11/b.jpg",
        "https://cdn.tgdd.vn/2026/07/timerseo/12-600x600-1.png",
    ]


@pytest.mark.parametrize(
    "source_url",
    ["http://www.dienmayxanh.com/tu-lanh", "https://example.com/tu-lanh"],
)
def test_parser_rejects_non_first_party_source(source_url):
    with pytest.raises(ValueError):
        parse_representative_images(LISTING_HTML, source_url, "Samsung")


def test_group_key_uses_normalized_brand_when_brand_id_is_missing():
    assert group_key("49", None, "Ipad (Apple)") == "49:brand:ipad-apple"
    assert group_key("38", "2", "Samsung") == "38:2"


def test_assignment_is_stable_and_representative():
    group = {
        "group_key": "38:2",
        "mapping_version": 3,
        "images": [
            {"url": "https://cdn.tgdd.vn/Products/Images/1/a.jpg"},
            {"url": "https://cdn.tgdd.vn/Products/Images/1/b.jpg"},
            {"url": "https://cdn.tgdd.vn/Products/Images/1/c.jpg"},
        ],
    }
    first = assign_representative_image("1751097000147", group)
    second = assign_representative_image("1751097000147", group)
    assert first == second
    assert first["image_type"] == "representative"
    assert first["mapping_version"] == 3
    assert first["image_url"] in {image["url"] for image in group["images"]}


def test_assignment_accepts_production_url_strings():
    group = {
        "group_key": "38:2",
        "mapping_version": 1,
        "images": ["https://cdn.tgdd.vn/Products/Images/1/a.jpg"],
    }
    assert assign_representative_image("sku-1", group)["image_url"] == group["images"][0]


def test_assignment_returns_none_for_group_without_images():
    assert assign_representative_image("sku-1", {"group_key": "38:2", "images": []}) is None


def test_collect_group_isolates_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>no product list</html>", request=request)

    source = GroupSource("38", "2", "Samsung", "https://www.dienmayxanh.com/tu-lanh-samsung")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = collect_group(source, client, max_attempts=1)
    assert result["status"] == "not_found"
    assert result["failure_reason"] == "no_product_card_images"
    assert result["images"] == []


def test_collect_group_retries_transient_failure():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(200, text=LISTING_HTML, request=request)

    source = GroupSource("38", "2", "Samsung", "https://www.dienmayxanh.com/tu-lanh-samsung")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = collect_group(source, client, max_attempts=2, sleep=lambda _: None)
    assert attempts == 2
    assert result["status"] == "ready"
    assert len(result["images"]) == 3


def test_collect_group_treats_404_as_not_found_without_retry():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(404, request=request)

    source = GroupSource("38", "2", "Samsung", "https://www.dienmayxanh.com/missing")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = collect_group(source, client, max_attempts=3, sleep=lambda _: None)
    assert attempts == 1
    assert result["status"] == "not_found"
    assert result["failure_reason"] == "http_404"


def test_pilot_writer_helpers_are_importable(tmp_path: Path):
    from scripts.collect_representative_images import (
        _atomic_json,
        _write_review_csv,
    )

    group = {
        "group_key": "38:2",
        "category_code": "38",
        "brand_id": "2",
        "brand": "Samsung",
        "image_type": "representative",
        "status": "ready",
        "failure_reason": None,
        "source_url": "https://www.dienmayxanh.com/tu-lanh-samsung",
        "images": [
            {
                "position": 0,
                "url": "https://cdn.tgdd.vn/Products/Images/1/a.jpg",
                "source_url": "https://www.dienmayxanh.com/tu-lanh-samsung",
            }
        ],
    }
    mapping_path = tmp_path / "mapping.json"
    review_path = tmp_path / "review.csv"
    _atomic_json(mapping_path, {"groups": [group]})
    _write_review_csv(review_path, [group])
    assert '"group_key": "38:2"' in mapping_path.read_text(encoding="utf-8")
    assert "representative" in review_path.read_text(encoding="utf-8")
