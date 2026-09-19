from __future__ import annotations

import json
import logging
import uuid

import pytest

from wife_system.activity_import.context import ImportIdentity

from .conftest import OTHER_OWNER


PREVIEW = "/api/v1/activity-imports/preview"


def post_preview(client, markdown: str, key: str = "c9-http-preview", **extra):
    return client.post(PREVIEW, headers={"Idempotency-Key": key}, json={"markdown": markdown, **extra})


def decision(row: dict, value: str = "accept") -> dict:
    return {
        "candidate_id": row["candidate_id"],
        "decision": value,
        "expected_action": row["proposed_action"],
        "expected_template_version": row["target_expected_version"],
        "acknowledged_warning_codes": sorted(
            {issue["code"] for issue in row["issues"] if issue["severity"] == "warning"}
        ),
    }


def test_c9_http_preview_get_commit_replay_and_lost_response_recovery(http_stack) -> None:
    client, _ = http_stack
    first = post_preview(client, "## HTTP虚拟活动\n- 参考金额：12.00 元")
    assert first.status_code == 201
    body = first.json()
    replay = post_preview(client, "## HTTP虚拟活动\n- 参考金额：12.00 元")
    assert replay.status_code == 200 and replay.json()["replayed"] is True
    recovered = client.get(f"/api/v1/activity-imports/{body['batch_id']}")
    assert recovered.status_code == 200 and recovered.json()["status"] == "previewed"
    payload = {
        "confirmed": True,
        "batch_version": body["batch_version"],
        "content_digest": body["content_digest"],
        "decisions": [decision(body["candidates"][0])],
    }
    endpoint = f"/api/v1/activity-imports/{body['batch_id']}/commit"
    committed = client.post(endpoint, headers={"Idempotency-Key": "c9-http-commit"}, json=payload)
    assert committed.status_code == 200
    retry_after_lost_response = client.post(endpoint, headers={"Idempotency-Key": "c9-http-commit"}, json=payload)
    assert retry_after_lost_response.status_code == 200
    assert retry_after_lost_response.json()["replayed"] is True
    assert retry_after_lost_response.json()["results"] == committed.json()["results"]


@pytest.mark.parametrize(
    ("headers", "content", "status", "code"),
    [
        ({"Idempotency-Key": "x", "Content-Type": "text/plain"}, b'{"markdown":"## x"}', 415, "invalid_content_type"),
        ({"Idempotency-Key": "x", "Content-Type": "application/json; charset=latin-1"}, b'{"markdown":"## x"}', 415, "invalid_content_type"),
        ({"Content-Type": "application/json"}, b'{"markdown":"## x"}', 422, "invalid_request"),
        ({"Idempotency-Key": "\t", "Content-Type": "application/json"}, b'{"markdown":"## x"}', 422, "invalid_request"),
        ({"Idempotency-Key": "x", "Content-Type": "application/json"}, b'{"markdown":"## x","markdown":"## y"}', 422, "invalid_request"),
        ({"Idempotency-Key": "x", "Content-Type": "application/json"}, b'{"markdown":"## x","owner_id":"forged"}', 422, "invalid_request"),
        ({"Idempotency-Key": "x", "Content-Type": "application/json"}, b'{"markdown":', 422, "invalid_request"),
    ],
)
def test_c9_http_strict_boundary_and_safe_envelope(http_stack, headers, content, status, code) -> None:
    client, _ = http_stack
    response = client.post(PREVIEW, headers=headers, content=content)
    assert response.status_code == status
    assert set(response.json()) == {"request_id", "error"}
    assert response.json()["error"]["code"] == code
    assert set(response.json()["error"]) == {"code", "message", "retryable"}


def test_c9_http_body_text_line_candidate_and_content_limits(http_stack) -> None:
    client, _ = http_stack
    raw = client.post(
        PREVIEW,
        headers={"Idempotency-Key": "raw-over", "Content-Type": "application/json"},
        content=b'{"markdown":"## x' + b"a" * (96 * 1024) + b'"}',
    )
    assert (raw.status_code, raw.json()["error"]["code"]) == (413, "import_text_too_large")
    text = post_preview(client, "## 多字节\n" + "字" * 22_000, "text-over")
    assert (text.status_code, text.json()["error"]["code"]) == (413, "import_text_too_large")
    candidates = post_preview(client, "\n".join(f"## 候选{i}" for i in range(51)), "candidate-over")
    assert (candidates.status_code, candidates.json()["error"]["code"]) == (422, "import_candidate_limit_exceeded")


