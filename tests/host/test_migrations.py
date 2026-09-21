from __future__ import annotations

import ast
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from wife_system.finance.models import BOOTSTRAP_USER_ID


P3_HEAD = "c82d7a4f901e"
P4_IDENTITY = "p4_host_identity"
P4_USER_SCOPE = "p4_host_user_scope"
P4_HEAD = "p4_host_state"
ROOT = Path(__file__).resolve().parents[2]
SCOPED_TABLES = {
    "account", "category", "command_receipt", "audit_event",
    "financial_transaction", "transaction_entry", "activity_template",
    "activity_template_revision", "activity_import_batch",
    "activity_import_candidate", "activity_occurrence",
    "activity_entry_allocation", "income_schedule",
    "income_schedule_version", "income_expectation",
    "income_expectation_match", "budget_plan", "budget_version",
    "budget_allocation", "agent_run", "pending_action",
}
P4_STATE_TABLES = {
    "app_user", "password_credential", "device_session",
    "session_refresh_token", "channel_binding_code",
    "channel_identity_binding", "channel_binding_audit", "conversation",
    "conversation_message", "memory_candidate", "memory_item",
    "module_setting", "host_request_receipt",
}


def migration_config(url: str) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def sqlite_url(tmp_path: Path, name: str) -> str:
    return f"sqlite:///{(tmp_path / name).as_posix()}"


