from __future__ import annotations

from mcp_core.schemas import MCPTool


def render_tools(tools: list[MCPTool]) -> str:
    if not tools:
        return "No tools available."

    lines = []
    for tool in tools:
        params = ", ".join(
            f"{p.name}{'*' if p.required else ''}: {p.type}" for p in tool.parameters
        )
        lines.append(f"- [{tool.server}] {tool.name}({params}) — {tool.description}")

    return "\n".join(lines)


TOOL_SELECTION_PROMPT = """
You are the Tool Selector.

Given the user's request and the list of available MCP tools below,
choose exactly ONE tool to call and produce its arguments.

Available tools:
{tools}

User request:
{user_input}

Return ONLY JSON in this shape:
{{
  "server": "<server name>",
  "tool": "<tool name>",
  "arguments": {{}}
}}

If no tool fits, return:
{{"server": null, "tool": null, "arguments": {{}}}}
"""

RESPONDER_PROMPT = """
You are the Responder Agent.

Turn the tool execution result (or the plain conversation, if no tool
was used) into a clear, friendly final answer for the user.

Do not mention tools, servers, or internal steps — just answer naturally.
"""