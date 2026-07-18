"""Local CLI chat with the agent: uv run python -m backend.app.agent.demo

Runs fully deterministic (no provider keys needed). When the environment-owned
model routes are configured, the LLM extractor can be attached later without
changing this loop.
"""

import asyncio
import uuid

from backend.app.agent.contracts import AgentState
from backend.app.agent.graph import AgentDependencies, run_turn
from backend.app.observability import noop_agent_observer


async def main() -> None:
    print("Đang tải dữ liệu 14 ngành hàng...")
    deps = AgentDependencies.from_default_paths()
    state = AgentState(session_id="demo")
    observer = deps.observer or noop_agent_observer()
    print("Xong. Gõ tin nhắn (hoặc 'exit' để thoát).\n")
    try:
        while True:
            try:
                message = input("Bạn: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not message or message.lower() in ("exit", "quit"):
                break
            request_id = f"request-{uuid.uuid4().hex[:12]}"
            trace_id = uuid.uuid4().hex
            with observer.start_turn(
                trace_id=trace_id,
                session_id=state.session_id,
                request_id=request_id,
                user_id=None,
                input={"message": message, "state": state},
                metadata={
                    "environment": "hackathon",
                    "turn_number": state.turn_number + 1,
                },
            ) as turn:
                reply = await run_turn(state, message, deps)
                turn.update(output={"reply": reply, "state": state})
            print(f"\nBot: {reply.text}\n")
    finally:
        try:
            observer.flush()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
