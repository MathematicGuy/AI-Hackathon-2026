"""FastAPI dependencies: hand out a service backed by a pooled connection."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request

from backend.app.repositories.catalog_repository import CatalogRepository
from backend.app.services.catalog_service import CatalogService


def get_service(request: Request) -> Iterator[CatalogService]:
    pool = request.app.state.pool
    with pool.connection() as conn:
        yield CatalogService(CatalogRepository(conn))
