from __future__ import annotations

import json
import uuid

import pytest
from sqlalchemy import func, select

from wife_system.activity_import.errors import ActivityImportError
from wife_system.activity_import.schemas import Decision, PreviewRequest
from wife_system.finance.errors import FinanceError
from wife_system.finance.models import (
    Account,
    ActivityEntryAllocation,
    ActivityImportBatch,
    ActivityImportCandidate,
    ActivityOccurrence,
    ActivityTemplate,
    ActivityTemplateRevision,
    AuditEvent,
    BudgetAllocation,
    BudgetPlan,
    BudgetVersion,
    CommandReceipt,
    IncomeExpectation,
    IncomeExpectationMatch,
    IncomeSchedule,
    IncomeScheduleVersion,
    FinancialTransaction,
    TransactionEntry,
)
from wife_system.finance.schemas import ArchiveResource, CreateActivityTemplate, ReviseActivityTemplate

from .conftest import OTHER_OWNER, commit_payload, trusted_identity


BUSINESS_TABLES = (
    ActivityTemplate,
    ActivityTemplateRevision,
    ActivityOccurrence,
    ActivityEntryAllocation,
    Account,
    FinancialTransaction,
    TransactionEntry,
    BudgetPlan,
    BudgetVersion,
    BudgetAllocation,
    IncomeSchedule,
    IncomeScheduleVersion,
    IncomeExpectation,
    IncomeExpectationMatch,
    AuditEvent,
)


def counts(session, models=BUSINESS_TABLES) -> dict[str, int]:
    return {model.__tablename__: session.scalar(select(func.count(model.id))) or 0 for model in models}


def test_c9_preview_persists_only_allowed_metadata_and_is_business_pure(sqlite_stack) -> None:
    imports, _, sessions = sqlite_stack
    marker = "C9_PRIVATE_FREE_TEXT_CANARY"
    markdown = f"# 虚拟目录\n## 周末采购\n- 参考金额范围：80.00–120.00 元\n- 备注：{marker}"
    with sessions() as session:
        before = counts(session)
    first = imports.preview(
        trusted_identity(), PreviewRequest(markdown=markdown, source_label=r"C:\virtual\activities.md"), " preview-key "
    )
    replay = imports.preview(
        trusted_identity(), PreviewRequest(markdown=markdown, source_label="activities.md"), "preview-key"
    )
    with sessions() as session:
        assert counts(session) == before
        assert session.scalar(select(func.count(ActivityImportBatch.id))) == 1
        assert session.scalar(select(func.count(ActivityImportCandidate.id))) == 1
        assert session.scalar(select(func.count(CommandReceipt.id))) == 1
        batch = session.get(ActivityImportBatch, first.batch_id)
        candidate = session.get(ActivityImportCandidate, first.candidates[0].candidate_id)
        persisted = json.dumps({**vars(batch), **vars(candidate)}, default=str, ensure_ascii=False)
        assert markdown not in persisted
        assert marker not in persisted
        assert "C:\\virtual" not in persisted
        assert batch.source_label == "activities.md"
        assert len(batch.content_digest.rsplit(":", 1)[-1]) == 64
    assert replay.replayed is True
    assert replay.batch_id == first.batch_id
    assert replay.candidates[0].candidate_id == first.candidates[0].candidate_id
    assert (first.candidates[0].reference_minor, first.candidates[0].reference_min_minor, first.candidates[0].reference_max_minor) == (None, 8000, 12000)


def test_c9_new_preview_key_creates_new_uuid_but_stable_normalized_fields(sqlite_stack) -> None:
    imports, _, _ = sqlite_stack
    request = PreviewRequest(markdown="## CAFE\u0301\n- 参考金额：9.90 元")
    a = imports.preview(trusted_identity(), request, "new-batch-a")
    b = imports.preview(trusted_identity(), request, "new-batch-b")
    assert a.batch_id != b.batch_id
    assert a.candidates[0].candidate_id != b.candidates[0].candidate_id
    assert a.candidates[0].model_dump(exclude={"candidate_id"}) == b.candidates[0].model_dump(exclude={"candidate_id"})


