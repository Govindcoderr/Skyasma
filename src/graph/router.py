from __future__ import annotations

from agents.state import AgentState


def route_after_supervisor(state: AgentState) -> str:
    """general_chat has nothing to plan/execute — skip straight to responder."""
    if state["intent"] == "general_chat":
        return "responder"
    return "planner"


def route_after_executor(state: AgentState) -> str:
    """Single path for now; kept as a router so retry/clarify branches can be added later."""
    return "responder"