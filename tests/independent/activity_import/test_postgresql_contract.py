from __future__ import annotations

import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Lock

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from wife_system.activity_import.errors import ActivityImportError
from wife_system.activity_import.schemas import PreviewRequest
from wife_system.activity_import.service import ActivityImportService
from wife_system.finance.db import make_engine, make_session_factory
from wife_system.finance.errors import FinanceError
from wife_system.finance.models import (
    ActivityImportBatch,
    ActivityImportCandidate,
    ActivityTemplate,
    ActivityTemplateRevision,
    AuditEvent,
    CommandReceipt,
)
from wife_system.finance.schemas import ArchiveResource, CreateActivityTemplate, ReviseActivityTemplate
from wife_system.finance.service import FinanceService

from .conftest import KEYS, commit_payload, trusted_identity


def alembic_config(url: str) -> Config:
    root = Path(__file__).resolve().parents[3]
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return cfg


def schema_url(raw: str, schema: str) -> str:
    parsed = make_url(raw)
    query = dict(parsed.query)
    query["options"] = f"-csearch_path={schema},public"
    return parsed.set(query=query).render_as_string(hide_password=False)


@pytest.fixture(scope="module")
def pg_stack():
    raw = os.getenv("FINANCE_TEST_POSTGRES_URL")
    if not raw or make_url(raw).get_backend_name() != "postgresql":
        pytest.skip("real PostgreSQL URL required")
    schema = f"p3_c9_{uuid.uuid4().hex}"
    admin = make_engine(raw)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    scoped = schema_url(raw, schema)
    engine = None
    try:
        command.upgrade(alembic_config(scoped), "head")
        engine = make_engine(scoped)
        sessions = make_session_factory(engine)
        yield raw, admin, sessions, ActivityImportService(sessions, KEYS), FinanceService(sessions, KEYS)
    finally:
        if engine is not None:
            engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin.dispose()


def run_together(first, second=None):
    gate = Barrier(2)
    calls = (first, second or first)

    def invoke(call):
        gate.wait(timeout=15)
        try:
            return "ok", call()
        except ActivityImportError as exc:
            return exc.code, exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(invoke, call) for call in calls]
        return [future.result(timeout=45) for future in futures]


def test_c9_pg_concurrent_preview_same_key_is_one_persistent_batch(pg_stack) -> None:
    _, _, sessions, imports, _ = pg_stack
    request = PreviewRequest(markdown="## C9并发预览")
    outcomes = run_together(lambda: imports.preview(trusted_identity(), request, "c9-pg-preview-same"))
    assert [code for code, _ in outcomes].count("ok") == 2
    values = [value for _, value in outcomes]
    assert len({value.batch_id for value in values}) == 1
    assert sorted(value.replayed for value in values) == [False, True]
    with sessions() as session:
        assert session.scalar(select(func.count(ActivityImportBatch.id)).where(ActivityImportBatch.id == values[0].batch_id)) == 1


def test_c9_pg_concurrent_commit_same_key_is_exactly_once(pg_stack) -> None:
    _, _, sessions, imports, _ = pg_stack
    preview = imports.preview(trusted_identity(), PreviewRequest(markdown="## C9同键提交"), "c9-pg-commit-preview")
    payload = commit_payload(preview)
    outcomes = run_together(lambda: imports.commit(trusted_identity(), preview.batch_id, payload, "c9-pg-commit-same"))
    assert [code for code, _ in outcomes].count("ok") == 2
    values = [value for _, value in outcomes]
    assert len({value.results[0].template_id for value in values}) == 1
    assert sorted(value.replayed for value in values) == [False, True]
    with sessions() as session:
        assert session.scalar(select(func.count(ActivityTemplate.id)).where(ActivityTemplate.name_normalized == "c9同键提交")) == 1


