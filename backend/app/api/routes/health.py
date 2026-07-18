from fastapi import APIRouter, Request, Response

from backend.app.api.schemas.catalog import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request, response: Response) -> dict:
    """Liveness plus a database connectivity check."""
    try:
        with request.app.state.pool.connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "up"}
    except Exception:
        response.status_code = 503
        return {"status": "degraded", "database": "down"}
