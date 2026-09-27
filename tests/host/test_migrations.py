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
from wife_system.finance.db import Base
from wife_system.agent import models as agent_models  # noqa: F401
from wife_system.host import state_models  # noqa: F401


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
    binding_columns = {column["name"] for column in inspector.get_columns("channel_binding_code")}
    assert {"status", "revoked_at"} <= binding_columns
    binding_indexes = {item["name"]: item for item in inspector.get_indexes("channel_binding_code")}
    assert bool(binding_indexes["uq_binding_code_user_channel_active"]["unique"])
    assert binding_indexes["uq_binding_code_user_channel_active"]["column_names"] == ["user_id", "channel"]
    binding_checks = {item["name"] for item in inspector.get_check_constraints("channel_binding_code")}
    assert "ck_channel_binding_code_status" in binding_checks
    run_columns = {column["name"]: column for column in inspector.get_columns("agent_run")}
    assert run_columns["module_version"]["nullable"] is False
    assert run_columns["module_version"]["type"].length == 32
    candidate_columns = {
        column["name"]: column for column in inspector.get_columns("memory_candidate")
    }
    assert candidate_columns["proposed_by_profile_version"]["nullable"] is False
    assert candidate_columns["proposed_by_profile_version"]["type"].length == 32
    item_checks = {
        item["name"]: item["sqltext"]
        for item in inspector.get_check_constraints("memory_item")
    }
    assert "invalidated" in item_checks["ck_memory_item_status"]
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
            "SELECT user_id,actor_id,module_id,module_version,profile_id,profile_version,"
            "attempt_no,action_schema_version "
            "FROM agent_run WHERE id=:id"
        ), {"id": run_id}).one()
        assert run == (
            expected, expected, "daily_finance", "1.0.0",
            "daily_finance.assistant@1", "1.0.0", 1, 1,
        )
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


def _insert_active_user(connection, user_id: str, handle: str) -> None:
    connection.execute(text(
        "INSERT INTO app_user "
        "(id,handle_normalized,status,bootstrap_marker,initialized_at,deactivated_at,version_id,created_at) "
        "VALUES (:id,:handle,'active',NULL,CURRENT_TIMESTAMP,NULL,1,CURRENT_TIMESTAMP)"
    ), {"id": user_id, "handle": handle})


def _insert_conversation(connection, user_id: str, conversation_id: str) -> None:
    connection.execute(text(
        "INSERT INTO conversation "
        "(id,user_id,channel,module_id,profile_id,status,last_message_at,created_at) "
        "VALUES (:id,:user,'api_test','daily_finance','daily_finance.assistant@1',"
        "'active',NULL,CURRENT_TIMESTAMP)"
    ), {"id": conversation_id, "user": user_id})


def _insert_run(connection, *, user_id: str, run_id: str, conversation_id: str, suffix: str,
                status: str = "paused", pending_action_id: str | None = None) -> None:
    connection.execute(text(
        "INSERT INTO agent_run "
        "(id,user_id,actor_id,conversation_id,source_system,source_event_digest,request_fingerprint,"
        "status,pause_reason,pending_action_id,answer,error_code,result_json,events_json,model_name,"
        "module_id,module_version,profile_id,profile_version,attempt_no,lease_expires_at,action_schema_version,"
        "created_at,updated_at) VALUES "
        "(:id,:user,:user,:conversation,'test',:digest,:fingerprint,:status,NULL,:pending,NULL,NULL,"
        "NULL,NULL,'fake','daily_finance','1.0.0','daily_finance.assistant@1','1.0.0',1,NULL,1,"
        "CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
    ), {
        "id": run_id, "user": user_id, "conversation": conversation_id,
        "digest": f"digest-{suffix}", "fingerprint": f"fingerprint-{suffix}",
        "status": status, "pending": pending_action_id,
    })


def _insert_pending(connection, *, user_id: str, pending_id: str, run_id: str,
                    conversation_id: str, suffix: str, status: str = "needs_confirmation") -> None:
    connection.execute(text(
        "INSERT INTO pending_action "
        "(id,user_id,run_id,actor_id,conversation_id,source_system,action_type,action_json,"
        "missing_fields_json,resource_versions_json,status,version_id,confirmation_code,"
        "approval_grant_id,final_result_json,module_id,profile_id,action_schema_version,"
        "commit_attempt_no,commit_lease_expires_at,created_at,expires_at,updated_at) VALUES "
        "(:id,:user,:run,:user,:conversation,'test','record_expense','{}','[]','{}',:status,1,"
        ":code,NULL,NULL,'daily_finance','daily_finance.assistant@1',1,0,NULL,CURRENT_TIMESTAMP,"
        "datetime(CURRENT_TIMESTAMP,'+1 day'),CURRENT_TIMESTAMP)"
    ), {
        "id": pending_id, "user": user_id, "run": run_id,
        "conversation": conversation_id, "status": status, "code": f"C{suffix}"[:16],
    })