def test_c9_pg_same_batch_different_keys_has_one_winner(pg_stack) -> None:
    _, _, sessions, imports, _ = pg_stack
    preview = imports.preview(trusted_identity(), PreviewRequest(markdown="## C9异键同批"), "c9-pg-diff-preview")
    payload = commit_payload(preview)
    outcomes = run_together(
        lambda: imports.commit(trusted_identity(), preview.batch_id, payload, "c9-pg-diff-a"),
        lambda: imports.commit(trusted_identity(), preview.batch_id, payload, "c9-pg-diff-b"),
    )
    assert sorted(code for code, _ in outcomes) == ["import_already_committed", "ok"]
    with sessions() as session:
        assert session.scalar(select(func.count(CommandReceipt.id)).where(
            CommandReceipt.command_name == "activity_import.commit", CommandReceipt.result_id == preview.batch_id
        )) == 1


def test_c9_pg_different_batches_same_normalized_name_race_is_private(pg_stack, caplog) -> None:
    _, _, sessions, imports, _ = pg_stack
    marker = "C9-PG-PRIVATE-CANARY-7F31"
    caplog.set_level(logging.INFO, logger="wife_system.activity_import")
    a = imports.preview(trusted_identity(), PreviewRequest(markdown=f"## {marker}"), "c9-name-preview-a")
    b = imports.preview(trusted_identity(), PreviewRequest(markdown=f"## {marker}"), "c9-name-preview-b")
    outcomes = run_together(
        lambda: imports.commit(trusted_identity(), a.batch_id, commit_payload(a), "c9-name-commit-a"),
        lambda: imports.commit(trusted_identity(), b.batch_id, commit_payload(b), "c9-name-commit-b"),
    )
    assert sorted(code for code, _ in outcomes) == ["concurrent_modification", "ok"]
    assert marker not in "\n".join(record.getMessage() for record in caplog.records)
    assert all(marker not in str(value) for _, value in outcomes)
    with sessions() as session:
        assert session.scalar(select(func.count(ActivityTemplate.id)).where(ActivityTemplate.name_normalized == marker.casefold())) == 1


@pytest.mark.parametrize("change", ["revise", "archive"])
def test_c9_pg_stale_or_archived_target_is_rechecked(pg_stack, change: str) -> None:
    _, _, sessions, imports, finance = pg_stack
    name = f"C9目标复验{change}"
    base = finance.create_activity_template(CreateActivityTemplate(
        source_system="c9-pg", source_event_id=f"base-{change}", name=name, reference_amount="1.00"
    ))
    preview = imports.preview(trusted_identity(), PreviewRequest(markdown=f"## {name}\n- 参考金额：2.00 元"), f"preview-{change}")
    if change == "revise":
        finance.revise_activity_template(ReviseActivityTemplate(
            source_system="c9-pg", source_event_id="external-revise", template_id=base.result_id,
            expected_version=1, name=name, reference_amount="3.00",
        ))
    else:
        finance.archive_activity_template(ArchiveResource(
            source_system="c9-pg", source_event_id="external-archive", resource_id=base.result_id,
            expected_version=1, reason="虚拟并发归档",
        ))
    with pytest.raises(ActivityImportError) as raised:
        imports.commit(trusted_identity(), preview.batch_id, commit_payload(preview), f"commit-{change}")
    assert raised.value.code == "concurrent_modification"
    with sessions() as session:
        assert session.get(ActivityImportBatch, preview.batch_id).status == "previewed"


