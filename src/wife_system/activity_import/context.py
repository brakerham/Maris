"""Trusted application context; never constructed from an import request body."""

from __future__ import annotations

import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictStr, model_validator


class ImportIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    owner_id: uuid.UUID
    user_id: uuid.UUID | None = None
    # Keep the literal operation/channel/UUID namespace inside P1's 80 chars.
    channel: Annotated[StrictStr, Field(pattern=r"^[a-zA-Z0-9_.-]{1,19}$")]
    permissions: frozenset[str]

    @model_validator(mode="after")
    def normalize_user_id(self) -> "ImportIdentity":
        if self.user_id is None:
            object.__setattr__(self, "user_id", self.owner_id)
        elif self.user_id != self.owner_id:
            raise ValueError("user_id must equal owner_id")
        return self
