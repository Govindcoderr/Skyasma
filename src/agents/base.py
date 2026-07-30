from __future__ import annotations

import json
from abc import ABC
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import settings


class BaseAgent(ABC):
    """
    Base class for every agent.

    Responsibilities:
    - Create LLM
    - Invoke LLM
    - Return JSON/text
    """

    def __init__(
        self,
        system_prompt: str,
        temperature: float = settings.TEMPERATURE,
    ):

        self.system_prompt = system_prompt

        self.llm = ChatOpenAI(
            model=settings.MODEL_NAME,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
        )

    def invoke(self, user_prompt: str) -> str:

        response = self.llm.invoke(
            [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )

        return response.content

    def invoke_json(self, user_prompt: str) -> dict[str, Any]:

        raw = self.invoke(user_prompt)

        try:
            return json.loads(raw)

        except Exception as e:

            raise RuntimeError(
                f"Agent returned invalid JSON\n\n{raw}"
            ) from e