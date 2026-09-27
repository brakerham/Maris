from __future__ import annotations

import json
import uuid

from sqlalchemy import select

from .conftest import owner_headers
from wife_system.host.auth.models import ChannelBindingCode
from wife_system.host.state_models import HostRequestReceiptRecord


def test_c11_health_bootstrap_login_and_safe_module_summary(host_stack) -> None:
    client, _, _ = host_stack
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").json() == {"status": "ready"}
    assert client.get("/api/v1/auth/bootstrap-status").json() == {"needs_initialization": True}
    headers = owner_headers(client)
    response = client.get("/api/v1/modules", headers=headers)
    assert response.status_code == 200
    text = response.text.lower()
    assert "daily_finance" in text
    for forbidden in ("system_prompt", "factory", "import_path", "password", "secret"):
        assert forbidden not in text


def test_c11_untrusted_identity_fields_and_framework_errors_use_envelope(host_stack) -> None:
    client, _, _ = host_stack
    injected = client.post(
        "/api/v1/auth/login",
        json={
            "handle": "x", "password": "virtual passphrase", "client_fingerprint": "x",
            "device_name": "x", "platform": "api_test", "user_id": str(uuid.uuid4()),
        },
    )
    assert injected.status_code == 422 and injected.json()["error"]["code"] == "invalid_request"
    for response in (client.get("/does-not-exist"), client.post("/healthz")):
        body = response.json()
        assert set(body) == {"request_id", "error"}
        assert {"code", "message", "retryable"} == set(body["error"])


def test_c11_one_time_binding_secret_is_never_persisted_or_replayed(host_stack) -> None:
    client, _, sessions = host_stack
    headers = owner_headers(client)
    create_headers = {**headers, "Idempotency-Key": "ind-binding-1"}
    first = client.post("/api/v1/channel-bindings/codes", headers=create_headers, json={"channel": "wechat"})
    assert first.status_code == 201, first.text
    raw = first.json()["code"]
    replay = client.post("/api/v1/channel-bindings/codes", headers=create_headers, json={"channel": "wechat"})
    assert replay.status_code == 409
    assert replay.json()["error"]["code"] == "one_time_secret_unavailable"
    with sessions() as session:
        code = session.scalar(select(ChannelBindingCode))
        receipts = session.scalars(select(HostRequestReceiptRecord)).all()
    corpus = json.dumps([row.result_json for row in receipts], ensure_ascii=False)
    assert code is not None and code.code_digest != raw
    assert raw not in corpus


def test_c11_adapter_gate_precedes_code_lookup_and_is_privacy_safe(host_stack) -> None:
    client, _, sessions = host_stack
    body = {
        "code_id": str(uuid.uuid4()), "code": "ABCD-2345", "channel": "wechat",
        "provider_account": "VIRTUAL_PROVIDER", "external_subject": "VIRTUAL_SUBJECT",
    }
    before = 0
    with sessions() as session:
        before = len(session.scalars(select(ChannelBindingCode)).all())
    for headers in (
        {"Idempotency-Key": "consume-missing-adapter"},
        {"Idempotency-Key": "consume-wrong-adapter", "X-Channel-Adapter-Token": "wrong"},
    ):
        response = client.post("/api/v1/channel-bindings/consume", headers=headers, json=body)
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "channel_adapter_unauthorized"
        assert "VIRTUAL" not in response.text
    with sessions() as session:
        assert len(session.scalars(select(ChannelBindingCode)).all()) == before
