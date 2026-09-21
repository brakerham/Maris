"""Typed, post-commit in-process event notifications."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Literal

from wife_system.host.contracts import EventEnvelope


LOGGER = logging.getLogger("wife_system.host.events")
EventType = Literal[
    "agent.run_status_changed@1",
    "memory.changed@1",
    "module.setting_changed@1",
    "auth.session_revoked@1",
]


EventHandler = Callable[[EventEnvelope], None]


class InProcessEventBus:
    """Synchronous hints published only after the caller commits its fact."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: EventEnvelope) -> None:
        for handler in tuple(self._handlers.get(event.event_type, ())):
            try:
                handler(event)
            except Exception as exc:  # notification failures never alter committed facts
                LOGGER.error(
                    json.dumps(
                        {
                            "event": "host_event_handler_failed",
                            "event_id": str(event.event_id),
                            "event_type": event.event_type,
                            "handler_type": type(handler).__name__,
                            "error_type": type(exc).__name__,
                        },
                        separators=(",", ":"),
                    )
                )
