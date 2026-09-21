from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from wife_system.api.app import create_app
from wife_system.finance.db import Base, make_engine, make_session_factory
from wife_system.host.auth.service import AuthSecrets
from wife_system.host.factory import build_host_runtime
from wife_system.host.state import HostKeys


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
    app = create_app(host_runtime=runtime)
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


def test_authentication_error_envelope_has_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/modules")
    assert response.status_code == 401
    body = response.json()
    assert uuid.UUID(body["request_id"])
    assert body["error"]["code"] == "authentication_required"
