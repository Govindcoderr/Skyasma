from langchain_core.messages import HumanMessage



def create_initial_state(
    message: str,
    session_id: str = "default",
    thread_id: str = "default",
) -> AgentState:

    return AgentState(
        messages=[
            HumanMessage(content=message)
        ],
        user_input=message,
        intent=None,
        confidence=0,
        plan=[],
        selected_tool=None,
        tool_arguments={},
        discovered_tools=[],
        execution_result=None,
        error=None,
        final_response=None,
        session_id=session_id,
        thread_id=thread_id,
        requires_human=False,
        completed=False,

        available_tools: list,
        selected_server: str | None,
        selected_capability: str | None,
        tool_result: dict | None,
    )