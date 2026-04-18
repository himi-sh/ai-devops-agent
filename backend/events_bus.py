import asyncio
import json
from typing import AsyncIterator


class EventBus:
    """In-process pub/sub for SSE broadcasts."""

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[str]] = []

    async def subscribe(self) -> AsyncIterator[str]:
        q: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        self._subscribers.append(q)
        try:
            while True:
                msg = await q.get()
                yield msg
        finally:
            self._subscribers.remove(q)

    def publish(self, event_type: str, data: dict) -> None:
        payload = json.dumps({"type": event_type, "data": data})
        for q in list(self._subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass


bus = EventBus()
