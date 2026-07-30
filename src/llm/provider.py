from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from config import settings


@lru_cache(maxsize=None)
def get_llm(temperature: float | None = None) -> ChatOpenAI:
    """Shared, cached LLM client so agents/nodes don't each spin up their own."""
    return ChatOpenAI(
        model=settings.MODEL_NAME,
        api_key=settings.OPENAI_API_KEY,
        temperature=settings.TEMPERATURE if temperature is None else temperature,
    )