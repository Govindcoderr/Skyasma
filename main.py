from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from src.graph.workflow import Workflow
from api.schemas import ChatRequest, ChatResponse, HealthResponse


_workflow: Workflow | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _workflow
    _workflow = Workflow()
    yield
    if _workflow is not None:
        await _workflow.aclose()


app = FastAPI(
    title="Multi-Agent MCP Orchestrator",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if _workflow is None:
        raise HTTPException(status_code=503, detail="Workflow not ready")

    try:
        result = await _workflow.ainvoke(
            request.message,
            session_id=request.session_id,
            thread_id=request.thread_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return ChatResponse(
        intent=result.get("intent"),
        confidence=result.get("confidence"),
        plan=result.get("plan", []),
        selected_server=result.get("selected_server"),
        selected_capability=result.get("selected_capability"),
        execution_result=result.get("execution_result"),
        final_response=result.get("final_response"),
        error=result.get("error"),
    )