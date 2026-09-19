"""Stable public failures; never retain input or database exception text."""

_ERRORS: dict[str, tuple[int, bool, str]] = {
    "batch_not_found": (404, False, "Import batch was not found."),
    "duplicate_request_conflict": (409, False, "The request key has a different payload."),
    "import_content_mismatch": (409, False, "The import content no longer matches."),
    "concurrent_modification": (409, True, "The activity changed; create a new preview."),
    "candidate_not_actionable": (409, False, "This candidate cannot be accepted."),
    "unacknowledged_warning": (409, False, "Warning acknowledgements must match exactly."),
    "import_already_committed": (409, False, "This import batch was already committed."),
    "import_text_too_large": (413, False, "The import exceeds the text limit."),
    "invalid_content_type": (415, False, "A UTF-8 application/json request is required."),
    "invalid_request": (422, False, "The import request is invalid."),
    "invalid_markdown_structure": (422, False, "The Markdown structure is invalid."),
    "import_candidate_limit_exceeded": (422, False, "The import exceeds the candidate limit."),
    "invalid_candidate_selection": (422, False, "Each candidate must be selected exactly once."),
    "invalid_amount_precision": (422, False, "The amount format or precision is invalid."),
    "amount_out_of_range": (422, False, "The amount is outside the allowed range."),
    "unsupported_currency": (422, False, "Only the supported currency is allowed."),
    "database_unavailable": (503, True, "The database is temporarily unavailable."),
    "persistence_error": (500, True, "The import could not be saved."),
}


class ActivityImportError(Exception):
    def __init__(self, code: str, status_code: int | None = None, retryable: bool | None = None):
        status, retry, message = _ERRORS[code]
        self.code = code
        self.status_code = status if status_code is None else status_code
        self.retryable = retry if retryable is None else retryable
        self.safe_message = message
        super().__init__(message)
