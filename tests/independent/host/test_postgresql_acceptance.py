"""Independent P4-A PostgreSQL acceptance using random schemas and virtual data."""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from alembic import command
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError

from tests.host.test_postgresql_r2 import (  # fixture mechanics only; assertions below are independent
    NOW,
    P3_HEAD,
    P4_HEAD,
    PostgreSQLR2Harness,
    _candidate_application,
    _conversation,
    _stack,
    migrated_schema,
    migration_config,
    pg_r2,
    _production_config,
)
from tests.host.test_postgresql_r1 import _seed_cross_user_graph
from tests.independent.host.history_fixtures import seed_p3_history
from fastapi.testclient import TestClient
from wife_system.agent.models import AgentRunRecord
from wife_system.finance.db import make_engine
from wife_system.finance.models import BOOTSTRAP_USER_ID
from wife_system.host.auth.errors import AuthError
from wife_system.host.auth.models import ChannelBindingCode, ChannelIdentityBinding
from wife_system.host.state import HostStateError
from wife_system.host.state_models import HostRequestReceiptRecord, MemoryItemRecord, ModuleSettingRecord
from wife_system.host.workflows import RunLeaseCoordinator, WorkflowError
from wife_system.api.production import create_production_app
from wife_system.agent.providers import ScriptedModelProvider
from wife_system.agent.types import AssistantTurn


def test_c11_pg_migration_round_trip_and_real_constraint_catalog(pg_r2: PostgreSQLR2Harness) -> None:
    with migrated_schema(pg_r2.raw_url, pg_r2.admin, prefix="p4_c11_ind_migration") as (_, url, engine):
        with engine.begin() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == P4_HEAD
            connection.execute(text(
                "INSERT INTO account (id,user_id,name,currency,archived_at,created_at,version_id) "
                "VALUES (:id,:user,'virtual preserved','CNY',NULL,CURRENT_TIMESTAMP,1)"
            ), {"id": uuid.uuid4(), "user": BOOTSTRAP_USER_ID})
        command.downgrade(migration_config(url), P3_HEAD)
        command.upgrade(migration_config(url), P4_HEAD)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == P4_HEAD
            assert connection.scalar(text("SELECT count(*) FROM account WHERE name='virtual preserved'")) == 1

        inspector = inspect(engine)
        assert len(inspector.get_pk_constraint("app_user")["constrained_columns"]) == 1
        for table, expected in {
            "agent_run": {"uq_agent_run_user_id"},
            "pending_action": {"uq_pending_action_user_id"},
            "memory_item": {"uq_memory_item_user_id"},
        }.items():
            names = {item["name"] for item in inspector.get_unique_constraints(table)}
            assert expected <= names
        assert {fk["name"] for fk in inspector.get_foreign_keys("pending_action")} >= {
            "fk_pending_user_run", "fk_pending_user_conversation"
        }
        assert {fk["name"] for fk in inspector.get_foreign_keys("memory_item")} >= {
            "fk_memory_item_user_superseded"
        }

    graph = _seed_cross_user_graph(pg_r2)
    for statement, params in (
        ("UPDATE pending_action SET run_id=:foreign WHERE id=:target", {"foreign": graph["run_a"], "target": graph["pending_b"]}),
        ("UPDATE pending_action SET conversation_id=:foreign WHERE id=:target", {"foreign": graph["conversation_a"], "target": graph["pending_b"]}),
        ("UPDATE memory_item SET superseded_by_id=:foreign WHERE id=:target", {"foreign": graph["item_a"], "target": graph["item_b"]}),
    ):
        with pytest.raises(IntegrityError):
            with pg_r2.engine.begin() as connection:
                connection.execute(text(statement), params)


