"""Offline preview and atomic activity-template import orchestration."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from typing import Any, TypeVar

from pydantic import TypeAdapter
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.exc import StaleDataError

from wife_system.finance.errors import FinanceError
from wife_system.finance.models import (
    ActivityImportBatch,
    ActivityImportCandidate,
    ActivityTemplate,
    ActivityTemplateRevision,
    CommandReceipt,
    utc_now,
)
from wife_system.finance.service import FinanceService, IdempotencyKeys, _canonical

from .context import ImportIdentity
from .errors import ActivityImportError
from .parser import PARSER_VERSION, parse_markdown
from .repository import ImportRepository
from .schemas import (
    BatchResponse,
    CommitRequest,
    CommitResponse,
    ImportIssue,
    PreviewRequest,
    PreviewResponse,
)

LOGGER = logging.getLogger("wife_system.activity_import")
R = TypeVar("R")
ISSUES = TypeAdapter(list[ImportIssue])


@dataclass(frozen=True)
class _ReceiptSource:
    source_system: str
    source_event_id: str


def validate_idempotency_key(value: str) -> str:
    if not isinstance(value, str):
        raise ActivityImportError("invalid_request")
    value = value.strip()
    if not 1 <= len(value) <= 256 or any(not 32 <= ord(char) <= 126 for char in value):
        raise ActivityImportError("invalid_request")
    return value


def _require(identity: ImportIdentity, permission: str) -> None:
    if permission not in identity.permissions:
        raise ActivityImportError("invalid_request")


class ActivityImportService:
    def __init__(self, sessions: sessionmaker[Session], keys: IdempotencyKeys) -> None:
        self._sessions = sessions
        self._keys = keys
        self._finance = FinanceService(sessions, keys)

    def _digest(self, domain: str, value: str) -> str:
        version = self._keys.current_version
        digest = hmac.new(
            self._keys.current(),
            f"{domain}:v{version}\0".encode() + value.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"hmac-sha256:v{version}:{digest}"

    @staticmethod
    def _emit(**fields: Any) -> None:
        LOGGER.info(json.dumps(fields, separators=(",", ":"), ensure_ascii=False))

    def _run(self, request_id: uuid.UUID, operation: Callable[[], R]) -> R:
        started = monotonic()
        try:
            return operation()
        except ActivityImportError as exc:
            error = exc
        except FinanceError as exc:
            code = exc.code if exc.code in {
                "duplicate_request_conflict",
                "concurrent_modification",
                "database_unavailable",
                "persistence_error",
            } else "concurrent_modification"
            error = ActivityImportError(code)
        except StaleDataError:
            error = ActivityImportError("concurrent_modification")
        except OperationalError as exc:
            sqlstate = getattr(exc.orig, "sqlstate", None)
            code = "concurrent_modification" if sqlstate in {"40001", "40P01"} else "database_unavailable"
            error = ActivityImportError(code)
        except IntegrityError as exc:
            constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
            name_race = constraint == "uq_activity_template_name_normalized"
            if getattr(exc.orig, "sqlite_errorname", None) == "SQLITE_CONSTRAINT_UNIQUE":
                name_race = "activity_template.name_normalized" in str(exc.orig)
            error = ActivityImportError("concurrent_modification" if name_race else "persistence_error")
        except DBAPIError:
            error = ActivityImportError("persistence_error")
        except Exception:
            error = ActivityImportError("persistence_error")
        self._emit(
            request_id=str(request_id),
            error_code=error.code,
            duration_ms=round((monotonic() - started) * 1000, 3),
        )
        raise error from None

    def _claim(
        self,
        session: Session,
        identity: ImportIdentity,
        key: str,
        operation: str,
        payload: dict[str, Any],
    ) -> tuple[CommandReceipt, bool]:
        source = _ReceiptSource(
            f"activity_import.{operation}:{identity.channel}:{identity.owner_id}",
            key,
        )
        return self._finance._claim(session, source, f"activity_import.{operation}", payload)  # type: ignore[arg-type]

    @staticmethod
    def _save_receipt(
        session: Session,
        receipt: CommandReceipt,
        outcome: PreviewResponse | CommitResponse,
    ) -> None:
        receipt.result_type = "activity_import_batch"
        receipt.result_id = outcome.batch_id
        receipt.result_json = outcome.model_dump_json()
        receipt.completed_at = utc_now()
        session.flush()

    @staticmethod
    def _candidate_view(row: ActivityImportCandidate) -> dict[str, Any]:
        issues = ISSUES.validate_json(row.issues_json)
        return {
            "candidate_id": row.id,
            "ordinal": row.ordinal,
            "source_heading": row.source_heading,
            "source_line_start": row.source_line_start,
            "source_line_end": row.source_line_end,
            "name_normalized": row.name_normalized,
            "currency": row.currency,
            "reference_minor": row.reference_minor,
            "reference_min_minor": row.reference_min_minor,
            "reference_max_minor": row.reference_max_minor,
            "proposed_action": row.proposed_action,
            "target_template_id": row.target_template_id,
            "target_expected_version": row.target_expected_version,
            "issues": issues,
            "decision": {"accept": "accepted", "skip": "skipped"}.get(row.decision),
            "result_template_id": row.result_template_id,
            "result_version": row.result_template_version,
        }

    @staticmethod
    def _results(rows: list[ActivityImportCandidate]) -> list[dict[str, Any]]:
        return [
            {
                "candidate_id": row.id,
                "decision": "accepted" if row.decision == "accept" else "skipped",
                "template_id": row.result_template_id,
                "template_version": row.result_template_version,
            }
            for row in rows
            if row.decision is not None
        ]

    def _view(
        self,
        request_id: uuid.UUID,
        batch: ActivityImportBatch,
        rows: list[ActivityImportCandidate],
        *,
        preview: bool = False,
    ) -> BatchResponse | PreviewResponse:
        response = {
            "request_id": request_id,
            "batch_id": batch.id,
            "batch_version": batch.version_id,
            "status": batch.status,
            "parser_version": batch.parser_version,
            "content_digest": batch.content_digest,
            "replayed": False,
            "candidates": [self._candidate_view(row) for row in rows],
            "results": self._results(rows),
        }
        return PreviewResponse(**response) if preview else BatchResponse(**response)

    def preview(
        self,
        identity: ImportIdentity,
        payload: PreviewRequest,
        idempotency_key: str,
        *,
        request_id: uuid.UUID | None = None,
    ) -> PreviewResponse:
        request_id = request_id or uuid.uuid4()

        def work() -> PreviewResponse:
            _require(identity, "finance:write")
            key = validate_idempotency_key(idempotency_key)
            document = parse_markdown(payload.markdown)
            content_digest = self._digest("p3-content", document.normalized_markdown)
            fingerprint_payload = {
                "content_digest": content_digest,
                "source_label": payload.source_label,
            }
            with self._sessions() as session, session.begin():
                receipt, replayed = self._claim(session, identity, key, "preview", fingerprint_payload)
                if replayed:
                    stored = PreviewResponse.model_validate_json(receipt.result_json or "{}")
                    return stored.model_copy(update={"replayed": True})
                batch = ActivityImportBatch(
                    owner_id=identity.owner_id,
                    status="previewed",
                    parser_version=PARSER_VERSION,
                    source_label=payload.source_label,
                    content_key_version=self._keys.current_version,
                    content_digest=content_digest,
                    preview_receipt_id=receipt.id,
                    version_id=1,
                )
                session.add(batch)
                session.flush()
                repository = ImportRepository(session)
                historical_names = repository.historical_name_index()
                rows: list[ActivityImportCandidate] = []
                for candidate in document.candidates:
                    action, target_id, target_version = "create", None, None
                    matches = repository.named_templates(candidate.name_normalized)
                    historical_ids = historical_names.get(candidate.name_normalized, set())
                    if candidate.duplicate_name:
                        action = "conflict"
                    elif candidate.unresolved:
                        action = "unresolved"
                    elif (
                        len(matches) > 1
                        or (matches and matches[0].archived_at is not None)
                        or (not matches and historical_ids)
                        or (matches and historical_ids - {matches[0].id})
                    ):
                        action = "conflict"
                    elif matches:
                        template = matches[0]
                        revision = session.get(ActivityTemplateRevision, template.current_revision_id)
                        if revision is None:
                            action = "conflict"
                        else:
                            target_id, target_version = template.id, template.version_id
                            identical = (
                                revision.name == candidate.source_heading
                                and revision.reference_minor == candidate.reference_minor
                                and revision.reference_min_minor == candidate.reference_min_minor
                                and revision.reference_max_minor == candidate.reference_max_minor
                            )
                            action = "unchanged" if identical else "revise"
                    row = ActivityImportCandidate(
                        batch_id=batch.id,
                        ordinal=candidate.ordinal,
                        source_heading=candidate.source_heading,
                        source_line_start=candidate.source_line_start,
                        source_line_end=candidate.source_line_end,
                        block_digest=self._digest("p3-block", candidate.block_text),
                        name_normalized=candidate.name_normalized,
                        currency="CNY",
                        reference_minor=candidate.reference_minor,
                        reference_min_minor=candidate.reference_min_minor,
                        reference_max_minor=candidate.reference_max_minor,
                        proposed_action=action,
                        target_template_id=target_id,
                        target_expected_version=target_version,
                        issues_json=json.dumps(
                            [issue.model_dump(mode="json") for issue in candidate.issues],
                            separators=(",", ":"),
                            ensure_ascii=False,
                        ),
                    )
                    session.add(row)
                    rows.append(row)
                session.flush()
                outcome = self._view(request_id, batch, rows, preview=True)
                assert isinstance(outcome, PreviewResponse)
                self._save_receipt(session, receipt, outcome)
            self._emit(
                request_id=str(request_id),
                batch_id=str(batch.id),
                parser_version=PARSER_VERSION,
                digest_prefix=content_digest.rsplit(":", 1)[-1][:12],
                candidate_count=len(rows),
                action_counts=dict(Counter(row.proposed_action for row in rows)),
                replayed=False,
            )
            return outcome

        return self._run(request_id, work)

    def get(
        self,
        identity: ImportIdentity,
        batch_id: uuid.UUID,
        *,
        request_id: uuid.UUID | None = None,
    ) -> BatchResponse:
        request_id = request_id or uuid.uuid4()

        def work() -> BatchResponse:
            _require(identity, "finance:read")
            with self._sessions() as session:
                repository = ImportRepository(session)
                batch = repository.batch(batch_id, identity.owner_id)
                if batch is None:
                    raise ActivityImportError("batch_not_found")
                result = self._view(request_id, batch, repository.candidates(batch.id))
                assert isinstance(result, BatchResponse)
                return result

        return self._run(request_id, work)

    @staticmethod
    def _selection_payload(batch_id: uuid.UUID, payload: CommitRequest) -> dict[str, Any]:
        values = payload.model_dump(mode="json")
        for decision in values["decisions"]:
            decision["acknowledged_warning_codes"] = sorted(decision["acknowledged_warning_codes"])
        values["decisions"].sort(key=lambda decision: decision["candidate_id"])
        return {"batch_id": str(batch_id), **values}

    @staticmethod
    def _validate_selection(
        batch: ActivityImportBatch,
        rows: list[ActivityImportCandidate],
        payload: CommitRequest,
    ) -> dict[uuid.UUID, Any]:
        if batch.content_digest != payload.content_digest:
            raise ActivityImportError("import_content_mismatch")
        if batch.version_id != payload.batch_version:
            raise ActivityImportError("concurrent_modification")
        decisions = {decision.candidate_id: decision for decision in payload.decisions}
        if len(decisions) != len(payload.decisions) or set(decisions) != {row.id for row in rows}:
            raise ActivityImportError("invalid_candidate_selection")
        accepted_names: set[str] = set()
        accepted_targets: set[uuid.UUID] = set()
        for row in rows:
            decision = decisions[row.id]
            if decision.expected_action != row.proposed_action:
                raise ActivityImportError("invalid_candidate_selection")
            if decision.expected_template_version != row.target_expected_version:
                raise ActivityImportError("concurrent_modification")
            issues = ISSUES.validate_json(row.issues_json)
            warning_codes = {issue.code for issue in issues if issue.severity == "warning"}
            codes = decision.acknowledged_warning_codes
            if len(codes) != len(set(codes)) or set(codes) != warning_codes:
                raise ActivityImportError("unacknowledged_warning")
            if decision.decision == "skip":
                continue
            if row.proposed_action not in {"create", "revise"} or any(
                issue.severity == "error" for issue in issues
            ):
                raise ActivityImportError("candidate_not_actionable")
            if row.name_normalized in accepted_names or (
                row.target_template_id is not None and row.target_template_id in accepted_targets
            ):
                raise ActivityImportError("invalid_candidate_selection")
            accepted_names.add(row.name_normalized)
            if row.target_template_id is not None:
                accepted_targets.add(row.target_template_id)
        return decisions

    def commit(
        self,
        identity: ImportIdentity,
        batch_id: uuid.UUID,
        payload: CommitRequest,
        idempotency_key: str,
        *,
        request_id: uuid.UUID | None = None,
    ) -> CommitResponse:
        request_id = request_id or uuid.uuid4()

        def work() -> CommitResponse:
            _require(identity, "finance:write")
            key = validate_idempotency_key(idempotency_key)
            selection = self._selection_payload(batch_id, payload)
            with self._sessions() as session, session.begin():
                receipt, replayed = self._claim(session, identity, key, "commit", selection)
                if replayed:
                    stored = CommitResponse.model_validate_json(receipt.result_json or "{}")
                    return stored.model_copy(update={"replayed": True})
                repository = ImportRepository(session)
                batch = repository.batch(batch_id, identity.owner_id, lock=True)
                if batch is None:
                    raise ActivityImportError("batch_not_found")
                if batch.status == "committed":
                    raise ActivityImportError("import_already_committed")
                rows = repository.candidates(batch.id)
                decisions = self._validate_selection(batch, rows, payload)
                accepted = [row for row in rows if decisions[row.id].decision == "accept"]
                targets = repository.lock_targets({
                    row.target_template_id
                    for row in accepted
                    if row.target_template_id is not None
                })
                current_history = repository.historical_name_index()
                for row in accepted:
                    if row.proposed_action == "create":
                        if (
                            repository.named_templates(row.name_normalized)
                            or current_history.get(row.name_normalized)
                        ):
                            raise ActivityImportError("concurrent_modification")
                    else:
                        template = targets.get(row.target_template_id)
                        if (
                            template is None
                            or template.archived_at is not None
                            or template.version_id != row.target_expected_version
                            or template.name_normalized != row.name_normalized
                            or current_history.get(row.name_normalized, set()) - {row.target_template_id}
                        ):
                            raise ActivityImportError("concurrent_modification")
                for row in rows:
                    if decisions[row.id].decision == "skip":
                        row.decision = "skip"
                        continue
                    arguments = {
                        "name": row.source_heading,
                        "reference_minor": row.reference_minor,
                        "reference_min_minor": row.reference_min_minor,
                        "reference_max_minor": row.reference_max_minor,
                        "source_import_candidate_id": row.id,
                    }
                    if row.proposed_action == "create":
                        result = self._finance._create_activity_template_in_session(
                            session, receipt, **arguments
                        )
                    else:
                        result = self._finance._revise_activity_template_in_session(
                            session,
                            receipt,
                            template=targets[row.target_template_id],
                            expected_version=row.target_expected_version,
                            **arguments,
                        )
                    row.decision = "accept"
                    row.result_template_id = result.result_id
                    row.result_template_version = result.version_id
                batch.status = "committed"
                batch.version_id += 1
                batch.commit_receipt_id = receipt.id
                batch.selection_fingerprint = hmac.new(
                    self._keys.current(),
                    b"p3-selection\0" + _canonical(selection),
                    hashlib.sha256,
                ).hexdigest()
                batch.committed_at = utc_now()
                session.flush()
                outcome = CommitResponse(
                    request_id=request_id,
                    batch_id=batch.id,
                    batch_version=batch.version_id,
                    status="committed",
                    replayed=False,
                    results=self._results(rows),
                )
                self._save_receipt(session, receipt, outcome)
            self._emit(
                request_id=str(request_id),
                batch_id=str(batch_id),
                accepted_count=len(accepted),
                replayed=False,
            )
            return outcome

        return self._run(request_id, work)
