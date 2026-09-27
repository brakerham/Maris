"""Executor-only real PostgreSQL evidence for P4-B6-R2-S2.

These tests intentionally migrate random schemas with Alembic and exercise real
PostgreSQL transactions.  They are execution-party evidence, not independent
acceptance tests.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import event, inspect, select, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import IntegrityError

from wife_system.agent.application import (
    AgentApplicationError,
    build_agent_application,
)
from wife_system.agent.finance_tools import FinanceToolAdapter
from wife_system.agent.models import AgentRunRecord, PendingActionRecord
from wife_system.agent.pending import PendingActionStore
from wife_system.agent.providers import ScriptedModelProvider
from wife_system.agent.types import (
    AgentRunResult,
    AssistantTurn,
    ConversationMessage,
    RunStatus,
    ToolCall,
)
from wife_system.api.app import create_app
from wife_system.api.production import ProductionConfig, create_production_app
from wife_system.finance.db import make_engine, make_session_factory
from wife_system.finance.models import BOOTSTRAP_USER_ID
from wife_system.finance.schemas import CreateAccount, CreateCategory
from wife_system.finance.service import FinanceService, IdempotencyKeys
from wife_system.host.auth.models import AppUser
from wife_system.host.auth.service import AuthSecrets
from wife_system.host.cursor import InvalidCursorError
from wife_system.host.events import InProcessEventBus
from wife_system.host.factory import build_host_runtime
from wife_system.host.state import (
    HostIdempotency,
    HostKeys,
    HostStateError,
    MemoryService,
)
from wife_system.host.state_models import (
    ConversationMessageRecord,
    ConversationRecord,
    HostRequestReceiptRecord,
    MemoryCandidateRecord,
    MemoryItemRecord,
    ModuleSettingRecord,
)
from wife_system.host.workflows import RunLeaseCoordinator, WorkflowError


P3_HEAD = "c82d7a4f901e"
P4_HEAD = "p4_host_state"
ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


def migration_config(url: str) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def isolated_url(raw_url: str, schema: str) -> str:
    parsed = make_url(raw_url)
    query = dict(parsed.query)
    query["options"] = f"-csearch_path={schema},public"
    return parsed.set(query=query).render_as_string(hide_password=False)


@dataclass(frozen=True)
class PostgreSQLR2Harness:
    raw_url: str
    schema: str
    url: str
    admin: Engine
    engine: Engine
    sessions: object


@contextmanager
def migrated_schema(
    raw_url: str,
    admin: Engine,
    *,
    prefix: str,
    revision: str = P4_HEAD,
) -> Iterator[tuple[str, str, Engine]]:
    schema = f"{prefix}_{uuid.uuid4().hex}"
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    url = isolated_url(raw_url, schema)
    engine: Engine | None = None
    try:
        command.upgrade(migration_config(url), revision)
        engine = make_engine(url)
        yield schema, url, engine
    finally:
        if engine is not None:
            engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))


@pytest.fixture(scope="module")
def pg_r2() -> Iterator[PostgreSQLR2Harness]:
    raw_url = os.getenv("FINANCE_TEST_POSTGRES_URL")
    if not raw_url or make_url(raw_url).get_backend_name() != "postgresql":
        pytest.skip("FINANCE_TEST_POSTGRES_URL is required for P4-B6-R2-S2")
    admin = make_engine(raw_url)
    with migrated_schema(raw_url, admin, prefix="p4_b6_r2_s2") as (
        schema,
        url,
        engine,
    ):
        yield PostgreSQLR2Harness(
            raw_url=raw_url,
            schema=schema,
            url=url,
            admin=admin,
            engine=engine,
            sessions=make_session_factory(engine),
        )
    admin.dispose()


def _stack(pg: PostgreSQLR2Harness):
    sessions = pg.sessions
    finance = FinanceService(
        sessions,
        IdempotencyKeys({1: b"p4-r2-postgresql-finance-key"}),
        user_id=BOOTSTRAP_USER_ID,
    )
    pending = PendingActionStore(sessions)
    adapter = FinanceToolAdapter(finance, pending)
    runtime = build_host_runtime(
        sessions=sessions,
        finance_adapter=adapter,
        auth_secrets=AuthSecrets(
            bootstrap_token=b"b" * 32,
            binding_hmac_key=b"h" * 32,
            adapter_token=b"a" * 32,
        ),
        state_keys=HostKeys({1: b"s" * 32}),
        cursor_secret=b"c" * 32,
    )
    return finance, pending, adapter, runtime


def _conversation(runtime, *, key: str, now: datetime = NOW):
    return runtime.conversations.create(
        user_id=BOOTSTRAP_USER_ID,
        channel="api_test",
        module_id="daily_finance",
        profile_id="daily_finance.assistant@1",
        idempotency_key=key,
        now=now,
    )[0]


def _candidate_application(pg: PostgreSQLR2Harness, *, suffix: str):
    finance, _, _, runtime = _stack(pg)
    account = finance.create_account(
        CreateAccount(
            source_system="p4-r2-pg",
            source_event_id=f"account-{suffix}",
            name=f"虚拟账户-{suffix}",
        )
    )
    category = finance.create_category(
        CreateCategory(
            source_system="p4-r2-pg",
            source_event_id=f"category-{suffix}",
            kind="expense",
            name=f"虚拟分类-{suffix}",
        )
    )
    conversation = _conversation(runtime, key=f"conversation-{suffix}")
    provider = ScriptedModelProvider(
        [
            AssistantTurn(
                tool_calls=(
                    ToolCall(
                        id=f"tool-{suffix}",
                        name="finance_record_expense",
                        arguments={
                            "amount": "18.00",
                            "account_id": str(account.result_id),
                            "category_id": str(category.result_id),
                        },
                    ),
                )
            )
        ]
    )
    application = build_agent_application(
        sessions=pg.sessions,
        finance=finance,
        provider=provider,
        digest_key=b"p4-r2-postgresql-agent-key-32b",
        host_runtime=runtime,
    )
    candidate = application.start(
        actor_id=BOOTSTRAP_USER_ID,
        conversation_id=conversation.id,
        client_event_id=uuid.uuid4(),
        message=f"虚拟午饭 {suffix}",
        permissions=frozenset({"finance:write"}),
        received_at=NOW,
        channel="api_test",
    )
    assert candidate.status == "paused"
    assert candidate.result is not None
    return finance, runtime, application, conversation, candidate


def _insert_p3_history(connection) -> dict[str, uuid.UUID]:
    values = {
        name: uuid.uuid4()
        for name in (
            "account",
            "category",
            "finance_receipt",
            "transaction",
            "account_entry",
            "expense_entry",
            "run",
            "pending",
            "conversation",
            "preview_receipt",
            "import_batch",
            "import_candidate",
        )
    }
    connection.execute(
        text(
            "INSERT INTO account (id,name,currency,archived_at,created_at,version_id) "
            "VALUES (:id,'legacy virtual account','CNY',NULL,:now,1)"
        ),
        {"id": values["account"], "now": NOW},
    )
    connection.execute(
        text(
            "INSERT INTO category "
            "(id,kind,name,name_normalized,archived_at,created_at,version_id) "
            "VALUES (:id,'expense','legacy virtual expense','legacy virtual expense',NULL,:now,1)"
        ),
        {"id": values["category"], "now": NOW},
    )
    connection.execute(
        text(
            "INSERT INTO command_receipt "
            "(id,source_system,key_version,key_digest,request_fingerprint,command_name,"
            "result_type,result_id,result_json,completed_at,created_at) VALUES "
            "(:id,'r3-executor-history',1,:digest,:fingerprint,'record_expense',"
            "'financial_transaction',:result_id,NULL,:now,:now)"
        ),
        {
            "id": values["finance_receipt"],
            "digest": "a" * 64,
            "fingerprint": "b" * 64,
            "result_id": values["transaction"],
            "now": NOW,
        },
    )
    connection.execute(
        text(
            "INSERT INTO financial_transaction "
            "(id,kind,status,occurred_at,currency,related_transaction_id,relation_kind,"
            "command_receipt_id,created_at) VALUES "
            "(:id,'expense','posted',:now,'CNY',NULL,NULL,:receipt,:now)"
        ),
        {
            "id": values["transaction"],
            "receipt": values["finance_receipt"],
            "now": NOW,
        },
    )
    connection.execute(
        text(
            "INSERT INTO transaction_entry "
            "(id,transaction_id,line_no,entry_role,amount_minor,account_id,category_id) VALUES "
            "(:account_entry,:transaction,1,'account',-4321,:account,NULL),"
            "(:expense_entry,:transaction,2,'expense',4321,NULL,:category)"
        ),
        {
            "account_entry": values["account_entry"],
            "expense_entry": values["expense_entry"],
            "transaction": values["transaction"],
            "account": values["account"],
            "category": values["category"],
        },
    )
    connection.execute(
        text(
            "INSERT INTO agent_run "
            "(id,actor_id,conversation_id,source_system,source_event_digest,request_fingerprint,status,"
            "pause_reason,pending_action_id,answer,error_code,result_json,events_json,model_name,created_at,updated_at) "
            "VALUES (:id,:owner,:conversation,'test','event-digest','request-fingerprint','paused',"
            "'needs_confirmation',:pending,NULL,NULL,NULL,NULL,'fake',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
        ),
        {
            "id": values["run"],
            "owner": BOOTSTRAP_USER_ID,
            "conversation": values["conversation"],
            "pending": values["pending"],
        },
    )
    connection.execute(
        text(
            "INSERT INTO pending_action "
            "(id,run_id,actor_id,conversation_id,source_system,action_type,action_json,missing_fields_json,"
            "resource_versions_json,status,version_id,confirmation_code,approval_grant_id,final_result_json,"
            "created_at,expires_at,updated_at) VALUES "
            "(:id,:run,:owner,:conversation,'test','record_expense','{}','[]','{}','needs_confirmation',1,"
            "'R2S2PG',NULL,NULL,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP + INTERVAL '1 day',CURRENT_TIMESTAMP)"
        ),
        {
            "id": values["pending"],
            "run": values["run"],
            "owner": BOOTSTRAP_USER_ID,
            "conversation": values["conversation"],
        },
    )
    connection.execute(
        text(
            "INSERT INTO command_receipt "
            "(id,source_system,key_version,key_digest,request_fingerprint,command_name,"
            "result_type,result_id,result_json,completed_at,created_at) VALUES "
            "(:id,'activity_import',1,:digest,:fingerprint,'preview_activity_import',"
            "'activity_import_batch',:result_id,NULL,:now,:now)"
        ),
        {
            "id": values["preview_receipt"],
            "digest": "e" * 64,
            "fingerprint": "f" * 64,
            "result_id": values["import_batch"],
            "now": NOW,
        },
    )
    connection.execute(
        text(
            "INSERT INTO activity_import_batch "
            "(id,owner_id,status,parser_version,source_label,content_key_version,content_digest,"
            "preview_receipt_id,commit_receipt_id,selection_fingerprint,version_id,created_at,committed_at) "
            "VALUES (:id,:owner,'previewed','activity-md-v1','executor virtual history',1,:digest,"
            ":receipt,NULL,NULL,1,:now,NULL)"
        ),
        {
            "id": values["import_batch"],
            "owner": BOOTSTRAP_USER_ID,
            "digest": "1" * 128,
            "receipt": values["preview_receipt"],
            "now": NOW,
        },
    )
    connection.execute(
        text(
            "INSERT INTO activity_import_candidate "
            "(id,batch_id,ordinal,source_heading,source_line_start,source_line_end,block_digest,"
            "name_normalized,currency,reference_minor,reference_min_minor,reference_max_minor,"
            "proposed_action,target_template_id,target_expected_version,issues_json,decision,"
            "result_template_id,result_template_version) VALUES "
            "(:id,:batch,1,'executor virtual history',1,2,:digest,'executor virtual history','CNY',"
            "2500,2500,2500,'create',NULL,NULL,'[]',NULL,NULL,NULL)"
        ),
        {
            "id": values["import_candidate"],
            "batch": values["import_batch"],
            "digest": "2" * 128,
        },
    )
    return values


def test_postgresql_s1_migration_empty_history_and_round_trip(
    pg_r2: PostgreSQLR2Harness,
) -> None:
    inspector = inspect(pg_r2.engine)
    with pg_r2.engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == P4_HEAD
    run_columns = {column["name"]: column for column in inspector.get_columns("agent_run")}
    candidate_columns = {
        column["name"]: column for column in inspector.get_columns("memory_candidate")
    }
    assert run_columns["module_version"]["nullable"] is False
    assert run_columns["module_version"]["type"].length == 32
    assert candidate_columns["proposed_by_profile_version"]["nullable"] is False
    assert candidate_columns["proposed_by_profile_version"]["type"].length == 32
    item_checks = {
        item["name"]: item["sqltext"]
        for item in inspector.get_check_constraints("memory_item")
    }
    assert "invalidated" in item_checks["ck_memory_item_status"]

    with migrated_schema(
        pg_r2.raw_url, pg_r2.admin, prefix="p4_b6_r2_s2_history", revision=P3_HEAD
    ) as (_, url, engine):
        with engine.begin() as connection:
            values = _insert_p3_history(connection)
        engine.dispose()
        config = migration_config(url)
        try:
            command.upgrade(config, P4_HEAD)
        except Exception:
            rollback_engine = make_engine(url)
            try:
                rollback_inspector = inspect(rollback_engine)
                with rollback_engine.connect() as connection:
                    assert connection.scalar(
                        text("SELECT version_num FROM alembic_version")
                    ) == P3_HEAD
                    assert connection.scalar(
                        text(
                            "SELECT COUNT(*) FROM transaction_entry "
                            "WHERE transaction_id=:transaction"
                        ),
                        {"transaction": values["transaction"]},
                    ) == 2
                assert "app_user" not in rollback_inspector.get_table_names()
                for table in (
                    "financial_transaction",
                    "transaction_entry",
                    "agent_run",
                    "pending_action",
                    "activity_import_batch",
                    "activity_import_candidate",
                ):
                    assert "user_id" not in {
                        column["name"] for column in rollback_inspector.get_columns(table)
                    }
            finally:
                rollback_engine.dispose()
            raise
        engine = make_engine(url)
        upgraded = inspect(engine)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == P4_HEAD
            assert connection.scalar(text("SELECT COUNT(*) FROM alembic_version")) == 1
            assert connection.execute(
                text(
                    "SELECT name,currency,version_id,user_id FROM account WHERE id=:id"
                ),
                {"id": values["account"]},
            ).one() == ("legacy virtual account", "CNY", 1, BOOTSTRAP_USER_ID)
            assert connection.execute(
                text(
                    "SELECT kind,status,currency,user_id FROM financial_transaction WHERE id=:id"
                ),
                {"id": values["transaction"]},
            ).one() == ("expense", "posted", "CNY", BOOTSTRAP_USER_ID)
            assert connection.execute(
                text(
                    "SELECT line_no,entry_role,amount_minor,user_id FROM transaction_entry "
                    "WHERE transaction_id=:id ORDER BY line_no"
                ),
                {"id": values["transaction"]},
            ).all() == [
                (1, "account", -4321, BOOTSTRAP_USER_ID),
                (2, "expense", 4321, BOOTSTRAP_USER_ID),
            ]
            assert connection.execute(
                text(
                    "SELECT status,pause_reason,pending_action_id,user_id,actor_id,module_id,"
                    "module_version,profile_id,profile_version,attempt_no "
                    "FROM agent_run WHERE id=:id"
                ),
                {"id": values["run"]},
            ).one() == (
                "paused",
                "needs_confirmation",
                values["pending"],
                BOOTSTRAP_USER_ID,
                BOOTSTRAP_USER_ID,
                "daily_finance",
                "1.0.0",
                "daily_finance.assistant@1",
                "1.0.0",
                1,
            )
            assert connection.execute(
                text(
                    "SELECT status,action_json,user_id,actor_id,module_id,profile_id,"
                    "action_schema_version FROM pending_action WHERE id=:id"
                ),
                {"id": values["pending"]},
            ).one() == (
                "needs_confirmation",
                "{}",
                BOOTSTRAP_USER_ID,
                BOOTSTRAP_USER_ID,
                "daily_finance",
                "daily_finance.assistant@1",
                1,
            )
            assert connection.execute(
                text(
                    "SELECT status,owner_id,user_id FROM activity_import_batch WHERE id=:id"
                ),
                {"id": values["import_batch"]},
            ).one() == ("previewed", BOOTSTRAP_USER_ID, BOOTSTRAP_USER_ID)
            assert connection.execute(
                text(
                    "SELECT batch_id,ordinal,reference_minor,proposed_action,user_id "
                    "FROM activity_import_candidate WHERE id=:id"
                ),
                {"id": values["import_candidate"]},
            ).one() == (
                values["import_batch"],
                1,
                2500,
                "create",
                BOOTSTRAP_USER_ID,
            )
            for table in (
                "account",
                "category",
                "command_receipt",
                "financial_transaction",
                "transaction_entry",
                "agent_run",
                "pending_action",
                "activity_import_batch",
                "activity_import_candidate",
            ):
                assert connection.scalar(
                    text(f"SELECT COUNT(*) FROM {table} WHERE user_id IS NULL")
                ) == 0
            assert connection.scalar(
                text(
                    "SELECT COUNT(*) FROM transaction_entry e "
                    "LEFT JOIN financial_transaction t "
                    "ON e.user_id=t.user_id AND e.transaction_id=t.id "
                    "WHERE t.id IS NULL"
                )
            ) == 0
            assert connection.scalar(
                text(
                    "SELECT COUNT(*) FROM pending_action p LEFT JOIN agent_run r "
                    "ON p.user_id=r.user_id AND p.run_id=r.id WHERE r.id IS NULL"
                )
            ) == 0
            assert connection.scalar(
                text(
                    "SELECT COUNT(*) FROM activity_import_candidate c "
                    "LEFT JOIN activity_import_batch b "
                    "ON c.user_id=b.user_id AND c.batch_id=b.id WHERE b.id IS NULL"
                )
            ) == 0
        for table in (
            "account",
            "financial_transaction",
            "transaction_entry",
            "agent_run",
            "pending_action",
            "activity_import_batch",
            "activity_import_candidate",
        ):
            user_column = next(
                column for column in upgraded.get_columns(table) if column["name"] == "user_id"
            )
            assert user_column["nullable"] is False
            assert user_column["default"] is None
        expected_fks = {
            ("transaction_entry", "fk_entry_user_transaction"): (
                ("user_id", "transaction_id"),
                "financial_transaction",
                ("user_id", "id"),
            ),
            ("pending_action", "fk_pending_user_run"): (
                ("user_id", "run_id"),
                "agent_run",
                ("user_id", "id"),
            ),
            ("activity_import_candidate", "fk_candidate_user_batch"): (
                ("user_id", "batch_id"),
                "activity_import_batch",
                ("user_id", "id"),
            ),
        }
        for (table, name), expected in expected_fks.items():
            actual = {fk["name"]: fk for fk in upgraded.get_foreign_keys(table)}[name]
            assert (
                tuple(actual["constrained_columns"]),
                actual["referred_table"],
                tuple(actual["referred_columns"]),
            ) == expected
        for table in (
            "financial_transaction",
            "agent_run",
            "activity_import_batch",
        ):
            assert f"uq_{table}_user_id" in {
                item["name"] for item in upgraded.get_unique_constraints(table)
            }
        assert "ck_agent_run_actor_user" in {
            item["name"] for item in upgraded.get_check_constraints("agent_run")
        }
        assert "ck_import_batch_owner_user" in {
            item["name"] for item in upgraded.get_check_constraints("activity_import_batch")
        }
        command.upgrade(config, P4_HEAD)
        engine.dispose()
        command.downgrade(config, P3_HEAD)
        engine = make_engine(url)
        with engine.connect() as connection:
            assert connection.scalar(
                text("SELECT name FROM account WHERE id=:id"), {"id": values["account"]}
            ) == "legacy virtual account"
            assert connection.scalar(
                text("SELECT status FROM pending_action WHERE id=:id"),
                {"id": values["pending"]},
            ) == "needs_confirmation"
            assert connection.execute(
                text(
                    "SELECT line_no,entry_role,amount_minor FROM transaction_entry "
                    "WHERE transaction_id=:id ORDER BY line_no"
                ),
                {"id": values["transaction"]},
            ).all() == [(1, "account", -4321), (2, "expense", 4321)]
            assert connection.scalar(
                text(
                    "SELECT reference_minor FROM activity_import_candidate WHERE id=:id"
                ),
                {"id": values["import_candidate"]},
            ) == 2500
        engine.dispose()
        command.upgrade(config, P4_HEAD)
        engine = make_engine(url)
        roundtrip = inspect(engine)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == P4_HEAD
            assert connection.scalar(
                text("SELECT module_version FROM agent_run WHERE id=:id"),
                {"id": values["run"]},
            ) == "1.0.0"
            assert connection.execute(
                text(
                    "SELECT line_no,amount_minor,user_id FROM transaction_entry "
                    "WHERE transaction_id=:id ORDER BY line_no"
                ),
                {"id": values["transaction"]},
            ).all() == [
                (1, -4321, BOOTSTRAP_USER_ID),
                (2, 4321, BOOTSTRAP_USER_ID),
            ]
        assert "invalidated" in {
            item["name"]: item["sqltext"]
            for item in roundtrip.get_check_constraints("memory_item")
        }["ck_memory_item_status"]
        engine.dispose()


@pytest.mark.parametrize(
    ("invalid_history", "message"),
    (
        ("orphaned_run", "rejected orphaned legacy relationships"),
        ("contradictory_owner", "rejected contradictory legacy owners"),
    ),
)
def test_postgresql_s1_migration_rejects_invalid_history_atomically(
    pg_r2: PostgreSQLR2Harness,
    invalid_history: str,
    message: str,
) -> None:
    with migrated_schema(
        pg_r2.raw_url,
        pg_r2.admin,
        prefix=f"p4_b6_r3_invalid_{invalid_history}",
        revision=P3_HEAD,
    ) as (_, url, engine):
        invalid_value = uuid.uuid4()
        with engine.begin() as connection:
            values = _insert_p3_history(connection)
            if invalid_history == "orphaned_run":
                # An isolated corrupted P3 schema must be rejected before any
                # P4 DDL.  Drop only the legacy single-id FK in this fixture so
                # the migration's own graph validation sees the orphan.
                connection.execute(
                    text(
                        "ALTER TABLE pending_action DROP CONSTRAINT "
                        "fk_pending_action_run_id_agent_run"
                    )
                )
                connection.execute(
                    text("UPDATE pending_action SET run_id=:value WHERE id=:id"),
                    {"value": invalid_value, "id": values["pending"]},
                )
            else:
                connection.execute(
                    text("UPDATE pending_action SET actor_id=:value WHERE id=:id"),
                    {"value": invalid_value, "id": values["pending"]},
                )
        engine.dispose()

        with pytest.raises(RuntimeError, match=message):
            command.upgrade(migration_config(url), P4_HEAD)

        rollback_engine = make_engine(url)
        try:
            rollback_inspector = inspect(rollback_engine)
            with rollback_engine.connect() as connection:
                assert connection.scalar(
                    text("SELECT version_num FROM alembic_version")
                ) == P3_HEAD
                assert connection.scalar(
                    text(
                        "SELECT COUNT(*) FROM transaction_entry "
                        "WHERE transaction_id=:transaction"
                    ),
                    {"transaction": values["transaction"]},
                ) == 2
                if invalid_history == "orphaned_run":
                    assert connection.scalar(
                        text("SELECT run_id FROM pending_action WHERE id=:id"),
                        {"id": values["pending"]},
                    ) == invalid_value
                else:
                    assert connection.scalar(
                        text("SELECT actor_id FROM pending_action WHERE id=:id"),
                        {"id": values["pending"]},
                    ) == invalid_value
            assert "app_user" not in rollback_inspector.get_table_names()
            for table in (
                "financial_transaction",
                "transaction_entry",
                "agent_run",
                "pending_action",
                "activity_import_batch",
                "activity_import_candidate",
            ):
                assert "user_id" not in {
                    column["name"] for column in rollback_inspector.get_columns(table)
                }
        finally:
            rollback_engine.dispose()


def test_postgresql_candidate_version_recheck_and_confirm_race(
    pg_r2: PostgreSQLR2Harness,
) -> None:
    states = {"mode": "ok", "version": "1.4.0"}

    def validate(
        user_id,
        profile_id,
        source_namespace,
        target_namespace,
        kind,
        operation,
        expected_profile_version,
    ) -> str:
        del user_id
        valid = (
            states["mode"] == "ok"
            and profile_id == "daily_finance.assistant@1"
            and source_namespace == "daily_finance.candidates"
            and target_namespace == "daily_finance.confirmed"
            and kind == "goal"
            and operation == "propose"
            and (
                expected_profile_version is None
                or expected_profile_version == states["version"]
            )
        )
        if not valid:
            raise HostStateError("memory_candidate_conflict")
        return states["version"]

    events = InProcessEventBus()
    published = []
    events.subscribe("memory.changed@1", published.append)
    service = MemoryService(
        pg_r2.sessions,
        HostIdempotency(HostKeys({1: b"v" * 32})),
        events,
        validate,
    )

    for failure in ("profile_missing", "module_disabled", "version_changed", "grant_revoked"):
        states["mode"] = "ok"
        states["version"] = "1.4.0"
        candidate = service.propose(
            user_id=BOOTSTRAP_USER_ID,
            source_namespace="daily_finance.candidates",
            target_namespace="daily_finance.confirmed",
            kind="goal",
            value={"description": f"virtual-{failure}"},
            tags=[],
            source_type="test",
            source_ref_digest=uuid.uuid4().hex * 2,
            sensitivity="private",
            proposed_by_profile_id="daily_finance.assistant@1",
            now=NOW,
        )
        assert candidate.proposed_by_profile_version == "1.4.0"
        if failure == "version_changed":
            states["version"] = "1.5.0"
        else:
            states["mode"] = failure
        with pytest.raises(HostStateError, match="memory_candidate_conflict"):
            service.decide(
                candidate.id,
                user_id=BOOTSTRAP_USER_ID,
                confirm=True,
                target_namespace=None,
                allowed_namespaces=frozenset({"daily_finance.confirmed"}),
                idempotency_key=f"candidate-failure-{failure}",
                now=NOW,
            )
        with pg_r2.sessions() as session:
            assert session.scalar(
                select(MemoryCandidateRecord.status).where(
                    MemoryCandidateRecord.id == candidate.id
                )
            ) == "pending"
            assert session.scalars(
                select(HostRequestReceiptRecord).where(
                    HostRequestReceiptRecord.operation == "memory.confirm",
                    HostRequestReceiptRecord.request_fingerprint.is_not(None),
                    HostRequestReceiptRecord.created_at == NOW,
                )
            ).all() == []

    states["mode"] = "ok"
    states["version"] = "1.4.0"
    candidate = service.propose(
        user_id=BOOTSTRAP_USER_ID,
        source_namespace="daily_finance.candidates",
        target_namespace="daily_finance.confirmed",
        kind="goal",
        value={"description": "one real item"},
        tags=[],
        source_type="test",
        source_ref_digest=uuid.uuid4().hex * 2,
        sensitivity="private",
        proposed_by_profile_id="daily_finance.assistant@1",
        now=NOW + timedelta(seconds=1),
    )
    barrier = Barrier(2, timeout=10)

    def synchronize_candidate_update(
        _connection, _cursor, statement, _parameters, _context, _executemany
    ) -> None:
        normalized = " ".join(statement.casefold().split())
        if normalized.startswith("update memory_candidate set") and "status" in normalized:
            barrier.wait()

    event.listen(pg_r2.engine, "before_cursor_execute", synchronize_candidate_update)

    def confirm(key: str):
        try:
            item, replayed = service.decide(
                candidate.id,
                user_id=BOOTSTRAP_USER_ID,
                confirm=True,
                target_namespace=None,
                allowed_namespaces=frozenset({"daily_finance.confirmed"}),
                idempotency_key=key,
                now=NOW + timedelta(seconds=2),
            )
            return "ok", item.id, replayed
        except HostStateError as exc:
            return exc.code, None, False

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(confirm, ("candidate-race-a", "candidate-race-b")))
    finally:
        event.remove(pg_r2.engine, "before_cursor_execute", synchronize_candidate_update)
    assert sorted(item[0] for item in outcomes) == ["memory_candidate_conflict", "ok"]
    winner = next(item for item in outcomes if item[0] == "ok")
    with pg_r2.sessions() as session:
        assert session.scalar(
            select(MemoryCandidateRecord.status).where(
                MemoryCandidateRecord.id == candidate.id
            )
        ) == "confirmed"
        assert len(
            session.scalars(
                select(MemoryItemRecord).where(MemoryItemRecord.id == winner[1])
            ).all()
        ) == 1
    winning_key = "candidate-race-a" if outcomes[0][0] == "ok" else "candidate-race-b"
    replay, replayed = service.decide(
        candidate.id,
        user_id=BOOTSTRAP_USER_ID,
        confirm=True,
        target_namespace=None,
        allowed_namespaces=frozenset({"daily_finance.confirmed"}),
        idempotency_key=winning_key,
        now=NOW + timedelta(seconds=3),
    )
    assert replayed and replay is not None and replay.id == winner[1]


def test_postgresql_memory_supersede_invalidate_cas_and_cleanup(
    pg_r2: PostgreSQLR2Harness,
) -> None:
    events = InProcessEventBus()
    published = []
    events.subscribe("memory.changed@1", published.append)
    service = MemoryService(
        pg_r2.sessions,
        HostIdempotency(HostKeys({1: b"m" * 32})),
        events,
        lambda *_args: "1.0.0",
    )
    item = MemoryItemRecord(
        user_id=BOOTSTRAP_USER_ID,
        namespace="daily_finance.confirmed",
        kind="preference",
        value_json='{"note":"private-original"}',
        tags_json='["private-tag"]',
        source_type="test",
        source_ref_digest=uuid.uuid4().hex * 2,
        sensitivity="private",
        confirmed_at=NOW,
        audit_id=uuid.uuid4(),
    )
    with pg_r2.sessions() as session, session.begin():
        session.add(item)
    barrier = Barrier(2, timeout=10)

    def synchronize_item_update(
        _connection, _cursor, statement, _parameters, _context, _executemany
    ) -> None:
        normalized = " ".join(statement.casefold().split())
        if normalized.startswith("update memory_item set") and "version_id" in normalized:
            barrier.wait()

    event.listen(pg_r2.engine, "before_cursor_execute", synchronize_item_update)

    def supersede():
        try:
            replacement, _ = service.supersede(
                item.id,
                user_id=BOOTSTRAP_USER_ID,
                value={"note": "replacement"},
                expected_version=1,
                idempotency_key="memory-race-supersede",
                now=NOW + timedelta(seconds=1),
            )
            return "supersede", replacement.id
        except HostStateError as exc:
            return exc.code, None

    def invalidate():
        try:
            invalidated, _ = service.invalidate(
                item.id,
                user_id=BOOTSTRAP_USER_ID,
                expected_version=1,
                idempotency_key="memory-race-invalidate",
                now=NOW + timedelta(seconds=1),
            )
            return "invalidate", invalidated.id
        except HostStateError as exc:
            return exc.code, None

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = (pool.submit(supersede), pool.submit(invalidate))
            outcomes = [future.result() for future in futures]
    finally:
        event.remove(pg_r2.engine, "before_cursor_execute", synchronize_item_update)
    assert sorted(value[0] for value in outcomes) in (
        ["memory_version_conflict", "supersede"],
        ["invalidate", "memory_version_conflict"],
    )
    with pg_r2.sessions() as session:
        rows = session.scalars(
            select(MemoryItemRecord).where(
                MemoryItemRecord.user_id == BOOTSTRAP_USER_ID,
                MemoryItemRecord.audit_id == item.audit_id,
            )
        ).all()
        receipts = session.scalars(
            select(HostRequestReceiptRecord).where(
                HostRequestReceiptRecord.operation.in_(
                    ("memory.supersede", "memory.invalidate")
                )
            )
        ).all()
        current = session.get(MemoryItemRecord, item.id)
        assert current is not None
    assert len(receipts) == 1
    assert len(published) == 1
    assert "private-original" not in json.dumps(published[0].model_dump(mode="json"))
    if current.status == "invalidated":
        assert len(rows) == 1
        assert item.id not in {
            row.id
            for row in service.retrieve(
                user_id=BOOTSTRAP_USER_ID,
                allowed_namespaces=frozenset({"daily_finance.confirmed"}),
                now=NOW + timedelta(seconds=2),
            )
        }
        assert service.delete(
            item.id,
            user_id=BOOTSTRAP_USER_ID,
            expected_version=2,
            idempotency_key="delete-invalidated-race-winner",
            now=NOW + timedelta(seconds=2),
        )
    else:
        assert current.status == "superseded"
        with pg_r2.sessions() as session:
            assert len(
                [
                    row
                    for row in session.scalars(select(MemoryItemRecord)).all()
                    if row.id != item.id
                ]
            ) >= 1


def test_postgresql_pending_confirm_cancel_and_commit_recovery(
    pg_r2: PostgreSQLR2Harness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    finance, runtime, first, conversation, candidate = _candidate_application(
        pg_r2, suffix=uuid.uuid4().hex[:8]
    )
    second = build_agent_application(
        sessions=pg_r2.sessions,
        finance=finance,
        provider=ScriptedModelProvider([]),
        digest_key=b"p4-r2-postgresql-agent-key-32b",
        host_runtime=runtime,
    )
    barrier = Barrier(2, timeout=10)

    def double_confirm(application):
        barrier.wait()
        try:
            result = application.resume(
                candidate.run_id,
                actor_id=BOOTSTRAP_USER_ID,
                conversation_id=conversation.id,
                action="confirm",
                permissions=frozenset({"finance:write"}),
                confirmation_code=candidate.result["confirmation_code"],
                now=NOW + timedelta(seconds=1),
                channel="api_test",
            )
            return result.status
        except AgentApplicationError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(double_confirm, (first, second)))
    assert "success" in outcomes
    expenses = [row for row in finance.list_transactions() if row.kind == "expense"]
    assert len(expenses) == 1

    finance2, runtime2, confirm_app, conversation2, candidate2 = _candidate_application(
        pg_r2, suffix=uuid.uuid4().hex[:8]
    )
    cancel_app = build_agent_application(
        sessions=pg_r2.sessions,
        finance=finance2,
        provider=ScriptedModelProvider([]),
        digest_key=b"p4-r2-postgresql-agent-key-32b",
        host_runtime=runtime2,
    )
    barrier2 = Barrier(2, timeout=10)

    def race(action: str, application):
        barrier2.wait()
        try:
            result = application.resume(
                candidate2.run_id,
                actor_id=BOOTSTRAP_USER_ID,
                conversation_id=conversation2.id,
                action=action,
                permissions=frozenset({"finance:write"}),
                confirmation_code=(
                    candidate2.result["confirmation_code"] if action == "confirm" else None
                ),
                now=NOW + timedelta(seconds=2),
                channel="api_test",
            )
            return result.status
        except AgentApplicationError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = (
            pool.submit(race, "confirm", confirm_app),
            pool.submit(race, "cancel", cancel_app),
        )
        cancel_confirm = [future.result() for future in futures]
    with pg_r2.sessions() as session:
        pending = session.get(PendingActionRecord, candidate2.pending_action_id)
        assert pending is not None and pending.status in {"committed", "cancelled"}
    assert set(cancel_confirm) & {"success", "cancelled"}

    finance3, runtime3, crashing, conversation3, candidate3 = _candidate_application(
        pg_r2, suffix=uuid.uuid4().hex[:8]
    )
    original_mark = crashing._pending.mark_committed

    def crash_after_finance(*_args, **_kwargs):
        raise RuntimeError("virtual crash after finance commit")

    monkeypatch.setattr(crashing._pending, "mark_committed", crash_after_finance)
    with pytest.raises(RuntimeError, match="virtual crash after finance commit"):
        crashing.resume(
            candidate3.run_id,
            actor_id=BOOTSTRAP_USER_ID,
            conversation_id=conversation3.id,
            action="confirm",
            permissions=frozenset({"finance:write"}),
            confirmation_code=candidate3.result["confirmation_code"],
            now=NOW + timedelta(seconds=3),
            channel="api_test",
        )
    before_recovery = [row for row in finance3.list_transactions() if row.kind == "expense"]
    assert len(before_recovery) >= 1
    monkeypatch.setattr(crashing._pending, "mark_committed", original_mark)
    recovered = crashing.resume(
        candidate3.run_id,
        actor_id=BOOTSTRAP_USER_ID,
        conversation_id=conversation3.id,
        action="confirm",
        permissions=frozenset({"finance:write"}),
        confirmation_code=candidate3.result["confirmation_code"],
        now=NOW + timedelta(seconds=64),
        channel="api_test",
    )
    assert recovered.status == "success"
    after_recovery = [row for row in finance3.list_transactions() if row.kind == "expense"]
    assert len(after_recovery) == len(before_recovery)


def test_postgresql_run_takeover_attempt_fence_and_exhaustion(
    pg_r2: PostgreSQLR2Harness,
) -> None:
    finance, _, _, runtime = _stack(pg_r2)
    conversation = _conversation(runtime, key=f"run-fence-{uuid.uuid4()}")
    run = AgentRunRecord(
        user_id=BOOTSTRAP_USER_ID,
        actor_id=BOOTSTRAP_USER_ID,
        conversation_id=conversation.id,
        source_system="api_test",
        source_event_digest=uuid.uuid4().hex * 2,
        request_fingerprint=uuid.uuid4().hex * 2,
        status="running",
        module_id="daily_finance",
        module_version="1.0.0",
        profile_id="daily_finance.assistant@1",
        profile_version="1.0.0",
        attempt_no=1,
        lease_expires_at=NOW - timedelta(seconds=1),
        created_at=NOW - timedelta(minutes=1),
        updated_at=NOW - timedelta(minutes=1),
    )
    with pg_r2.sessions() as session, session.begin():
        session.add(run)
    coordinator = RunLeaseCoordinator(pg_r2.sessions)
    barrier = Barrier(2, timeout=10)

    def acquire():
        barrier.wait()
        try:
            return "ok", coordinator.acquire(
                run.id, user_id=BOOTSTRAP_USER_ID, now=NOW
            ).attempt_no
        except WorkflowError as exc:
            return exc.code, None

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: acquire(), range(2)))
    assert sorted(item[0] for item in outcomes) == ["ok", "run_lease_active"]
    assert next(item[1] for item in outcomes if item[0] == "ok") == 2
    coordinator.renew(
        run.id, user_id=BOOTSTRAP_USER_ID, attempt_no=2, now=NOW
    )
    with pytest.raises(WorkflowError, match="run_lease_lost"):
        coordinator.renew(
            run.id, user_id=BOOTSTRAP_USER_ID, attempt_no=1, now=NOW
        )

    application = build_agent_application(
        sessions=pg_r2.sessions,
        finance=finance,
        provider=ScriptedModelProvider([]),
        digest_key=b"p4-r2-postgresql-agent-key-32b",
        host_runtime=runtime,
    )
    with pytest.raises(AgentApplicationError, match="run_lease_lost"):
        application._append_message(
            run_id=run.id,
            user_id=BOOTSTRAP_USER_ID,
            attempt_no=1,
            message=ConversationMessage(role="assistant", content="stale"),
            now=NOW,
        )
    with pytest.raises(AgentApplicationError, match="run_lease_lost"):
        application._save_result(
            run.id,
            AgentRunResult(
                request_id=str(run.id),
                status=RunStatus.SUCCESS,
                answer="stale terminal",
                events=(),
            ),
            user_id=BOOTSTRAP_USER_ID,
            attempt_no=1,
            now=NOW,
        )
    with pg_r2.sessions() as session, session.begin():
        row = session.get(AgentRunRecord, run.id)
        assert row is not None
        row.lease_expires_at = NOW - timedelta(seconds=1)
    third = coordinator.acquire(run.id, user_id=BOOTSTRAP_USER_ID, now=NOW)
    assert third.attempt_no == 3
    with pg_r2.sessions() as session, session.begin():
        row = session.get(AgentRunRecord, run.id)
        assert row is not None
        row.lease_expires_at = NOW - timedelta(seconds=1)
    with pg_r2.sessions() as session:
        exhausted = session.get(AgentRunRecord, run.id)
        assert exhausted is not None
        application._save_exhausted(exhausted, user_id=BOOTSTRAP_USER_ID, now=NOW)
    with pg_r2.sessions() as session:
        terminal = session.get(AgentRunRecord, run.id)
        assert terminal is not None
        assert terminal.status == "error" and terminal.error_code == "run_attempts_exhausted"


def test_postgresql_messages_constraints_and_post_commit_events(
    pg_r2: PostgreSQLR2Harness,
    caplog: pytest.LogCaptureFixture,
) -> None:
    finance, _, _, runtime = _stack(pg_r2)
    observed: list[object] = []
    for event_type in (
        "agent.run_status_changed@1",
        "memory.changed@1",
        "module.setting_changed@1",
        "auth.session_revoked@1",
    ):
        runtime.events.subscribe(event_type, observed.append)
    runtime.events.subscribe(
        "module.setting_changed@1",
        lambda _event: (_ for _ in ()).throw(RuntimeError("virtual subscriber failure")),
    )
    conversation = _conversation(runtime, key=f"messages-{uuid.uuid4()}")
    application = build_agent_application(
        sessions=pg_r2.sessions,
        finance=finance,
        provider=ScriptedModelProvider([AssistantTurn(content="虚拟完成")]),
        digest_key=b"p4-r2-postgresql-agent-key-32b",
        host_runtime=runtime,
    )
    result = application.start(
        actor_id=BOOTSTRAP_USER_ID,
        conversation_id=conversation.id,
        client_event_id=uuid.uuid4(),
        message="虚拟消息",
        permissions=frozenset({"finance:read"}),
        received_at=NOW + timedelta(minutes=5),
        channel="api_test",
    )
    assert result.status == "success"
    with pg_r2.sessions() as session:
        messages = session.scalars(
            select(ConversationMessageRecord)
            .where(ConversationMessageRecord.run_id == result.run_id)
            .order_by(ConversationMessageRecord.run_sequence)
        ).all()
    assert [row.run_sequence for row in messages] == [0, 1]
    assert [row.role for row in messages] == ["user", "assistant"]

    duplicate = ConversationMessageRecord(
        user_id=BOOTSTRAP_USER_ID,
        conversation_id=conversation.id,
        run_id=result.run_id,
        run_sequence=1,
        role="tool",
        content="duplicate",
        content_digest=uuid.uuid4().hex * 2,
        sensitivity="private",
        created_at=NOW,
    )
    with pytest.raises(IntegrityError):
        with pg_r2.sessions() as session, session.begin():
            session.add(duplicate)

    candidate = runtime.memories.propose(
        user_id=BOOTSTRAP_USER_ID,
        source_namespace="daily_finance.candidates",
        target_namespace="daily_finance.confirmed",
        kind="preference",
        value={"drink": "virtual tea"},
        tags=[],
        source_type="test",
        source_ref_digest=uuid.uuid4().hex * 2,
        sensitivity="private",
        proposed_by_profile_id="daily_finance.assistant@1",
        now=NOW,
    )
    runtime.memories.decide(
        candidate.id,
        user_id=BOOTSTRAP_USER_ID,
        confirm=True,
        target_namespace=None,
        allowed_namespaces=frozenset({"daily_finance.confirmed"}),
        idempotency_key=f"event-memory-{uuid.uuid4()}",
        now=NOW,
    )
    setting, _ = runtime.settings.put(
        user_id=BOOTSTRAP_USER_ID,
        module_id="daily_finance",
        key="assistant_mode",
        value={"enabled": True},
        schema_version=1,
        expected_version=None,
        idempotency_key=f"event-setting-{uuid.uuid4()}",
        now=NOW,
    )
    assert setting.value_json == '{"enabled":true}'

    app = create_app(host_runtime=runtime)
    with TestClient(
        app, client=("127.0.0.1", 50000), raise_server_exceptions=False
    ) as client:
        handle = f"owner_{uuid.uuid4().hex[:8]}"
        initialized = client.post(
            "/api/v1/auth/initialize",
            headers={
                "Idempotency-Key": f"event-init-{uuid.uuid4()}",
                "X-Bootstrap-Token": "b" * 32,
            },
            json={
                "handle": handle,
                "password": "correct horse battery staple",
            },
        )
        assert initialized.status_code == 200
        login = client.post(
            "/api/v1/auth/login",
            json={
                "handle": handle,
                "password": "correct horse battery staple",
                "client_fingerprint": "p4-r2-s2-events",
                "device_name": "pytest",
                "platform": "api_test",
            },
        )
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200

    event_types = {item.event_type for item in observed}
    assert {
        "agent.run_status_changed@1",
        "memory.changed@1",
        "module.setting_changed@1",
        "auth.session_revoked@1",
    } <= event_types
    serialized = json.dumps(
        [item.model_dump(mode="json") for item in observed], ensure_ascii=False
    )
    assert "virtual tea" not in serialized
    assert "correct horse battery staple" not in serialized
    assert "host_event_handler_failed" in caplog.text
    assert '"error_type":"RuntimeError"' in caplog.text
    assert "virtual subscriber failure" not in caplog.text
    with pg_r2.sessions() as session:
        assert session.get(ModuleSettingRecord, setting.id) is not None


def test_postgresql_setting_receipt_atomicity_and_concurrent_keys(
    pg_r2: PostgreSQLR2Harness,
) -> None:
    _, _, _, runtime = _stack(pg_r2)
    observed = []
    runtime.events.subscribe("module.setting_changed@1", observed.append)
    before = len(observed)
    with pytest.raises(HostStateError, match="setting_secret_forbidden"):
        runtime.settings.put(
            user_id=BOOTSTRAP_USER_ID,
            module_id="daily_finance",
            key="assistant_mode",
            value={"nested": {"refresh_token": "never-store"}},
            schema_version=1,
            expected_version=None,
            idempotency_key=f"secret-reject-{uuid.uuid4()}",
            now=NOW,
        )
    assert len(observed) == before

    key = f"setting-race-{uuid.uuid4()}"
    barrier = Barrier(2, timeout=10)

    def put():
        barrier.wait()
        try:
            row, replayed = runtime.settings.put(
                user_id=BOOTSTRAP_USER_ID,
                module_id="daily_finance",
                key="module_enabled",
                value={"enabled": True},
                schema_version=1,
                expected_version=None,
                idempotency_key=key,
                now=NOW + timedelta(minutes=1),
            )
            return "ok", row.id, replayed
        except HostStateError as exc:
            return exc.code, None, False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: put(), range(2)))
    assert any(item[0] == "ok" for item in outcomes)
    replay, replayed = runtime.settings.put(
        user_id=BOOTSTRAP_USER_ID,
        module_id="daily_finance",
        key="module_enabled",
        value={"enabled": True},
        schema_version=1,
        expected_version=None,
        idempotency_key=key,
        now=NOW + timedelta(minutes=1),
    )
    assert replayed and replay.value_json == '{"enabled":true}'
    with pytest.raises(HostStateError, match="idempotency_conflict"):
        runtime.settings.put(
            user_id=BOOTSTRAP_USER_ID,
            module_id="daily_finance",
            key="module_enabled",
            value={"enabled": False},
            schema_version=1,
            expected_version=1,
            idempotency_key=key,
            now=NOW + timedelta(minutes=2),
        )
    with pg_r2.sessions() as session:
        setting = session.scalar(
            select(ModuleSettingRecord).where(
                ModuleSettingRecord.user_id == BOOTSTRAP_USER_ID,
                ModuleSettingRecord.module_id == "daily_finance",
                ModuleSettingRecord.key == "module_enabled",
            )
        )
        receipt = session.scalar(
            select(HostRequestReceiptRecord).where(
                HostRequestReceiptRecord.user_id == BOOTSTRAP_USER_ID,
                HostRequestReceiptRecord.operation == "setting.put",
                HostRequestReceiptRecord.completed_at.is_not(None),
            ).order_by(HostRequestReceiptRecord.created_at.desc())
        )
        assert setting is not None and receipt is not None


def test_postgresql_page_cursor_uuid_boundary_and_binding(
    pg_r2: PostgreSQLR2Harness,
) -> None:
    _, _, _, runtime = _stack(pg_r2)
    same_time = NOW + timedelta(days=30)
    original = [
        _conversation(runtime, key=f"page-{uuid.uuid4()}", now=same_time)
        for _ in range(4)
    ]
    expected = sorted((row.id for row in original), key=str)
    first = runtime.conversations.list(
        user_id=BOOTSTRAP_USER_ID, limit=2, before=None
    )
    first = [row for row in first if row.created_at == same_time][:2]
    assert [row.id for row in first] == expected[:2]
    cursor = runtime.cursor.encode(
        endpoint="conversations:v1",
        user_id=BOOTSTRAP_USER_ID,
        sort_time=first[-1].created_at,
        item_id=first[-1].id,
    )
    boundary = runtime.cursor.decode(
        cursor,
        endpoint="conversations:v1",
        user_id=BOOTSTRAP_USER_ID,
    )
    inserted = _conversation(
        runtime,
        key=f"page-new-{uuid.uuid4()}",
        now=same_time + timedelta(seconds=1),
    )
    second = runtime.conversations.list(
        user_id=BOOTSTRAP_USER_ID, limit=10, before=boundary
    )
    second_ids = [row.id for row in second if row.id in expected]
    assert second_ids == expected[2:]
    assert inserted.id not in second_ids
    assert not set(row.id for row in first).intersection(second_ids)
    with pytest.raises(InvalidCursorError, match="invalid_cursor"):
        runtime.cursor.decode(
            cursor,
            endpoint="conversation-messages:v1:virtual",
            user_id=BOOTSTRAP_USER_ID,
        )
    with pytest.raises(InvalidCursorError, match="invalid_cursor"):
        runtime.cursor.decode(
            cursor,
            endpoint="conversations:v1",
            user_id=uuid.uuid4(),
        )
    with pytest.raises(InvalidCursorError, match="invalid_cursor"):
        runtime.cursor.decode(
            cursor,
            endpoint="conversations:v1",
            user_id=BOOTSTRAP_USER_ID,
            filter_fingerprint="changed",
        )


def _production_config(url: str) -> ProductionConfig:
    return ProductionConfig(
        database_url=url,
        bootstrap_token=b"b" * 32,
        binding_hmac_key=b"h" * 32,
        adapter_token=b"a" * 32,
        host_state_key=b"s" * 32,
        cursor_key=b"c" * 32,
        agent_digest_key=b"d" * 32,
        finance_receipt_key=b"f" * 32,
    )


def test_postgresql_production_factory_ready_smoke_and_stale_schema(
    pg_r2: PostgreSQLR2Harness,
) -> None:
    with migrated_schema(
        pg_r2.raw_url, pg_r2.admin, prefix="p4_b6_r2_s2_production"
    ) as (_, url, _engine):
        app = create_production_app(
            _production_config(url),
            provider=ScriptedModelProvider([AssistantTurn(content="虚拟 Agent 完成")]),
        )
        with TestClient(
            app, client=("127.0.0.1", 50000), raise_server_exceptions=False
        ) as client:
            assert client.get("/healthz").status_code == 200
            assert client.get("/readyz").status_code == 200
            initialized = client.post(
                "/api/v1/auth/initialize",
                headers={
                    "Idempotency-Key": "production-initialize",
                    "X-Bootstrap-Token": "b" * 32,
                },
                json={
                    "handle": "production_owner",
                    "password": "correct horse battery staple",
                },
            )
            assert initialized.status_code == 200, initialized.text
            login = client.post(
                "/api/v1/auth/login",
                json={
                    "handle": "production_owner",
                    "password": "correct horse battery staple",
                    "client_fingerprint": "p4-r2-production",
                    "device_name": "pytest",
                    "platform": "api_test",
                },
            )
            assert login.status_code == 200
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
            modules = client.get("/api/v1/modules", headers=headers)
            assert modules.status_code == 200
            assert [item["module_id"] for item in modules.json()] == ["daily_finance"]
            conversation = client.post(
                "/api/v1/conversations",
                headers={**headers, "Idempotency-Key": "production-conversation"},
                json={
                    "channel": "api_test",
                    "module_id": "daily_finance",
                    "profile_id": "daily_finance.assistant@1",
                },
            )
            assert conversation.status_code == 200
            agent = client.post(
                "/api/v1/agent/runs",
                headers=headers,
                json={
                    "conversation_id": conversation.json()["id"],
                    "client_event_id": str(uuid.uuid4()),
                    "message": "虚拟生产组合冒烟",
                },
            )
            assert agent.status_code == 200, agent.text
            assert agent.json()["status"] == "success"
            activity = client.post(
                "/api/v1/activity-imports/preview",
                headers={**headers, "Idempotency-Key": "production-import"},
                json={"markdown": "## 虚拟活动", "source_label": "virtual.md"},
            )
            assert activity.status_code == 201, activity.text
        app.state.engine.dispose()

    with migrated_schema(
        pg_r2.raw_url,
        pg_r2.admin,
        prefix="p4_b6_r2_s2_stale",
        revision=P3_HEAD,
    ) as (_, url, engine):
        app = create_production_app(
            _production_config(url),
            provider=ScriptedModelProvider([]),
        )
        with TestClient(
            app, client=("127.0.0.1", 50000), raise_server_exceptions=False
        ) as client:
            assert client.get("/healthz").status_code == 200
            ready = client.get("/readyz")
            assert ready.status_code == 503
            assert ready.json()["error"]["code"] == "migration_not_current"
            assert "wife_test_only" not in ready.text
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == P3_HEAD
        app.state.engine.dispose()
