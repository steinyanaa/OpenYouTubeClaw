"""Runtime event broadcasting for popup live status updates."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuntimeEventHub:
    """Broadcast lightweight runtime events to interested subscribers."""

    _subscribers: set[asyncio.Queue[dict[str, Any]]] = field(default_factory=set)
    _subscriber_loops: dict[asyncio.Queue[dict[str, Any]], asyncio.AbstractEventLoop] = field(
        default_factory=dict
    )

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        """Register one subscriber queue."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subscribers.add(queue)
        self._subscriber_loops[queue] = asyncio.get_running_loop()
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        """Remove one subscriber queue."""
        self._subscribers.discard(queue)
        self._subscriber_loops.pop(queue, None)

    async def publish(self, event: dict[str, Any]) -> None:
        """Fan out one event to all current subscribers."""
        current_loop = asyncio.get_running_loop()
        for queue in list(self._subscribers):
            with suppress(asyncio.QueueFull):
                target_loop = self._subscriber_loops.get(queue)
                if target_loop is not None and target_loop is not current_loop:
                    target_loop.call_soon_threadsafe(queue.put_nowait, dict(event))
                else:
                    queue.put_nowait(dict(event))
