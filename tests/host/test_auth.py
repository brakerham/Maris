from __future__ import annotations

import re
import secrets
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from wife_system.finance.db import Base, make_engine, make_session_factory
from wife_system.host.auth import (
    AppUser,
    AuthError,
    AuthSecrets,
    AuthService,
    AuthenticatedSession,
    ChannelBindingCode,
    ChannelIdentityBinding,
    DeviceSession,
    PasswordCredential,
    SessionRefreshToken,
)


NOW = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
PASSWORD = "correct horse battery staple"


@dataclass
class Harness:
    sessions: sessionmaker[Session]
    service: AuthService
    secrets: AuthSecrets
    user_id: uuid.UUID

    def login(self, *, device_name: str = "Test device", now: datetime = NOW):
        return self.service.login(
            handle="owner_user",
            password=PASSWORD,
            client_fingerprint="fixture-client",
            device_name=device_name,
            platform="api_test",
            now=now,
        )


@pytest.fixture
def harness(tmp_path: Path) -> Harness:
    engine = make_engine(f"sqlite+pysqlite:///{tmp_path / 'auth.db'}")
    Base.metadata.create_all(engine)
    sessions = make_session_factory(engine)
    config = AuthSecrets(
        bootstrap_token=secrets.token_bytes(32),
        binding_hmac_key=secrets.token_bytes(32),
        adapter_token=secrets.token_bytes(32),
    )
    service = AuthService(sessions, config, random_bytes=secrets.token_bytes)
    service.ensure_pending_owner(now=NOW)
    user_id = service.initialize(
        handle="  Owner_User ",
        password=PASSWORD,
        bootstrap_token=config.bootstrap_token,
        client_host="127.0.0.1",
        now=NOW,
    )
    result = Harness(sessions, service, config, user_id)
    yield result
    engine.dispose()


def error_code(exc: pytest.ExceptionInfo[AuthError]) -> str:
    return exc.value.code


def test_bootstrap_validation_hash_contract_and_single_initialization(tmp_path: Path) -> None:
    engine = make_engine(f"sqlite+pysqlite:///{tmp_path / 'bootstrap.db'}")
    Base.metadata.create_all(engine)
    sessions = make_session_factory(engine)
    config = AuthSecrets(secrets.token_bytes(32), secrets.token_bytes(32), secrets.token_bytes(32))
    service = AuthService(sessions, config)
    service.ensure_pending_owner(now=NOW)

    assert service.bootstrap_status() is True
    with pytest.raises(AuthError) as caught:
        service.initialize(
            handle="owner_user",
            password=PASSWORD,
            bootstrap_token=config.bootstrap_token,
            client_host="192.0.2.10",
            now=NOW,
        )
    assert error_code(caught) == "bootstrap_unauthorized"
    for invalid in ("short", "contains\x00control", "x" * 129, "surrogate\ud800value"):
        with pytest.raises(AuthError) as caught:
            service.initialize(
                handle="owner_user",
                password=invalid,
                bootstrap_token=config.bootstrap_token,
                client_host="::1",
                now=NOW,
            )
        assert error_code(caught) == "invalid_password"

    user_id = service.initialize(
        handle=" Owner_User ",
        password=PASSWORD,
        bootstrap_token=config.bootstrap_token,
        client_host="::1",
        now=NOW,
    )
    assert service.bootstrap_status() is False
    with sessions() as session:
        user = session.get(AppUser, user_id)
        credential = session.scalar(select(PasswordCredential).where(PasswordCredential.user_id == user_id))
        assert user is not None and user.handle == "owner_user" and user.status == "active"
        assert credential is not None and credential.algorithm == "argon2id"
        assert PASSWORD not in credential.password_hash
        assert credential.password_hash.startswith("$argon2id$v=19$m=65536,t=3,p=1$")
    with pytest.raises(AuthError) as caught:
        service.initialize(
            handle="another_owner",
            password=PASSWORD,
            bootstrap_token=config.bootstrap_token,
            client_host="127.0.0.1",
            now=NOW,
        )
    assert error_code(caught) == "already_initialized"
    engine.dispose()