def test_c11_pg_p3_history_forward_upgrade_preserves_p1_p2_p3_facts(
    pg_r2: PostgreSQLR2Harness,
) -> None:
    with migrated_schema(
        pg_r2.raw_url,
        pg_r2.admin,
        prefix="p4_c11_r1_ind_history",
        revision=P3_HEAD,
    ) as (_, url, engine):
        config = migration_config(url)
        with engine.begin() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == P3_HEAD
            values = seed_p3_history(connection)

        engine.dispose()
        command.upgrade(config, P4_HEAD)
        engine = make_engine(url)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == P4_HEAD
            assert connection.scalar(text("SELECT COUNT(*) FROM alembic_version")) == 1
            assert connection.execute(
                text("SELECT name,currency,version_id,user_id FROM account WHERE id=:id"),
                {"id": values["account"]},
            ).one() == ("virtual P3 history account", "CNY", 1, BOOTSTRAP_USER_ID)
            assert connection.execute(
                text("SELECT kind,name,user_id FROM category WHERE id=:id"),
                {"id": values["category"]},
            ).one() == ("expense", "virtual P3 history expense", BOOTSTRAP_USER_ID)
            assert connection.execute(
                text("SELECT kind,status,currency,user_id FROM financial_transaction WHERE id=:id"),
                {"id": values["transaction"]},
            ).one() == ("expense", "posted", "CNY", BOOTSTRAP_USER_ID)
            assert connection.execute(
                text(
                    "SELECT line_no,entry_role,amount_minor,pg_typeof(amount_minor)::text,user_id "
                    "FROM transaction_entry WHERE transaction_id=:id ORDER BY line_no"
                ),
                {"id": values["transaction"]},
            ).all() == [
                (1, "account", -4321, "bigint", BOOTSTRAP_USER_ID),
                (2, "expense", 4321, "bigint", BOOTSTRAP_USER_ID),
            ]
            assert connection.execute(
                text(
                    "SELECT status,pause_reason,pending_action_id,module_id,profile_id,attempt_no,"
                    "actor_id,user_id FROM agent_run WHERE id=:id"
                ),
                {"id": values["run"]},
            ).one() == (
                "paused",
                "needs_confirmation",
                values["pending"],
                "daily_finance",
                "daily_finance.assistant@1",
                1,
                BOOTSTRAP_USER_ID,
                BOOTSTRAP_USER_ID,
            )
            assert connection.execute(
                text(
                    "SELECT status,action_json,module_id,profile_id,action_schema_version,actor_id,user_id "
                    "FROM pending_action WHERE id=:id"
                ),
                {"id": values["pending"]},
            ).one() == (
                "needs_confirmation",
                '{"amount":"43.21"}',
                "daily_finance",
                "daily_finance.assistant@1",
                1,
                BOOTSTRAP_USER_ID,
                BOOTSTRAP_USER_ID,
            )
            assert connection.execute(
                text("SELECT status,owner_id,user_id FROM activity_import_batch WHERE id=:id"),
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

        inspector = inspect(engine)
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
            ("agent_run", "fk_run_user_pending"): (
                ("user_id", "pending_action_id"),
                "pending_action",
                ("user_id", "id"),
            ),
            ("memory_item", "fk_memory_item_user_superseded"): (
                ("user_id", "superseded_by_id"),
                "memory_item",
                ("user_id", "id"),
            ),
            ("memory_candidate", "fk_memory_candidate_user_item"): (
                ("user_id", "memory_item_id"),
                "memory_item",
                ("user_id", "id"),
            ),
        }
        for (table, name), expected in expected_fks.items():
            actual = {fk["name"]: fk for fk in inspector.get_foreign_keys(table)}[name]
            assert (
                tuple(actual["constrained_columns"]),
                actual["referred_table"],
                tuple(actual["referred_columns"]),
            ) == expected
        for table in (
            "financial_transaction",
            "transaction_entry",
            "agent_run",
            "pending_action",
            "activity_import_batch",
            "activity_import_candidate",
        ):
            user_column = next(
                column
                for column in inspector.get_columns(table)
                if column["name"] == "user_id"
            )
            assert user_column["nullable"] is False
            assert user_column["default"] is None
            assert f"uq_{table}_user_id" in {
                item["name"] for item in inspector.get_unique_constraints(table)
            }
        assert "ck_agent_run_actor_user" in {
            item["name"] for item in inspector.get_check_constraints("agent_run")
        }
        assert "ck_pending_action_actor_user" in {
            item["name"] for item in inspector.get_check_constraints("pending_action")
        }
        assert "ck_import_batch_owner_user" in {
            item["name"]
            for item in inspector.get_check_constraints("activity_import_batch")
        }
        assert ScriptDirectory.from_config(config).get_heads() == [P4_HEAD]

        command.upgrade(config, P4_HEAD)
        engine.dispose()
        command.downgrade(config, P3_HEAD)
        downgraded = make_engine(url)
        with downgraded.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == P3_HEAD
            assert connection.execute(
                text(
                    "SELECT line_no,entry_role,amount_minor FROM transaction_entry "
                    "WHERE transaction_id=:id ORDER BY line_no"
                ),
                {"id": values["transaction"]},
            ).all() == [(1, "account", -4321), (2, "expense", 4321)]
            assert connection.execute(
                text(
                    "SELECT status,pause_reason,pending_action_id,actor_id "
                    "FROM agent_run WHERE id=:id"
                ),
                {"id": values["run"]},
            ).one() == (
                "paused",
                "needs_confirmation",
                values["pending"],
                BOOTSTRAP_USER_ID,
            )
            assert connection.execute(
                text(
                    "SELECT status,run_id,actor_id,action_json "
                    "FROM pending_action WHERE id=:id"
                ),
                {"id": values["pending"]},
            ).one() == (
                "needs_confirmation",
                values["run"],
                BOOTSTRAP_USER_ID,
                '{"amount":"43.21"}',
            )
            assert connection.execute(
                text(
                    "SELECT status,owner_id FROM activity_import_batch WHERE id=:id"
                ),
                {"id": values["import_batch"]},
            ).one() == ("previewed", BOOTSTRAP_USER_ID)
            assert connection.scalar(
                text(
                    "SELECT reference_minor FROM activity_import_candidate WHERE id=:id"
                ),
                {"id": values["import_candidate"]},
            ) == 2500
        downgraded.dispose()

        command.upgrade(config, P4_HEAD)
        roundtrip = make_engine(url)
        with roundtrip.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == P4_HEAD
            assert connection.scalar(text("SELECT COUNT(*) FROM alembic_version")) == 1
            assert connection.execute(
                text(
                    "SELECT line_no,entry_role,amount_minor,user_id "
                    "FROM transaction_entry WHERE transaction_id=:id ORDER BY line_no"
                ),
                {"id": values["transaction"]},
            ).all() == [
                (1, "account", -4321, BOOTSTRAP_USER_ID),
                (2, "expense", 4321, BOOTSTRAP_USER_ID),
            ]
            assert connection.execute(
                text(
                    "SELECT status,pending_action_id,actor_id,user_id "
                    "FROM agent_run WHERE id=:id"
                ),
                {"id": values["run"]},
            ).one() == (
                "paused",
                values["pending"],
                BOOTSTRAP_USER_ID,
                BOOTSTRAP_USER_ID,
            )
            assert connection.execute(
                text(
                    "SELECT status,run_id,actor_id,user_id "
                    "FROM pending_action WHERE id=:id"
                ),
                {"id": values["pending"]},
            ).one() == (
                "needs_confirmation",
                values["run"],
                BOOTSTRAP_USER_ID,
                BOOTSTRAP_USER_ID,
            )
            assert connection.execute(
                text(
                    "SELECT status,owner_id,user_id FROM activity_import_batch WHERE id=:id"
                ),
                {"id": values["import_batch"]},
            ).one() == ("previewed", BOOTSTRAP_USER_ID, BOOTSTRAP_USER_ID)
            assert connection.execute(
                text(
                    "SELECT reference_minor,user_id FROM activity_import_candidate WHERE id=:id"
                ),
                {"id": values["import_candidate"]},
            ).one() == (2500, BOOTSTRAP_USER_ID)
        roundtrip.dispose()


