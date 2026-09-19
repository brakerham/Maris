from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from threading import Barrier

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from wife_system.activity_import.context import ImportIdentity
from wife_system.activity_import.errors import ActivityImportError
from wife_system.activity_import.schemas import CommitRequest, Decision, PreviewRequest
from wife_system.activity_import.service import ActivityImportService
from wife_system.finance.db import make_engine, make_session_factory
from wife_system.finance.models import (
    ActivityImportBatch,
    ActivityImportCandidate,
    ActivityTemplate,
    ActivityTemplateRevision,
    AuditEvent,
    CommandReceipt,
)
from wife_system.finance.schemas import ArchiveResource, CreateActivityTemplate, ReviseActivityTemplate
from wife_system.finance.service import FinanceService, IdempotencyKeys


OWNER = uuid.UUID("50000000-0000-0000-0000-000000000001")
KEYS = IdempotencyKeys({1: b"virtual-postgresql-import-key"})


def migration_config(database_url: str) -> Config:
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def isolated_url(raw_url: str, schema: str) -> str:
    parsed = make_url(raw_url)
    query = dict(parsed.query)
    query["options"] = f"-csearch_path={schema},public"
    return parsed.set(query=query).render_as_string(hide_password=False)


@dataclass
class Harness:
    raw_url: str
    schema: str
    admin: object
    sessions: sessionmaker[Session]
    imports: ActivityImportService
    finance: FinanceService


@pytest.fixture(scope="module")
def pg() -> Harness:
    raw_url = os.getenv("FINANCE_TEST_POSTGRES_URL")
    if not raw_url or make_url(raw_url).get_backend_name() != "postgresql":
        pytest.skip("FINANCE_TEST_POSTGRES_URL is required for P3 PostgreSQL evidence")
    schema = f"p3_b5_{uuid.uuid4().hex}"
    admin = make_engine(raw_url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    url = isolated_url(raw_url, schema)
    engine = None
    try:
        command.upgrade(migration_config(url), "head")
        engine = make_engine(url)
        sessions = make_session_factory(engine)
        yield Harness(
            raw_url=raw_url,
            schema=schema,
            admin=admin,
            sessions=sessions,
            imports=ActivityImportService(sessions, KEYS),
            finance=FinanceService(sessions, KEYS),
        )
    finally:
        if engine is not None:
            engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin.dispose()


def identity() -> ImportIdentity:
    return ImportIdentity(
        owner_id=OWNER,
        channel="postgresql",
        permissions=frozenset({"finance:read", "finance:write"}),
    )


def commit_payload(preview, *, accept: bool = True) -> CommitRequest:
    return CommitRequest(
        confirmed=True,
        batch_version=preview.batch_version,
        content_digest=preview.content_digest,
        decisions=[
            Decision(
                candidate_id=row.candidate_id,
                decision="accept" if accept else "skip",
                expected_action=row.proposed_action,
                expected_template_version=row.target_expected_version,
                acknowledged_warning_codes=sorted({
                    issue.code for issue in row.issues if issue.severity == "warning"
                }),
            )
            for row in preview.candidates
        ],
    )


def concurrent(callable_):
    barrier = Barrier(2)

    def run():
        barrier.wait(timeout=10)
        try:
            return ("ok", callable_())
        except ActivityImportError as exc:
            return (exc.code, exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run), pool.submit(run)]
        return [future.result(timeout=30) for future in futures]


def test_postgresql_concurrent_preview_same_key_writes_one_batch(pg: Harness) -> None:
    payload = PreviewRequest(markdown="## PG虚拟并发预览")
    outcomes = concurrent(lambda: pg.imports.preview(identity(), payload, "pg-preview-same"))
    assert [code for code, _ in outcomes] == ["ok", "ok"]
    results = [value for _, value in outcomes]
    assert len({result.batch_id for result in results}) == 1
    assert sorted(result.replayed for result in results) == [False, True]
    with pg.sessions() as session:
        assert session.scalar(select(func.count(ActivityImportBatch.id)).where(
            ActivityImportBatch.id == results[0].batch_id
        )) == 1


