from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from tests.independent.host.history_fixtures import seed_p3_history
from wife_system.finance.models import BOOTSTRAP_USER_ID


ROOT = Path(__file__).resolve().parents[3]


def cfg(url: str) -> Config:
    value = Config(str(ROOT / "alembic.ini"))
    value.set_main_option("script_location", str(ROOT / "migrations"))
    value.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return value


def test_c11_sqlite_empty_upgrade_single_head_and_real_constraints(tmp_path: Path) -> None:
    url = f"sqlite:///{(tmp_path / 'empty.sqlite3').as_posix()}"
    command.upgrade(cfg(url), "head")
    engine = create_engine(url)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "p4_host_state"
        assert connection.scalar(text("PRAGMA foreign_key_check")) is None
        tables = set(inspect(connection).get_table_names())
    assert {"app_user", "agent_run", "pending_action", "memory_item", "memory_candidate"} <= tables
    fks = {item["name"] for item in inspect(engine).get_foreign_keys("agent_run")}
    assert "fk_run_user_pending" in fks
    engine.dispose()


def test_c11_sqlite_head_p3_head_keeps_old_fact_tables(tmp_path: Path) -> None:
    url = f"sqlite:///{(tmp_path / 'roundtrip.sqlite3').as_posix()}"
    config = cfg(url)
    command.upgrade(config, "head")
    engine = create_engine(url)
    with engine.connect() as connection:
        before = {name for name in inspect(connection).get_table_names() if name in {"account", "financial_transaction", "activity_template", "agent_run"}}
    engine.dispose()
    command.downgrade(config, "c82d7a4f901e")
    command.upgrade(config, "head")
    engine = create_engine(url)
    with engine.connect() as connection:
        assert before <= set(inspect(connection).get_table_names())
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "p4_host_state"
        assert connection.scalar(text("PRAGMA foreign_key_check")) is None
    engine.dispose()


def test_c11_sqlite_p3_history_forward_upgrade_preserves_p1_p2_p3_facts(
    tmp_path: Path,
) -> None:
    url = f"sqlite:///{(tmp_path / 'p3-history.sqlite3').as_posix()}"
    config = cfg(url)
    command.upgrade(config, "c82d7a4f901e")
    engine = create_engine(url)
    with engine.begin() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "c82d7a4f901e"
        values = seed_p3_history(connection)
    engine.dispose()

    command.upgrade(config, "p4_host_state")
    engine = create_engine(url)
    owner = BOOTSTRAP_USER_ID.hex
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "p4_host_state"
        assert connection.scalar(text("PRAGMA foreign_key_check")) is None
        assert connection.execute(
            text("SELECT name,currency,version_id,user_id FROM account WHERE id=:id"),
            {"id": values["account"]},
        ).one() == ("virtual P3 history account", "CNY", 1, owner)
        assert connection.execute(
            text("SELECT kind,name,user_id FROM category WHERE id=:id"),
            {"id": values["category"]},
        ).one() == ("expense", "virtual P3 history expense", owner)
        assert connection.execute(
            text("SELECT kind,status,currency,user_id FROM financial_transaction WHERE id=:id"),
            {"id": values["transaction"]},
        ).one() == ("expense", "posted", "CNY", owner)
        assert connection.execute(
            text(
                "SELECT line_no,entry_role,amount_minor,typeof(amount_minor),user_id "
                "FROM transaction_entry WHERE transaction_id=:id ORDER BY line_no"
            ),
            {"id": values["transaction"]},
        ).all() == [
            (1, "account", -4321, "integer", owner),
            (2, "expense", 4321, "integer", owner),
        ]
        assert connection.execute(
            text(
                "SELECT status,pause_reason,pending_action_id,module_id,profile_id,attempt_no,user_id "
                "FROM agent_run WHERE id=:id"
            ),
            {"id": values["run"]},
        ).one() == (
            "paused",
            "needs_confirmation",
            values["pending"],
            "daily_finance",
            "daily_finance.assistant@1",
            1,
            owner,
        )
        assert connection.execute(
            text(
                "SELECT status,action_json,module_id,profile_id,action_schema_version,user_id "
                "FROM pending_action WHERE id=:id"
            ),
            {"id": values["pending"]},
        ).one() == (
            "needs_confirmation",
            '{"amount":"43.21"}',
            "daily_finance",
            "daily_finance.assistant@1",
            1,
            owner,
        )
        assert connection.execute(
            text("SELECT status,owner_id,user_id FROM activity_import_batch WHERE id=:id"),
            {"id": values["import_batch"]},
        ).one() == ("previewed", owner, owner)
        assert connection.execute(
            text(
                "SELECT batch_id,ordinal,reference_minor,proposed_action,user_id "
                "FROM activity_import_candidate WHERE id=:id"
            ),
            {"id": values["import_candidate"]},
        ).one() == (values["import_batch"], 1, 2500, "create", owner)
        assert connection.scalar(
            text(
                "SELECT COUNT(*) FROM pending_action p LEFT JOIN agent_run r "
                "ON p.user_id=r.user_id AND p.run_id=r.id WHERE r.id IS NULL"
            )
        ) == 0
        assert connection.scalar(
            text(
                "SELECT COUNT(*) FROM agent_run r LEFT JOIN pending_action p "
                "ON r.user_id=p.user_id AND r.pending_action_id=p.id "
                "WHERE r.pending_action_id IS NOT NULL AND p.id IS NULL"
            )
        ) == 0
        assert connection.scalar(
            text(
                "SELECT COUNT(*) FROM activity_import_candidate c LEFT JOIN activity_import_batch b "
                "ON c.user_id=b.user_id AND c.batch_id=b.id WHERE b.id IS NULL"
            )
        ) == 0
        assert connection.scalar(
            text(
                "SELECT COUNT(*) FROM conversation WHERE id=:id AND user_id=:owner"
            ),
            {"id": values["conversation"], "owner": owner},
        ) == 1
    assert ScriptDirectory.from_config(config).get_heads() == ["p4_host_state"]
    engine.dispose()
