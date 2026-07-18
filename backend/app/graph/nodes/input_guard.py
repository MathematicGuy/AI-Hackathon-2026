"""Graph node applying the input guardrail over the workflow state."""

from backend.app.graph.state import WorkflowState
from backend.app.guardrails.input_rules import InputGuardResult, evaluate_input
from backend.app.guardrails.nemo.input import NemoInputRail, default_input_rail


def _latest_message(state: WorkflowState) -> str:
    messages = state.get("messages") or []
    if not messages:
        return ""
    last = messages[-1]
    if isinstance(last, str):
        return last
    if isinstance(last, dict):
        return str(last.get("content", ""))
    return str(getattr(last, "content", ""))


def input_guard_node(
    state: WorkflowState, *, nemo: NemoInputRail | None = None
) -> WorkflowState:
    result: InputGuardResult = evaluate_input(
        _latest_message(state), nemo=nemo or default_input_rail()
    )
    flags = list(state.get("guardrail_flags", []))
    flags.extend(result.flags)
    if result.blocked:
        flags.append("guardrail_block")

    new_state = dict(state)
    new_state["guardrail_flags"] = flags
    return new_state  # type: ignore[return-value]
