from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wife_system.activity_import.context import ImportIdentity
from wife_system.activity_import.schemas import CommitRequest, Decision
from wife_system.activity_import.service import ActivityImportService
from wife_system.api.app import create_app
from wife_system.finance.db import Base, make_engine, make_session_factory
from wife_system.finance.service import FinanceService, IdempotencyKeys
from wife_system.host.auth.models import AppUser


OWNER = uuid.UUID("81000000-0000-0000-0000-000000000001")
OTHER_OWNER = uuid.UUID("81000000-0000-0000-0000-000000000002")
KEYS = IdempotencyKeys({1: b"p3-c9-independent-virtual-key"})


def trusted_identity(owner: uuid.UUID = OWNER, *, permissions: frozenset[str] | None = None) -> ImportIdentity:
    return ImportIdentity(
        owner_id=owner,
        channel="p3-c9-independent",
        permissions=permissions or frozenset({"finance:read", "finance:write"}),
    )


def commit_payload(preview, *, accepted: set[int] | None = None) -> CommitRequest:
    accepted = set(range(1, len(preview.candidates) + 1)) if accepted is None else accepted
    return CommitRequest(
        confirmed=True,
        batch_version=preview.batch_version,
        content_digest=preview.content_digest,
        decisions=[
            Decision(
                candidate_id=row.candidate_id,
                decision="accept" if row.ordinal in accepted else "skip",
                expected_action=row.proposed_action,
                expected_template_version=row.target_expected_version,
                acknowledged_warning_codes=sorted(
                    {issue.code for issue in row.issues if issue.severity == "warning"}
                ),
            )
            for row in preview.candidates
        ],
    )


@pytest.fixture
def sqlite_stack(tmp_path: Path):
    engine = make_engine(f"sqlite+pysqlite:///{tmp_path / 'p3-c9.sqlite3'}")
    Base.metadata.create_all(engine)
    sessions = make_session_factory(engine)
    with sessions() as session, session.begin():
        session.add_all([
            AppUser(id=OWNER, handle="virtual_owner", status="active", bootstrap_marker="primary"),
            AppUser(id=OTHER_OWNER, handle="virtual_other", status="active", bootstrap_marker=None),
        ])
    imports = ActivityImportService(sessions, KEYS)
    finance = FinanceService(sessions, KEYS, user_id=OWNER)
    yield imports, finance, sessions
    engine.dispose()


@pytest.fixture
def http_stack(tmp_path: Path):
    engine = make_engine(f"sqlite+pysqlite:///{tmp_path / 'p3-c9-http.sqlite3'}")
    Base.metadata.create_all(engine)
    sessions = make_session_factory(engine)
    with sessions() as session, session.begin():
        session.add(AppUser(id=OWNER, handle="virtual_owner", status="active", bootstrap_marker="primary"))
    service = ActivityImportService(sessions, KEYS)
    app = create_app(activity_import_service=service, activity_import_identity=trusted_identity())
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, sessions
    engine.dispose()
