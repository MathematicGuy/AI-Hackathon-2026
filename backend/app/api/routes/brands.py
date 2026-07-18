from fastapi import APIRouter, Depends

from backend.app.api.deps import get_service
from backend.app.api.schemas.catalog import BrandList
from backend.app.api.schemas.common import ErrorResponse
from backend.app.services.catalog_service import CatalogService

router = APIRouter(prefix="/api/v1", tags=["brands"])


@router.get(
    "/brands", response_model=BrandList, responses={404: {"model": ErrorResponse}}
)
def list_brands(
    category_code: str | None = None,
    service: CatalogService = Depends(get_service),
) -> dict:
    """List brands, optionally scoped to one category."""
    rows = service.list_brands(category_code)
    return {"items": rows, "total": len(rows)}
