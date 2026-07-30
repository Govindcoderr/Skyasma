from dotenv import load_dotenv
from dataclasses import dataclass
import os

load_dotenv()


@dataclass(frozen=True)
class Settings:

    #############################
    # LLM
    #############################

    MODEL_NAME: str = os.getenv(
        "MODEL_NAME",
        "gpt-4.1"
    )

    OPENAI_API_KEY: str = os.getenv(
        "OPENAI_API_KEY",
        ""
    )

    TEMPERATURE: float = float(
        os.getenv(
            "TEMPERATURE",
            "0"
        )
    )

    #############################
    # LangGraph
    #############################

    THREAD_ID: str = os.getenv(
        "THREAD_ID",
        "default"
    )

    #############################
    # Logging
    #############################

    LOG_LEVEL: str = os.getenv(
        "LOG_LEVEL",
        "INFO"
    )

    #############################
    # Streaming
    #############################

    STREAMING: bool = True

    #############################
    # MCP
    #############################

    MCP_TIMEOUT: int = 30

    MCP_DISCOVERY_TIMEOUT: int = 10


    ##################################################
# MCP SERVERS
##################################################

MCP_SERVERS = {

    "gmail": {
        "command": "python",
        "args": [
            "servers/gmail/server.py"
        ]
    },

    "github": {
        "command": "python",
        "args": [
            "servers/github/server.py"
        ]
    },

    "slack": {
        "command": "python",
        "args": [
            "servers/slack/server.py"
        ]
    }

}


settings = Settings()