def test_bootstrap_initialization_is_single_winner_under_concurrency(tmp_path: Path) -> None:
    engine = make_engine(f"sqlite+pysqlite:///{tmp_path / 'bootstrap-race.db'}")
    Base.metadata.create_all(engine)
    sessions = make_session_factory(engine)
    config = AuthSecrets(secrets.token_bytes(32), secrets.token_bytes(32), secrets.token_bytes(32))
    service = AuthService(sessions, config)
    service.ensure_pending_owner(now=NOW)
    barrier = Barrier(2)

    def initialize():
        barrier.wait()
        try:
            return service.initialize(
                handle="owner_user",
                password=PASSWORD,
                bootstrap_token=config.bootstrap_token,
                client_host="127.0.0.1",
                now=NOW,
            )
        except AuthError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: initialize(), range(2)))
    assert len([value for value in outcomes if isinstance(value, uuid.UUID)]) == 1
    assert [value for value in outcomes if isinstance(value, str)] == ["already_initialized"]
    with sessions() as session:
        assert session.scalar(select(func.count(PasswordCredential.id))) == 1
    engine.dispose()


def test_successful_login_rehashes_outdated_argon2_parameters(harness: Harness) -> None:
    old_hasher = PasswordHash(
        [Argon2Hasher(time_cost=1, memory_cost=8192, parallelism=1, salt_len=8, hash_len=16)]
    )
    with harness.sessions() as session, session.begin():
        credential = session.scalar(select(PasswordCredential).where(PasswordCredential.user_id == harness.user_id))
        assert credential is not None
        credential.password_hash = old_hasher.hash(PASSWORD)
    harness.login()
    with harness.sessions() as session:
        credential = session.scalar(select(PasswordCredential).where(PasswordCredential.user_id == harness.user_id))
        assert credential is not None
        assert credential.password_hash.startswith("$argon2id$v=19$m=65536,t=3,p=1$")


def test_login_tokens_are_opaque_digest_only_and_expire_at_exact_boundaries(harness: Harness) -> None:
    issued = harness.login()
    assert len(issued.access_token) == len(issued.refresh_token) == 43
    assert issued.access_token != issued.refresh_token
    principal = harness.service.authenticate_access(issued.access_token, now=NOW + timedelta(minutes=14, seconds=59))
    assert principal.user_id == harness.user_id
    with pytest.raises(AuthError) as caught:
        harness.service.authenticate_access(issued.access_token, now=NOW + timedelta(minutes=15))
    assert error_code(caught) == "session_expired"
    with harness.sessions() as session:
        row = session.get(DeviceSession, issued.session_id)
        refresh = session.scalar(select(SessionRefreshToken).where(SessionRefreshToken.session_id == issued.session_id))
        assert row is not None and refresh is not None
        stored = " ".join((row.access_digest, refresh.token_digest))
        assert issued.access_token not in stored and issued.refresh_token not in stored
        assert re.fullmatch(r"[0-9a-f]{64}", row.access_digest)
        assert re.fullmatch(r"[0-9a-f]{64}", refresh.token_digest)


def test_refresh_rotates_both_tokens_and_replay_revokes_the_family(harness: Harness) -> None:
    first = harness.login()
    second = harness.service.refresh(first.refresh_token, now=NOW + timedelta(minutes=1))
    assert second.session_id == first.session_id
    assert second.refresh_expires_at == first.refresh_expires_at
    with pytest.raises(AuthError) as caught:
        harness.service.authenticate_access(first.access_token, now=NOW + timedelta(minutes=1))
    assert error_code(caught) == "session_revoked"
    with pytest.raises(AuthError) as caught:
        harness.service.refresh(first.refresh_token, now=NOW + timedelta(minutes=2))
    assert error_code(caught) == "session_refresh_replayed"
    with pytest.raises(AuthError) as caught:
        harness.service.authenticate_access(second.access_token, now=NOW + timedelta(minutes=2))
    assert error_code(caught) == "session_revoked"


