"""Executor-only real PostgreSQL evidence for the P4-B6-R1 schema slice."""

from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import event, func, inspect, select, text, update
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import IntegrityError

from wife_system.api import host_routes
from wife_system.api.app import create_app
from wife_system.finance.db import make_engine, make_session_factory
from wife_system.finance.models import BOOTSTRAP_USER_ID
from wife_system.host.auth.errors import AuthError
from wife_system.host.auth.models import (
    AppUser,
    ChannelBindingAudit,
    ChannelBindingCode,
    ChannelIdentityBinding,
)
from wife_system.host.auth.service import AuthenticatedSession, AuthSecrets, AuthService
from wife_system.host.factory import build_host_runtime
from wife_system.host.state import (
    CommandOutcome,
    HostCommandService,
    HostIdempotency,
    HostKeys,
    HostStateError,
)
from wife_system.host.state_models import HostRequestReceiptRecord


P3_HEAD = "c82d7a4f901e"
P4_HEAD = "p4_host_state"
ROOT = Path(__file__).resolve().parents[2]


class _FinanceAdapter:
    def __getattr__(self, name):
        if name.startswith(("list_", "get_", "account_", "monthly_", "record_")):
            return lambda *_args, **_kwargs: {"status": "ok"}
        raise AttributeError(name)


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
class PostgreSQLHarness:
    raw_url: str
    schema: str
    admin: Engine
    engine: Engine
    url: str


