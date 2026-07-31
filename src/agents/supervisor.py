from __future__ import annotations

from src.agents.base import BaseAgent
from src.agents.state import AgentState


SUPERVISOR_PROMPT = """
You are the Supervisor Agent.

Your job is ONLY to classify the user's request.

Available intents

send_email

reply_email

search_email

read_email

calendar

slack

github

drive

general_chat

Return ONLY JSON.

Example

{
    "intent":"send_email",
    "confidence":0.98
}
"""


class SupervisorAgent(BaseAgent):

    def __init__(self):

        super().__init__(SUPERVISOR_PROMPT)

    def __call__(self, state: AgentState):

        result = self.invoke_json(
            state["user_input"]
        )

        state["intent"] = result["intent"]

        state["confidence"] = result["confidence"]

        return state