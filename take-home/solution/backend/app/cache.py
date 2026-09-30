import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable, Hashable
from typing import Any

from cachetools import TTLCache

from .errors import UpstreamRateLimited


class AsyncTTLCache:
    """In-memory TTL cache for async fetches.

    Callers asking for the same key at the same time share one fetch (in-flight dedup),
    so the two weather endpoints loading a new city together only hit Open-Meteo once.
    Failed fetches are not cached.
    """

    def __init__(self, ttl_s: float, maxsize: int):
        self._data: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl_s)
        self._pending: dict[Hashable, asyncio.Task] = {}

    async def get(self, key: Hashable, fetch: Callable[[], Awaitable[Any]]) -> Any:
        if key in self._data:
            return self._data[key]
        task = self._pending.get(key)
        if task is None:
            task = asyncio.create_task(fetch())
            self._pending[key] = task
            task.add_done_callback(lambda t: self._finish(key, t))
        # shield: one caller disconnecting must not cancel a fetch others are waiting on
        return await asyncio.shield(task)

    def _finish(self, key: Hashable, task: asyncio.Task) -> None:
        self._pending.pop(key, None)
        if not task.cancelled() and task.exception() is None:
            self._data[key] = task.result()


class CallBudget:
    """Sliding 60-second count of upstream calls. Refuses before Open-Meteo would."""

    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self._calls: deque[float] = deque()

    def take(self) -> None:
        now = time.monotonic()
        while self._calls and now - self._calls[0] >= 60:
            self._calls.popleft()
        if len(self._calls) >= self.per_minute:
            wait = int(60 - (now - self._calls[0])) + 1
            raise UpstreamRateLimited(
                f"Too many weather lookups right now. Try again in {wait} s.", retry_after_s=wait
            )
        self._calls.append(now)
