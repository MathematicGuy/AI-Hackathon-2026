import importlib

import pytest


class MissingModule:
    def __init__(self, name):
        self.name = name

    def __getattr__(self, _attribute):
        pytest.fail(f"US-201 {self.name} module is not implemented")


@pytest.fixture
def registry_module():
    try:
        return importlib.import_module("backend.app.agent.catalog.registry")
    except ModuleNotFoundError:
        return MissingModule("category registry")


def test_registry_has_all_14_categories(registry_module):
    registry = registry_module.CategoryRegistry()
    assert len(registry.all()) == 14


def test_known_category_codes(registry_module):
    registry = registry_module.CategoryRegistry()
    assert registry.by_code("36").sheet_name == "Máy lạnh"
    assert registry.by_code("38").sheet_name == "Tủ Lạnh"
    assert registry.by_code("115").sheet_name == "Máy giặt"
    assert registry.by_code("30").sheet_name == "Máy tính bảng"
    assert registry.by_code("72").sheet_name == "Máy tính để bàn"


def test_codes_are_normalized_strings(registry_module):
    registry = registry_module.CategoryRegistry()
    for category in registry.all():
        assert isinstance(category.code, str) and category.code.isdigit()


def test_detect_category_from_vietnamese_text(registry_module):
    registry = registry_module.CategoryRegistry()
    assert registry.detect("Tôi muốn mua tủ lạnh cho gia đình 4 người").code == "38"
    assert registry.detect("cần một chiếc máy giặt cửa trước").code == "115"
    assert registry.detect("tư vấn điều hòa cho phòng ngủ").code == "36"
    assert registry.detect("mua may tinh bang cho con học").code == "30"


def test_detect_returns_none_for_unsupported(registry_module):
    registry = registry_module.CategoryRegistry()
    assert registry.detect("tôi muốn mua ô tô điện") is None
    assert registry.detect("xin chào") is None


def test_every_category_has_markers(registry_module):
    registry = registry_module.CategoryRegistry()
    for category in registry.all():
        assert category.markers, f"{category.sheet_name} needs detection markers"
