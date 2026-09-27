from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select, text

from wife_system.activity_import.context import ImportIdentity
from wife_system.activity_import.service import ActivityImportService
from wife_system.api.app import create_app
from wife_system.finance.db import Base, make_engine, make_session_factory
from wife_system.finance.models import ActivityImportBatch, CommandReceipt
from wife_system.finance.service import IdempotencyKeys
from wife_system.host.auth.errors import AUTH_ERROR_CODES, AuthError
from wife_system.host.auth.models import AppUser, ChannelBindingCode
from wife_system.host.auth.service import AuthenticatedSession, AuthSecrets
from wife_system.host.factory import build_host_runtime
from wife_system.host.state import HostKeys
from wife_system.host.state_models import HostRequestReceiptRecord


class _FinanceAdapter:
    def __getattr__(self, name):
        if name.startswith(("list_", "get_", "account_", "monthly_", "record_")):
            return lambda *_args, **_kwargs: {"status": "ok"}
        raise AttributeError(name)


@pytest.fixture
def client(tmp_path):
    engine = make_engine(f"sqlite:///{(tmp_path / 'host-api.sqlite3').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = make_session_factory(engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        connection.execute(text("INSERT INTO alembic_version VALUES ('p4_host_state')"))
    runtime = build_host_runtime(
        sessions=sessions,
        finance_adapter=_FinanceAdapter(),
        auth_secrets=AuthSecrets(
            bootstrap_token=b"b" * 32,
            binding_hmac_key=b"h" * 32,
            adapter_token=b"a" * 32,
        ),
        state_keys=HostKeys({1: b"s" * 32}),
        cursor_secret=b"c" * 32,
    )
    runtime.auth.ensure_pending_owner(now=__import__("datetime").datetime.now(__import__("datetime").UTC))
    app = create_app(
        host_runtime=runtime,
        activity_import_service=ActivityImportService(
            sessions, IdempotencyKeys({1: b"activity-import-api-test-key"})
        ),
    )
    app.state.test_sessions = sessions
    with TestClient(app, client=("127.0.0.1", 50000), raise_server_exceptions=False) as test_client:
        yield test_client
    engine.dispose()


def _initialize_and_login(client: TestClient) -> dict[str, str]:
    initialized = client.post(
        "/api/v1/auth/initialize",
        headers={"Idempotency-Key": "init-1", "X-Bootstrap-Token": "b" * 32},
        json={"handle": "owner", "password": "correct horse battery staple"},
    )
    assert initialized.status_code == 200, initialized.text
    login = client.post(
        "/api/v1/auth/login",
        json={
            "handle": "owner",
            "password": "correct horse battery staple",
            "client_fingerprint": "test-client",
            "device_name": "pytest",
            "platform": "api_test",
        },
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_health_ready_bootstrap_and_strict_body(client: TestClient) -> None:
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").json() == {"status": "ready"}
    assert client.get("/api/v1/auth/bootstrap-status").json() == {"needs_initialization": True}
    rejected = client.post(
        "/api/v1/auth/login",
        json={"handle": "owner", "password": "x", "client_fingerprint": "x", "device_name": "x", "platform": "api_test", "user_id": str(uuid.uuid4())},
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "invalid_request"


def test_authenticated_module_conversation_idempotency_and_cursor(client: TestClient) -> None:
    headers = _initialize_and_login(client)
    modules = client.get("/api/v1/modules", headers=headers)
    assert modules.status_code == 200
    assert [item["module_id"] for item in modules.json()] == ["daily_finance"]
    payload = {
        "channel": "api_test",
        "module_id": "daily_finance",
        "profile_id": "daily_finance.assistant@1",
    }
    first = client.post("/api/v1/conversations", headers={**headers, "Idempotency-Key": "conversation-1"}, json=payload)
    replay = client.post("/api/v1/conversations", headers={**headers, "Idempotency-Key": "conversation-1"}, json=payload)
    assert first.status_code == replay.status_code == 200
    assert first.json()["id"] == replay.json()["id"] and replay.json()["replayed"] is True
    invalid_cursor = client.get("/api/v1/conversations?cursor=not-a-cursor", headers=headers)
    assert invalid_cursor.status_code == 422
    assert invalid_cursor.json()["error"]["code"] == "invalid_cursor"


def test_page_endpoints_emit_bound_next_cursor(client: TestClient) -> None:
    headers = _initialize_and_login(client)
    runtime = client.app.state.host_runtime
    principal = runtime.auth.authenticate_access(
        headers["Authorization"].removeprefix("Bearer "), now=datetime.now(UTC)
    )
    payload = {
        "channel": "api_test",
        "module_id": "daily_finance",
        "profile_id": "daily_finance.assistant@1",
    }
    ids: list[str] = []
    for index in range(3):
        response = client.post(
            "/api/v1/conversations",
            headers={**headers, "Idempotency-Key": f"page-conversation-{index}"},
            json=payload,
        )
        assert response.status_code == 200
        ids.append(response.json()["id"])
    first_page = client.get("/api/v1/conversations?limit=1", headers=headers)
    assert first_page.status_code == 200
    assert len(first_page.json()["items"]) == 1
    cursor = first_page.json()["next_cursor"]
    assert cursor
    second_page = client.get(
        f"/api/v1/conversations?limit=1&cursor={cursor}", headers=headers
    )
    assert second_page.status_code == 200
    assert second_page.json()["items"][0]["id"] != first_page.json()["items"][0]["id"]
    cross_endpoint = client.get(
        f"/api/v1/conversations/{ids[0]}/messages?cursor={cursor}", headers=headers
    )
    assert cross_endpoint.status_code == 422

    now = datetime.now(UTC)
    runtime.memories.propose(
        user_id=principal.user_id,
        source_namespace="daily_finance.candidates",
        target_namespace="daily_finance.confirmed",
        kind="preference",
        value={"drink": "tea"},
        tags=[],
        source_type="conversation",
        source_ref_digest="f" * 64,
        sensitivity="private",
        proposed_by_profile_id="daily_finance.assistant@1",
        now=now,
    )
    runtime.memories.propose(
        user_id=principal.user_id,
        source_namespace="daily_finance.candidates",
        target_namespace="daily_finance.confirmed",
        kind="preference",
        value={"drink": "water"},
        tags=[],
        source_type="conversation",
        source_ref_digest="e" * 64,
        sensitivity="private",
        proposed_by_profile_id="daily_finance.assistant@1",
        now=now,
    )
    candidate_page = client.get(
        "/api/v1/memory-candidates?status=pending&limit=1", headers=headers
    )
    assert candidate_page.status_code == 200
    candidate_cursor = candidate_page.json()["next_cursor"]
    assert candidate_cursor
    changed_filter = client.get(
        f"/api/v1/memory-candidates?status=confirmed&limit=1&cursor={candidate_cursor}",
        headers=headers,
    )
    assert changed_filter.status_code == 422


def test_binding_code_is_one_time_adapter_gated_and_receipt_safe(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    headers = _initialize_and_login(client)
    first = client.post(
        "/api/v1/channel-bindings/codes",
        headers={**headers, "Idempotency-Key": "binding-code-first"},
        json={"channel": "fake_wechat"},
    )
    assert first.status_code == 201, first.text
    created = first.json()
    code_id = created["code_id"]
    raw_code = created["code"]
    assert created["replayed"] is False

    replay = client.post(
        "/api/v1/channel-bindings/codes",
        headers={**headers, "Idempotency-Key": "binding-code-first"},
        json={"channel": "fake_wechat"},
    )
    assert replay.status_code == 409
    assert replay.json()["error"]["code"] == "one_time_secret_unavailable"
    conflict = client.post(
        "/api/v1/channel-bindings/codes",
        headers={**headers, "Idempotency-Key": "binding-code-first"},
        json={"channel": "other_channel"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "idempotency_conflict"

    consume_payload = {
        "code_id": code_id,
        "channel": "fake_wechat",
        "provider_account": "virtual-provider",
        "external_subject": "virtual-subject",
        "code": raw_code,
    }
    for index, adapter in enumerate((None, "", "wrong-adapter")):
        request_headers = {"Idempotency-Key": f"adapter-rejected-{index}"}
        if adapter is not None:
            request_headers["X-Channel-Adapter-Token"] = adapter
        response = client.post(
            "/api/v1/channel-bindings/consume",
            headers=request_headers,
            json=consume_payload,
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "channel_adapter_unauthorized"

    with client.app.state.test_sessions() as session:
        row = session.get(ChannelBindingCode, uuid.UUID(code_id))
        assert row is not None and row.attempts == 0 and row.status == "active"
        receipts = session.scalars(select(HostRequestReceiptRecord)).all()
        persisted = "\n".join(item.result_json or "" for item in receipts)
        assert raw_code not in persisted
        assert "virtual-provider" not in persisted
        assert "virtual-subject" not in persisted

    consumed = client.post(
        "/api/v1/channel-bindings/consume",
        headers={
            "Idempotency-Key": "binding-consume-ok",
            "X-Channel-Adapter-Token": "a" * 32,
        },
        json=consume_payload,
    )
    assert consumed.status_code == 200, consumed.text
    assert consumed.json()["replayed"] is False
    consumed_replay = client.post(
        "/api/v1/channel-bindings/consume",
        headers={
            "Idempotency-Key": "binding-consume-ok",
            "X-Channel-Adapter-Token": "a" * 32,
        },
        json=consume_payload,
    )
    assert consumed_replay.status_code == 200
    assert consumed_replay.json()["replayed"] is True
    assert consumed_replay.json()["binding_id"] == consumed.json()["binding_id"]
    access_token = headers["Authorization"].removeprefix("Bearer ")
    with client.app.state.test_sessions() as session:
        connection = session.connection()
        values: list[str] = []
        for table in inspect(connection).get_table_names():
            columns = [item["name"] for item in inspect(connection).get_columns(table)]
            if not columns:
                continue
            quoted = ",".join(f'"{column}"' for column in columns)
            values.extend(
                repr(row)
                for row in connection.exec_driver_sql(
                    f'SELECT {quoted} FROM "{table}"'
                ).all()
            )
        persisted_database_text = "\n".join(values)
    for secret in (
        raw_code,
        "virtual-provider",
        "virtual-subject",
        access_token,
        "correct horse battery staple",
    ):
        assert secret not in persisted_database_text
        assert secret not in "\n".join(record.getMessage() for record in caplog.records)


def test_binding_conflict_receipt_replays_and_code_retries_after_revoke(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    headers = _initialize_and_login(client)
    runtime = client.app.state.host_runtime
    now = datetime.now(UTC)
    owner = runtime.auth.authenticate_access(
        headers["Authorization"].removeprefix("Bearer "), now=now
    )
    other_user_id = uuid.uuid4()
    other = AuthenticatedSession(
        user_id=other_user_id,
        session_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        authenticated_at=now,
    )
    with client.app.state.test_sessions() as session, session.begin():
        session.add(
            AppUser(
                id=other_user_id,
                handle=f"binding_other_{other_user_id.hex[:8]}",
                status="active",
                version_id=1,
                created_at=now,
            )
        )
    winner_code = runtime.auth.create_binding_code(owner, channel="fake_wechat", now=now)
    loser_code = runtime.auth.create_binding_code(
        other, channel="fake_wechat", now=now
    )
    provider_account = f"private-provider-{uuid.uuid4()}"
    external_subject = f"private-subject-{uuid.uuid4()}"

    def payload(created) -> dict[str, str]:
        return {
            "code_id": str(created.code_id),
            "channel": "fake_wechat",
            "provider_account": provider_account,
            "external_subject": external_subject,
            "code": created.code,
        }

    winner = client.post(
        "/api/v1/channel-bindings/consume",
        headers={
            "Idempotency-Key": "binding-sequential-winner",
            "X-Channel-Adapter-Token": "a" * 32,
        },
        json=payload(winner_code),
    )
    assert winner.status_code == 200, winner.text
    conflict_headers = {
        "Idempotency-Key": "binding-sequential-conflict",
        "X-Channel-Adapter-Token": "a" * 32,
    }
    conflict = client.post(
        "/api/v1/channel-bindings/consume",
        headers=conflict_headers,
        json=payload(loser_code),
    )
    replay = client.post(
        "/api/v1/channel-bindings/consume",
        headers=conflict_headers,
        json=payload(loser_code),
    )
    assert conflict.status_code == replay.status_code == 409
    assert conflict.json()["error"]["code"] == "channel_identity_conflict"
    assert replay.json()["error"]["code"] == "channel_identity_conflict"

    with client.app.state.test_sessions() as session:
        code_row = session.get(ChannelBindingCode, loser_code.code_id)
        assert code_row is not None
        assert code_row.status == "active" and code_row.attempts == 0
        receipts = session.scalars(
            select(HostRequestReceiptRecord).where(
                HostRequestReceiptRecord.user_id == other_user_id,
                HostRequestReceiptRecord.operation == "binding.code.consume",
            )
        ).all()
        assert len(receipts) == 1
        assert receipts[0].result_json is not None
        assert '"__error_code":"channel_identity_conflict"' in receipts[0].result_json
        safe_receipt = receipts[0].result_json

    winner_binding_id = uuid.UUID(winner.json()["binding_id"])
    runtime.auth.revoke_binding(
        owner.user_id, winner_binding_id, now=now
    )
    retry = client.post(
        "/api/v1/channel-bindings/consume",
        headers={
            "Idempotency-Key": "binding-sequential-retry",
            "X-Channel-Adapter-Token": "a" * 32,
        },
        json=payload(loser_code),
    )
    assert retry.status_code == 200, retry.text
    with client.app.state.test_sessions() as session:
        code_row = session.get(ChannelBindingCode, loser_code.code_id)
        assert code_row is not None and code_row.status == "consumed"

    safe_output = "\n".join(
        (
            conflict.text,
            replay.text,
            safe_receipt,
            *(record.getMessage() for record in caplog.records),
        )
    )
    for private_value in (
        provider_account,
        external_subject,
        winner_code.code,
        loser_code.code,
        "uq_binding_active_subject",
        "IntegrityError",
    ):
        assert private_value not in safe_output


def test_authentication_error_envelope_has_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/modules")
    assert response.status_code == 401
    body = response.json()
    assert uuid.UUID(body["request_id"])
    assert body["error"]["code"] == "authentication_required"


def test_host_and_static_activity_import_identity_are_mutually_exclusive(client: TestClient) -> None:
    with pytest.raises(ValueError, match="mutually exclusive"):
        create_app(
            host_runtime=client.app.state.host_runtime,
            activity_import_identity=ImportIdentity(
                owner_id=uuid.uuid4(),
                channel="test",
                permissions=frozenset({"finance:read", "finance:write"}),
            ),
        )


def test_activity_import_requires_host_access_and_failed_auth_writes_nothing(
    client: TestClient,
) -> None:
    payload = {"markdown": "## API 虚拟活动"}
    request_headers = {"Idempotency-Key": "host-import-auth"}
    missing = client.post(
        "/api/v1/activity-imports/preview", headers=request_headers, json=payload
    )
    wrong = client.post(
        "/api/v1/activity-imports/preview",
        headers={**request_headers, "Authorization": "Bearer invalid-token"},
        json=payload,
    )
    assert (missing.status_code, wrong.status_code) == (401, 401)
    assert missing.json()["error"]["code"] == "authentication_required"
    assert wrong.json()["error"]["code"] == "session_revoked"
    with client.app.state.test_sessions() as session:
        assert session.scalar(select(func.count(ActivityImportBatch.id))) == 0


def test_activity_import_uses_authenticated_principal_and_revoked_token_is_zero_write(
    client: TestClient,
) -> None:
    headers = _initialize_and_login(client)
    created = client.post(
        "/api/v1/activity-imports/preview",
        headers={**headers, "Idempotency-Key": "host-import-ok"},
        json={"markdown": "## API 虚拟活动"},
    )
    assert created.status_code == 201, created.text
    with client.app.state.test_sessions() as session:
        row = session.scalar(select(ActivityImportBatch))
        assert row is not None
        assert row.owner_id == row.user_id
        receipt = session.get(CommandReceipt, row.preview_receipt_id)
        assert receipt is not None
        assert receipt.source_system.startswith("activity_import.preview:api_test:")

    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    revoked = client.post(
        "/api/v1/activity-imports/preview",
        headers={**headers, "Idempotency-Key": "host-import-revoked"},
        json={"markdown": "## 不应写入"},
    )
    assert revoked.status_code == 401
    assert revoked.json()["error"]["code"] == "session_revoked"
    with client.app.state.test_sessions() as session:
        assert session.scalar(select(func.count(ActivityImportBatch.id))) == 1


def test_auth_error_mapping_is_exhaustive_and_404_405_use_envelope(client: TestClient) -> None:
    from wife_system.api.app import AUTH_ERROR_STATUS_BY_CODE

    assert frozenset(AUTH_ERROR_STATUS_BY_CODE) == AUTH_ERROR_CODES

    @client.app.get("/_executor/auth-error/{code}")
    def raise_auth_error(code: str) -> None:
        retry_after = 7 if code == "login_rate_limited" else None
        raise AuthError(code, retry_after=retry_after)

    for code in sorted(AUTH_ERROR_CODES):
        response = client.get(f"/_executor/auth-error/{code}")
        assert response.status_code == AUTH_ERROR_STATUS_BY_CODE[code]
        assert response.json()["error"]["code"] == code
        assert uuid.UUID(response.json()["request_id"])
        if code == "login_rate_limited":
            assert response.headers["Retry-After"] == "7"

    missing = client.get("/definitely-not-a-route")
    wrong_method = client.put("/healthz")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "route_not_found"
    assert wrong_method.status_code == 405
    assert wrong_method.json()["error"]["code"] == "method_not_allowed"