def test_p4_revisions_are_one_linear_head_and_identifiers_are_bounded() -> None:
    script = ScriptDirectory.from_config(migration_config("sqlite://"))
    assert script.get_heads() == [P4_HEAD]
    assert script.get_revision(P4_HEAD).down_revision == P4_USER_SCOPE
    assert script.get_revision(P4_USER_SCOPE).down_revision == P4_IDENTITY
    assert script.get_revision(P4_IDENTITY).down_revision == P3_HEAD

    for filename in ("p4_host_identity.py", "p4_host_user_scope.py", "p4_host_state.py"):
        tree = ast.parse((ROOT / "migrations" / "versions" / filename).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                    assert len(keyword.value.value) <= 63


def test_empty_upgrade_has_bootstrap_scope_state_and_safe_downgrade(tmp_path: Path) -> None:
    url = sqlite_url(tmp_path, "empty.db")
    config = migration_config(url)
    command.upgrade(config, "head")
    command.upgrade(config, "head")
    engine = create_engine(url)
    inspector = inspect(engine)
    assert SCOPED_TABLES | P4_STATE_TABLES <= set(inspector.get_table_names())
    for table in SCOPED_TABLES:
        user_column = next(column for column in inspector.get_columns(table) if column["name"] == "user_id")
        assert user_column["nullable"] is False
    with engine.connect() as connection:
        owner = connection.execute(text(
            "SELECT id,status,handle_normalized,bootstrap_marker,version_id FROM app_user"
        )).one()
        assert uuid.UUID(owner.id) == BOOTSTRAP_USER_ID
        assert owner.status == "pending_setup"
        assert owner.handle_normalized is None
        assert owner.bootstrap_marker == "bootstrap-owner"
        assert owner.version_id == 1
        assert connection.scalar(text("PRAGMA foreign_key_check")) is None
    engine.dispose()

    command.downgrade(config, P3_HEAD)
    engine = create_engine(url)
    inspector = inspect(engine)
    assert not (P4_STATE_TABLES & set(inspector.get_table_names()))
    assert all("user_id" not in {column["name"] for column in inspector.get_columns(table)} for table in SCOPED_TABLES)
    engine.dispose()


def _seed_coherent_p3_history(connection) -> tuple[str, str, str]:
    legacy_owner = uuid.UUID("10000000-0000-0000-0000-000000000001").hex
    account_id = uuid.uuid4().hex
    run_id = uuid.uuid4().hex
    pending_id = uuid.uuid4().hex
    conversation_id = uuid.uuid4().hex
    connection.execute(text(
        "INSERT INTO account (id,name,currency,archived_at,created_at,version_id) "
        "VALUES (:id,'legacy virtual account','CNY',NULL,CURRENT_TIMESTAMP,1)"
    ), {"id": account_id})
    connection.execute(text(
        "INSERT INTO agent_run "
        "(id,actor_id,conversation_id,source_system,source_event_digest,request_fingerprint,status,"
        "pause_reason,pending_action_id,answer,error_code,result_json,events_json,model_name,created_at,updated_at) "
        "VALUES (:id,:owner,:conversation,'test','event-digest','request-fingerprint','paused',"
        "'needs_confirmation',:pending,NULL,NULL,NULL,NULL,'fake',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
    ), {"id": run_id, "owner": legacy_owner, "conversation": conversation_id, "pending": pending_id})
    connection.execute(text(
        "INSERT INTO pending_action "
        "(id,run_id,actor_id,conversation_id,source_system,action_type,action_json,missing_fields_json,"
        "resource_versions_json,status,version_id,confirmation_code,approval_grant_id,final_result_json,"
        "created_at,expires_at,updated_at) VALUES "
        "(:id,:run,:owner,:conversation,'test','record_expense','{}','[]','{}','needs_confirmation',1,"
        "'ABC123',NULL,NULL,CURRENT_TIMESTAMP,datetime(CURRENT_TIMESTAMP,'+1 day'),CURRENT_TIMESTAMP)"
    ), {"id": pending_id, "run": run_id, "owner": legacy_owner, "conversation": conversation_id})
    return account_id, run_id, pending_id


def test_existing_p3_history_is_scoped_and_survives_round_trip(tmp_path: Path) -> None:
    url = sqlite_url(tmp_path, "history.db")
    config = migration_config(url)
    command.upgrade(config, P3_HEAD)
    engine = create_engine(url)
    with engine.begin() as connection:
        account_id, run_id, pending_id = _seed_coherent_p3_history(connection)
    engine.dispose()

    command.upgrade(config, "head")
    engine = create_engine(url)
    with engine.connect() as connection:
        expected = BOOTSTRAP_USER_ID.hex
        assert connection.scalar(text("SELECT user_id FROM account WHERE id=:id"), {"id": account_id}) == expected
        run = connection.execute(text(
            "SELECT user_id,actor_id,module_id,profile_id,profile_version,attempt_no,action_schema_version "
            "FROM agent_run WHERE id=:id"
        ), {"id": run_id}).one()
        assert run == (expected, expected, "daily_finance", "daily_finance.assistant@1", "1.0.0", 1, 1)
        pending = connection.execute(text(
            "SELECT user_id,actor_id,module_id,profile_id,action_schema_version "
            "FROM pending_action WHERE id=:id"
        ), {"id": pending_id}).one()
        assert pending == (expected, expected, "daily_finance", "daily_finance.assistant@1", 1)
        assert connection.scalar(text("SELECT COUNT(*) FROM conversation")) == 1
        assert connection.scalar(text("PRAGMA foreign_key_check")) is None
    engine.dispose()

    command.downgrade(config, P3_HEAD)
    engine = create_engine(url)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT name FROM account WHERE id=:id"), {"id": account_id}) == "legacy virtual account"
        assert connection.scalar(text("SELECT status FROM agent_run WHERE id=:id"), {"id": run_id}) == "paused"
        assert connection.scalar(text("SELECT status FROM pending_action WHERE id=:id"), {"id": pending_id}) == "needs_confirmation"
        assert connection.scalar(text("PRAGMA foreign_key_check")) is None
    engine.dispose()


def test_contradictory_legacy_owners_are_rejected_before_identity_schema(tmp_path: Path) -> None:
    url = sqlite_url(tmp_path, "contradictory.db")
    config = migration_config(url)
    command.upgrade(config, P3_HEAD)
    engine = create_engine(url)
    with engine.begin() as connection:
        _, run_id, pending_id = _seed_coherent_p3_history(connection)
        connection.execute(
            text("UPDATE pending_action SET actor_id=:owner WHERE id=:id"),
            {"owner": uuid.UUID("10000000-0000-0000-0000-000000000002").hex, "id": pending_id},
        )
    engine.dispose()

    with pytest.raises(RuntimeError, match="contradictory legacy owners"):
        command.upgrade(config, "head")
    engine = create_engine(url)
    assert engine.connect().scalar(text("SELECT version_num FROM alembic_version")) == P3_HEAD
    assert "app_user" not in inspect(engine).get_table_names()
    engine.dispose()


def test_composite_scope_fk_rejects_cross_user_reference(tmp_path: Path) -> None:
    url = sqlite_url(tmp_path, "cross-user.db")
    command.upgrade(migration_config(url), "head")
    engine = create_engine(url)
    second_user = uuid.uuid4().hex
    account_id = uuid.uuid4().hex
    receipt_id = uuid.uuid4().hex
    transaction_id = uuid.uuid4().hex
    entry_id = uuid.uuid4().hex
    with engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))
        connection.execute(text(
            "INSERT INTO app_user (id,handle_normalized,status,bootstrap_marker,initialized_at,deactivated_at,version_id,created_at) "
            "VALUES (:id,'second_user','active',NULL,CURRENT_TIMESTAMP,NULL,1,CURRENT_TIMESTAMP)"
        ), {"id": second_user})
        connection.execute(text(
            "INSERT INTO account (id,user_id,name,currency,archived_at,created_at,version_id) "
            "VALUES (:id,:user,'second account','CNY',NULL,CURRENT_TIMESTAMP,1)"
        ), {"id": account_id, "user": second_user})
        connection.execute(text(
            "INSERT INTO command_receipt "
            "(id,user_id,source_system,key_version,key_digest,request_fingerprint,command_name,result_type,"
            "result_id,result_json,completed_at,created_at) VALUES "
            "(:id,:user,'test',1,'digest','fingerprint','expense',NULL,NULL,NULL,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
        ), {"id": receipt_id, "user": BOOTSTRAP_USER_ID.hex})
        connection.execute(text(
            "INSERT INTO financial_transaction "
            "(id,user_id,kind,status,occurred_at,currency,related_transaction_id,relation_kind,command_receipt_id,created_at) "
            "VALUES (:id,:user,'expense','posted',CURRENT_TIMESTAMP,'CNY',NULL,NULL,:receipt,CURRENT_TIMESTAMP)"
        ), {"id": transaction_id, "user": BOOTSTRAP_USER_ID.hex, "receipt": receipt_id})
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("PRAGMA foreign_keys=ON"))
            connection.execute(text(
                "INSERT INTO transaction_entry "
                "(id,user_id,transaction_id,line_no,entry_role,amount_minor,account_id,category_id) "
                "VALUES (:id,:user,:transaction,1,'account',-100,:account,NULL)"
            ), {
                "id": entry_id, "user": BOOTSTRAP_USER_ID.hex,
                "transaction": transaction_id, "account": account_id,
            })
    engine.dispose()