def test_concurrent_refresh_has_one_success_and_replay_revokes_winner(harness: Harness) -> None:
    original = harness.login()

    def rotate():
        try:
            return harness.service.refresh(original.refresh_token, now=NOW + timedelta(minutes=1))
        except AuthError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: rotate(), range(2)))
    successes = [value for value in outcomes if not isinstance(value, str)]
    failures = [value for value in outcomes if isinstance(value, str)]
    assert len(successes) == 1
    assert failures == ["session_refresh_replayed"]
    with pytest.raises(AuthError) as caught:
        harness.service.authenticate_access(successes[0].access_token, now=NOW + timedelta(minutes=2))
    assert error_code(caught) == "session_revoked"


def test_login_rate_limit_session_revoke_change_password_and_deactivate(harness: Harness) -> None:
    for attempt in range(5):
        with pytest.raises(AuthError) as caught:
            harness.service.login(
                handle="owner_user",
                password="wrong password value",
                client_fingerprint="limited-client",
                device_name="Device",
                platform="api_test",
                now=NOW + timedelta(seconds=attempt),
            )
        assert error_code(caught) == ("login_rate_limited" if attempt == 4 else "invalid_credentials")
    with pytest.raises(AuthError) as caught:
        harness.service.login(
            handle="owner_user",
            password=PASSWORD,
            client_fingerprint="limited-client",
            device_name="Device",
            platform="api_test",
            now=NOW + timedelta(minutes=1),
        )
    assert error_code(caught) == "login_rate_limited" and caught.value.retry_after is not None

    first = harness.login(device_name="First")
    second = harness.service.login(
        handle="owner_user",
        password=PASSWORD,
        client_fingerprint="second-client",
        device_name="Second",
        platform="api_test",
        now=NOW,
    )
    principal = harness.service.authenticate_access(first.access_token, now=NOW)
    assert len(harness.service.list_sessions(principal, now=NOW)) == 2
    harness.service.revoke_session(principal, second.session_id, now=NOW + timedelta(seconds=1))
    with pytest.raises(AuthError):
        harness.service.authenticate_access(second.access_token, now=NOW + timedelta(seconds=1))

    replacement = harness.service.change_password(
        first.access_token,
        old_password=PASSWORD,
        new_password="new password material",
        now=NOW + timedelta(minutes=1),
    )
    with pytest.raises(AuthError):
        harness.service.authenticate_access(first.access_token, now=NOW + timedelta(minutes=1))
    assert harness.service.authenticate_access(replacement.access_token, now=NOW + timedelta(minutes=1)).user_id == harness.user_id
    harness.service.deactivate_account(harness.user_id, now=NOW + timedelta(minutes=2))
    with pytest.raises(AuthError) as caught:
        harness.service.authenticate_access(replacement.access_token, now=NOW + timedelta(minutes=2))
    assert error_code(caught) == "session_revoked"


def test_active_device_session_limit_is_ten(harness: Harness) -> None:
    for index in range(10):
        harness.service.login(
            handle="owner_user",
            password=PASSWORD,
            client_fingerprint=f"client-{index}",
            device_name=f"Device {index}",
            platform="api_test",
            now=NOW,
        )
    with pytest.raises(AuthError) as caught:
        harness.service.login(
            handle="owner_user",
            password=PASSWORD,
            client_fingerprint="client-overflow",
            device_name="Overflow",
            platform="api_test",
            now=NOW,
        )
    assert error_code(caught) == "active_session_limit"


