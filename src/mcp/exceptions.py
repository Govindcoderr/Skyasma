class MCPException(Exception):
    """Base MCP exception."""


class MCPConnectionError(MCPException):
    """Unable to connect to MCP server."""


class MCPTimeoutError(MCPException):
    """Server timeout."""


class MCPToolNotFound(MCPException):
    """Requested tool doesn't exist."""


class MCPExecutionError(MCPException):
    """Tool execution failed."""