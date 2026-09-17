from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


HEAD = "7f3e2d1c9a4b"
P1_HEAD = "1377551283d0"


def config_for(url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    return config


def test_p2_migration_upgrade_repeat_downgrade_and_recover(tmp_path: Path) -> None:
    url = f"sqlite:///{(tmp_path / 'p2-agent.sqlite3').as_posix()}"
    config = config_for(url)
    command.upgrade(config, "head")
    command.upgrade(config, "head")
    engine = create_engine(url)
    inspector = inspect(engine)
    assert {"agent_run", "pending_action"}.issubset(inspector.get_table_names())
    assert engine.connect().scalar(text("SELECT version_num FROM alembic_version")) == HEAD
    pending_columns = {column["name"] for column in inspector.get_columns("pending_action")}
    assert {
        "source_system",
        "action_json",
        "resource_versions_json",
        "version_id",
        "expires_at",
        "final_result_json",
    }.issubset(pending_columns)
    engine.dispose()

    command.downgrade(config, P1_HEAD)
    engine = create_engine(url)
    assert "agent_run" not in inspect(engine).get_table_names()
    assert engine.connect().scalar(text("SELECT version_num FROM alembic_version")) == P1_HEAD
    engine.dispose()
    command.upgrade(config, "head")