def test_c9_candidate_actions_follow_exact_name_and_history_rules(sqlite_stack) -> None:
    imports, finance, _ = sqlite_stack
    same = finance.create_activity_template(CreateActivityTemplate(
        source_system="c9", source_event_id="same", name="每日散步", reference_amount="1.00"
    ))
    changed = finance.create_activity_template(CreateActivityTemplate(
        source_system="c9", source_event_id="changed", name="周末游泳", reference_amount="2.00"
    ))
    archived = finance.create_activity_template(CreateActivityTemplate(
        source_system="c9", source_event_id="archived", name="归档活动"
    ))
    finance.archive_activity_template(ArchiveResource(
        source_system="c9", source_event_id="archive", resource_id=archived.result_id,
        expected_version=1, reason="虚拟归档",
    ))
    historical = finance.create_activity_template(CreateActivityTemplate(
        source_system="c9", source_event_id="history", name="旧名字"
    ))
    finance.revise_activity_template(ReviseActivityTemplate(
        source_system="c9", source_event_id="rename", template_id=historical.result_id,
        expected_version=1, name="新名字",
    ))
    preview = imports.preview(trusted_identity(), PreviewRequest(markdown=(
        "## 新活动\n"
        "## 每日散步\n- 参考金额：1.00 元\n"
        "## 周末游泳\n- 参考金额范围：2.00–3.00 元\n"
        "## 归档活动\n"
        "## 旧名字\n"
        "## 不完整\n- 参考金额：1.234 元\n"
        "## 重名\n## 重名\n"
        "## 每日慢走"
    )), "actions")
    assert [row.proposed_action for row in preview.candidates] == [
        "create", "unchanged", "revise", "conflict", "conflict", "unresolved", "conflict", "conflict", "create"
    ]
    assert preview.candidates[1].target_template_id == same.result_id
    assert preview.candidates[2].target_template_id == changed.result_id


def test_c9_atomic_create_revise_skip_and_provenance(sqlite_stack) -> None:
    imports, finance, sessions = sqlite_stack
    target = finance.create_activity_template(CreateActivityTemplate(
        source_system="c9", source_event_id="base", name="虚拟骑行", reference_amount="8.00"
    ))
    preview = imports.preview(trusted_identity(), PreviewRequest(markdown=(
        "## 虚拟瑜伽\n- 参考金额：0 元\n"
        "## 虚拟骑行\n- 参考金额范围：6.00至10.00 元\n"
        "## 略过活动"
    )), "atomic-preview")
    payload = commit_payload(preview, accepted={1, 2})
    result = imports.commit(trusted_identity(), preview.batch_id, payload, "atomic-commit")
    replay = imports.commit(trusted_identity(), preview.batch_id, payload, "atomic-commit")
    assert replay.replayed is True and replay.results == result.results
    assert [row.decision for row in result.results] == ["accepted", "accepted", "skipped"]
    with sessions() as session:
        template = session.get(ActivityTemplate, target.result_id)
        revision = session.get(ActivityTemplateRevision, template.current_revision_id)
        assert template.version_id == 2
        assert (revision.reference_minor, revision.reference_min_minor, revision.reference_max_minor) == (None, 600, 1000)
        assert revision.source_import_candidate_id == preview.candidates[1].candidate_id
        assert session.get(ActivityImportBatch, preview.batch_id).status == "committed"
        assert session.scalar(select(func.count(AuditEvent.id))) == 3  # one base create plus two imported actions
        assert session.scalar(select(func.count(CommandReceipt.id))) == 3  # direct base + preview + one atomic commit receipt


def test_c9_all_skip_commits_without_templates(sqlite_stack) -> None:
    imports, _, sessions = sqlite_stack
    preview = imports.preview(trusted_identity(), PreviewRequest(markdown="## 只预览活动"), "skip-preview")
    result = imports.commit(trusted_identity(), preview.batch_id, commit_payload(preview, accepted=set()), "skip-commit")
    with sessions() as session:
        assert session.scalar(select(func.count(ActivityTemplate.id))) == 0
        assert session.get(ActivityImportBatch, preview.batch_id).status == "committed"
    assert result.results[0].decision == "skipped"


def test_c9_owner_and_permission_isolation(sqlite_stack) -> None:
    imports, _, _ = sqlite_stack
    preview = imports.preview(trusted_identity(), PreviewRequest(markdown="## 私有活动"), "private-preview")
    with pytest.raises(ActivityImportError) as hidden:
        imports.get(trusted_identity(OTHER_OWNER), preview.batch_id)
    assert hidden.value.code == "batch_not_found"
    with pytest.raises(ActivityImportError) as denied:
        imports.preview(trusted_identity(permissions=frozenset({"finance:read"})), PreviewRequest(markdown="## x"), "denied")
    assert denied.value.code == "invalid_request"