def test_postgresql_concurrent_commit_same_key_writes_once(pg: Harness) -> None:
    preview = pg.imports.preview(identity(), PreviewRequest(markdown="## PG虚拟同键确认"), "pg-commit-preview")
    payload = commit_payload(preview)
    outcomes = concurrent(lambda: pg.imports.commit(identity(), preview.batch_id, payload, "pg-commit-same"))
    assert [code for code, _ in outcomes] == ["ok", "ok"]
    results = [value for _, value in outcomes]
    assert len({result.results[0].template_id for result in results}) == 1
    assert sorted(result.replayed for result in results) == [False, True]


def test_postgresql_same_batch_different_keys_allows_one_commit(pg: Harness) -> None:
    preview = pg.imports.preview(identity(), PreviewRequest(markdown="## PG虚拟异键确认"), "pg-diff-preview")
    payload = commit_payload(preview)
    keys = iter(("pg-diff-a", "pg-diff-b"))
    key_lock = __import__("threading").Lock()

    def submit():
        with key_lock:
            key = next(keys)
        return pg.imports.commit(identity(), preview.batch_id, payload, key)

    outcomes = concurrent(submit)
    assert sorted(code for code, _ in outcomes) == ["import_already_committed", "ok"]
    with pg.sessions() as session:
        assert session.scalar(select(func.count(CommandReceipt.id)).where(
            CommandReceipt.command_name == "activity_import.commit",
            CommandReceipt.result_id == preview.batch_id,
        )) == 1


def test_postgresql_different_batches_same_name_create_race(pg: Harness) -> None:
    a = pg.imports.preview(identity(), PreviewRequest(markdown="## PG虚拟同名竞争"), "pg-name-preview-a")
    b = pg.imports.preview(identity(), PreviewRequest(markdown="## PG虚拟同名竞争"), "pg-name-preview-b")
    submissions = iter(((a, "pg-name-a"), (b, "pg-name-b")))
    lock = __import__("threading").Lock()

    def submit():
        with lock:
            current, key = next(submissions)
        return pg.imports.commit(identity(), current.batch_id, commit_payload(current), key)

    outcomes = concurrent(submit)
    assert sorted(code for code, _ in outcomes) == ["concurrent_modification", "ok"]
    with pg.sessions() as session:
        assert session.scalar(select(func.count(ActivityTemplate.id)).where(
            ActivityTemplate.name_normalized == "pg虚拟同名竞争"
        )) == 1


def test_postgresql_stale_and_archived_targets_are_rejected(pg: Harness) -> None:
    stale = pg.finance.create_activity_template(CreateActivityTemplate(
        source_system="p3-pg", source_event_id="stale-base", name="PG虚拟过期", reference_amount="1.00"
    ))
    stale_preview = pg.imports.preview(identity(), PreviewRequest(markdown="## PG虚拟过期\n- 参考金额：2.00 元"), "pg-stale-preview")
    pg.finance.revise_activity_template(ReviseActivityTemplate(
        source_system="p3-pg", source_event_id="stale-change", template_id=stale.result_id,
        expected_version=1, name="PG虚拟过期", reference_amount="3.00",
    ))
    with pytest.raises(ActivityImportError) as stale_error:
        pg.imports.commit(identity(), stale_preview.batch_id, commit_payload(stale_preview), "pg-stale-commit")
    assert stale_error.value.code == "concurrent_modification"

    archived = pg.finance.create_activity_template(CreateActivityTemplate(
        source_system="p3-pg", source_event_id="archive-base", name="PG虚拟归档后变更", reference_amount="1.00"
    ))
    archived_preview = pg.imports.preview(identity(), PreviewRequest(markdown="## PG虚拟归档后变更\n- 参考金额：2.00 元"), "pg-archive-preview")
    pg.finance.archive_activity_template(ArchiveResource(
        source_system="p3-pg", source_event_id="archive-change", resource_id=archived.result_id,
        expected_version=1, reason="虚拟并发归档",
    ))
    with pytest.raises(ActivityImportError) as archive_error:
        pg.imports.commit(identity(), archived_preview.batch_id, commit_payload(archived_preview), "pg-archive-commit")
    assert archive_error.value.code == "concurrent_modification"


