"""FastAPI endpoint for the E02 agent: POST /api/v1/agent/respond.

Sessions are held in-process (demo-grade); durable checkpointer persistence is
deferred and recorded on US-206. Separate from the M1 rig's advisor endpoint.
"""

import uuid

from fastapi import APIRouter, FastAPI
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


def create_agent_router(deps: AgentDependencies) -> APIRouter:
    router = APIRouter()
    sessions: dict[str, AgentState] = {}

    @router.post("/api/v1/agent/respond", response_model=AgentResponse)
    async def respond(request: AgentRequest) -> AgentResponse:
        session_id = request.session_id or f"session-{uuid.uuid4().hex[:12]}"
        state = sessions.setdefault(session_id, AgentState(session_id=session_id))
        reply = await run_turn(state, request.message, deps)
        return AgentResponse(
            session_id=session_id,
            request_id=f"request-{uuid.uuid4().hex[:12]}",
            intent=reply.intent,
            text=reply.text,
            flags=reply.flags,
            presented_ids=reply.presented_ids,
        )

    return router


def create_agent_app(deps: AgentDependencies | None = None) -> FastAPI:
    app = FastAPI(title="DMX Multi-Category Sales Agent")
    app.include_router(create_agent_router(deps or AgentDependencies.from_default_paths()))
    return app