def test_r1_constraint_shapes_match_orm_metadata(tmp_path: Path) -> None:
    url = sqlite_url(tmp_path, "r1-shapes.db")
    command.upgrade(migration_config(url), "head")
    engine = create_engine(url)
    inspector = inspect(engine)

    def fk_map(table: str) -> dict[str, tuple[tuple[str, ...], str, tuple[str, ...]]]:
        return {
            item["name"]: (
                tuple(item["constrained_columns"]),
                item["referred_table"],
                tuple(item["referred_columns"]),
            )
            for item in inspector.get_foreign_keys(table)
        }

    assert fk_map("memory_item")["fk_memory_item_user_superseded"] == (
        ("user_id", "superseded_by_id"), "memory_item", ("user_id", "id"),
    )
    assert fk_map("memory_candidate")["fk_memory_candidate_user_item"] == (
        ("user_id", "memory_item_id"), "memory_item", ("user_id", "id"),
    )
    assert fk_map("agent_run")["fk_run_user_pending"] == (
        ("user_id", "pending_action_id"), "pending_action", ("user_id", "id"),
    )
    assert fk_map("pending_action")["fk_pending_user_run"] == (
        ("user_id", "run_id"), "agent_run", ("user_id", "id"),
    )
    assert "fk_pending_action_run_id_agent_run" not in fk_map("pending_action")
    assert fk_map("conversation_message")["fk_message_user_run"] == (
        ("user_id", "run_id"), "agent_run", ("user_id", "id"),
    )

    for table_name, names in {
        "memory_item": {"uq_memory_item_user_id"},
        "conversation_message": {"uq_message_user_run_sequence"},
        "agent_run": {"uq_agent_run_user_id"},
        "pending_action": {"uq_pending_action_user_id"},
    }.items():
        actual = {item["name"] for item in inspector.get_unique_constraints(table_name)}
        assert names <= actual

    assert {"commit_attempt_no", "commit_lease_expires_at"} <= {
        column["name"] for column in inspector.get_columns("pending_action")
    }
    assert {"run_id", "run_sequence", "tool_call_id"} <= {
        column["name"] for column in inspector.get_columns("conversation_message")
    }

    expected_orm_constraints = {
        "fk_memory_item_user_superseded",
        "fk_memory_candidate_user_item",
        "fk_run_user_pending",
        "fk_pending_user_run",
        "fk_message_user_run",
        "uq_memory_item_user_id",
        "uq_message_user_run_sequence",
        "uq_agent_run_user_id",
        "uq_pending_action_user_id",
    }
    orm_names = {
        constraint.name
        for table in Base.metadata.tables.values()
        for constraint in table.constraints
        if constraint.name is not None
    }
    assert expected_orm_constraints <= orm_names
    engine.dispose()