@pytest.fixture(scope="module")
def pg_r1() -> Iterator[PostgreSQLHarness]:
    raw_url = os.getenv("FINANCE_TEST_POSTGRES_URL")
    if not raw_url or make_url(raw_url).get_backend_name() != "postgresql":
        pytest.skip("FINANCE_TEST_POSTGRES_URL is required for P4-B6-R1 PostgreSQL evidence")
    schema = f"p4_b6_r1_schema_{uuid.uuid4().hex}"
    admin = make_engine(raw_url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    url = isolated_url(raw_url, schema)
    engine: Engine | None = None
    try:
        command.upgrade(migration_config(url), P4_HEAD)
        engine = make_engine(url)
        yield PostgreSQLHarness(raw_url, schema, admin, engine, url)
    finally:
        if engine is not None:
            engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        admin.dispose()


def _foreign_keys(engine: Engine, table: str) -> dict[str, tuple[tuple[str, ...], str, tuple[str, ...]]]:
    return {
        item["name"]: (
            tuple(item["constrained_columns"]),
            item["referred_table"],
            tuple(item["referred_columns"]),
        )
        for item in inspect(engine).get_foreign_keys(table)
    }


def _seed_cross_user_graph(pg: PostgreSQLHarness) -> dict[str, uuid.UUID]:
    values = {
        name: uuid.uuid4()
        for name in (
            "user_b", "conversation_a", "conversation_b", "run_a", "run_b",
            "pending_b", "item_a", "item_b",
        )
    }
    with pg.engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO app_user "
            "(id,handle_normalized,status,bootstrap_marker,initialized_at,deactivated_at,version_id,created_at) "
            "VALUES (:id,'r1_pg_other','active',NULL,CURRENT_TIMESTAMP,NULL,1,CURRENT_TIMESTAMP)"
        ), {"id": values["user_b"]})
        for conversation, user in (
            (values["conversation_a"], BOOTSTRAP_USER_ID),
            (values["conversation_b"], values["user_b"]),
        ):
            connection.execute(text(
                "INSERT INTO conversation "
                "(id,user_id,channel,module_id,profile_id,status,last_message_at,created_at) "
                "VALUES (:id,:user,'api_test','daily_finance','daily_finance.assistant@1',"
                "'active',NULL,CURRENT_TIMESTAMP)"
            ), {"id": conversation, "user": user})
        for suffix, run, user, conversation in (
            ("a", values["run_a"], BOOTSTRAP_USER_ID, values["conversation_a"]),
            ("b", values["run_b"], values["user_b"], values["conversation_b"]),
        ):
            connection.execute(text(
                "INSERT INTO agent_run "
                "(id,user_id,actor_id,conversation_id,source_system,source_event_digest,request_fingerprint,"
                "status,pause_reason,pending_action_id,answer,error_code,result_json,events_json,model_name,"
                "module_id,module_version,profile_id,profile_version,attempt_no,lease_expires_at,action_schema_version,"
                "created_at,updated_at) VALUES "
                "(:id,:user,:user,:conversation,'test',:digest,:fingerprint,'paused',NULL,NULL,NULL,NULL,"
                "NULL,NULL,'fake','daily_finance','1.0.0','daily_finance.assistant@1','1.0.0',1,NULL,1,"
                "CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
            ), {
                "id": run, "user": user, "conversation": conversation,
                "digest": f"digest-{suffix}", "fingerprint": f"fingerprint-{suffix}",
            })
        connection.execute(text(
            "INSERT INTO pending_action "
            "(id,user_id,run_id,actor_id,conversation_id,source_system,action_type,action_json,"
            "missing_fields_json,resource_versions_json,status,version_id,confirmation_code,"
            "approval_grant_id,final_result_json,module_id,profile_id,action_schema_version,"
            "commit_attempt_no,commit_lease_expires_at,created_at,expires_at,updated_at) VALUES "
            "(:id,:user,:run,:user,:conversation,'test','record_expense','{}','[]','{}',"
            "'needs_confirmation',1,'PGR1B',NULL,NULL,'daily_finance','daily_finance.assistant@1',"
            "1,0,NULL,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP + INTERVAL '1 day',CURRENT_TIMESTAMP)"
        ), {
            "id": values["pending_b"], "user": values["user_b"],
            "run": values["run_b"], "conversation": values["conversation_b"],
        })
        for item, user in (
            (values["item_a"], BOOTSTRAP_USER_ID),
            (values["item_b"], values["user_b"]),
        ):
            connection.execute(text(
                "INSERT INTO memory_item "
                "(id,user_id,namespace,kind,value_json,tags_json,source_type,source_ref_digest,"
                "sensitivity,status,confirmed_at,expires_at,deleted_at,superseded_by_id,audit_id,version_id) "
                "VALUES (:id,:user,'daily_finance','preference','{}','[]','test',:digest,"
                "'private','active',CURRENT_TIMESTAMP,NULL,NULL,NULL,:audit,1)"
            ), {"id": item, "user": user, "digest": uuid.uuid4().hex * 2, "audit": uuid.uuid4()})
    return values


