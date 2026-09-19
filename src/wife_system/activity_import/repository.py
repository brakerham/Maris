"""Session-scoped reads; transaction ownership stays with the import service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from wife_system.finance.models import (
    ActivityImportBatch,
    ActivityImportCandidate,
    ActivityTemplate,
    ActivityTemplateRevision,
)

from .parser import normalize_name


class ImportRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def batch(self, batch_id: uuid.UUID, owner_id: uuid.UUID, *, lock: bool = False) -> ActivityImportBatch | None:
        statement = select(ActivityImportBatch).where(
            ActivityImportBatch.id == batch_id,
            ActivityImportBatch.owner_id == owner_id,
        )
        if lock:
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def candidates(self, batch_id: uuid.UUID) -> list[ActivityImportCandidate]:
        return list(self.session.scalars(
            select(ActivityImportCandidate)
            .where(ActivityImportCandidate.batch_id == batch_id)
            .order_by(ActivityImportCandidate.ordinal)
        ))

    def named_templates(self, normalized: str) -> list[ActivityTemplate]:
        return list(self.session.scalars(
            select(ActivityTemplate).where(ActivityTemplate.name_normalized == normalized)
        ))

    def historical_name_index(self) -> dict[str, set[uuid.UUID]]:
        rows = self.session.execute(select(
            ActivityTemplateRevision.template_id,
            ActivityTemplateRevision.name,
        ))
        result: dict[str, set[uuid.UUID]] = {}
        for template_id, name in rows:
            result.setdefault(normalize_name(name), set()).add(template_id)
        return result

    def lock_targets(self, target_ids: set[uuid.UUID]) -> dict[uuid.UUID, ActivityTemplate]:
        if not target_ids:
            return {}
        rows = self.session.scalars(
            select(ActivityTemplate)
            .where(ActivityTemplate.id.in_(target_ids))
            .order_by(ActivityTemplate.id)
            .with_for_update()
        )
        return {row.id: row for row in rows}