@pytest.mark.parametrize(
    ("invalid_history", "expected_diagnostic"),
    (
        ("orphaned_pending_run", "rejected orphaned legacy relationships"),
        ("contradictory_pending_owner", "rejected contradictory legacy owners"),
    ),
)
def test_c11_pg_p3_invalid_history_is_rejected_before_user_scope_ddl(
    pg_r2: PostgreSQLR2Harness,
    invalid_history: str,
    expected_diagnostic: str,
) -> None:
    scoped_tables = (
        "account",
        "category",
        "command_receipt",
        "audit_event",
        "financial_transaction",
        "transaction_entry",
        "activity_template",
        "activity_template_revision",
        "activity_import_batch",
        "activity_import_candidate",
        "activity_occurrence",
        "activity_entry_allocation",
        "income_schedule",
        "income_schedule_version",
        "income_expectation",
        "income_expectation_match",
        "budget_plan",
        "budget_version",
        "budget_allocation",
        "agent_run",
        "pending_action",
    )
    with migrated_schema(
        pg_r2.raw_url,
        pg_r2.admin,
        prefix=f"p4_c11_r2_invalid_{invalid_history}",
        revision=P3_HEAD,
    ) as (_, url, engine):
        invalid_value = uuid.uuid4()
        with engine.begin() as connection:
            values = seed_p3_history(connection)
            if invalid_history == "orphaned_pending_run":
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

        with pytest.raises(RuntimeError, match=expected_diagnostic) as rejected:
            command.upgrade(migration_config(url), P4_HEAD)

        diagnostic = str(rejected.value)
        assert expected_diagnostic in diagnostic
        assert str(invalid_value) not in diagnostic
        assert "virtual" not in diagnostic.lower()
        assert "password" not in diagnostic.lower()
        assert "postgresql://" not in diagnostic.lower()
        assert "@" not in diagnostic

        rollback = make_engine(url)
        try:
            rollback_inspector = inspect(rollback)
            with rollback.connect() as connection:
                assert connection.scalar(
                    text("SELECT version_num FROM alembic_version")
                ) == P3_HEAD
                assert connection.execute(
                    text(
                        "SELECT line_no,entry_role,amount_minor FROM transaction_entry "
                        "WHERE transaction_id=:id ORDER BY line_no"
                    ),
                    {"id": values["transaction"]},
                ).all() == [(1, "account", -4321), (2, "expense", 4321)]
                assert connection.scalar(
                    text("SELECT COUNT(*) FROM financial_transaction WHERE id=:id"),
                    {"id": values["transaction"]},
                ) == 1
                assert connection.scalar(
                    text("SELECT COUNT(*) FROM pending_action WHERE id=:id"),
                    {"id": values["pending"]},
                ) == 1
                assert connection.scalar(
                    text("SELECT actor_id FROM agent_run WHERE id=:id"),
                    {"id": values["run"]},
                ) == BOOTSTRAP_USER_ID
                if invalid_history == "orphaned_pending_run":
                    assert connection.execute(
                        text(
                            "SELECT run_id,actor_id FROM pending_action WHERE id=:id"
                        ),
                        {"id": values["pending"]},
                    ).one() == (invalid_value, BOOTSTRAP_USER_ID)
                else:
                    assert connection.execute(
                        text(
                            "SELECT run_id,actor_id FROM pending_action WHERE id=:id"
                        ),
                        {"id": values["pending"]},
                    ).one() == (values["run"], invalid_value)
            assert "app_user" not in rollback_inspector.get_table_names()
            for table in scoped_tables:
                assert "user_id" not in {
                    column["name"]
                    for column in rollback_inspector.get_columns(table)
                }
        finally:
            rollback.dispose()


