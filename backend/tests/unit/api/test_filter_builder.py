import pytest

from backend.app.repositories.catalog_repository import (
    build_attribute_condition,
    build_order_by,
)

NUMERIC_RE = r"^-?[0-9]+(\.[0-9]+)?$"


def test_eq_is_parameterized():
    sql, params = build_attribute_condition("Loại Gas", "eq", "R-32")
    assert sql == "p.attributes ->> %s = %s"
    assert params == ["Loại Gas", "R-32"]


def test_neq_uses_is_distinct_from():
    sql, params = build_attribute_condition("brand", "neq", "Daikin")
    assert "IS DISTINCT FROM %s" in sql
    assert params == ["brand", "Daikin"]


def test_contains_wraps_value_with_wildcards():
    sql, params = build_attribute_condition("brand", "contains", "pana")
    assert "ILIKE %s" in sql
    assert params == ["brand", "%pana%"]


def test_in_coerces_values_to_text():
    sql, params = build_attribute_condition("brand", "in", ["Panasonic", 5])
    assert "= ANY(%s)" in sql
    assert params == ["brand", ["Panasonic", "5"]]


def test_gte_uses_numeric_guard_and_binds_key_twice():
    sql, params = build_attribute_condition("giá khuyến mãi", "gte", 1000)
    assert "::numeric" in sql and ">= %s" in sql
    assert params == ["giá khuyến mãi", NUMERIC_RE, "giá khuyến mãi", 1000]


def test_exists_true_and_false():
    sql_true, params_true = build_attribute_condition("Inverter", "exists", True)
    assert sql_true == "p.attributes ->> %s IS NOT NULL"
    assert params_true == ["Inverter"]
    sql_false, _ = build_attribute_condition("Inverter", "exists", False)
    assert sql_false == "p.attributes ->> %s IS NULL"


def test_unsupported_operator_raises():
    with pytest.raises(ValueError):
        build_attribute_condition("x", "like", "y")


def test_order_default_is_sku():
    sql, params = build_order_by([])
    assert sql == " ORDER BY p.sku ASC"
    assert params == []


def test_order_by_whitelisted_column():
    sql, params = build_order_by([("brand", "desc", False)])
    assert "p.brand DESC NULLS LAST" in sql
    assert params == []


def test_order_by_attribute_text():
    sql, params = build_order_by([("Loại Gas", "desc", False)])
    assert "p.attributes ->> %s DESC NULLS LAST" in sql
    assert params == ["Loại Gas"]


def test_order_by_attribute_numeric_binds_key_twice():
    sql, params = build_order_by([("giá khuyến mãi", "asc", True)])
    assert "::numeric" in sql
    assert params == ["giá khuyến mãi", NUMERIC_RE, "giá khuyến mãi"]
