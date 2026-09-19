from __future__ import annotations

import re
import unicodedata
import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator

Action = Literal["create", "revise", "unchanged", "conflict", "unresolved"]
PositiveInt = Annotated[StrictInt, Field(ge=1)]
Minor = Annotated[StrictInt, Field(ge=0, le=999_999_999_999)]
Digest = Annotated[StrictStr, Field(pattern=r"^hmac-sha256:v[0-9]+:[0-9a-f]{64}$")]
SafeCode = Annotated[StrictStr, Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")]


class ImportModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImportIssue(ImportModel):
    code: SafeCode
    severity: Literal["warning", "error"]
    field: SafeCode
    line: PositiveInt


def unsafe_unicode(value: str) -> bool:
    return any(
        (ord(char) < 32 and char not in "\n\t")
        or 0xD800 <= ord(char) <= 0xDFFF
        or ord(char) in {0x061C, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E, 0x2066, 0x2067, 0x2068, 0x2069}
        for char in value
    )


class PreviewRequest(ImportModel):
    markdown: StrictStr
    source_label: Annotated[StrictStr, Field(max_length=120)] | None = None

    @field_validator("source_label")
    @classmethod
    def basename_only(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if unsafe_unicode(value) or "\n" in value or "\r" in value or "\t" in value:
            raise ValueError("invalid source label")
        if re.search(r"[<>]|\]\(|[a-zA-Z][a-zA-Z0-9+.-]*://", value):
            raise ValueError("invalid source label")
        # Pure string processing, including Windows paths on every platform.
        basic = unicodedata.normalize("NFC", value.replace("\\", "/").rsplit("/", 1)[-1]).strip()
        if basic in {".", ".."} or ":" in basic:
            raise ValueError("invalid source label")
        return basic


class Decision(ImportModel):
    candidate_id: uuid.UUID
    decision: Literal["accept", "skip"]
    expected_action: Action
    expected_template_version: PositiveInt | None
    acknowledged_warning_codes: list[SafeCode]


class CommitRequest(ImportModel):
    confirmed: Literal[True]
    batch_version: PositiveInt
    content_digest: Digest
    decisions: list[Decision]

    @field_validator("confirmed", mode="before")
    @classmethod
    def explicit_true(cls, value: object) -> bool:
        if value is not True:
            raise ValueError("explicit confirmation is required")
        return True


class CandidateView(ImportModel):
    candidate_id: uuid.UUID
    ordinal: PositiveInt
    source_heading: Annotated[StrictStr, Field(min_length=1, max_length=120)]
    source_line_start: PositiveInt
    source_line_end: PositiveInt
    name_normalized: StrictStr
    currency: Literal["CNY"] = "CNY"
    reference_minor: Minor | None = None
    reference_min_minor: Minor | None = None
    reference_max_minor: Minor | None = None
    proposed_action: Action
    target_template_id: uuid.UUID | None = None
    target_expected_version: PositiveInt | None = None
    issues: list[ImportIssue] = Field(default_factory=list)
    decision: Literal["accepted", "skipped"] | None = None
    result_template_id: uuid.UUID | None = None
    result_version: PositiveInt | None = None


class CandidateResult(ImportModel):
    candidate_id: uuid.UUID
    decision: Literal["accepted", "skipped"]
    template_id: uuid.UUID | None = None
    template_version: PositiveInt | None = None


class PreviewResponse(ImportModel):
    request_id: uuid.UUID
    batch_id: uuid.UUID
    batch_version: PositiveInt
    status: Literal["previewed", "committed"]
    parser_version: Literal["activity-md-v1"] = "activity-md-v1"
    content_digest: Digest
    replayed: bool = False
    candidates: list[CandidateView]
    results: list[CandidateResult] = Field(default_factory=list)


class BatchResponse(PreviewResponse):
    pass


class CommitResponse(ImportModel):
    request_id: uuid.UUID
    batch_id: uuid.UUID
    batch_version: PositiveInt
    status: Literal["committed"]
    replayed: bool = False
    results: list[CandidateResult]