def test_c11_pg_auth_initialize_refresh_and_binding_linearize(pg_r2: PostgreSQLR2Harness) -> None:
    _, _, _, runtime = _stack(pg_r2)
    barrier = Barrier(2, timeout=10)

    def initialize():
        barrier.wait()
        try:
            return "ok", runtime.auth.initialize(
                handle="c11_pg_owner", password="virtual passphrase 123",
                bootstrap_token=b"b" * 32, client_host="127.0.0.1", now=NOW,
            )
        except AuthError as exc:
            return exc.code, None

    with ThreadPoolExecutor(max_workers=2) as pool:
        initialized = list(pool.map(lambda _: initialize(), range(2)))
    assert sorted(item[0] for item in initialized) == ["already_initialized", "ok"]
    tokens = runtime.auth.login(
        handle="c11_pg_owner", password="virtual passphrase 123",
        client_fingerprint="c11-pg", device_name="virtual device", platform="api_test", now=NOW,
    )
    principal = runtime.auth.authenticate_access(tokens.access_token, now=NOW)
    code = runtime.auth.create_binding_code(principal, channel="virtual_channel", now=NOW)
    barrier = Barrier(2, timeout=10)

    def consume():
        barrier.wait()
        try:
            return "ok", runtime.auth.consume_binding_code(
                adapter_token=b"a" * 32, code_id=code.code_id, channel="virtual_channel",
                provider_account="virtual-provider", external_subject="virtual-subject",
                code=code.code, now=NOW,
            )
        except AuthError as exc:
            return exc.code, None

    with ThreadPoolExecutor(max_workers=2) as pool:
        consumed = list(pool.map(lambda _: consume(), range(2)))
    assert sorted(item[0] for item in consumed) == ["binding_code_invalid", "ok"]
    with pg_r2.sessions() as session:
        assert session.scalar(select(ChannelBindingCode).where(ChannelBindingCode.id == code.code_id)).status == "consumed"
        assert len(session.scalars(select(ChannelIdentityBinding)).all()) == 1

    barrier = Barrier(2, timeout=10)
    def refresh():
        barrier.wait()
        try:
            return "ok", runtime.auth.refresh(tokens.refresh_token, now=NOW + timedelta(seconds=1))
        except AuthError as exc:
            return exc.code, None
    with ThreadPoolExecutor(max_workers=2) as pool:
        refreshed = list(pool.map(lambda _: refresh(), range(2)))
    assert {item[0] for item in refreshed} == {"ok", "session_refresh_replayed"}