def test_c9_pg_mid_batch_fault_is_fully_rolled_back(pg_stack, monkeypatch) -> None:
    _, _, sessions, imports, _ = pg_stack
    preview = imports.preview(trusted_identity(), PreviewRequest(markdown="## C9回滚一\n## C9回滚二"), "c9-pg-rollback-preview")
    with sessions() as session:
        before_receipts = session.scalar(select(func.count(CommandReceipt.id))) or 0
        before_audits = session.scalar(select(func.count(AuditEvent.id))) or 0
    original = imports._finance._create_activity_template_in_session
    calls = 0

    def fail_on_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise FinanceError("persistence_error")
        return original(*args, **kwargs)

    monkeypatch.setattr(imports._finance, "_create_activity_template_in_session", fail_on_second)
    with pytest.raises(ActivityImportError) as raised:
        imports.commit(trusted_identity(), preview.batch_id, commit_payload(preview), "c9-pg-rollback-commit")
    assert raised.value.code == "persistence_error"
    with sessions() as session:
        assert session.scalar(select(func.count(ActivityTemplate.id)).where(ActivityTemplate.name_normalized.like("c9回滚%"))) == 0
        assert session.get(ActivityImportBatch, preview.batch_id).status == "previewed"
        assert all(row.decision is None for row in session.scalars(select(ActivityImportCandidate).where(ActivityImportCandidate.batch_id == preview.batch_id)))
        assert session.scalar(select(func.count(CommandReceipt.id))) == before_receipts
        assert session.scalar(select(func.count(AuditEvent.id))) == before_audits


def test_c9_pg_constraints_reject_duplicate_name_and_bad_amount_shape(pg_stack) -> None:
    _, _, sessions, _, finance = pg_stack
    a = finance.create_activity_template(CreateActivityTemplate(source_system="c9-pg", source_event_id="constraint-a", name="C9约束甲"))
    b = finance.create_activity_template(CreateActivityTemplate(source_system="c9-pg", source_event_id="constraint-b", name="C9约束乙"))
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            session.get(ActivityTemplate, b.result_id).name_normalized = "c9约束甲"
            session.flush()
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            template = session.get(ActivityTemplate, a.result_id)
            revision = session.get(ActivityTemplateRevision, template.current_revision_id)
            revision.reference_minor = None
            revision.reference_min_minor = 200
            revision.reference_max_minor = 100
            session.flush()


def test_c9_pg_empty_and_existing_p2_schema_migrations(pg_stack) -> None:
    raw, admin, _, _, _ = pg_stack
    schema = f"p3_c9_migration_{uuid.uuid4().hex}"
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    url = schema_url(raw, schema)
    template, revision = uuid.uuid4(), uuid.uuid4()
    try:
        cfg = alembic_config(url)
        command.upgrade(cfg, "7f3e2d1c9a4b")
        engine = make_engine(url)
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO activity_template (id,current_revision_id,archived_at,created_at,version_id) VALUES (:id,NULL,NULL,CURRENT_TIMESTAMP,1)"
            ), {"id": template})
            connection.execute(text(
                "INSERT INTO activity_template_revision (id,template_id,revision_no,name,reference_minor,currency,created_at) "
                "VALUES (:id,:template,1,'C9 PG历史',789,'CNY',CURRENT_TIMESTAMP)"
            ), {"id": revision, "template": template})
            connection.execute(text("UPDATE activity_template SET current_revision_id=:revision WHERE id=:template"), {"revision": revision, "template": template})
        engine.dispose()
        command.upgrade(cfg, "head")
        engine = make_engine(url)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "c82d7a4f901e"
            assert connection.execute(text(
                "SELECT reference_minor,reference_min_minor,reference_max_minor FROM activity_template_revision WHERE id=:id"
            ), {"id": revision}).one() == (789, 789, 789)
        engine.dispose()
    finally:
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))


def test_c9_pg_lost_response_replay_and_new_key_recovery(pg_stack) -> None:
    _, _, sessions, imports, _ = pg_stack
    preview = imports.preview(trusted_identity(), PreviewRequest(markdown="## C9响应恢复"), "c9-recovery-preview")
    payload = commit_payload(preview)
    first = imports.commit(trusted_identity(), preview.batch_id, payload, "c9-recovery-commit")
    restarted = ActivityImportService(sessions, KEYS)
    replay = restarted.commit(trusted_identity(), preview.batch_id, payload, "c9-recovery-commit")
    assert replay.replayed is True and replay.results == first.results
    assert restarted.get(trusted_identity(), preview.batch_id).results == first.results
    with pytest.raises(ActivityImportError) as second_key:
        restarted.commit(trusted_identity(), preview.batch_id, payload, "c9-recovery-new-key")
    assert second_key.value.code == "import_already_committed"
