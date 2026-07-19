from types import SimpleNamespace

import pytest

from backend.app.catalog_images.mapping import (
    PLACEHOLDER_IMAGE_URL,
    RepresentativeImageMapping,
    load_default_mapping,
)
from backend.app.catalog_images.sources import catalog_group_sources, source_for_group


def payload(images=None):
    return {
        "mapping_version": 4,
        "generated_at": "2026-07-19T00:00:00+00:00",
        "groups": {
            "38:2": {
                "category_code": "38",
                "brand_id": "2",
                "brand": "Samsung",
                "image_type": "representative",
                "images": images
                or [
                    "https://cdn.tgdd.vn/Products/Images/1/a.jpg",
                    "https://cdn.tgdd.vn/Products/Images/1/b.jpg",
                    "https://cdn.tgdd.vn/Products/Images/1/c.jpg",
                ],
                "source_url": "https://www.dienmayxanh.com/tu-lanh-samsung",
            }
        },
    }


def product(*, sku="sku-1", code="38", brand_id="2", brand="Samsung"):
    return SimpleNamespace(
        sku=sku,
        category_code=code,
        brand_id=brand_id,
        brand=brand,
    )


def test_mapping_assigns_same_url_and_version_for_same_sku():
    mapping = RepresentativeImageMapping.from_payload(payload())
    first = mapping.projection_for(product())
    second = mapping.projection_for(product())
    assert first == second
    assert first["image_type"] == "representative"
    assert first["mapping_version"] == 4
    assert first["image_url"] in payload()["groups"]["38:2"]["images"]


def test_mapping_uses_placeholder_when_group_or_sku_is_missing():
    mapping = RepresentativeImageMapping.from_payload(payload())
    assert mapping.projection_for(product(code="36"))["image_url"] == PLACEHOLDER_IMAGE_URL
    assert mapping.projection_for(product(sku=None))["image_url"] == PLACEHOLDER_IMAGE_URL


@pytest.mark.parametrize(
    "images",
    [
        ["https://example.com/Products/Images/1/a.jpg"],
        ["https://cdn.tgdd.vn/not-products/a.jpg"],
        [
            "https://cdn.tgdd.vn/Products/Images/1/a.jpg",
            "https://cdn.tgdd.vn/Products/Images/1/a.jpg",
        ],
        [
            "https://cdn.tgdd.vn/Products/Images/1/a.jpg",
            "https://cdn.tgdd.vn/Products/Images/1/b.jpg",
            "https://cdn.tgdd.vn/Products/Images/1/c.jpg",
            "https://cdn.tgdd.vn/Products/Images/1/d.jpg",
        ],
    ],
)
def test_mapping_rejects_non_allowlisted_duplicate_or_excess_images(images):
    with pytest.raises(ValueError):
        RepresentativeImageMapping.from_payload(payload(images))


def test_default_mapping_is_the_reviewed_five_group_seed():
    mapping = load_default_mapping()
    assert mapping.mapping_version == 1
    assert set(mapping.groups) == {"38:2", "36:7", "115:315", "39:133", "41:355"}


def test_catalog_group_sources_are_unique_stable_and_first_party():
    products = [
        product(sku="1"),
        product(sku="2"),
        product(sku="3", code="49", brand_id=None, brand="Apple"),
        product(sku="4", code="115", brand_id=None, brand="#N/A"),
    ]
    sources = catalog_group_sources(products)
    assert [source.key for source in sources] == [
        "38:2",
        "49:brand:apple",
        "115:brand:n-a",
    ]
    assert sources[0].source_url == "https://www.dienmayxanh.com/tu-lanh-samsung"
    assert sources[1].source_url == "https://www.dienmayxanh.com/dong-ho-thong-minh-apple"
    assert sources[2].source_url is None


def test_source_aliases_ipad_brand_for_page_card_matching():
    source = source_for_group("30", None, "Ipad (Apple)")
    assert source.source_url == "https://www.dienmayxanh.com/may-tinh-bang-apple"
    assert source.match_brand == "Apple"
