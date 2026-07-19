"""FastAPI endpoint for the E02 agent: POST /api/v1/agent/respond.

Sessions are held in-process (demo-grade); durable checkpointer persistence is
deferred and recorded on US-206. Separate from the M1 rig's advisor endpoint.

The endpoints are unauthenticated by design for this phase, so US-125 bounds
them instead: a payload cap, a per-client rate limit, and a session ceiling
that evicts least-recently-used sessions rather than growing without limit.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from collections import OrderedDict, deque
from collections.abc import Callable

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.agent.contracts import AgentPresentation, AgentState
from backend.app.agent.graph import AgentDependencies, run_turn

logger = logging.getLogger(__name__)

DEFAULT_MAX_MESSAGE_CHARS = 2000
DEFAULT_RATE_LIMIT_REQUESTS = 20
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60
DEFAULT_MAX_SESSIONS = 5000


def _env_int(name: str, default: int) -> int:
    """Positive integer from the environment, falling back on anything unusable."""
    raw = os.environ.get(name, "")
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


class _RateLimiter:
    """Fixed-window-per-client request limiter.

    In-process like the session store: it bounds a single container's exposure
    to abuse. It is not a distributed limiter, and nginx applies its own
    `limit_req` in front (see infra/nginx/default.conf).
    """

    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = {}

    def check(self, client_key: str, now: float | None = None) -> float | None:
        """None when allowed; otherwise the seconds the client should wait."""
        moment = time.monotonic() if now is None else now
        hits = self._hits.setdefault(client_key, deque())
        cutoff = moment - self._window
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= self._limit:
            return max(1.0, self._window - (moment - hits[0]))
        hits.append(moment)
        if len(self._hits) > 10_000:  # bound the limiter's own memory
            for key in [k for k, v in self._hits.items() if not v]:
                del self._hits[key]
        return None


def _client_key(request: Request) -> str:
    """Client identity for rate limiting, trusting the nginx forwarded header."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class AgentRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1)


class ComparisonProduct(BaseModel):
    id: str
    name: str
    brand: str | None = None
    effective_price: int | None = None
    list_price: int | None = None
    discount_percent: float | None = None
    gift: str | None = None


class ComparisonRow(BaseModel):
    label: str
    unit: str = ""
    explain: str = ""
    values: dict[str, str]
    winner_id: str | None = None


class ComparisonView(BaseModel):
    products: list[ComparisonProduct]
    rows: list[ComparisonRow] = []
    price_delta: int | None = None


class AgentResponse(BaseModel):
    session_id: str
    request_id: str
    intent: str
    text: str
    flags: list[str] = Field(default_factory=list)
    presented_ids: list[str] = Field(default_factory=list)
    presentation: AgentPresentation | None = None


class FeedbackRequest(BaseModel):
    session_id: str
    message_index: int = Field(ge=0)
    rating: str = Field(pattern="^(like|dislike)$")