def test_postgresql_r1_constraints_are_real_bounded_and_reject_cross_user_sql(
    pg_r1: PostgreSQLHarness,
) -> None:
    assert _foreign_keys(pg_r1.engine, "memory_item")["fk_memory_item_user_superseded"] == (
        ("user_id", "superseded_by_id"), "memory_item", ("user_id", "id"),
    )
    assert _foreign_keys(pg_r1.engine, "memory_candidate")["fk_memory_candidate_user_item"] == (
        ("user_id", "memory_item_id"), "memory_item", ("user_id", "id"),
    )
    assert _foreign_keys(pg_r1.engine, "agent_run")["fk_run_user_pending"] == (
        ("user_id", "pending_action_id"), "pending_action", ("user_id", "id"),
    )
    with pg_r1.engine.connect() as connection:
        constraint = connection.execute(text(
            "SELECT condeferrable, condeferred FROM pg_constraint "
            "WHERE conname='fk_run_user_pending' AND connamespace=to_regnamespace(:schema)"
        ), {"schema": pg_r1.schema}).one()
        assert constraint == (True, True)
        assert connection.scalar(text(
            "SELECT COALESCE(MAX(length(conname)),0) FROM pg_constraint "
            "WHERE connamespace=to_regnamespace(:schema)"
        ), {"schema": pg_r1.schema}) <= 63

    values = _seed_cross_user_graph(pg_r1)
    failures = (
        (
            "UPDATE memory_item SET superseded_by_id=:foreign WHERE id=:local",
            {"foreign": values["item_b"], "local": values["item_a"]},
        ),
        (
            "INSERT INTO memory_candidate "
            "(id,user_id,source_namespace,target_namespace,kind,value_json,tags_json,source_type,"
            "source_ref_digest,sensitivity,status,proposed_by_profile_id,proposed_by_profile_version,"
            "created_at,expires_at,"
            "decided_at,memory_item_id,audit_id,version_id) VALUES "
            "(:id,:user,'daily_finance','daily_finance','preference','{}','[]','test',:digest,"
            "'private','confirmed','daily_finance.assistant@1','1.0.0',CURRENT_TIMESTAMP,"
            "CURRENT_TIMESTAMP + INTERVAL '1 day',NULL,:foreign,NULL,1)",
            {"id": uuid.uuid4(), "user": BOOTSTRAP_USER_ID,
             "digest": uuid.uuid4().hex * 2, "foreign": values["item_b"]},
        ),
        (
            "UPDATE agent_run SET pending_action_id=:foreign WHERE id=:local",
            {"foreign": values["pending_b"], "local": values["run_a"]},
        ),
    )
    for statement, params in failures:
        with pytest.raises(IntegrityError):
            with pg_r1.engine.begin() as connection:
                connection.execute(text(statement), params)


def test_postgresql_cancelled_downgrade_upgrade_round_trip(pg_r1: PostgreSQLHarness) -> None:
    schema = f"p4_b6_r1_roundtrip_{uuid.uuid4().hex}"
    with pg_r1.admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    url = isolated_url(pg_r1.raw_url, schema)
    engine: Engine | None = None
    run_id, pending_id, conversation_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    try:
        config = migration_config(url)
        command.upgrade(config, P4_HEAD)
        engine = make_engine(url)
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO conversation "
                "(id,user_id,channel,module_id,profile_id,status,last_message_at,created_at) "
                "VALUES (:id,:user,'api_test','daily_finance','daily_finance.assistant@1',"
                "'active',NULL,CURRENT_TIMESTAMP)"
            ), {"id": conversation_id, "user": BOOTSTRAP_USER_ID})
            connection.execute(text(
                "INSERT INTO agent_run "
                "(id,user_id,actor_id,conversation_id,source_system,source_event_digest,request_fingerprint,"
                "status,pause_reason,pending_action_id,answer,error_code,result_json,events_json,model_name,"
                "module_id,module_version,profile_id,profile_version,attempt_no,lease_expires_at,action_schema_version,"
                "created_at,updated_at) VALUES "
                "(:id,:user,:user,:conversation,'test','roundtrip-digest','roundtrip-fingerprint',"
                "'cancelled','needs_confirmation',NULL,NULL,NULL,NULL,NULL,'fake','daily_finance',"
                "'1.0.0','daily_finance.assistant@1','1.0.0',1,NULL,1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
            ), {"id": run_id, "user": BOOTSTRAP_USER_ID, "conversation": conversation_id})
            connection.execute(text(
                "INSERT INTO pending_action "
                "(id,user_id,run_id,actor_id,conversation_id,source_system,action_type,action_json,"
                "missing_fields_json,resource_versions_json,status,version_id,confirmation_code,"
                "approval_grant_id,final_result_json,module_id,profile_id,action_schema_version,"
                "commit_attempt_no,commit_lease_expires_at,created_at,expires_at,updated_at) VALUES "
                "(:id,:user,:run,:user,:conversation,'test','record_expense','{}','[]','{}',"
                "'cancelled',1,'PGR1RT',NULL,NULL,'daily_finance','daily_finance.assistant@1',1,0,NULL,"
                "CURRENT_TIMESTAMP,CURRENT_TIMESTAMP + INTERVAL '1 day',CURRENT_TIMESTAMP)"
            ), {"id": pending_id, "user": BOOTSTRAP_USER_ID, "run": run_id,
                "conversation": conversation_id})
            connection.execute(
                text("UPDATE agent_run SET pending_action_id=:pending WHERE id=:run"),
                {"pending": pending_id, "run": run_id},
            )
        engine.dispose()
        engine = None

        command.downgrade(config, P3_HEAD)
        engine = make_engine(url)
        with engine.connect() as connection:
            assert connection.execute(text(
                "SELECT status,error_code,pause_reason FROM agent_run WHERE id=:id"
            ), {"id": run_id}).one() == ("error", "cancelled", None)
            assert connection.scalar(text(
                "SELECT status FROM pending_action WHERE id=:id"
            ), {"id": pending_id}) == "cancelled"
        engine.dispose()
        engine = None

        command.upgrade(config, P4_HEAD)
        engine = make_engine(url)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == P4_HEAD
            assert connection.scalar(text(
                "SELECT error_code FROM agent_run WHERE id=:id"
            ), {"id": run_id}) == "cancelled"
            assert connection.scalar(text(
                "SELECT COUNT(*) FROM pending_action WHERE id=:id"
            ), {"id": pending_id}) == 1
    finally:
        if engine is not None:
            engine.dispose()
        with pg_r1.admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))


