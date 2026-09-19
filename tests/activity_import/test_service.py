from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from sqlalchemy import func, select

from wife_system.activity_import.context import ImportIdentity
from wife_system.activity_import.errors import ActivityImportError
from wife_system.activity_import.schemas import CommitRequest, Decision, PreviewRequest
from wife_system.activity_import.service import ActivityImportService
from wife_system.finance.db import Base, make_engine, make_session_factory
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
from wife_system.finance.service import FinanceService, IdempotencyKeys


OWNER = uuid.UUID("30000000-0000-0000-0000-000000000001")
OTHER = uuid.UUID("30000000-0000-0000-0000-000000000002")


@pytest.fixture
def services(tmp_path: Path):
    engine = make_engine(f"sqlite+pysqlite:///{tmp_path / 'imports.sqlite3'}")
    Base.metadata.create_all(engine)
    sessions = make_session_factory(engine)
    keys = IdempotencyKeys({1: b"virtual-p3-key"})
    yield ActivityImportService(sessions, keys), FinanceService(sessions, keys), sessions
    engine.dispose()


def identity(owner: uuid.UUID = OWNER) -> ImportIdentity:
    return ImportIdentity(owner_id=owner, channel="test", permissions=frozenset({"finance:read", "finance:write"}))


def decisions(preview, *, accept: set[int] | None = None) -> list[Decision]:
    accept = set(range(1, len(preview.candidates) + 1)) if accept is None else accept
    return [
        Decision(
            candidate_id=row.candidate_id,
            decision="accept" if row.ordinal in accept else "skip",
            expected_action=row.proposed_action,
            expected_template_version=row.target_expected_version,
            acknowledged_warning_codes=sorted({
                issue.code for issue in row.issues if issue.severity == "warning"
            }),
        )
        for row in preview.candidates
    ]


def commit_request(preview, *, accept: set[int] | None = None) -> CommitRequest:
    return CommitRequest(
        confirmed=True,
        batch_version=preview.batch_version,
        content_digest=preview.content_digest,
        decisions=decisions(preview, accept=accept),
    )


def test_preview_is_persistent_private_idempotent_and_business_pure(services) -> None:
    service, _, sessions = services
    markdown = "# 虚拟清单\n## 虚拟午餐\n- 参考金额范围：15.00–20.00 元\n- 备注：仅测试"
    first = service.preview(identity(), PreviewRequest(markdown=markdown, source_label=r"C:\virtual\items.md"), " preview-1 ")
    replay = service.preview(identity(), PreviewRequest(markdown=markdown, source_label="items.md"), "preview-1")

    assert first.replayed is False
    assert replay.replayed is True
    assert replay.batch_id == first.batch_id
    assert replay.candidates[0].candidate_id == first.candidates[0].candidate_id
    assert first.candidates[0].reference_minor is None
    assert (first.candidates[0].reference_min_minor, first.candidates[0].reference_max_minor) == (1500, 2000)
    with sessions() as session:
        assert session.scalar(select(func.count(ActivityTemplate.id))) == 0
        assert session.scalar(select(func.count(ActivityTemplateRevision.id))) == 0
        assert session.scalar(select(func.count(AuditEvent.id))) == 0
        assert session.scalar(select(func.count(ActivityImportBatch.id))) == 1
        batch = session.get(ActivityImportBatch, first.batch_id)
        candidate = session.get(ActivityImportCandidate, first.candidates[0].candidate_id)
        assert batch.source_label == "items.md"
        persisted = " ".join(str(value) for value in vars(batch).values()) + " " + " ".join(str(value) for value in vars(candidate).values())
        assert "仅测试" not in persisted
        assert markdown not in persisted

    with pytest.raises(ActivityImportError, match="different payload") as raised:
        service.preview(identity(), PreviewRequest(markdown="## 另一活动"), "preview-1")
    assert raised.value.code == "duplicate_request_conflict"


def test_preview_classifies_create_revise_unchanged_conflict_unresolved(services) -> None:
    service, finance, _ = services
    exact = finance.create_activity_template(CreateActivityTemplate(
        source_system="p3-test", source_event_id="exact", name="虚拟散步", reference_amount="1.00"
    ))
    revise = finance.create_activity_template(CreateActivityTemplate(
        source_system="p3-test", source_event_id="revise", name="虚拟游泳", reference_amount="2.00"
    ))
    archived = finance.create_activity_template(CreateActivityTemplate(
        source_system="p3-test", source_event_id="archived", name="虚拟归档", reference_amount=None
    ))
    finance.archive_activity_template(ArchiveResource(
        source_system="p3-test", source_event_id="archive", resource_id=archived.result_id,
        expected_version=1, reason="虚拟归档测试",
    ))
    preview = service.preview(identity(), PreviewRequest(markdown=(
        "## 虚拟新建\n"
        "## 虚拟散步\n- 参考金额：1.00 元\n"
        "## 虚拟游泳\n- 参考金额范围：2.00-3.00 元\n"
        "## 虚拟归档\n"
        "## 虚拟错误\n- 参考金额：1.234 元\n"
        "## 重复\n## 重复"
    )), "classify")
    assert [row.proposed_action for row in preview.candidates] == [
        "create", "unchanged", "revise", "conflict", "unresolved", "conflict", "conflict"
    ]
    assert preview.candidates[1].target_template_id == exact.result_id
    assert preview.candidates[2].target_template_id == revise.result_id


