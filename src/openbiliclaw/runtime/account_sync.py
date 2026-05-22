"""YouTube history sync — data arrives via extension yt_tasks, not periodic poll."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class SupportsAccountSyncState(Protocol):
    def load_account_sync_state(self) -> dict[str, object]: ...
    def save_account_sync_state(self, state: dict[str, object]) -> None: ...


@dataclass
class AccountSyncService:
    """No-op compatibility stub.

    YouTube watch history, playlists, and subscriptions arrive via the
    browser extension's YouTube task pipeline (``yt_tasks``), not through
    periodic API polling. This class keeps the runtime wiring intact
    while doing nothing on its own.
    """

    memory_manager: Any
    sync_interval_hours: int = 6
    check_interval_seconds: int = 300

    # Legacy constructor args — silently ignored.
    def __init__(self, memory_manager: Any = None, **_kwargs: Any) -> None:
        self.memory_manager = memory_manager
        self.check_interval_seconds = int(_kwargs.get("check_interval_seconds", 300))

    async def sync_if_due(self) -> dict[str, object]:
        return {"synced": False, "new_event_count": 0, "reason": "yt_tasks_pipeline"}

    async def sync_now(self) -> dict[str, object]:
        return {"synced": False, "new_event_count": 0, "reason": "yt_tasks_pipeline"}

    def get_runtime_status(self) -> dict[str, object]:
        state: dict[str, object] = {}
        if self.memory_manager is not None:
            with suppress(Exception):
                state = self.memory_manager.load_account_sync_state()
        return {
            "last_account_sync_at": str(state.get("last_account_sync_at", "")),
            "last_account_sync_error": str(state.get("last_sync_error", "")),
        }

    async def run_forever(self) -> None:
        """Idle loop — YouTube data arrives push-based via extension tasks."""
        while True:
            await asyncio.sleep(self.check_interval_seconds)

    def _is_due(self, last_sync_at: str) -> bool:
        parsed = self._parse_iso_datetime(last_sync_at)
        if parsed is None:
            return True
        return datetime.now(tz=UTC) - parsed >= timedelta(hours=self.sync_interval_hours)

    @staticmethod
    def _parse_iso_datetime(value: str) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
