from __future__ import annotations

from config import settings, MCP_SERVERS
from src.mcp_core.client import MCPClient
from src.mcp_core.schemas import MCPServerConfig, MCPToolResult
from src.mcp_core.exceptions import MCPException
from src.llm.provider import get_llm
from src.llm.prompts import TOOL_SELECTION_PROMPT, render_tools
from src.llm.output_parser import parse_json, OutputParseError
from src.agents.state import AgentState

from langchain_core.messages import SystemMessage, HumanMessage


# Which MCP server(s) handle which supervisor intent.
INTENT_SERVER_MAP: dict[str, list[str]] = {
    "send_email": ["gmail"],
    "reply_email": ["gmail"],
    "search_email": ["gmail"],
    "read_email": ["gmail"],
    "slack": ["slack"],
    "github": ["github"],
}

# One MCPClient per server, reused instead of reconnecting every call.
_clients: dict[str, MCPClient] = {}


def _get_client(server_name: str) -> MCPClient:
    if server_name not in _clients:
        cfg = MCP_SERVERS[server_name]
        _clients[server_name] = MCPClient(
            MCPServerConfig(
                name=server_name,
                command=cfg["command"],
                args=cfg.get("args", []),
                env=cfg.get("env", {}),
                timeout=settingsmcp_core_TIMEOUT,
            )
        )
    return _clients[server_name]


class ExecutorAgent:
    """Discovers tools for the classified intent, picks one via LLM, executes it."""

    def __init__(self):
        self.llm = get_llm()

    async def __call__(self, state: AgentState) -> AgentState:
        servers = INTENT_SERVER_MAP.get(state["intent"], [])

        if not servers:
            state["execution_result"] = None
            return state

        try:
            tools = await self._discover(servers)
            state["available_tools"] = tools

            if not tools:
                state["error"] = f"No tools available on server(s): {servers}"
                return state

            selection = await self._select_tool(state["user_input"], tools)

            if not selection.get("tool"):
                state["execution_result"] = None
                return state

            state["selected_server"] = selection["server"]
            state["selected_capability"] = selection["tool"]
            state["tool_arguments"] = selection.get("arguments", {})

            result = await self._execute(selection)

            state["tool_result"] = result.model_dump()
            state["execution_result"] = result.output if result.success else None

            if not result.success:
                state["error"] = result.error

        except MCPException as e:
            state["error"] = str(e)
            state["execution_result"] = None

        return state

    async def _discover(self, servers: list[str]):
        all_tools = []
        for server_name in servers:
            client = _get_client(server_name)
            all_tools.extend(await client.list_tools())
        return all_tools

    async def _select_tool(self, user_input: str, tools) -> dict:
        prompt = TOOL_SELECTION_PROMPT.format(
            tools=render_tools(tools), user_input=user_input
        )
        response = await self.llm.ainvoke(
            [SystemMessage(content="You output only JSON."), HumanMessage(content=prompt)]
        )
        try:
            return parse_json(response.content)
        except OutputParseError:
            return {"server": None, "tool": None, "arguments": {}}

    async def _execute(self, selection: dict) -> MCPToolResult:
        client = _get_client(selection["server"])
        return await client.execute(selection["tool"], selection.get("arguments", {}))