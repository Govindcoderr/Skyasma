from __future__ import annotations

import json
from abc import ABC
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from llm.provider import get_llm, get_llm_no_tools
from llm.output_parser import parse_json, OutputParseError


class BaseAgent(ABC):
    """
    Base class for every agent.

    needs_tools=False (default): Supervisor, Planner, Responder → get_llm_no_tools
    needs_tools=True: Executor's tool-selection step → get_llm
    """

    def __init__(
        self,
        system_prompt: str,
        temperature: float | None = None,
        needs_tools: bool = False,
    ):
        self.system_prompt = system_prompt
        self.llm = get_llm(temperature) if needs_tools else get_llm_no_tools(temperature)

    def invoke(self, user_prompt: str) -> str:
        response = self.llm.invoke(
            [SystemMessage(content=self.system_prompt), HumanMessage(content=user_prompt)]
        )
        return response.content

    def invoke_json(self, user_prompt: str) -> dict[str, Any]:
        raw = self.invoke(user_prompt)
        try:
            return parse_json(raw)
        except OutputParseError as e:
            raise RuntimeError(str(e)) from e