def test_historical_name_reuse_is_a_conflict(services) -> None:
    service, finance, _ = services
    original = finance.create_activity_template(CreateActivityTemplate(
        source_system="p3-test", source_event_id="history-base", name="虚拟旧名称"
    ))
    finance.revise_activity_template(ReviseActivityTemplate(
        source_system="p3-test", source_event_id="history-revise", template_id=original.result_id,
        expected_version=1, name="虚拟新名称",
    ))
    preview = service.preview(identity(), PreviewRequest(markdown="## 虚拟旧名称"), "history-preview")
    assert preview.candidates[0].proposed_action == "conflict"
    assert preview.candidates[0].target_template_id is None


def test_commit_creates_and_revises_in_one_transaction_with_provenance(services) -> None:
    service, finance, sessions = services
    existing = finance.create_activity_template(CreateActivityTemplate(
        source_system="p3-test", source_event_id="base", name="虚拟骑行", reference_amount="8.00"
    ))
    preview = service.preview(identity(), PreviewRequest(markdown=(
        "## 虚拟瑜伽\n- 参考金额：0 元\n"
        "## 虚拟骑行\n- 参考金额范围：6.00至10.00 元"
    )), "preview-commit")
    result = service.commit(identity(), preview.batch_id, commit_request(preview), "commit-1")
    replay = service.commit(identity(), preview.batch_id, commit_request(preview), "commit-1")

    assert result.replayed is False
    assert replay.replayed is True
    assert result.batch_version == 2
    assert [row.decision for row in result.results] == ["accepted", "accepted"]
    with sessions() as session:
        assert session.scalar(select(func.count(ActivityTemplate.id))) == 2
        revised = session.get(ActivityTemplate, existing.result_id)
        assert revised.version_id == 2
        revision = session.get(ActivityTemplateRevision, revised.current_revision_id)
        assert revision.reference_minor is None
        assert (revision.reference_min_minor, revision.reference_max_minor) == (600, 1000)
        assert revision.source_import_candidate_id == preview.candidates[1].candidate_id
        created = session.get(ActivityTemplateRevision, session.get(ActivityTemplate, result.results[0].template_id).current_revision_id)
        assert (created.reference_minor, created.reference_min_minor, created.reference_max_minor) == (0, 0, 0)
        assert session.get(ActivityImportBatch, preview.batch_id).status == "committed"


def test_all_skip_is_legal_and_owner_isolation_hides_batch(services) -> None:
    service, _, sessions = services
    preview = service.preview(identity(), PreviewRequest(markdown="## 虚拟略过\n- 备注：忽略"), "skip-preview")
    result = service.commit(identity(), preview.batch_id, commit_request(preview, accept=set()), "skip-commit")
    assert result.results[0].decision == "skipped"
    assert result.results[0].template_id is None
    with sessions() as session:
        assert session.scalar(select(func.count(ActivityTemplate.id))) == 0
    with pytest.raises(ActivityImportError) as raised:
        service.get(identity(OTHER), preview.batch_id)
    assert raised.value.code == "batch_not_found"


def test_selection_errors_and_mid_batch_failure_roll_back_everything(services, monkeypatch) -> None:
    service, _, sessions = services
    preview = service.preview(identity(), PreviewRequest(markdown="## 虚拟甲\n## 虚拟乙"), "rollback-preview")
    invalid = commit_request(preview)
    invalid.decisions[0].acknowledged_warning_codes = ["unknown_import_field"]
    with pytest.raises(ActivityImportError) as raised:
        service.commit(identity(), preview.batch_id, invalid, "invalid-commit")
    assert raised.value.code == "unacknowledged_warning"

    original = service._finance._create_activity_template_in_session
    calls = 0

    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise FinanceError("persistence_error")
        return original(*args, **kwargs)

    monkeypatch.setattr(service._finance, "_create_activity_template_in_session", fail_second)
    with pytest.raises(ActivityImportError) as raised:
        service.commit(identity(), preview.batch_id, commit_request(preview), "rollback-commit")
    assert raised.value.code == "persistence_error"
    with sessions() as session:
        assert session.scalar(select(func.count(ActivityTemplate.id))) == 0
        assert session.scalar(select(func.count(ActivityTemplateRevision.id))) == 0
        assert session.scalar(select(func.count(AuditEvent.id))) == 0
        assert session.get(ActivityImportBatch, preview.batch_id).status == "previewed"
        assert all(row.decision is None for row in session.scalars(select(ActivityImportCandidate)))
        assert session.scalar(select(func.count(CommandReceipt.id))) == 1
