"""Trusted application context; never constructed from an import request body."""

from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictStr


class ImportIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    owner_id: uuid.UUID
    # Keep the literal operation/channel/UUID namespace inside P1's 80 chars.
    channel: Annotated[StrictStr, Field(pattern=r"^[a-zA-Z0-9_.-]{1,19}$")]
    permissions: frozenset[str]
