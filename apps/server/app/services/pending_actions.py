import json
import time
from typing import Any

import redis

from app.core.config import settings


class PendingActionStore:
    def __init__(self) -> None:
        self._memory: dict[str, tuple[float, dict[str, Any]]] = {}
        try:
            self._redis = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            self._redis.ping()
        except Exception:
            self._redis = None

    @staticmethod
    def key(user_id: int, bot_id: str) -> str:
        return f"bot:pending_action:{user_id}:{bot_id}"

    def set(self, user_id: int, bot_id: str, value: dict[str, Any], ttl: int = 300) -> None:
        key = self.key(user_id, bot_id)
        if self._redis:
            self._redis.setex(key, ttl, json.dumps(value))
            return
        self._memory[key] = (time.time() + ttl, value)

    def get(self, user_id: int, bot_id: str) -> dict[str, Any] | None:
        key = self.key(user_id, bot_id)
        if self._redis:
            raw = self._redis.get(key)
            return json.loads(raw) if raw else None
        item = self._memory.get(key)
        if not item:
            return None
        expires_at, value = item
        if expires_at < time.time():
            self._memory.pop(key, None)
            return None
        return value

    def delete(self, user_id: int, bot_id: str) -> None:
        key = self.key(user_id, bot_id)
        if self._redis:
            self._redis.delete(key)
            return
        self._memory.pop(key, None)


pending_actions = PendingActionStore()