def test_binding_code_hmac_expiry_adapter_gate_and_no_raw_identity(harness: Harness) -> None:
    principal = harness.service.authenticate_access(harness.login().access_token, now=NOW)
    created = harness.service.create_binding_code(principal, channel="fake_wechat", now=NOW)
    assert re.fullmatch(r"[23456789A-HJ-NP-Z]{4}-[23456789A-HJ-NP-Z]{4}", created.code)
    with pytest.raises(AuthError) as caught:
        harness.service.consume_binding_code(
            adapter_token=secrets.token_bytes(32),
            channel="fake_wechat",
            provider_account="virtual-provider",
            external_subject="virtual-subject",
            code=created.code,
            now=NOW,
        )
    assert error_code(caught) == "channel_adapter_unauthorized"
    with harness.sessions() as session:
        row = session.get(ChannelBindingCode, created.code_id)
        assert row is not None and row.attempts == 0 and row.consumed_at is None
        assert created.code not in row.code_digest

    with pytest.raises(AuthError) as caught:
        harness.service.consume_binding_code(
            adapter_token=harness.secrets.adapter_token,
            channel="fake_wechat",
            provider_account="virtual-provider",
            external_subject="virtual-subject",
            code=created.code,
            now=NOW + timedelta(minutes=10),
        )
    assert error_code(caught) == "binding_code_expired"

    fresh = harness.service.create_binding_code(principal, channel="fake_wechat", now=NOW)
    binding = harness.service.consume_binding_code(
        adapter_token=harness.secrets.adapter_token,
        channel="fake_wechat",
        provider_account="virtual-provider",
        external_subject="virtual-subject",
        code=fresh.code,
        now=NOW + timedelta(seconds=1),
    )
    assert harness.service.list_bindings(harness.user_id) == [binding]
    with harness.sessions() as session:
        row = session.get(ChannelIdentityBinding, binding.binding_id)
        assert row is not None
        persisted = f"{row.provider_account_digest} {row.external_subject_digest}"
        assert "virtual-provider" not in persisted and "virtual-subject" not in persisted


def test_binding_concurrent_consume_conflict_and_revoked_identity_can_rebind(harness: Harness) -> None:
    principal = harness.service.authenticate_access(harness.login().access_token, now=NOW)
    created = harness.service.create_binding_code(principal, channel="fake_wechat", now=NOW)

    def consume():
        try:
            return harness.service.consume_binding_code(
                adapter_token=harness.secrets.adapter_token,
                channel="fake_wechat",
                provider_account="provider-a",
                external_subject="subject-a",
                code=created.code,
                now=NOW + timedelta(seconds=1),
            )
        except AuthError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: consume(), range(2)))
    winners = [value for value in outcomes if not isinstance(value, str)]
    assert len(winners) == 1
    assert [value for value in outcomes if isinstance(value, str)] == ["binding_code_consumed"]

    other_user = uuid.uuid4()
    with harness.sessions() as session, session.begin():
        session.add(AppUser(id=other_user, handle="other_owner", status="active", bootstrap_marker=None, created_at=NOW))
    other_principal = AuthenticatedSession(other_user, uuid.uuid4(), uuid.uuid4(), NOW)
    conflict_code = harness.service.create_binding_code(other_principal, channel="fake_wechat", now=NOW)
    with pytest.raises(AuthError) as caught:
        harness.service.consume_binding_code(
            adapter_token=harness.secrets.adapter_token,
            channel="fake_wechat",
            provider_account="provider-b",
            external_subject="subject-a",
            code=conflict_code.code,
            now=NOW + timedelta(seconds=2),
        )
    assert error_code(caught) == "channel_identity_conflict"

    harness.service.revoke_binding(harness.user_id, winners[0].binding_id, now=NOW + timedelta(seconds=3))
    rebound = harness.service.consume_binding_code(
        adapter_token=harness.secrets.adapter_token,
        channel="fake_wechat",
        provider_account="provider-b",
        external_subject="subject-a",
        code=conflict_code.code,
        now=NOW + timedelta(seconds=4),
    )
    assert harness.service.list_bindings(other_user) == [rebound]