def test_c9_http_owner_isolation_and_unavailable_service(http_stack) -> None:
    client, _ = http_stack
    batch = post_preview(client, "## 所有者隔离", "owner-preview").json()
    client.app.state.activity_import_identity = ImportIdentity(
        owner_id=OTHER_OWNER,
        channel="p3-c9-independent",
        permissions=frozenset({"finance:read", "finance:write"}),
    )
    hidden = client.get(f"/api/v1/activity-imports/{batch['batch_id']}")
    assert (hidden.status_code, hidden.json()["error"]["code"]) == (404, "batch_not_found")
    client.app.state.activity_import_service = None
    unavailable = post_preview(client, "## 后端不可用", "no-service")
    assert unavailable.status_code == 503
    assert unavailable.json()["error"] == {
        "code": "database_unavailable",
        "message": "The database is temporarily unavailable.",
        "retryable": True,
    }


def test_c9_http_logs_and_errors_do_not_leak_canaries(http_stack, caplog) -> None:
    client, _ = http_stack
    marker = "C9_PRIVATE_MARKDOWN_CANARY"
    key = "C9_PRIVATE_IDEMPOTENCY_CANARY"
    caplog.set_level(logging.INFO)
    response = post_preview(
        client,
        f"## 日志安全活动\n- 备注：{marker}\nhttps://example.invalid/private",
        key,
        source_label=r"C:\private\virtual.md",
    )
    assert response.status_code == 201
    logs = "\n".join(record.getMessage() for record in caplog.records)
    serialized_response = json.dumps(response.json(), ensure_ascii=False)
    for forbidden in (marker, key, r"C:\private", "example.invalid", response.json()["content_digest"]):
        assert forbidden not in logs
    assert marker not in serialized_response


@pytest.mark.parametrize("confirmed", [False, 0, 1, "true", None])
def test_c9_http_commit_confirmation_is_literal_true(http_stack, confirmed) -> None:
    client, _ = http_stack
    preview = post_preview(client, "## 严格确认", f"confirm-preview-{confirmed}").json()
    payload = {
        "confirmed": confirmed,
        "batch_version": preview["batch_version"],
        "content_digest": preview["content_digest"],
        "decisions": [decision(preview["candidates"][0], "skip")],
    }
    response = client.post(
        f"/api/v1/activity-imports/{preview['batch_id']}/commit",
        headers={"Idempotency-Key": f"confirm-commit-{confirmed}"},
        json=payload,
    )
    assert (response.status_code, response.json()["error"]["code"]) == (422, "invalid_request")


def test_c9_http_candidate_id_and_digest_tampering_are_rejected(http_stack) -> None:
    client, _ = http_stack
    preview = post_preview(client, "## 防篡改活动", "tamper-preview").json()
    endpoint = f"/api/v1/activity-imports/{preview['batch_id']}/commit"
    base = {
        "confirmed": True,
        "batch_version": preview["batch_version"],
        "content_digest": preview["content_digest"],
        "decisions": [decision(preview["candidates"][0])],
    }
    wrong_candidate = json.loads(json.dumps(base))
    wrong_candidate["decisions"][0]["candidate_id"] = str(uuid.uuid4())
    one = client.post(endpoint, headers={"Idempotency-Key": "tamper-candidate"}, json=wrong_candidate)
    assert (one.status_code, one.json()["error"]["code"]) == (422, "invalid_candidate_selection")
    wrong_digest = json.loads(json.dumps(base))
    wrong_digest["content_digest"] = "hmac-sha256:v1:" + "0" * 64
    two = client.post(endpoint, headers={"Idempotency-Key": "tamper-digest"}, json=wrong_digest)
    assert (two.status_code, two.json()["error"]["code"]) == (409, "import_content_mismatch")
