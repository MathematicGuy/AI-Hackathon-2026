import importlib

import pytest


class MissingModule:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, _attribute):
        pytest.fail(f"US-201 {self.name} module is not implemented")


@pytest.fixture
def adapter_module():
    try:
        return importlib.import_module("backend.app.agent.catalog.dataset_adapter")
    except ModuleNotFoundError:
        return MissingModule("dataset adapter")


@pytest.fixture(scope="module")
def loaded_products():
    module = importlib.import_module("backend.app.agent.catalog.dataset_adapter")
    adapter = module.ExcelDatasetAdapter()
    return adapter.load()


def test_load_returns_products_for_all_14_categories(adapter_module, loaded_products):
    codes = {product.category_code for product in loaded_products}
    assert len(loaded_products) > 5000
    assert len(codes) == 14


def test_known_panasonic_aircon_row_preserved(adapter_module, loaded_products):
    match = [p for p in loaded_products if p.productidweb == "362465"]
    assert len(match) == 1
    product = match[0]
    assert product.category_code == "36"
    assert product.brand == "Panasonic"
    # Original Vietnamese attribute keys must be preserved verbatim.
    assert "Công nghệ làm lạnh" in product.attributes
    assert product.attributes["Sản xuất tại"] == "Malaysia"
    assert product.list_price == 29_490_000
    assert product.gift_promotion.startswith("Phiếu mua hàng Máy lọc không khí/Hút bụi")


def test_category_codes_normalized_to_strings(adapter_module, loaded_products):
    assert all(isinstance(p.category_code, str) for p in loaded_products)


def test_category_name_comes_from_sheet(adapter_module, loaded_products):
    names = {p.category_name for p in loaded_products if p.category_code == "38"}
    assert names == {"Tủ Lạnh"}


def test_missing_file_raises_clear_error(adapter_module, tmp_path):
    adapter = adapter_module.ExcelDatasetAdapter(path=tmp_path / "missing.xlsx")
    with pytest.raises(FileNotFoundError):
        adapter.load()


def test_env_path_override(adapter_module, monkeypatch, tmp_path):
    monkeypatch.setenv("AGENT_DATASET_PATH", str(tmp_path / "somewhere.xlsx"))
    adapter = adapter_module.ExcelDatasetAdapter()
    assert str(adapter.path) == str(tmp_path / "somewhere.xlsx")


def test_load_is_cached(adapter_module):
    adapter = adapter_module.ExcelDatasetAdapter()
    first = adapter.load()
    second = adapter.load()
    assert first is second
