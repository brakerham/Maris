"""Endpoint- and user-bound opaque cursor codec."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime


class InvalidCursorError(ValueError):
    pass


class CursorCodec:
    def __init__(self, secret: bytes) -> None:
        if len(secret) < 32:
            raise ValueError("cursor secret must contain at least 32 bytes")
        self._secret = secret

    def encode(
        self,
        *,
        endpoint: str,
        user_id: uuid.UUID,
        sort_time: datetime,
        item_id: uuid.UUID,
    ) -> str:
        payload = json.dumps(
            {
                "endpoint": endpoint,
                "user_id": str(user_id),
                "sort_time": sort_time.isoformat(),
                "item_id": str(item_id),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        signature = hmac.new(self._secret, b"wife.cursor.v1\0" + payload, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(payload + signature).decode().rstrip("=")

    def decode(self, value: str, *, endpoint: str, user_id: uuid.UUID) -> tuple[datetime, uuid.UUID]:
        if not isinstance(value, str) or not value or len(value) > 512:
            raise InvalidCursorError("invalid_cursor")
        try:
            raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
            payload, signature = raw[:-32], raw[-32:]
            expected = hmac.new(self._secret, b"wife.cursor.v1\0" + payload, hashlib.sha256).digest()
            if not hmac.compare_digest(signature, expected):
                raise InvalidCursorError("invalid_cursor")
            decoded = json.loads(payload)
            if decoded["endpoint"] != endpoint or decoded["user_id"] != str(user_id):
                raise InvalidCursorError("invalid_cursor")
            return datetime.fromisoformat(decoded["sort_time"]), uuid.UUID(decoded["item_id"])
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
            if isinstance(exc, InvalidCursorError):
                raise
            raise InvalidCursorError("invalid_cursor") from exc
