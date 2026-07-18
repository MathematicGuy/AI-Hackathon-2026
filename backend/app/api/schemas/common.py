"""Shared API request/response building blocks."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Operator = Literal["eq", "neq", "contains", "in", "gte", "lte", "exists"]
SortDirection = Literal["asc", "desc"]

# Sortable typed columns (not attribute keys). Used by both the service (for
# validation) and the repository (for building ORDER BY).
SORT_COLUMNS: frozenset[str] = frozenset(
    {"sku", "brand", "productidweb", "category_code", "updated_at"}
)


class APIModel(BaseModel):
    """Base model that rejects unknown fields."""

    model_config = ConfigDict(extra="forbid")


class AttributeFilter(APIModel):
    """A single, validated attribute filter over a category's JSONB attributes."""

    key: str = Field(min_length=1)
    op: Operator
    value: Any = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"key": "Loại Gas", "op": "eq", "value": "R-32"},
                {"key": "giá khuyến mãi", "op": "lte", "value": 12000000},
                {"key": "Inverter", "op": "exists", "value": True},
            ]
        },
    )

    @model_validator(mode="after")
    def _validate_value_for_op(self) -> AttributeFilter:
        op, value = self.op, self.value
        if op in ("eq", "neq", "contains"):
            if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                raise ValueError(f"operator '{op}' requires a string or number value")
        elif op == "in":
            if not isinstance(value, list) or not value or any(
                isinstance(v, bool) or not isinstance(v, (str, int, float))
                for v in value
            ):
                raise ValueError(
                    "operator 'in' requires a non-empty list of strings or numbers"
                )
        elif op in ("gte", "lte"):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"operator '{op}' requires a numeric value")
        elif op == "exists":
            if value is None:
                object.__setattr__(self, "value", True)
            elif not isinstance(value, bool):
                raise ValueError("operator 'exists' requires a boolean value")
        return self


class SortSpec(APIModel):
    field: str = Field(min_length=1, description="A sort column or an attribute key")
    direction: SortDirection = "asc"
    numeric: bool = Field(
        default=False, description="Cast attribute value to number for sorting"
    )


class ErrorBody(APIModel):
    code: str
    message: str
    details: list[str] | None = None


class ErrorResponse(APIModel):
    """Unified error envelope returned by every failing request."""

    error: ErrorBody

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "error": {
                        "code": "invalid_attribute_filter",
                        "message": "unknown attribute keys for category 36",
                        "details": ["Không tồn tại"],
                    }
                }
            ]
        },
    )
