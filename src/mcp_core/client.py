from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from typing import Any

from src.mcp_core import ClientSession
from src.mcp_core import StdioServerParameters
from src.mcp_core.client.stdio import stdio_client

from src.mcp_core.schemas import (
    MCPServerConfig,
    MCPTool,
    MCPParameter,
    MCPToolResult,
)

from mcp.exceptions import (
    MCPConnectionError,
    MCPExecutionError,
)


class MCPClient:

    """
    Generic MCP Client.

    One instance connects to ONE MCP Server.

    Example:
        Gmail MCP
        GitHub MCP
        Slack MCP

    """

    def __init__(self, config: MCPServerConfig):

        self.config = config
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        self.connected = False


    # CONNECT
    async def connect(self):

        if self.connected:
            return

        params = StdioServerParameters(
            command=self.config.command,
            args=self.config.args,
            env=self.config.env,
        )

        try:

            read_stream, write_stream = (
                await self.exit_stack.enter_async_context(
                    stdio_client(params)
                )
            )

            self.session = await self.exit_stack.enter_async_context(
                ClientSession(
                    read_stream,
                    write_stream,
                )
            )

            await self.session.initialize()

            self.connected = True

        except Exception as e:

            raise MCPConnectionError(
                str(e)
            ) from e

    ###############################################################
    # DISCONNECT
    ###############################################################

    async def disconnect(self):

        await self.exit_stack.aclose()

        self.connected = False

    ###############################################################
    # LIST TOOLS
    ###############################################################

    async def list_tools(

        self,

    ) -> list[MCPTool]:

        if not self.connected:

            await self.connect()

        result = await self.session.list_tools()

        tools = []

        for tool in result.tools:

            params = []

            schema = tool.inputSchema or {}

            properties = schema.get(
                "properties",
                {},
            )

            required = schema.get(
                "required",
                [],
            )

            for name, info in properties.items():

                params.append(

                    MCPParameter(
                        name=name,
                        type=info.get(
                            "type",
                            "string",
                        ),
                        description=info.get(
                            "description",
                            "",
                        ),
                        required=name in required,
                    )

                )

            tools.append(

                MCPTool(
                    server=self.config.name,
                    name=tool.name,
                    description=tool.description or "",
                    parameters=params,
                )

            )

        return tools

    ###############################################################
    # EXECUTE TOOL
    ###############################################################

    async def execute(

        self,

        tool_name: str,

        arguments: dict[str, Any],

    ) -> MCPToolResult:

        if not self.connected:

            await self.connect()

        try:

            result = await self.session.call_tool(

                tool_name,

                arguments=arguments,

            )

            output = []

            for item in result.content:

                if hasattr(item, "text"):
                    output.append(item.text)

                else:
                    output.append(str(item))

            return MCPToolResult(

                success=True,

                output="\n".join(output),

            )

        except Exception as e:

            raise MCPExecutionError(
                str(e)

            ) from e