from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from config import settings
from src.llm.custom_llm import Q0CustomLLM


def _get_groq_key() -> str:
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set")
    return settings.GROQ_API_KEY


def get_llm(temperature: float | None = None) -> BaseChatModel:
    """
    Tool-calling capable LLM — used by the Executor (tool selection).
    Routed to the Q0 native-tools endpoint (OpenAI-compatible).
    """
    temp = temperature if temperature is not None else settings.LLM_TEMPERATURE

    print(f"Tool LLM: Q0 native tools ({settings.Q0_TOOLS_MODEL})")

    return ChatOpenAI(
        model=settings.Q0_TOOLS_MODEL,
        base_url=settings.Q0_tools_URL,
        api_key=settings.Q0_dummy_KEY,
        temperature=temp,
        max_tokens=settings.Q0_MAX_TOKENS,
    )


def get_llm_no_tools(temperature: float | None = None) -> BaseChatModel:
    """
    Plain chat LLM — used by Supervisor, Planner, Responder (no tool calling needed).
    Tries Q0 first, falls back to Groq on failure.
    """
    temp = temperature if temperature is not None else settings.LLM_TEMPERATURE

    if settings.USE_Q0_MODEL:
        try:
            print("Fast LLM: Q0CustomLLM")
            return Q0CustomLLM(
                api_url=settings.Q0_API_URL,
                temperature=temp,
                max_tokens=settings.Q0_MAX_TOKENS,
                top_p=settings.Q0_TOP_P,
            )
        except Exception as e:
            print(f"Q0 init failed: {e} — falling back to ChatGroq")

    print(f"Fast LLM: Groq ({settings.LLM_MODEL_FAST})")
    return ChatGroq(
        model=settings.LLM_MODEL_FAST,
        groq_api_key=_get_groq_key(),
        temperature=temp,
        max_retries=2,
    )