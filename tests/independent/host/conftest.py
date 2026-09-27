from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from wife_system.activity_import.service import ActivityImportService
from wife_system.api.app import create_app
from wife_system.finance.db import Base, make_engine, make_session_factory
from wife_system.finance.service import IdempotencyKeys
from wife_system.host.auth.service import AuthSecrets
from wife_system.host.factory import build_host_runtime
from wife_system.host.state import HostKeys


class VirtualFinanceAdapter:
    def __getattr__(self, name):
        if name.startswith(("list_", "get_", "account_", "monthly_", "record_")):
            return lambda *_args, **_kwargs: {"status": "ok", "items": []}
        raise AttributeError(name)


@pytest.fixture
def host_stack(tmp_path: Path) -> Iterator[tuple[TestClient, object, object]]:
    engine = make_engine(f"sqlite:///{(tmp_path / 'independent-host.sqlite3').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = make_session_factory(engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        connection.execute(text("INSERT INTO alembic_version VALUES ('p4_host_state')"))
    runtime = build_host_runtime(
        sessions=sessions,
        finance_adapter=VirtualFinanceAdapter(),
        auth_secrets=AuthSecrets(
            bootstrap_token=b"B" * 32,
            binding_hmac_key=b"H" * 32,
            adapter_token=b"A" * 32,
        ),
        state_keys=HostKeys({1: b"S" * 32}),
        cursor_secret=b"C" * 32,
    )
    from datetime import UTC, datetime
    runtime.auth.ensure_pending_owner(now=datetime.now(UTC))
    app = create_app(
        host_runtime=runtime,
        activity_import_service=ActivityImportService(
            sessions, IdempotencyKeys({1: b"independent-activity-key"})
        ),
    )
    with TestClient(app, client=("127.0.0.1", 43111), raise_server_exceptions=False) as client:
        yield client, runtime, sessions
    engine.dispose()


def owner_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/initialize",
        headers={"Idempotency-Key": "ind-init", "X-Bootstrap-Token": "B" * 32},
        json={"handle": "local_owner", "password": "virtual passphrase 123"},
    )
    assert response.status_code == 200, response.text
    login = client.post(
        "/api/v1/auth/login",
        json={
            "handle": "local_owner",
            "password": "virtual passphrase 123",
            "client_fingerprint": "independent-host",
            "device_name": "C11 fixture",
            "platform": "api_test",
        },
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}
