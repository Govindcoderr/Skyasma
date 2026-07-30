from __future__ import annotations

from contextlib import asynccontextmanager

from langgraph.checkpoint.redis.aio import AsyncRedisSaver

from config import settings


@asynccontextmanager
async def get_checkpointer():
    """
    Usage:
        async with get_checkpointer() as checkpointer:
            graph = WorkflowBuilder().build(checkpointer=checkpointer)
    """
    async with AsyncRedisSaver.from_conn_string(settings.REDIS_URL) as saver:
        await saver.asetup()
        yield saver