def test_postgresql_binding_replacement_and_fifth_attempt_race(
    pg_r1: PostgreSQLHarness,
) -> None:
    sessions = make_session_factory(pg_r1.engine)
    secrets_config = AuthSecrets(
        bootstrap_token=b"p" * 32,
        binding_hmac_key=b"h" * 32,
        adapter_token=b"a" * 32,
    )
    auth = AuthService(sessions, secrets_config)
    now = datetime(2026, 9, 26, 1, 0, tzinfo=UTC)
    auth.initialize(
        handle="r1_pg_owner",
        password="correct horse battery staple",
        bootstrap_token=b"p" * 32,
        client_host="127.0.0.1",
        now=now,
    )
    tokens = auth.login(
        handle="r1_pg_owner",
        password="correct horse battery staple",
        client_fingerprint="r1-pg",
        device_name="pytest-postgresql",
        platform="api_test",
        now=now,
    )
    principal = auth.authenticate_access(tokens.access_token, now=now)
    old = auth.create_binding_code(principal, channel="fake_wechat", now=now)
    current = auth.create_binding_code(
        principal, channel="fake_wechat", now=now + timedelta(seconds=1)
    )
    with sessions() as session, session.begin():
        assert session.get(ChannelBindingCode, old.code_id).status == "revoked"
        current_row = session.get(ChannelBindingCode, current.code_id)
        assert current_row is not None
        current_row.attempts = 4

    def consume(code: str) -> object:
        try:
            return auth.consume_binding_code(
                adapter_token=b"a" * 32,
                code_id=current.code_id,
                channel="fake_wechat",
                provider_account="virtual-pg-provider",
                external_subject="virtual-pg-subject",
                code=code,
                now=now + timedelta(seconds=2),
            )
        except AuthError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        wrong_future = pool.submit(consume, "WRNG-CODE")
        correct_future = pool.submit(consume, current.code)
        wrong, correct = wrong_future.result(), correct_future.result()
    assert wrong == "binding_code_invalid"
    with sessions() as session:
        row = session.get(ChannelBindingCode, current.code_id)
        assert row is not None
        if row.status == "consumed":
            assert row.attempts == 4 and not isinstance(correct, str)
        else:
            assert row.status == "locked" and row.attempts == 5
            assert correct == "binding_code_invalid"

    with ThreadPoolExecutor(max_workers=2) as pool:
        replacements = list(
            pool.map(
                lambda offset: auth.create_binding_code(
                    principal,
                    channel="fake_wechat",
                    now=now + timedelta(seconds=10 + offset),
                ),
                range(2),
            )
        )
    with sessions() as session:
        rows = session.scalars(
            select(ChannelBindingCode).where(
                ChannelBindingCode.user_id == principal.user_id,
                ChannelBindingCode.channel == "fake_wechat",
            )
        ).all()
        active = [row for row in rows if row.status == "active"]
        assert len(active) == 1
        assert active[0].id in {item.code_id for item in replacements}
        assert sum(row.status == "revoked" for row in rows) >= 2


