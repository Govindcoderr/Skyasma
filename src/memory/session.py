from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis

from config import settings


class SessionStore:
    def __init__(self, redis_url: str | None = None, ttl_seconds: int = 60 * 60 * 24):
        self.redis = redis.from_url(redis_url or settings.REDIS_URL, decode_responses=True)
        self.ttl_seconds = ttl_seconds

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    async def get(self, session_id: str) -> dict[str, Any]:
        raw = await self.redis.get(self._key(session_id))
        return json.loads(raw) if raw else {}

    async def save(self, session_id: str, data: dict[str, Any]) -> None:
        await self.redis.set(self._key(session_id), json.dumps(data), ex=self.ttl_seconds)

    async def update(self, session_id: str, **fields: Any) -> dict[str, Any]:
        data = await self.get(session_id)
        data.update(fields)
        await self.save(session_id, data)
        return data

    async def clear(self, session_id: str) -> None:
        await self.redis.delete(self._key(session_id))