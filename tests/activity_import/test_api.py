from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wife_system.activity_import.context import ImportIdentity
from wife_system.activity_import.service import ActivityImportService
from wife_system.api.app import create_app
from wife_system.finance.db import Base, make_engine, make_session_factory
from wife_system.finance.service import IdempotencyKeys


OWNER = uuid.UUID("40000000-0000-0000-0000-000000000001")


@pytest.fixture
def client(tmp_path: Path):
    engine = make_engine(f"sqlite+pysqlite:///{tmp_path / 'api.sqlite3'}")
    Base.metadata.create_all(engine)
    service = ActivityImportService(make_session_factory(engine), IdempotencyKeys({1: b"virtual-api-key"}))
    application = create_app(
        activity_import_service=service,
        activity_import_identity=ImportIdentity(
            owner_id=OWNER,
            channel="test-http",
            permissions=frozenset({"finance:read", "finance:write"}),
        ),
    )
    with TestClient(application, raise_server_exceptions=False) as test_client:
        yield test_client
    engine.dispose()


def preview(client: TestClient, markdown: str, key: str = "preview"):
    return client.post(
        "/api/v1/activity-imports/preview",
        headers={"Idempotency-Key": key},
        json={"markdown": markdown, "source_label": "virtual.md"},
    )


def decision(candidate: dict, value: str = "accept") -> dict:
    return {
        "candidate_id": candidate["candidate_id"],
        "decision": value,
        "expected_action": candidate["proposed_action"],
        "expected_template_version": candidate["target_expected_version"],
        "acknowledged_warning_codes": sorted({
            issue["code"] for issue in candidate["issues"] if issue["severity"] == "warning"
        }),
    }


def test_preview_get_commit_and_replay_statuses(client: TestClient) -> None:
    first = preview(client, "## 虚拟活动\n- 参考金额：12.00 元")
    assert first.status_code == 201
    body = first.json()
    replay = preview(client, "## 虚拟活动\n- 参考金额：12.00 元")
    assert replay.status_code == 200
    assert replay.json()["replayed"] is True
    assert replay.json()["batch_id"] == body["batch_id"]

    recovered = client.get(f"/api/v1/activity-imports/{body['batch_id']}")
    assert recovered.status_code == 200
    assert recovered.json()["status"] == "previewed"
    commit_body = {
        "confirmed": True,
        "batch_version": body["batch_version"],
        "content_digest": body["content_digest"],
        "decisions": [decision(body["candidates"][0])],
    }
    committed = client.post(
        f"/api/v1/activity-imports/{body['batch_id']}/commit",
        headers={"Idempotency-Key": "commit"},
        json=commit_body,
    )
    assert committed.status_code == 200
    assert committed.json()["status"] == "committed"
    commit_replay = client.post(
        f"/api/v1/activity-imports/{body['batch_id']}/commit",
        headers={"Idempotency-Key": "commit"},
        json=commit_body,
    )
    assert commit_replay.status_code == 200
    assert commit_replay.json()["replayed"] is True


@pytest.mark.parametrize(
    ("headers", "content", "expected"),
    [
        ({"Idempotency-Key": "x", "Content-Type": "text/plain"}, b'{"markdown":"## x"}', 415),
        ({"Idempotency-Key": "x", "Content-Type": "application/json; charset=latin-1"}, b'{"markdown":"## x"}', 415),
        ({"Content-Type": "application/json"}, b'{"markdown":"## x"}', 422),
        ({"Idempotency-Key": "\t", "Content-Type": "application/json"}, b'{"markdown":"## x"}', 422),
        ({"Idempotency-Key": "x", "Content-Type": "application/json"}, b'{"markdown":"## x","markdown":"## y"}', 422),
        ({"Idempotency-Key": "x", "Content-Type": "application/json"}, b'{"markdown":"## x","owner_id":"bad"}', 422),
    ],
)
def test_strict_post_boundary(client: TestClient, headers: dict, content: bytes, expected: int) -> None:
    response = client.post("/api/v1/activity-imports/preview", headers=headers, content=content)
    assert response.status_code == expected
    assert set(response.json()) == {"request_id", "error"}


def test_body_and_normalized_text_limits_are_distinct(client: TestClient) -> None:
    normalized_too_large = preview(client, "## 虚拟\n" + "字" * 22_000, "normalized-limit")
    assert normalized_too_large.status_code == 413
    assert normalized_too_large.json()["error"]["code"] == "import_text_too_large"
    raw_too_large = client.post(
        "/api/v1/activity-imports/preview",
        headers={"Idempotency-Key": "raw-limit", "Content-Type": "application/json"},
        content=b'{"markdown":"## x' + b"a" * (96 * 1024) + b'"}',
    )
    assert raw_too_large.status_code == 413


def test_owner_mismatch_and_backend_failure_use_safe_envelopes(client: TestClient) -> None:
    created = preview(client, "## 私有虚拟活动", "owner-preview").json()
    client.app.state.activity_import_identity = ImportIdentity(
        owner_id=uuid.UUID("40000000-0000-0000-0000-000000000002"),
        channel="test-http",
        permissions=frozenset({"finance:read", "finance:write"}),
    )
    hidden = client.get(f"/api/v1/activity-imports/{created['batch_id']}")
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "batch_not_found"
    client.app.state.activity_import_service = None
    unavailable = preview(client, "## 无服务", "no-backend")
    assert unavailable.status_code == 503
    assert unavailable.json()["error"] == {
        "code": "database_unavailable",
        "message": "The database is temporarily unavailable.",
        "retryable": True,
    }


def test_logs_do_not_contain_markdown_labels_or_full_digests(client: TestClient, caplog) -> None:
    secret = "PRIVATE_ACTIVITY_MARKER"
    caplog.set_level(logging.INFO)
    response = preview(client, f"## 虚拟日志活动\n- 备注：{secret}", "private-key")
    assert response.status_code == 201
    serialized = "\n".join(record.getMessage() for record in caplog.records)
    assert secret not in serialized
    assert "virtual.md" not in serialized
    assert "private-key" not in serialized
    assert response.json()["content_digest"] not in serialized


def test_commit_rejects_coerced_confirmation_and_candidate_tampering(client: TestClient) -> None:
    created = preview(client, "## 虚拟确认", "confirm-preview").json()
    body = {
        "confirmed": 1,
        "batch_version": created["batch_version"],
        "content_digest": created["content_digest"],
        "decisions": [decision(created["candidates"][0])],
    }
    endpoint = f"/api/v1/activity-imports/{created['batch_id']}/commit"
    coerced = client.post(endpoint, headers={"Idempotency-Key": "bad-confirm"}, json=body)
    assert coerced.status_code == 422
    body["confirmed"] = True
    body["decisions"][0]["candidate_id"] = str(uuid.uuid4())
    tampered = client.post(endpoint, headers={"Idempotency-Key": "tampered"}, json=body)
    assert tampered.status_code == 422
    assert tampered.json()["error"]["code"] == "invalid_candidate_selection"
