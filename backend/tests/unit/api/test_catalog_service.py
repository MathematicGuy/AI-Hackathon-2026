import pytest
from pydantic import ValidationError

from backend.app.api.errors import (
    InvalidAttributeFilterError,
    NotFoundError,
    ValidationAppError,
)
from backend.app.api.schemas.catalog import CompareRequest, SearchRequest
from backend.app.services.catalog_service import CatalogService


class FakeRepo:
    def __init__(self, rows=None, total=0, products=None):
        self._rows = rows or []
        self._total = total
        self.products = products or {}
        self.search_args = None
        self.categories = {"36": {"category_code": "36", "name": "Máy lạnh"}}
        self.attrs = {
            "36": [
                {"key": "Loại Gas", "non_null_count": 10, "total": 10},
                {"key": "giá khuyến mãi", "non_null_count": 8, "total": 10},
            ]
        }

    def get_category(self, code):
        return self.categories.get(code)

    def category_attributes(self, code):
        return self.attrs.get(code, [])

    def get_product(self, sku):
        return self.products.get(sku)

    def get_products_by_skus(self, skus):
        return [self.products[s] for s in skus if s in self.products]

    def search(self, **kwargs):
        self.search_args = kwargs
        return self._rows, self._total


def _service(**kw):
    return CatalogService(FakeRepo(**kw))


def test_attribute_filter_requires_category():
    service = _service()
    request = SearchRequest(attribute_filters=[{"key": "Loại Gas", "op": "eq", "value": "R-32"}])
    with pytest.raises(InvalidAttributeFilterError):
        service.search(request)


def test_unknown_category_raises_not_found():
    service = _service()
    with pytest.raises(NotFoundError):
        service.search(SearchRequest(category_code="999"))


def test_unknown_attribute_key_rejected():
    service = _service()
    request = SearchRequest(
        category_code="36",
        attribute_filters=[{"key": "Không tồn tại", "op": "eq", "value": "x"}],
    )
    with pytest.raises(InvalidAttributeFilterError) as exc:
        service.search(request)
    assert exc.value.details == ["Không tồn tại"]


def test_sort_by_attribute_requires_category():
    service = _service()
    with pytest.raises(ValidationAppError):
        service.search(SearchRequest(sort=[{"field": "Loại Gas", "direction": "asc"}]))


def test_sort_by_unknown_attribute_rejected():
    service = _service()
    request = SearchRequest(category_code="36", sort=[{"field": "Nope", "direction": "asc"}])
    with pytest.raises(ValidationAppError):
        service.search(request)


def test_valid_search_passes_primitive_tuples_to_repo():
    repo = FakeRepo(rows=[{"sku": "1"}], total=45)
    service = CatalogService(repo)
    request = SearchRequest(
        category_code="36",
        brands=["Panasonic"],
        attribute_filters=[{"key": "Loại Gas", "op": "eq", "value": "R-32"}],
        sort=[{"field": "brand", "direction": "desc"}],
        page=2,
        page_size=20,
    )
    rows, total, total_pages = service.search(request)
    assert total == 45
    assert total_pages == 3  # ceil(45 / 20)
    assert repo.search_args["attribute_filters"] == [("Loại Gas", "eq", "R-32")]
    assert repo.search_args["sort"] == [("brand", "desc", False)]
    assert repo.search_args["brands"] == ["Panasonic"]


def test_get_product_not_found():
    service = _service()
    with pytest.raises(NotFoundError):
        service.get_product("missing")


def test_batch_dedupes_and_reports_missing():
    products = {"a": {"sku": "a", "category_code": "36", "attributes": {}}}
    service = _service(products=products)
    rows, missing = service.batch(["a", "a", "b"])
    assert [r["sku"] for r in rows] == ["a"]
    assert missing == ["b"]


def test_compare_same_category_builds_union_matrix():
    products = {
        "a": {"sku": "a", "category_code": "36", "attributes": {"Loại Gas": "R-32", "Độ ồn": "38 dB"}},
        "b": {"sku": "b", "category_code": "36", "attributes": {"Loại Gas": "R-410A"}},
    }
    service = _service(products=products)
    ordered, same, category_code, matrix, warnings = service.compare(["a", "b", "z"])
    assert [p["sku"] for p in ordered] == ["a", "b"]
    assert same is True
    assert category_code == "36"
    keys = [row["key"] for row in matrix]
    assert keys == ["Loại Gas", "Độ ồn"]  # union, first-seen order
    assert matrix[1]["values"] == {"a": "38 dB", "b": None}
    assert any("z" in w for w in warnings)


def test_compare_mixed_category_warns():
    products = {
        "a": {"sku": "a", "category_code": "36", "attributes": {}},
        "b": {"sku": "b", "category_code": "38", "attributes": {}},
    }
    service = _service(products=products)
    _, same, category_code, _, warnings = service.compare(["a", "b"])
    assert same is False
    assert category_code is None
    assert any("multiple categories" in w for w in warnings)


def test_page_size_over_100_is_rejected_by_schema():
    with pytest.raises(ValidationError):
        SearchRequest(page_size=101)


def test_compare_over_5_skus_rejected_by_schema():
    with pytest.raises(ValidationError):
        CompareRequest(skus=["1", "2", "3", "4", "5", "6"])
