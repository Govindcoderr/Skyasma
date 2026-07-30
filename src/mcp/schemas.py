"""
Core MCP Schemas

Shared across the entire system.

These classes are intentionally independent from
LangGraph so they can also be reused in REST APIs,
CLI applications, and tests.
"""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel, Field


# ==========================================================
# Tool Parameter
# ==========================================================

class MCPParameter(BaseModel):
    """
    Represents one input parameter for an MCP tool.
    """

    name: str

    type: str = "string"

    description: str = ""

    required: bool = False

    default: Optional[Any] = None


# ==========================================================
# Tool Definition
# ==========================================================

class MCPTool(BaseModel):
    """
    A tool discovered from an MCP server.
    """

    server: str

    name: str

    description: str

    parameters: List[MCPParameter] = Field(default_factory=list)

    metadata: Dict[str, Any] = Field(default_factory=dict)


# ==========================================================
# Tool Call
# ==========================================================

class MCPToolCall(BaseModel):

    tool_name: str

    arguments: Dict[str, Any] = Field(default_factory=dict)


# ==========================================================
# Tool Result
# ==========================================================

class MCPToolResult(BaseModel):

    success: bool

    output: Any = None

    error: Optional[str] = None

    execution_time: float = 0.0


# ==========================================================
# Discovery Response
# ==========================================================

class MCPDiscoveryResponse(BaseModel):

    server_name: str

    tools: List[MCPTool]


# ==========================================================
# Server Configuration
# ==========================================================

class MCPServerConfig(BaseModel):

    name: str

    command: str

    args: List[str] = Field(default_factory=list)

    env: Dict[str, str] = Field(default_factory=dict)

    timeout: int = 30

    enabled: bool = True


# ==========================================================
# Registry
# ==========================================================

class MCPRegistryState(BaseModel):

    servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)

    tools: Dict[str, MCPTool] = Field(default_factory=dict)


# ==========================================================
# Planner Output
# ==========================================================

class PlannerAction(BaseModel):

    capability: str

    tool: Optional[str] = None

    reason: str = ""


# ==========================================================
# Execution Request
# ==========================================================

class ExecutionRequest(BaseModel):

    server: str

    tool: str

    arguments: Dict[str, Any]


# ==========================================================
# Execution Response
# ==========================================================

class ExecutionResponse(BaseModel):

    success: bool

    data: Any = None

    error: Optional[str] = None
    