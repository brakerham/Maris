from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from wife_system.agent.providers import ScriptedModelProvider
from wife_system.api.production import (
    ProductionConfig,
    ProductionConfigError,
    create_production_app,
)
from wife_system.finance.db import Base, make_engine


def _config(database_url: str) -> ProductionConfig:
    return ProductionConfig(
        database_url=database_url,
        bootstrap_token=b"b" * 32,
        binding_hmac_key=b"h" * 32,
        adapter_token=b"a" * 32,
        host_state_key=b"s" * 32,
        cursor_key=b"c" * 32,
        agent_digest_key=b"d" * 32,
        finance_receipt_key=b"f" * 32,
    )


def _database(path: Path) -> str:
    url = f"sqlite+pysqlite:///{path}"
    engine = make_engine(url)
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        connection.execute(
            text("INSERT INTO alembic_version(version_num) VALUES ('p4_host_state')")
        )
    engine.dispose()
    return url


def test_production_config_fails_closed_without_echoing_secret() -> None:
    secret = "do-not-echo-this-secret"
    with pytest.raises(ProductionConfigError) as captured:
        ProductionConfig.from_environment(
            {
                "WIFE_DATABASE_URL": "sqlite+pysqlite:///:memory:",
                "WIFE_BOOTSTRAP_TOKEN": secret,
            }
        )
    assert secret not in str(captured.value)


def test_production_factory_readiness_tracks_provider(tmp_path: Path) -> None:
    database_url = _database(tmp_path / "production.db")
    unconfigured = TestClient(create_production_app(_config(database_url)))
    assert unconfigured.get("/healthz").status_code == 200
    response = unconfigured.get("/readyz")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "agent_provider_unconfigured"

    configured = TestClient(
        create_production_app(
            _config(database_url), provider=ScriptedModelProvider([])
        )
    )
    assert configured.get("/readyz").status_code == 200
