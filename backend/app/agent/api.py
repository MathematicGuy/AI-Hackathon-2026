"""FastAPI endpoint for the E02 agent: POST /api/v1/agent/respond.

Sessions are held in-process (demo-grade); durable checkpointer persistence is
deferred and recorded on US-206. Separate from the M1 rig's advisor endpoint.
"""

import asyncio
import json
import os
import uuid
from collections.abc import Callable

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.agent.contracts import AgentState
from backend.app.agent.graph import AgentDependencies, run_turn


class AgentRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1)


class AgentResponse(BaseModel):
    session_id: str
    request_id: str
    intent: str
    text: str
    flags: list[str] = []
    presented_ids: list[str] = []


def create_agent_router(
    deps: AgentDependencies | Callable[[], AgentDependencies],
) -> APIRouter:
    """Mount POST /api/v1/agent/respond.

    `deps` may be a provider so a host app can build the router at import time
    and resolve dependencies later from its own lifespan (see
    `backend.app.api.main`).
    """
    router = APIRouter()
    sessions: dict[str, AgentState] = {}
    resolve = deps if callable(deps) else lambda: deps

    @router.post("/api/v1/agent/respond", response_model=AgentResponse)
    async def respond(request: AgentRequest) -> AgentResponse:
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:12]}"
        state = sessions.setdefault(session_id, AgentState(session_id=session_id))
        reply = await run_turn(state, request.message, resolve())
        return AgentResponse(
            session_id=session_id,
            request_id=f"request-{uuid.uuid4().hex[:12]}",
            intent=reply.intent,
            text=reply.text,
            flags=reply.flags,
            presented_ids=reply.presented_ids,
        )

    @router.post("/api/v1/agent/respond/stream")
    async def respond_stream(request: AgentRequest) -> StreamingResponse:
        """Presentation streaming: the deterministic pipeline produces the
        full grounded text, which is then streamed in small chunks (NDJSON
        events). Token-level streaming arrives when the sell step itself runs
        on a streaming LLM."""
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:12]}"
        state = sessions.setdefault(session_id, AgentState(session_id=session_id))

        async def generate():
            reply = await run_turn(state, request.message, deps)
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
                },
                ensure_ascii=False,
            ) + "\n"

        return StreamingResponse(generate(), media_type="application/x-ndjson")

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