def create_agent_router(
    deps: AgentDependencies | Callable[[], AgentDependencies],
) -> APIRouter:
    """Mount POST /api/v1/agent/respond.

    `deps` may be a provider so a host app can build the router at import time
    and resolve dependencies later from its own lifespan (see
    `backend.app.api.main`).
    """
    router = APIRouter()
    # LRU-ordered so the session ceiling evicts the coldest session instead of
    # letting the map grow without bound.
    sessions: OrderedDict[str, AgentState] = OrderedDict()
    feedback_log: deque[dict] = deque(maxlen=1000)
    resolve = deps if callable(deps) else lambda: deps

    max_message_chars = _env_int("AGENT_MAX_MESSAGE_CHARS", DEFAULT_MAX_MESSAGE_CHARS)
    max_sessions = _env_int("AGENT_MAX_SESSIONS", DEFAULT_MAX_SESSIONS)
    limiter = _RateLimiter(
        _env_int("AGENT_RATE_LIMIT_REQUESTS", DEFAULT_RATE_LIMIT_REQUESTS),
        _env_int("AGENT_RATE_LIMIT_WINDOW_SECONDS", DEFAULT_RATE_LIMIT_WINDOW_SECONDS),
    )

    def guard(http_request: Request, agent_request: AgentRequest) -> None:
        """Payload and rate limits for the unauthenticated agent endpoints."""
        if len(agent_request.message) > max_message_chars:
            logger.warning(
                "agent.message_too_large chars=%d limit=%d",
                len(agent_request.message),
                max_message_chars,
            )
            raise HTTPException(
                status_code=413,
                detail=(
                    f"Tin nhắn quá dài (tối đa {max_message_chars} ký tự). "
                    "Anh/chị rút ngắn giúp em nhé ạ."
                ),
            )
        retry_after = limiter.check(_client_key(http_request))
        if retry_after is not None:
            logger.warning("agent.rate_limited retry_after=%.0f", retry_after)
            raise HTTPException(
                status_code=429,
                detail="Anh/chị gửi hơi nhanh, chờ em một chút rồi thử lại ạ.",
                headers={"Retry-After": str(int(retry_after))},
            )

    def session_state(session_id: str) -> AgentState:
        state = sessions.get(session_id)
        if state is None:
            state = AgentState(session_id=session_id)
            sessions[session_id] = state
            while len(sessions) > max_sessions:
                evicted, _ = sessions.popitem(last=False)
                logger.info("agent.session_evicted session_id=%s", evicted)
        else:
            sessions.move_to_end(session_id)
        return state

    def serialize_comparison(reply) -> dict | None:
        """Structured comparison view, or None on a non-comparison turn."""
        view = getattr(reply, "comparison", None)
        if view is None:
            return None
        return {
            "products": [
                {
                    "id": product.productidweb,
                    "name": product.name,
                    "brand": product.brand,
                    "effective_price": product.effective_price,
                    "list_price": product.list_price,
                    "discount_percent": product.discount_percent,
                    "gift": product.gift,
                }
                for product in view.products
            ],
            "rows": [
                {
                    "label": row.label,
                    "unit": row.unit,
                    "explain": row.explain,
                    "values": row.values,
                    "winner_id": row.winner_id,
                }
                for row in view.rows
            ],
            "price_delta": view.price_delta,
        }

    @router.post("/api/v1/agent/respond", response_model=AgentResponse)
    async def respond(http_request: Request, request: AgentRequest) -> AgentResponse:
        guard(http_request, request)
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:12]}"
        state = session_state(session_id)
        reply = await run_turn(state, request.message, resolve())
        return AgentResponse(
            session_id=session_id,
            request_id=f"request-{uuid.uuid4().hex[:12]}",
            intent=reply.intent,
            text=reply.text,
            flags=reply.flags,
            presented_ids=reply.presented_ids,
            presentation=reply.presentation,
        )

    @router.post("/api/v1/agent/respond/stream")
    async def respond_stream(
        http_request: Request, request: AgentRequest
    ) -> StreamingResponse:
        """Presentation streaming: the deterministic pipeline produces the
        full grounded text, which is then streamed in small chunks (NDJSON
        events). Token-level streaming arrives when the sell step itself runs
        on a streaming LLM."""
        guard(http_request, request)
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:12]}"
        state = session_state(session_id)

        async def generate():
            reply = await run_turn(state, request.message, resolve())
            text = reply.text
            step = 28
            for start in range(0, len(text), step):
                chunk = text[start : start + step]
                yield json.dumps(
                    {"type": "chunk", "text": chunk}, ensure_ascii=False
                ) + "\n"
                await asyncio.sleep(0.025)
            yield json.dumps(
                {
                    "type": "done",
                    "session_id": session_id,
                    "intent": reply.intent,
                    "flags": reply.flags,
                    "presented_ids": reply.presented_ids,
                    "presentation": reply.presentation.model_dump() if reply.presentation else None,
                },
                ensure_ascii=False,
            ) + "\n"

        return StreamingResponse(generate(), media_type="application/x-ndjson")

    @router.post("/api/v1/agent/feedback")
    async def feedback(request: FeedbackRequest) -> dict:
        """Like/dislike on an assistant message. In-memory for now; the
        Langfuse hookup is deferred with the judge wiring."""
        entry = request.model_dump()
        feedback_log.append(entry)
        # Rating and position only: the customer's message text never reaches
        # the logs.
        logger.info(
            "agent.feedback session_id=%s message_index=%d rating=%s",
            request.session_id,
            request.message_index,
            request.rating,
        )
        return {"status": "recorded", "count": len(feedback_log)}

    return router


DEFAULT_CORS_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000"


def create_agent_app(deps: AgentDependencies | None = None) -> FastAPI:
    app = FastAPI(title="DMX Multi-Category Sales Agent")
    origins = [
        origin.strip()
        for origin in os.environ.get(
            "AGENT_CORS_ORIGINS", DEFAULT_CORS_ORIGINS
        ).split(",")
        if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(create_agent_router(deps or AgentDependencies.from_default_paths()))
    return app
