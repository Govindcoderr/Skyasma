from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage


class AgentState(TypedDict):

    messages: List[BaseMessage]

    user_input: str
    intent: Optional[str]
    confidence: float

    plan: List[str]

    selected_tool: Optional[str]
    tool_arguments: Dict[str, Any]

    discovered_tools: List[Any]
    available_tools: List[Any]

    selected_server: Optional[str]
    selected_capability: Optional[str]

    execution_result: Optional[Any]
    tool_result: Optional[Dict[str, Any]]

    error: Optional[str]
    final_response: Optional[str]

    session_id: str
    thread_id: str

    requires_human: bool
    completed: bool


def create_initial_state(
    message: str,
    session_id: str = "default",
    thread_id: str = "default",
) -> AgentState:

    return AgentState(
        messages=[HumanMessage(content=message)],
        user_input=message,
        intent=None,
        confidence=0.0,
        plan=[],
        selected_tool=None,
        tool_arguments={},
        discovered_tools=[],
        available_tools=[],
        selected_server=None,
        selected_capability=None,
        execution_result=None,
        tool_result=None,
        error=None,
        final_response=None,
        session_id=session_id,
        thread_id=thread_id,
        requires_human=False,
        completed=False,
    )