def test_c11_pg_receipt_setting_memory_cursor_and_lease_are_linearizable(pg_r2: PostgreSQLR2Harness) -> None:
    _, _, _, runtime = _stack(pg_r2)
    key = f"conversation-{uuid.uuid4()}"
    barrier = Barrier(2, timeout=10)
    def create():
        barrier.wait()
        try:
            row, replayed = runtime.conversations.create(
                user_id=BOOTSTRAP_USER_ID, channel="api_test", module_id="daily_finance",
                profile_id="daily_finance.assistant@1", idempotency_key=key, now=NOW,
            )
            return "ok", row.id, replayed
        except HostStateError as exc:
            return exc.code, None, False
    with ThreadPoolExecutor(max_workers=2) as pool:
        conversations = list(pool.map(lambda _: create(), range(2)))
    assert sorted(item[0] for item in conversations) == ["concurrent_modification", "ok"]
    winner = next(item[1] for item in conversations if item[0] == "ok")
    replay, replayed = runtime.conversations.create(
        user_id=BOOTSTRAP_USER_ID, channel="api_test", module_id="daily_finance",
        profile_id="daily_finance.assistant@1", idempotency_key=key, now=NOW,
    )
    assert replayed and replay.id == winner

    with pytest.raises(HostStateError, match="setting_secret_forbidden"):
        runtime.settings.put(
            user_id=BOOTSTRAP_USER_ID, module_id="daily_finance", key="assistant_mode",
            value={"nested": {"api_key": "virtual-secret"}}, schema_version=1,
            expected_version=None, idempotency_key=f"secret-{uuid.uuid4()}", now=NOW,
        )
    setting, replayed = runtime.settings.put(
        user_id=BOOTSTRAP_USER_ID, module_id="daily_finance", key="assistant_mode",
        value={"enabled": True}, schema_version=1, expected_version=None,
        idempotency_key=f"setting-{uuid.uuid4()}", now=NOW,
    )
    assert not replayed and setting.value_json == '{"enabled":true}'
    race_key = f"setting-race-{uuid.uuid4()}"
    barrier = Barrier(2, timeout=10)
    def put_setting():
        barrier.wait()
        try:
            row, replay = runtime.settings.put(
                user_id=BOOTSTRAP_USER_ID, module_id="daily_finance", key="module_enabled",
                value={"enabled": True}, schema_version=1, expected_version=None,
                idempotency_key=race_key, now=NOW,
            )
            return "ok", row.id, replay
        except HostStateError as exc:
            return exc.code, None, False
    with ThreadPoolExecutor(max_workers=2) as pool:
        setting_race = list(pool.map(lambda _: put_setting(), range(2)))
    assert sorted(item[0] for item in setting_race) == ["concurrent_modification", "ok"]
    replay_setting, was_replayed = runtime.settings.put(
        user_id=BOOTSTRAP_USER_ID, module_id="daily_finance", key="module_enabled",
        value={"enabled": True}, schema_version=1, expected_version=None,
        idempotency_key=race_key, now=NOW,
    )
    assert was_replayed and replay_setting.id == next(item[1] for item in setting_race if item[0] == "ok")

    candidate = runtime.memories.propose(
        user_id=BOOTSTRAP_USER_ID, source_namespace="daily_finance.candidates",
        target_namespace="daily_finance.confirmed", kind="preference",
        value={"drink": "virtual tea"}, tags=["virtual"], source_type="test",
        source_ref_digest=uuid.uuid4().hex * 2, sensitivity="private",
        proposed_by_profile_id="daily_finance.assistant@1", now=NOW,
    )
    barrier = Barrier(2, timeout=10)
    def confirm():
        barrier.wait()
        try:
            item, replay = runtime.memories.decide(
                candidate.id, user_id=BOOTSTRAP_USER_ID, confirm=True, target_namespace=None,
                allowed_namespaces=frozenset({"daily_finance.confirmed"}),
                idempotency_key=f"confirm-{uuid.uuid4()}", now=NOW,
            )
            return "ok", item.id, replay
        except HostStateError as exc:
            return exc.code, None, False
    with ThreadPoolExecutor(max_workers=2) as pool:
        confirmations = list(pool.map(lambda _: confirm(), range(2)))
    assert [item[0] for item in confirmations].count("ok") == 1
    assert any(item[0] == "memory_candidate_conflict" for item in confirmations)
    confirmed_item_id = next(item[1] for item in confirmations if item[0] == "ok")

    conversation = _conversation(runtime, key=f"lease-{uuid.uuid4()}")
    run = AgentRunRecord(
        user_id=BOOTSTRAP_USER_ID, actor_id=BOOTSTRAP_USER_ID, conversation_id=conversation.id,
        source_system="api_test", source_event_digest=uuid.uuid4().hex * 2,
        request_fingerprint=uuid.uuid4().hex * 2, status="running", module_id="daily_finance",
        module_version="1.0.0", profile_id="daily_finance.assistant@1", profile_version="1.0.0",
        attempt_no=1, lease_expires_at=NOW - timedelta(seconds=1), created_at=NOW, updated_at=NOW,
    )
    with pg_r2.sessions() as session, session.begin():
        session.add(run)
    lease = RunLeaseCoordinator(pg_r2.sessions)
    barrier = Barrier(2, timeout=10)
    def acquire():
        barrier.wait()
        try:
            return "ok", lease.acquire(run.id, user_id=BOOTSTRAP_USER_ID, now=NOW).attempt_no
        except WorkflowError as exc:
            return exc.code, None
    with ThreadPoolExecutor(max_workers=2) as pool:
        leases = list(pool.map(lambda _: acquire(), range(2)))
    assert sorted(item[0] for item in leases) == ["ok", "run_lease_active"]
    lease.renew(run.id, user_id=BOOTSTRAP_USER_ID, attempt_no=2, now=NOW)
    with pytest.raises(WorkflowError, match="run_lease_lost"):
        lease.renew(run.id, user_id=BOOTSTRAP_USER_ID, attempt_no=1, now=NOW)

    with pg_r2.sessions() as session:
        assert session.get(ModuleSettingRecord, setting.id) is not None
        assert session.get(MemoryItemRecord, confirmed_item_id).status == "active"
        completed = session.scalars(select(HostRequestReceiptRecord).where(HostRequestReceiptRecord.completed_at.is_not(None))).all()
        assert completed
        assert all("virtual-secret" not in (row.result_json or "") for row in completed)


