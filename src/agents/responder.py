from __future__ import annotations

from langchain_core.messages import SystemMessage, HumanMessage

from llm.provider import get_llm
from llm.prompts import RESPONDER_PROMPT
from agents.state import AgentState


class ResponderAgent:
    def __init__(self):
        self.llm = get_llm()

    async def __call__(self, state: AgentState) -> AgentState:
        parts = [f"User asked: {state['user_input']}"]

        if state.get("execution_result") is not None:
            parts.append(f"Tool result: {state['execution_result']}")

        if state.get("error"):
            parts.append(
                f"Note: something went wrong internally ({state['error']}), "
                "answer helpfully anyway without exposing internal details."
            )

        response = await self.llm.ainvoke(
            [SystemMessage(content=RESPONDER_PROMPT), HumanMessage(content="\n".join(parts))]
        )

        state["final_response"] = response.content
        state["completed"] = True
        return state