def test_postgresql_competing_binding_codes_return_safe_replayable_conflict(
    pg_r1: PostgreSQLHarness,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sessions = make_session_factory(pg_r1.engine)
    runtime = build_host_runtime(
        sessions=sessions,
        finance_adapter=_FinanceAdapter(),
        auth_secrets=AuthSecrets(
            bootstrap_token=b"b" * 32,
            binding_hmac_key=b"h" * 32,
            adapter_token=b"a" * 32,
        ),
        state_keys=HostKeys({1: b"r" * 32}),
        cursor_secret=b"c" * 32,
    )
    app = create_app(host_runtime=runtime)
    now = datetime(2026, 9, 26, 2, 0, tzinfo=UTC)

    class ControlledDateTime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[no-untyped-def]
            if tz is None:
                return now.astimezone().replace(tzinfo=None)
            return now.astimezone(tz)

    monkeypatch.setattr(host_routes, "datetime", ControlledDateTime)
    user_ids = (uuid.uuid4(), uuid.uuid4())
    with sessions() as session, session.begin():
        for index, user_id in enumerate(user_ids):
            session.add(
                AppUser(
                    id=user_id,
                    handle=f"r1_race_{index}_{user_id.hex[:8]}",
                    status="active",
                    version_id=1,
                    created_at=now,
                )
            )
    principals = tuple(
        AuthenticatedSession(
            user_id=user_id,
            session_id=uuid.uuid4(),
            device_id=uuid.uuid4(),
            authenticated_at=now,
        )
        for user_id in user_ids
    )
    codes = tuple(
        runtime.auth.create_binding_code(
            principal,
            channel="fake_wechat",
            now=now + timedelta(seconds=index),
        )
        for index, principal in enumerate(principals)
    )
    idempotency_keys = tuple(f"binding-race-{uuid.uuid4()}" for _ in user_ids)
    provider_account = f"virtual-race-provider-{uuid.uuid4()}"
    external_subject = f"virtual-race-subject-{uuid.uuid4()}"
    payloads = tuple(
        {
            "code_id": str(created.code_id),
            "channel": "fake_wechat",
            "provider_account": provider_account,
            "external_subject": external_subject,
            "code": created.code,
        }
        for created in codes
    )

    insert_barrier = Barrier(2)

    def synchronize_binding_insert(
        _connection, _cursor, statement, _parameters, _context, _executemany
    ) -> None:
        if statement.lstrip().lower().startswith("insert into channel_identity_binding"):
            insert_barrier.wait(timeout=10)

    event.listen(pg_r1.engine, "before_cursor_execute", synchronize_binding_insert)
    try:
        with TestClient(
            app,
            client=("127.0.0.1", 50001),
            raise_server_exceptions=False,
        ) as client:
            def consume(index: int):
                return client.post(
                    "/api/v1/channel-bindings/consume",
                    headers={
                        "Idempotency-Key": idempotency_keys[index],
                        "X-Channel-Adapter-Token": "a" * 32,
                    },
                    json=payloads[index],
                )

            with ThreadPoolExecutor(max_workers=2) as pool:
                responses = list(pool.map(consume, range(2)))
    finally:
        event.remove(pg_r1.engine, "before_cursor_execute", synchronize_binding_insert)

    assert sorted(response.status_code for response in responses) == [200, 409]
    winner_index = next(index for index, response in enumerate(responses) if response.status_code == 200)
    loser_index = 1 - winner_index
    winner_response = responses[winner_index]
    loser_response = responses[loser_index]
    assert loser_response.json()["error"]["code"] == "channel_identity_conflict"
    winner_binding_id = uuid.UUID(winner_response.json()["binding_id"])
    subject_digest = runtime.auth._binding_digest(b"external-subject", external_subject)

    with sessions() as session:
        active_bindings = session.scalars(
            select(ChannelIdentityBinding).where(
                ChannelIdentityBinding.channel == "fake_wechat",
                ChannelIdentityBinding.external_subject_digest == subject_digest,
                ChannelIdentityBinding.status == "active",
            )
        ).all()
        assert len(active_bindings) == 1
        assert active_bindings[0].id == winner_binding_id
        assert session.scalar(
            select(func.count(ChannelBindingAudit.id)).where(
                ChannelBindingAudit.binding_id == winner_binding_id,
                ChannelBindingAudit.action == "bound",
            )
        ) == 1
        winner_code = session.get(ChannelBindingCode, codes[winner_index].code_id)
        loser_code = session.get(ChannelBindingCode, codes[loser_index].code_id)
        assert winner_code is not None and winner_code.status == "consumed"
        assert loser_code is not None
        assert loser_code.status == "active" and loser_code.attempts == 0
        receipts = session.scalars(
            select(HostRequestReceiptRecord).where(
                HostRequestReceiptRecord.user_id.in_(user_ids),
                HostRequestReceiptRecord.operation == "binding.code.consume",
            )
        ).all()
        assert len(receipts) == 2
        loser_receipt = next(row for row in receipts if row.user_id == user_ids[loser_index])
        assert loser_receipt.result_json is not None
        assert '"__error_code":"channel_identity_conflict"' in loser_receipt.result_json
        safe_receipt_text = "\n".join(row.result_json or "" for row in receipts)

    with TestClient(
        app,
        client=("127.0.0.1", 50002),
        raise_server_exceptions=False,
    ) as replay_client:
        replay = replay_client.post(
            "/api/v1/channel-bindings/consume",
            headers={
                "Idempotency-Key": idempotency_keys[loser_index],
                "X-Channel-Adapter-Token": "a" * 32,
            },
            json=payloads[loser_index],
        )
    assert replay.status_code == 409
    assert replay.json()["error"]["code"] == "channel_identity_conflict"
    with sessions() as session:
        loser_code = session.get(ChannelBindingCode, codes[loser_index].code_id)
        assert loser_code is not None
        assert loser_code.status == "active" and loser_code.attempts == 0
        assert session.scalar(
            select(func.count(HostRequestReceiptRecord.id)).where(
                HostRequestReceiptRecord.user_id.in_(user_ids),
                HostRequestReceiptRecord.operation == "binding.code.consume",
            )
        ) == 2

    runtime.auth.revoke_binding(
        user_ids[winner_index],
        winner_binding_id,
        now=now + timedelta(seconds=10),
    )
    with TestClient(
        app,
        client=("127.0.0.1", 50003),
        raise_server_exceptions=False,
    ) as retry_client:
        retry = retry_client.post(
            "/api/v1/channel-bindings/consume",
            headers={
                "Idempotency-Key": f"binding-race-retry-{uuid.uuid4()}",
                "X-Channel-Adapter-Token": "a" * 32,
            },
            json=payloads[loser_index],
        )
    assert retry.status_code == 200, retry.text
    with sessions() as session:
        loser_code = session.get(ChannelBindingCode, codes[loser_index].code_id)
        assert loser_code is not None and loser_code.status == "consumed"
        rebound = session.get(ChannelIdentityBinding, uuid.UUID(retry.json()["binding_id"]))
        assert rebound is not None and rebound.user_id == user_ids[loser_index]

    safe_output = "\n".join(
        (
            loser_response.text,
            replay.text,
            safe_receipt_text,
            *(record.getMessage() for record in caplog.records),
        )
    )
    for private_value in (
        provider_account,
        external_subject,
        codes[0].code,
        codes[1].code,
        subject_digest,
        "uq_binding_active_subject",
        "duplicate key",
        "IntegrityError",
    ):
        assert private_value not in safe_output


@pytest.mark.parametrize(
    "operation",
    ["auth.initialize", "binding.code.create", "binding.code.consume", "binding.revoke"],
)
def test_postgresql_host_commands_are_atomic_recoverable_and_idempotent(
    pg_r1: PostgreSQLHarness, operation: str
) -> None:
    sessions = make_session_factory(pg_r1.engine)
    commands = HostCommandService(
        sessions, HostIdempotency(HostKeys({1: b"r" * 32}))
    )
    user_id = uuid.uuid4()
    safe_id = uuid.uuid4()
    raw_secret = "R1PG-SECRET" if operation == "binding.code.create" else None
    with sessions() as session, session.begin():
        session.add(
            AppUser(
                id=user_id,
                handle=f"r1_{user_id.hex[:12]}",
                status="active",
                version_id=1,
                created_at=datetime.now(UTC),
            )
        )

    def mutate(session):
        session.execute(
            update(AppUser)
            .where(AppUser.id == user_id)
            .values(version_id=AppUser.version_id + 1)
        )
        public = {"id": str(safe_id)}
        if raw_secret is not None:
            public["code"] = raw_secret
        return CommandOutcome(
            public_result=public,
            receipt_result={"id": str(safe_id), "status": "completed"},
        )

    def execute(payload: dict[str, str]) -> object:
        try:
            return commands.execute(
                user_id=user_id,
                operation=operation,
                idempotency_key="same-key",
                payload=payload,
                command=mutate,
                replay_error=(
                    "one_time_secret_unavailable"
                    if operation == "binding.code.create"
                    else None
                ),
            )
        except (AuthError, HostStateError) as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: execute({"value": "same"}), range(2)))
    with sessions() as session:
        assert session.get(AppUser, user_id).version_id == 2
        receipt = session.scalar(
            select(HostRequestReceiptRecord).where(
                HostRequestReceiptRecord.user_id == user_id,
                HostRequestReceiptRecord.operation == operation,
            )
        )
        assert receipt is not None
        assert raw_secret is None or raw_secret not in (receipt.result_json or "")
    if operation == "binding.code.create":
        assert sum(isinstance(value, tuple) for value in outcomes) == 1
        assert any(
            value in {"concurrent_modification", "one_time_secret_unavailable"}
            for value in outcomes
            if isinstance(value, str)
        )
        assert execute({"value": "same"}) == "one_time_secret_unavailable"
    else:
        assert sum(isinstance(value, tuple) for value in outcomes) >= 1
        assert all(
            isinstance(value, tuple) or value == "concurrent_modification"
            for value in outcomes
        )
        replay = execute({"value": "same"})
        assert isinstance(replay, tuple) and replay[1] is True

    assert execute({"value": "different"}) == "idempotency_conflict"

    failure_key = f"failure-{operation}"

    def fail_before_commit(session):
        session.execute(
            update(AppUser)
            .where(AppUser.id == user_id)
            .values(version_id=AppUser.version_id + 1)
        )
        raise RuntimeError("injected before commit")

    with pytest.raises(RuntimeError, match="injected before commit"):
        commands.execute(
            user_id=user_id,
            operation=operation,
            idempotency_key=failure_key,
            payload={"value": "retry"},
            command=fail_before_commit,
        )
    commands.execute(
        user_id=user_id,
        operation=operation,
        idempotency_key=failure_key,
        payload={"value": "retry"},
        command=mutate,
    )
    with sessions() as session:
        assert session.get(AppUser, user_id).version_id == 3