def test_c11_pg_pending_commit_recovery_is_exactly_once(pg_r2: PostgreSQLR2Harness, monkeypatch) -> None:
    finance, _, application, conversation, candidate = _candidate_application(
        pg_r2, suffix=f"c11-{uuid.uuid4().hex[:8]}"
    )
    original_mark = application._pending.mark_committed
    monkeypatch.setattr(
        application._pending,
        "mark_committed",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("virtual post-commit interruption")),
    )
    with pytest.raises(RuntimeError, match="virtual post-commit interruption"):
        application.resume(
            candidate.run_id, actor_id=BOOTSTRAP_USER_ID, conversation_id=conversation.id,
            action="confirm", permissions=frozenset({"finance:write"}),
            confirmation_code=candidate.result["confirmation_code"], now=NOW + timedelta(seconds=1),
            channel="api_test",
        )
    before = [row for row in finance.list_transactions() if row.kind == "expense"]
    assert len(before) == 1
    monkeypatch.setattr(application._pending, "mark_committed", original_mark)
    recovered = application.resume(
        candidate.run_id, actor_id=BOOTSTRAP_USER_ID, conversation_id=conversation.id,
        action="confirm", permissions=frozenset({"finance:write"}),
        confirmation_code=candidate.result["confirmation_code"], now=NOW + timedelta(seconds=62),
        channel="api_test",
    )
    assert recovered.status == "success"
    assert len([row for row in finance.list_transactions() if row.kind == "expense"]) == 1


def test_c11_pg_production_factory_ready_and_stale_schema_fail_closed(pg_r2: PostgreSQLR2Harness) -> None:
    with migrated_schema(pg_r2.raw_url, pg_r2.admin, prefix="p4_c11_ind_ready") as (_, url, _):
        app = create_production_app(
            _production_config(url),
            provider=ScriptedModelProvider([AssistantTurn(content="virtual ready")]),
        )
        with TestClient(app, client=("127.0.0.1", 53111), raise_server_exceptions=False) as client:
            assert client.get("/healthz").status_code == 200
            assert client.get("/readyz").status_code == 200
        app.state.engine.dispose()
    with migrated_schema(
        pg_r2.raw_url, pg_r2.admin, prefix="p4_c11_ind_stale", revision=P3_HEAD
    ) as (_, url, _):
        app = create_production_app(
            _production_config(url),
            provider=ScriptedModelProvider([AssistantTurn(content="virtual stale")]),
        )
        with TestClient(app, client=("127.0.0.1", 53112), raise_server_exceptions=False) as client:
            assert client.get("/healthz").status_code == 200
            assert client.get("/readyz").status_code == 503
        app.state.engine.dispose()