def test_c9_same_key_different_payloads_conflict_for_preview_and_commit(sqlite_stack) -> None:
    imports, _, _ = sqlite_stack
    first = imports.preview(trusted_identity(), PreviewRequest(markdown="## 甲"), "same-preview-key")
    with pytest.raises(ActivityImportError) as preview_conflict:
        imports.preview(trusted_identity(), PreviewRequest(markdown="## 乙"), "same-preview-key")
    assert preview_conflict.value.code == "duplicate_request_conflict"
    payload = commit_payload(first, accepted=set())
    imports.commit(trusted_identity(), first.batch_id, payload, "same-commit-key")
    changed = payload.model_copy(deep=True)
    changed.decisions[0].decision = "accept"
    with pytest.raises(ActivityImportError) as commit_conflict:
        imports.commit(trusted_identity(), first.batch_id, changed, "same-commit-key")
    assert commit_conflict.value.code == "duplicate_request_conflict"


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "wrong_action", "wrong_version", "warning"])
def test_c9_selection_tampering_is_rejected_atomically(sqlite_stack, mutation: str) -> None:
    imports, _, sessions = sqlite_stack
    preview = imports.preview(
        trusted_identity(), PreviewRequest(markdown="## 选择活动\n- 备注：虚拟 warning"), f"selection-{mutation}"
    )
    payload = commit_payload(preview)
    if mutation == "missing":
        payload.decisions = []
        expected = "invalid_candidate_selection"
    elif mutation == "duplicate":
        payload.decisions.append(payload.decisions[0].model_copy(deep=True))
        expected = "invalid_candidate_selection"
    elif mutation == "wrong_action":
        payload.decisions[0].expected_action = "revise"
        expected = "invalid_candidate_selection"
    elif mutation == "wrong_version":
        payload.decisions[0].expected_template_version = 1
        expected = "concurrent_modification"
    else:
        payload.decisions[0].acknowledged_warning_codes = []
        expected = "unacknowledged_warning"
    with pytest.raises(ActivityImportError) as raised:
        imports.commit(trusted_identity(), preview.batch_id, payload, f"commit-{mutation}")
    assert raised.value.code == expected
    with sessions() as session:
        assert session.scalar(select(func.count(ActivityTemplate.id))) == 0
        assert session.get(ActivityImportBatch, preview.batch_id).status == "previewed"


def test_c9_stale_and_archived_targets_fail_without_partial_writes(sqlite_stack) -> None:
    imports, finance, sessions = sqlite_stack
    target = finance.create_activity_template(CreateActivityTemplate(
        source_system="c9", source_event_id="stale-base", name="并发目标", reference_amount="1.00"
    ))
    stale = imports.preview(trusted_identity(), PreviewRequest(markdown="## 并发目标\n- 参考金额：2.00 元"), "stale-preview")
    finance.revise_activity_template(ReviseActivityTemplate(
        source_system="c9", source_event_id="stale-change", template_id=target.result_id,
        expected_version=1, name="并发目标", reference_amount="3.00",
    ))
    with pytest.raises(ActivityImportError) as raised:
        imports.commit(trusted_identity(), stale.batch_id, commit_payload(stale), "stale-commit")
    assert raised.value.code == "concurrent_modification"
    with sessions() as session:
        assert session.get(ActivityImportBatch, stale.batch_id).status == "previewed"
        assert session.get(ActivityTemplate, target.result_id).version_id == 2


def test_c9_mid_batch_fault_rolls_back_templates_audit_decisions_and_receipt(sqlite_stack, monkeypatch) -> None:
    imports, _, sessions = sqlite_stack
    preview = imports.preview(trusted_identity(), PreviewRequest(markdown="## 回滚甲\n## 回滚乙"), "rollback-preview")
    with sessions() as session:
        receipt_before = session.scalar(select(func.count(CommandReceipt.id)))
    original = imports._finance._create_activity_template_in_session
    calls = 0

    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise FinanceError("persistence_error")
        return original(*args, **kwargs)

    monkeypatch.setattr(imports._finance, "_create_activity_template_in_session", fail_second)
    with pytest.raises(ActivityImportError) as raised:
        imports.commit(trusted_identity(), preview.batch_id, commit_payload(preview), "rollback-commit")
    assert raised.value.code == "persistence_error"
    with sessions() as session:
        assert counts(session, (ActivityTemplate, ActivityTemplateRevision, AuditEvent)) == {
            "activity_template": 0, "activity_template_revision": 0, "audit_event": 0
        }
        assert session.scalar(select(func.count(CommandReceipt.id))) == receipt_before
        assert session.get(ActivityImportBatch, preview.batch_id).status == "previewed"
        assert all(row.decision is None for row in session.scalars(select(ActivityImportCandidate)))


def test_c9_failed_commit_can_retry_cleanly(sqlite_stack, monkeypatch) -> None:
    imports, _, sessions = sqlite_stack
    preview = imports.preview(trusted_identity(), PreviewRequest(markdown="## 恢复活动"), "retry-preview")
    original = imports._finance._create_activity_template_in_session
    monkeypatch.setattr(imports._finance, "_create_activity_template_in_session", lambda *a, **k: (_ for _ in ()).throw(FinanceError("persistence_error")))
    with pytest.raises(ActivityImportError):
        imports.commit(trusted_identity(), preview.batch_id, commit_payload(preview), "retry-commit")
    monkeypatch.setattr(imports._finance, "_create_activity_template_in_session", original)
    result = imports.commit(trusted_identity(), preview.batch_id, commit_payload(preview), "retry-commit")
    assert result.status == "committed"
    with sessions() as session:
        assert session.scalar(select(func.count(ActivityTemplate.id))) == 1
