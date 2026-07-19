"""FastAPI endpoint for the E02 agent: POST /api/v1/agent/respond.

Session memory is held in-process with a JSON write-through per session
(`AGENT_SESSION_DIR`, default data/agent-sessions/): the fixed-format need,
per-category archives, asked/shown lists. Inspectable on disk and it survives
restarts. Separate from the M1 rig's advisor endpoint.

The endpoints are unauthenticated by design for this phase, so US-125 bounds
them instead: a payload cap, a per-client rate limit, and a session ceiling
that evicts least-recently-used sessions rather than growing without limit.
Eviction only drops the in-memory copy — the JSON write-through above means an
evicted session is reloaded from disk on its next turn.
"""

import asyncio
import json
import logging
import os
import re
import time
import uuid
from collections import OrderedDict, deque
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.agent.catalog.dimensions import (
    better_of,
    dimension_display,
    dimension_value,
    dimensions_for,
    rankable,
)
from backend.app.agent.contracts import AgentState
from backend.app.agent.graph import AgentDependencies, run_turn
from backend.app.catalog_images import RepresentativeImageMapping, load_default_mapping
from backend.app.observability import noop_agent_observer

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


class AgentResponse(BaseModel):
    session_id: str
    request_id: str
    trace_id: str
    intent: str
    text: str
    flags: list[str] = []
    presented_ids: list[str] = []
    # The EXISTING comparison, structured for embedding (round 7): present
    # only on compare replies, built from the same tools the text used.
    # Optional and additive — older clients ignore it.
    table: dict | None = None
    # Presentation-only imagery for the first product in the turn (US-126).
    # Null on non-product turns; never persisted to a catalog row.
    image_url: str | None = None
    image_type: str | None = None
    mapping_version: int | None = None


class FeedbackRequest(BaseModel):
    session_id: str
    message_index: int = Field(ge=0)
    rating: str = Field(pattern="^(like|dislike)$")


def _comparison_table(deps: AgentDependencies, reply) -> dict | None:
    """Structure the comparison the reply ALREADY made (same tools as
    `_compare_flow`'s text) so the UI can embed it as a table. Only for
    compare replies with two products — nowhere else."""
    if reply.intent != "compare_products" or len(reply.presented_ids) < 2:
        return None
    selected = [
        p
        for pid in reply.presented_ids[:2]
        for p in deps.products
        if p.productidweb == pid
    ]
    if len(selected) < 2:
        return None
    products = []
    for p in selected:
        products.append(
            {
                "id": p.productidweb,
                "name": p.name,
                "brand": p.brand,
                "list_price": p.list_price,
                "sale_price": p.sale_price,
                "effective_price": p.effective_price,
                "discount_percent": p.promotion.discount_percent,
                "gift": bool(p.gift_promotion),
            }
        )
    rows = []
    first, second = selected
    for dim in dimensions_for(first.category_code):
        shown_a = dimension_display(first, dim)
        shown_b = dimension_display(second, dim)
        if shown_a is None or shown_b is None:
            continue
        winner_id = None
        if rankable(dim):
            verdict = better_of(
                dimension_value(first, dim), dimension_value(second, dim), dim
            )
            if verdict == -1:
                winner_id = first.productidweb
            elif verdict == 1:
                winner_id = second.productidweb
        rows.append(
            {"label": dim.label, "values": [shown_a, shown_b], "winner_id": winner_id}
        )
    return {"products": products, "rows": rows}


def _session_dir() -> Path:
    return Path(os.environ.get("AGENT_SESSION_DIR") or Path("data") / "agent-sessions")


def _session_path(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:80]
    return _session_dir() / f"{safe}.json"


def _load_session(session_id: str) -> AgentState | None:
    try:
        path = _session_path(session_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return AgentState.from_json_dict(payload)
    except Exception:
        return None  # a corrupt file must never break the turn


def _persist_session(state: AgentState) -> None:
    try:
        directory = _session_dir()
        directory.mkdir(parents=True, exist_ok=True)
        path = _session_path(state.session_id)
        path.write_text(
            json.dumps(state.to_json_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass  # persistence is best-effort; the in-process state is primary


def create_agent_router(
    deps: AgentDependencies | Callable[[], AgentDependencies],
    *,
    image_mapping: RepresentativeImageMapping | None = None,
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
    representative_images = image_mapping or load_default_mapping()

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

    def _session(session_id: str) -> AgentState:
        state = sessions.get(session_id)
        if state is None:
            state = _load_session(session_id) or AgentState(session_id=session_id)
            sessions[session_id] = state
            # Safe to drop the coldest entries: _persist_session has already
            # written them to disk, so an evicted session is reloaded intact.
            while len(sessions) > max_sessions:
                evicted, _ = sessions.popitem(last=False)
                logger.info("agent.session_evicted session_id=%s", evicted)
        else:
            sessions.move_to_end(session_id)
        return state

    def serialize_representative_image(reply, agent_deps: AgentDependencies) -> dict:
        """Project one disclosed image without changing the agent graph reply."""
        product_ids = list(getattr(reply, "presented_ids", []) or [])
        product = next(
            (
                candidate
                for product_id in product_ids[:1]
                for candidate in agent_deps.products
                if candidate.productidweb == product_id
            ),
            None,
        )
        if product is None:
            return {"image_url": None, "image_type": None, "mapping_version": None}
        return representative_images.projection_for(product)

    @router.post("/api/v1/agent/respond", response_model=AgentResponse)
    async def respond(http_request: Request, request: AgentRequest) -> AgentResponse:
        guard(http_request, request)
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:12]}"
        request_id = f"request-{uuid.uuid4().hex[:12]}"
        trace_id = uuid.uuid4().hex
        state = _session(session_id)
        # Resolve once: `deps` may be a provider callable (the catalog app
        # mounts this router before its lifespan builds the dependencies), so
        # the observer must be read off the resolved object, not off `deps`.
        agent_deps = resolve()
        observer = agent_deps.observer or noop_agent_observer()
        try:
            with observer.start_turn(
                trace_id=trace_id,
                session_id=session_id,
                request_id=request_id,
                user_id=None,
                input={"message": request.message, "state": state},
                metadata={
                    "environment": "hackathon",
                    "turn_number": state.turn_number + 1,
                },
            ) as turn:
                reply = await run_turn(state, request.message, agent_deps)
                turn.update(output={"reply": reply, "state": state})
            _persist_session(state)
        finally:
            try:
                observer.flush()
            except Exception:
                pass
        image = serialize_representative_image(reply, agent_deps)
        return AgentResponse(
            session_id=session_id,
            request_id=request_id,
            trace_id=trace_id,
            intent=reply.intent,
            text=reply.text,
            flags=reply.flags,
            presented_ids=reply.presented_ids,
            table=_comparison_table(agent_deps, reply),
            **image,
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
        state = _session(session_id)

        async def generate():
            agent_deps = resolve()
            reply = await run_turn(state, request.message, agent_deps)
            _persist_session(state)
            text = reply.text
            step = 28
            for start in range(0, len(text), step):
                chunk = text[start : start + step]
                yield json.dumps(
                    {"type": "chunk", "text": chunk}, ensure_ascii=False
                ) + "\n"
                await asyncio.sleep(0.025)
            image = serialize_representative_image(reply, agent_deps)
            yield json.dumps(
                {
                    "type": "done",
                    "session_id": session_id,
                    "intent": reply.intent,
                    "flags": reply.flags,
                    "presented_ids": reply.presented_ids,
                    "table": _comparison_table(agent_deps, reply),
                    **image,
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
