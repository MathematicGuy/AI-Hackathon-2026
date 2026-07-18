from fastapi import APIRouter, Depends

from backend.app.api.deps import get_service
from backend.app.api.schemas.catalog import CategoryAttributes, CategoryList
from backend.app.api.schemas.common import ErrorResponse
from backend.app.services.catalog_service import CatalogService

router = APIRouter(prefix="/api/v1", tags=["categories"])


@router.get("/categories", response_model=CategoryList)
def list_categories(service: CatalogService = Depends(get_service)) -> dict:
    """List every product category with its product count."""
    rows = service.list_categories()
    return {"items": rows, "total": len(rows)}


@router.get(
    "/categories/{category_code}/attributes",
    response_model=CategoryAttributes,
    responses={404: {"model": ErrorResponse}},
)
def category_attributes(
    category_code: str, service: CatalogService = Depends(get_service)
) -> dict:
    """List the attribute keys valid for a category (use these in filters)."""
    category, attributes = service.get_category_attributes(category_code)
    return {
        "category_code": category["category_code"],
        "name": category["name"],
        "attributes": attributes,
    }
