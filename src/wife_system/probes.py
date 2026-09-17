"""Probe creation and process-local idempotency, independent of HTTP."""

from __future__ import annotations

import secrets
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


SHANGHAI_TIMEZONE = timezone(timedelta(hours=8), name="Asia/Shanghai")


@dataclass(frozen=True)
class ProbeRecord:
    request_id: str
    challenge: str
    receipt: str
    created_at: datetime


@dataclass(frozen=True)
class ProbeResult:
    record: ProbeRecord
    replayed: bool


class DuplicateProbeRequestError(RuntimeError):
    """An idempotency key was reused with a different challenge."""

    def __init__(self, request_id: str) -> None:
        super().__init__("The idempotency key was already used for different input.")
        self.request_id = request_id


class InMemoryProbeStore:
    """Concurrency-safe probe storage for one Python process."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: dict[str, ProbeRecord] = {}

    def get_or_create(
        self,
        idempotency_key: str,
        challenge: str,
        create_record: Callable[[], ProbeRecord],
    ) -> ProbeResult:
        with self._lock:
            existing = self._records.get(idempotency_key)
            if existing is not None:
                if existing.challenge != challenge:
                    raise DuplicateProbeRequestError(existing.request_id)
                return ProbeResult(record=existing, replayed=True)

            record = create_record()
            self._records[idempotency_key] = record
            return ProbeResult(record=record, replayed=False)


class ProbeService:
    """Generate probe receipts while keeping idempotency outside the API route."""

    def __init__(
        self,
        store: InMemoryProbeStore | None = None,
        *,
        receipt_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = InMemoryProbeStore() if store is None else store
        self._receipt_factory = self._new_receipt if receipt_factory is None else receipt_factory
        self._clock = (lambda: datetime.now(SHANGHAI_TIMEZONE)) if clock is None else clock

    def create(
        self,
        *,
        idempotency_key: str,
        challenge: str,
        candidate_request_id: str | None = None,
    ) -> ProbeResult:
        request_id = candidate_request_id or str(uuid.uuid4())

        def build_record() -> ProbeRecord:
            created_at = self._clock()
            if created_at.tzinfo is None or created_at.utcoffset() is None:
                raise ValueError("Probe clock must return a timezone-aware datetime.")
            return ProbeRecord(
                request_id=request_id,
                challenge=challenge,
                receipt=self._receipt_factory(),
                created_at=created_at,
            )

        return self._store.get_or_create(idempotency_key, challenge, build_record)

    @staticmethod
    def _new_receipt() -> str:
        return f"POC-{secrets.token_hex(12)}"
