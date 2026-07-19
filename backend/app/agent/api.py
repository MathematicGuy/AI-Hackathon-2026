"""FastAPI endpoint for the E02 agent: POST /api/v1/agent/respond.

Session memory is held in-process with a JSON write-through per session
(`AGENT_SESSION_DIR`, default data/agent-sessions/): the fixed-format need,
per-category archives, asked/shown lists. Inspectable on disk and it survives
restarts. Separate from the M1 rig's advisor endpoint.
"""

import asyncio
import json
import os
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, FastAPI
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
from backend.app.observability import noop_agent_observer


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


def create_agent_router(deps: AgentDependencies) -> APIRouter:
    router = APIRouter()
    sessions: dict[str, AgentState] = {}
    feedback_log: list[dict] = []

    def _session(session_id: str) -> AgentState:
        state = sessions.get(session_id)
        if state is None:
            state = _load_session(session_id) or AgentState(session_id=session_id)
            sessions[session_id] = state
        return state

    @router.post("/api/v1/agent/respond", response_model=AgentResponse)
    async def respond(request: AgentRequest) -> AgentResponse:
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:12]}"
        request_id = f"request-{uuid.uuid4().hex[:12]}"
        trace_id = uuid.uuid4().hex
        state = _session(session_id)
        observer = deps.observer or noop_agent_observer()
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
                reply = await run_turn(state, request.message, deps)
                turn.update(output={"reply": reply, "state": state})
            _persist_session(state)
        finally:
            try:
                observer.flush()
            except Exception:
                pass
        return AgentResponse(
            session_id=session_id,
            request_id=request_id,
            trace_id=trace_id,
            intent=reply.intent,
            text=reply.text,
            flags=reply.flags,
            presented_ids=reply.presented_ids,
            table=_comparison_table(deps, reply),
        )

    @router.post("/api/v1/agent/respond/stream")
    async def respond_stream(request: AgentRequest) -> StreamingResponse:
        """Presentation streaming: the deterministic pipeline produces the
        full grounded text, which is then streamed in small chunks (NDJSON
        events). Token-level streaming arrives when the sell step itself runs
        on a streaming LLM."""
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:12]}"
        state = _session(session_id)

        async def generate():
            reply = await run_turn(state, request.message, deps)
            _persist_session(state)
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
                    "table": _comparison_table(deps, reply),
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
        print(f"[agent-feedback] {entry}", flush=True)
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
