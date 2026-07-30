from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    thread_id: str = "default"


class ChatResponse(BaseModel):
    intent: Optional[str] = None
    confidence: Optional[float] = None
    plan: List[str] = Field(default_factory=list)
    selected_server: Optional[str] = None
    selected_capability: Optional[str] = None
    execution_result: Optional[Any] = None
    final_response: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "ok"