def test_r1_composite_foreign_keys_reject_cross_user_direct_sql(tmp_path: Path) -> None:
    url = sqlite_url(tmp_path, "r1-cross-user.db")
    command.upgrade(migration_config(url), "head")
    engine = create_engine(url)
    user_a = BOOTSTRAP_USER_ID.hex
    user_b = uuid.uuid4().hex
    conversation_a, conversation_b = uuid.uuid4().hex, uuid.uuid4().hex
    run_a, run_b = uuid.uuid4().hex, uuid.uuid4().hex
    pending_b = uuid.uuid4().hex
    item_a, item_b = uuid.uuid4().hex, uuid.uuid4().hex
    with engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))
        _insert_active_user(connection, user_b, "r1_other")
        _insert_conversation(connection, user_a, conversation_a)
        _insert_conversation(connection, user_b, conversation_b)
        _insert_run(connection, user_id=user_a, run_id=run_a, conversation_id=conversation_a, suffix="a")
        _insert_run(connection, user_id=user_b, run_id=run_b, conversation_id=conversation_b, suffix="b")
        _insert_pending(
            connection, user_id=user_b, pending_id=pending_b, run_id=run_b,
            conversation_id=conversation_b, suffix="B",
        )
        for item_id, user_id in ((item_a, user_a), (item_b, user_b)):
            connection.execute(text(
                "INSERT INTO memory_item "
                "(id,user_id,namespace,kind,value_json,tags_json,source_type,source_ref_digest,"
                "sensitivity,status,confirmed_at,expires_at,deleted_at,superseded_by_id,audit_id,version_id) "
                "VALUES (:id,:user,'daily_finance','preference','{}','[]','test',:digest,"
                "'private','active',CURRENT_TIMESTAMP,NULL,NULL,NULL,:audit,1)"
            ), {"id": item_id, "user": user_id, "digest": uuid.uuid4().hex * 2, "audit": uuid.uuid4().hex})

    failing_statements = [
        ("UPDATE memory_item SET superseded_by_id=:foreign WHERE id=:local", {"foreign": item_b, "local": item_a}),
        (
            "INSERT INTO memory_candidate "
            "(id,user_id,source_namespace,target_namespace,kind,value_json,tags_json,source_type,"
            "source_ref_digest,sensitivity,status,proposed_by_profile_id,proposed_by_profile_version,"
            "created_at,expires_at,"
            "decided_at,memory_item_id,audit_id,version_id) VALUES "
            "(:id,:user,'daily_finance','daily_finance','preference','{}','[]','test',:digest,"
            "'private','confirmed','daily_finance.assistant@1','1.0.0',CURRENT_TIMESTAMP,"
            "datetime(CURRENT_TIMESTAMP,'+1 day'),NULL,:foreign,NULL,1)",
            {"id": uuid.uuid4().hex, "user": user_a, "digest": uuid.uuid4().hex * 2, "foreign": item_b},
        ),
        ("UPDATE agent_run SET pending_action_id=:foreign WHERE id=:local", {"foreign": pending_b, "local": run_a}),
        (
            "INSERT INTO conversation_message "
            "(id,user_id,conversation_id,run_id,run_sequence,tool_call_id,role,content,content_digest,"
            "sensitivity,created_at,deleted_at) VALUES "
            "(:id,:user,:conversation,:foreign,1,NULL,'assistant','virtual',:digest,'private',"
            "CURRENT_TIMESTAMP,NULL)",
            {"id": uuid.uuid4().hex, "user": user_a, "conversation": conversation_a,
             "foreign": run_b, "digest": uuid.uuid4().hex * 2},
        ),
    ]
    for statement, params in failing_statements:
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(text("PRAGMA foreign_keys=ON"))
                connection.execute(text(statement), params)
    engine.dispose()


def test_cancelled_runs_and_pending_states_survive_head_p3_head_round_trip(tmp_path: Path) -> None:
    url = sqlite_url(tmp_path, "r1-cancelled-roundtrip.db")
    config = migration_config(url)
    command.upgrade(config, "head")
    engine = create_engine(url)
    user_id = BOOTSTRAP_USER_ID.hex
    conversation_id = uuid.uuid4().hex
    pending_states = (
        "needs_input", "needs_confirmation", "committing",
        "committed", "expired", "cancelled",
    )
    run_ids: list[str] = []
    pending_ids: list[str] = []
    with engine.begin() as connection:
        _insert_conversation(connection, user_id, conversation_id)
        for index, pending_status in enumerate(pending_states):
            run_id, pending_id = uuid.uuid4().hex, uuid.uuid4().hex
            run_ids.append(run_id)
            pending_ids.append(pending_id)
            _insert_run(
                connection, user_id=user_id, run_id=run_id,
                conversation_id=conversation_id, suffix=str(index), status="cancelled",
            )
            _insert_pending(
                connection, user_id=user_id, pending_id=pending_id, run_id=run_id,
                conversation_id=conversation_id, suffix=str(index), status=pending_status,
            )
            connection.execute(
                text("UPDATE agent_run SET pending_action_id=:pending WHERE id=:run"),
                {"pending": pending_id, "run": run_id},
            )
    engine.dispose()

    command.downgrade(config, P3_HEAD)
    engine = create_engine(url)
    with engine.connect() as connection:
        rows = connection.execute(text(
            "SELECT status,error_code,pause_reason FROM agent_run ORDER BY source_event_digest"
        )).all()
        assert rows == [("error", "cancelled", None)] * len(pending_states)
        assert set(connection.execute(text("SELECT status FROM pending_action")).scalars()) == set(pending_states)
        assert connection.scalar(text("PRAGMA foreign_key_check")) is None
    engine.dispose()

    command.upgrade(config, "head")
    engine = create_engine(url)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT COUNT(*) FROM agent_run WHERE error_code='cancelled'")) == len(run_ids)
        assert connection.scalar(text("SELECT COUNT(*) FROM pending_action")) == len(pending_ids)
        assert connection.scalar(text("PRAGMA foreign_key_check")) is None
    engine.dispose()
