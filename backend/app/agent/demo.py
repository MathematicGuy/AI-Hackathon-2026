"""Local CLI chat with the agent: uv run python -m backend.app.agent.demo

Runs fully deterministic (no provider keys needed). When the environment-owned
model routes are configured, the LLM extractor can be attached later without
changing this loop.
"""

import asyncio

from backend.app.agent.contracts import AgentState
from backend.app.agent.graph import AgentDependencies, run_turn


async def main() -> None:
    print("Đang tải dữ liệu 14 ngành hàng...")
    deps = AgentDependencies.from_default_paths()
    state = AgentState(session_id="demo")
    print("Xong. Gõ tin nhắn (hoặc 'exit' để thoát).\n")
    while True:
        try:
            message = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not message or message.lower() in ("exit", "quit"):
            break
        reply = await run_turn(state, message, deps)
        print(f"\nBot: {reply.text}\n")


if __name__ == "__main__":
    asyncio.run(main())
