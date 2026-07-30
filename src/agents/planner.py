from __future__ import annotations

from src.agents.base import BaseAgent
from src.agents.state import AgentState


PLANNER_PROMPT = """
You are a Planning Agent.

Convert the intent into a list of execution steps.

Return JSON only.

Example

{
  "plan":[
      "Discover MCP tools",
      "Select best tool",
      "Extract parameters",
      "Execute tool",
      "Generate response"
  ]
}
"""


class PlannerAgent(BaseAgent):

    def __init__(self):

        super().__init__(PLANNER_PROMPT)

    def __call__(self, state: AgentState):

        prompt = f"""
Intent

{state["intent"]}

User

{state["user_input"]}
"""

        result = self.invoke_json(prompt)

        state["plan"] = result["plan"]

        return state