def test_postgresql_mid_batch_fault_rolls_back_domain_and_receipt(pg: Harness, monkeypatch) -> None:
    preview = pg.imports.preview(identity(), PreviewRequest(markdown="## PG虚拟回滚甲\n## PG虚拟回滚乙"), "pg-rollback-preview")
    before_receipts: int
    with pg.sessions() as session:
        before_receipts = session.scalar(select(func.count(CommandReceipt.id))) or 0
    original = pg.imports._finance._create_activity_template_in_session
    calls = 0

    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ActivityImportError("persistence_error")
        return original(*args, **kwargs)

    monkeypatch.setattr(pg.imports._finance, "_create_activity_template_in_session", fail_second)
    with pytest.raises(ActivityImportError):
        pg.imports.commit(identity(), preview.batch_id, commit_payload(preview), "pg-rollback-commit")
    with pg.sessions() as session:
        assert session.scalar(select(func.count(ActivityTemplate.id)).where(
            ActivityTemplate.name_normalized.in_({"pg虚拟回滚甲", "pg虚拟回滚乙"})
        )) == 0
        assert session.scalar(select(func.count(CommandReceipt.id))) == before_receipts
        assert session.get(ActivityImportBatch, preview.batch_id).status == "previewed"
        assert all(row.decision is None for row in session.scalars(
            select(ActivityImportCandidate).where(ActivityImportCandidate.batch_id == preview.batch_id)
        ))


def test_postgresql_database_constraints_reject_duplicate_name_and_bad_range(pg: Harness) -> None:
    first = pg.finance.create_activity_template(CreateActivityTemplate(
        source_system="p3-pg", source_event_id="constraint-a", name="PG虚拟约束甲"
    ))
    second = pg.finance.create_activity_template(CreateActivityTemplate(
        source_system="p3-pg", source_event_id="constraint-b", name="PG虚拟约束乙"
    ))
    with pytest.raises(IntegrityError):
        with pg.sessions.begin() as session:
            session.get(ActivityTemplate, second.result_id).name_normalized = "pg虚拟约束甲"
            session.flush()
    with pytest.raises(IntegrityError):
        with pg.sessions.begin() as session:
            template = session.get(ActivityTemplate, first.result_id)
            revision = session.get(ActivityTemplateRevision, template.current_revision_id)
            revision.reference_minor = None
            revision.reference_min_minor = 200
            revision.reference_max_minor = 100
            session.flush()


def test_postgresql_empty_and_existing_p2_schemas_upgrade(pg: Harness) -> None:
    schema = f"p3_existing_{uuid.uuid4().hex}"
    with pg.admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    url = isolated_url(pg.raw_url, schema)
    template_id, revision_id = uuid.uuid4(), uuid.uuid4()
    try:
        config = migration_config(url)
        command.upgrade(config, "7f3e2d1c9a4b")
        engine = make_engine(url)
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO activity_template (id,current_revision_id,archived_at,created_at,version_id) "
                "VALUES (:id,NULL,NULL,CURRENT_TIMESTAMP,1)"
            ), {"id": template_id})
            connection.execute(text(
                "INSERT INTO activity_template_revision "
                "(id,template_id,revision_no,name,reference_minor,currency,created_at) "
                "VALUES (:id,:template,1,'PG 虚拟历史',456,'CNY',CURRENT_TIMESTAMP)"
            ), {"id": revision_id, "template": template_id})
            connection.execute(text(
                "UPDATE activity_template SET current_revision_id=:revision WHERE id=:template"
            ), {"revision": revision_id, "template": template_id})
        engine.dispose()
        command.upgrade(config, "head")
        engine = make_engine(url)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "c82d7a4f901e"
            assert connection.execute(text(
                "SELECT reference_minor,reference_min_minor,reference_max_minor "
                "FROM activity_template_revision WHERE id=:id"
            ), {"id": revision_id}).one() == (456, 456, 456)
            assert connection.scalar(text(
                "SELECT name_normalized FROM activity_template WHERE id=:id"
            ), {"id": template_id}) == "pg 虚拟历史"
        engine.dispose()
    finally:
        with pg.admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))


def test_postgresql_lost_response_recovers_with_replay_and_get(pg: Harness) -> None:
    preview = pg.imports.preview(identity(), PreviewRequest(markdown="## PG虚拟响应恢复"), "pg-recovery-preview")
    payload = commit_payload(preview)
    first = pg.imports.commit(identity(), preview.batch_id, payload, "pg-recovery-commit")
    restarted = ActivityImportService(pg.sessions, KEYS)
    replay = restarted.commit(identity(), preview.batch_id, payload, "pg-recovery-commit")
    recovered = restarted.get(identity(), preview.batch_id)
    assert replay.replayed is True
    assert replay.results == first.results
    assert recovered.status == "committed"
    assert recovered.results == first.results
