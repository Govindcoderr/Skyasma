"""
Skyasma — single-file pipeline (Gmail only, for now).

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload
    # or: python main.py

Env vars needed (put in .env):
    OPENAI_API_KEY=sk-...
    MODEL_NAME=gpt-4.1-mini      # any OpenAI-compatible chat model
    TEMPERATURE=0
    GMAIL_CREDENTIALS_PATH=credentials.json   # optional, defaults shown
    GMAIL_TOKEN_PATH=token.json               # optional, defaults shown

The full multi-agent / LangGraph / Redis pipeline (src/agents, src/graph,
src/memory) is still in the repo untouched. This file is a deliberately
simplified stand-in so you have something running end-to-end today.
Add Slack/GitHub/planner back in gradually — see the comments below for
where each piece plugs back in.
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

# Make src/ importable, mirroring the Dockerfile's PYTHONPATH=/app/src
_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from mcp_core.client import MCPClient          # noqa: E402
from mcp_core.schemas import MCPServerConfig   # noqa: E402
from mcp_core.exceptions import MCPException   # noqa: E402
from llm.output_parser import parse_json, OutputParseError  # noqa: E402
from llm.prompts import render_tools           # noqa: E402


# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0"))

_ROOT = os.path.dirname(os.path.abspath(__file__))

GMAIL_SERVER_CONFIG = MCPServerConfig(
    name="gmail",
    # Use the exact interpreter running this process (your .venv's python),
    # not a bare "python" resolved via PATH — that can silently pick the
    # wrong interpreter (e.g. system Python without your pip installs).
    command=sys.executable,
    args=[os.path.join(_ROOT, "servers", "gmail", "server.py")],
)

# --- Add more servers here as you build them, e.g.: ---------------------
# SLACK_SERVER_CONFIG = MCPServerConfig(
#     name="slack", command="python",
#     args=[os.path.join(_ROOT, "servers", "slack", "server.py")],
# )
# Then add them to `mcp_clients` below and to the intent classifier.
# --------------------------------------------------------------------


def get_llm() -> ChatOpenAI:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set (check your .env)")
    return ChatOpenAI(model=MODEL_NAME, api_key=OPENAI_API_KEY, temperature=TEMPERATURE)


# ---------------------------------------------------------------------
# API schemas
# ---------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    intent: Optional[str] = None
    selected_tool: Optional[str] = None
    tool_arguments: dict[str, Any] = Field(default_factory=dict)
    execution_result: Optional[Any] = None
    final_response: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    gmail_connected: bool = False


# ---------------------------------------------------------------------
# In-memory session store.
# Swap for src/memory/session.py (Redis) once you bring Redis back.
# ---------------------------------------------------------------------

_sessions: dict[str, list[dict[str, str]]] = {}


def _history(session_id: str) -> list[dict[str, str]]:
    return _sessions.setdefault(session_id, [])


# ---------------------------------------------------------------------
# MCP clients (one per server) — just Gmail for now
# ---------------------------------------------------------------------

gmail_client = MCPClient(GMAIL_SERVER_CONFIG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await gmail_client.connect()
    yield
    await gmail_client.disconnect()


app = FastAPI(title="Skyasma — Gmail Pipeline", version="0.1.0", lifespan=lifespan)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(gmail_connected=gmail_client.connected)


# ---------------------------------------------------------------------
# Pipeline steps (Supervisor -> Executor -> Responder, collapsed into
# plain functions instead of a LangGraph for now)
# ---------------------------------------------------------------------

INTENT_PROMPT = """You classify a user's message into exactly one intent.

Intents:
- gmail: anything about sending, searching, reading, or replying to email
- general_chat: anything else

Return ONLY JSON like {"intent": "gmail"} or {"intent": "general_chat"}.
"""

TOOL_SELECTION_PROMPT = """You are the Tool Selector.

Given the user's request and the list of available Gmail tools below,
choose exactly ONE tool to call and produce its arguments.

Available tools:
{tools}

User request:
{user_input}

Return ONLY JSON in this shape:
{{"tool": "<tool name>", "arguments": {{}}}}

If no tool fits, return {{"tool": null, "arguments": {{}}}}
"""

RESPONDER_PROMPT = """Turn the tool result (or the plain conversation, if no
tool was used) into a clear, friendly final answer for the user. Do not
mention tools or internal steps — just answer naturally."""


async def classify_intent(llm: ChatOpenAI, message: str) -> str:
    response = await llm.ainvoke(
        [SystemMessage(content=INTENT_PROMPT), HumanMessage(content=message)]
    )
    try:
        return parse_json(response.content).get("intent", "general_chat")
    except OutputParseError:
        return "general_chat"


async def select_tool(llm: ChatOpenAI, message: str, tools) -> dict:
    prompt = TOOL_SELECTION_PROMPT.format(tools=render_tools(tools), user_input=message)
    response = await llm.ainvoke(
        [SystemMessage(content="You output only JSON."), HumanMessage(content=prompt)]
    )
    try:
        return parse_json(response.content)
    except OutputParseError:
        return {"tool": None, "arguments": {}}


async def generate_response(
    llm: ChatOpenAI, message: str, execution_result: Any, error: Optional[str]
) -> str:
    parts = [f"User asked: {message}"]
    if execution_result is not None:
        parts.append(f"Tool result: {execution_result}")
    if error:
        parts.append(
            f"Note: something went wrong internally ({error}), "
            "answer helpfully anyway without exposing internal details."
        )

    response = await llm.ainvoke(
        [SystemMessage(content=RESPONDER_PROMPT), HumanMessage(content="\n".join(parts))]
    )
    return response.content


# ---------------------------------------------------------------------
# /chat endpoint
# ---------------------------------------------------------------------

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    llm = get_llm()
    history = _history(request.session_id)
    history.append({"role": "user", "content": request.message})

    result = ChatResponse()

    try:
        intent = await classify_intent(llm, request.message)
        result.intent = intent

        if intent == "gmail":
            tools = await gmail_client.list_tools()

            if not tools:
                result.error = "Gmail MCP server returned no tools."
            else:
                selection = await select_tool(llm, request.message, tools)
                result.selected_tool = selection.get("tool")
                result.tool_arguments = selection.get("arguments", {})

                if result.selected_tool:
                    tool_result = await gmail_client.execute(
                        result.selected_tool, result.tool_arguments
                    )
                    result.execution_result = (
                        tool_result.output if tool_result.success else None
                    )
                    if not tool_result.success:
                        result.error = tool_result.error

    except MCPException as e:
        result.error = str(e)
    except Exception as e:  # noqa: BLE001 — surfaced via the responder, not raised raw
        result.error = str(e)

    result.final_response = await generate_response(
        llm, request.message, result.execution_result, result.error
    )
    history.append({"role": "assistant", "content": result.final_response})

    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)