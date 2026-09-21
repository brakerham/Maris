from __future__ import annotations

import base64
import hashlib
import hmac
import ipaddress
import re
import secrets
import threading
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from .errors import AuthError
from .models import (
    AppUser,
    ChannelBindingAudit,
    ChannelBindingCode,
    ChannelIdentityBinding,
    DeviceSession,
    PasswordCredential,
    SessionRefreshToken,
)
from wife_system.finance.models import BOOTSTRAP_USER_ID


ACCESS_TTL = timedelta(minutes=15)
SESSION_TTL = timedelta(days=30)
BINDING_CODE_TTL = timedelta(minutes=10)
LOGIN_WINDOW = timedelta(minutes=5)
LOGIN_LOCKOUT = timedelta(minutes=15)
MAX_ACTIVE_SESSIONS = 10
MAX_BINDING_ATTEMPTS = 5
BINDING_HMAC_DOMAIN = b"wife.channel-binding.v1"
_HANDLE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,31}$")
_BINDING_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _token(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


@dataclass(frozen=True)
class AuthSecrets:
    bootstrap_token: bytes = field(repr=False)
    binding_hmac_key: bytes = field(repr=False)
    adapter_token: bytes = field(repr=False)

    def __post_init__(self) -> None:
        for value in (self.bootstrap_token, self.binding_hmac_key, self.adapter_token):
            if len(value) < 32:
                raise ValueError("auth secrets must contain at least 32 bytes")


@dataclass(frozen=True)
class SessionTokens:
    session_id: uuid.UUID
    device_id: uuid.UUID
    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)
    access_expires_at: datetime
    refresh_expires_at: datetime


@dataclass(frozen=True)
class AuthenticatedSession:
    user_id: uuid.UUID
    session_id: uuid.UUID
    device_id: uuid.UUID
    authenticated_at: datetime


@dataclass(frozen=True)
class DeviceSessionView:
    session_id: uuid.UUID
    device_id: uuid.UUID
    device_name: str
    platform: str
    created_at: datetime
    expires_at: datetime
    current: bool


@dataclass(frozen=True)
class BindingCodeResult:
    code_id: uuid.UUID
    code: str = field(repr=False)
    expires_at: datetime


@dataclass(frozen=True)
class BindingView:
    binding_id: uuid.UUID
    channel: str
    created_at: datetime


class _LoginLimiter:
    def __init__(self) -> None:
        self._failures: dict[tuple[str, str], deque[datetime]] = defaultdict(deque)
        self._blocked_until: dict[tuple[str, str], datetime] = {}
        self._lock = threading.Lock()

    def check(self, key: tuple[str, str], now: datetime) -> None:
        with self._lock:
            until = self._blocked_until.get(key)
            if until is not None and now < until:
                seconds = max(1, int((until - now).total_seconds()))
                raise AuthError("login_rate_limited", retry_after=seconds)
            if until is not None:
                self._blocked_until.pop(key, None)

    def fail(self, key: tuple[str, str], now: datetime) -> None:
        with self._lock:
            failures = self._failures[key]
            cutoff = now - LOGIN_WINDOW
            while failures and failures[0] <= cutoff:
                failures.popleft()
            failures.append(now)
            if len(failures) >= 5:
                until = now + LOGIN_LOCKOUT
                self._blocked_until[key] = until
                failures.clear()
                raise AuthError("login_rate_limited", retry_after=int(LOGIN_LOCKOUT.total_seconds()))

    def success(self, key: tuple[str, str]) -> None:
        with self._lock:
            self._failures.pop(key, None)
            self._blocked_until.pop(key, None)


class AuthService:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        secrets_config: AuthSecrets,
        *,
        random_bytes: Callable[[int], bytes] = secrets.token_bytes,
    ) -> None:
        self._sessions = sessions
        self._binding_hmac_key = secrets_config.binding_hmac_key
        self._random_bytes = random_bytes
        self._bootstrap_digest = hashlib.sha256(secrets_config.bootstrap_token).digest()
        self._adapter_digest = hashlib.sha256(secrets_config.adapter_token).digest()
        self._passwords = PasswordHash(
            [Argon2Hasher(time_cost=3, memory_cost=65536, parallelism=1, salt_len=16, hash_len=32)]
        )
        self._dummy_hash = self._passwords.hash(_token(random_bytes(32)))
        self._limiter = _LoginLimiter()

    @staticmethod
    def normalize_handle(handle: str) -> str:
        normalized = handle.strip().lower()
        if not _HANDLE_PATTERN.fullmatch(normalized):
            raise AuthError("invalid_handle")
        return normalized

    @staticmethod
    def validate_password(password: str) -> None:
        if not 12 <= len(password) <= 128:
            raise AuthError("invalid_password")
        if any(ord(char) == 0 or ord(char) < 32 or 127 <= ord(char) <= 159 or 0xD800 <= ord(char) <= 0xDFFF for char in password):
            raise AuthError("invalid_password")

    @staticmethod
    def validate_device(device_name: str, platform: str) -> None:
        if not 1 <= len(device_name) <= 80 or platform not in {"windows_desktop", "api_test"}:
            raise AuthError("invalid_device")

    def ensure_pending_owner(self, *, now: datetime) -> uuid.UUID:
        """Create the migration-equivalent singleton for isolated component tests."""
        now = _utc(now)
        with self._sessions() as session, session.begin():
            existing = session.scalar(select(AppUser).where(AppUser.bootstrap_marker == "bootstrap-owner"))
            if existing is not None:
                return existing.id
            owner = AppUser(
                id=BOOTSTRAP_USER_ID,
                status="pending_setup",
                bootstrap_marker="bootstrap-owner",
                created_at=now,
            )
            session.add(owner)
            session.flush()
            return owner.id

    def bootstrap_status(self) -> bool:
        with self._sessions() as session:
            owner = session.scalar(select(AppUser).where(AppUser.bootstrap_marker == "bootstrap-owner"))
            if owner is None:
                return False
            credential = session.scalar(select(PasswordCredential.id).where(PasswordCredential.user_id == owner.id))
            return owner.status == "pending_setup" and credential is None

    def initialize(
        self,
        *,
        handle: str,
        password: str,
        bootstrap_token: bytes,
        client_host: str,
        now: datetime,
    ) -> uuid.UUID:
        now = _utc(now)
        try:
            is_loopback = ipaddress.ip_address(client_host).is_loopback
        except ValueError:
            is_loopback = False
        supplied = hashlib.sha256(bootstrap_token).digest()
        if not is_loopback or not hmac.compare_digest(supplied, self._bootstrap_digest):
            raise AuthError("bootstrap_unauthorized")
        normalized = self.normalize_handle(handle)
        self.validate_password(password)
        password_hash = self._passwords.hash(password)
        try:
            with self._sessions() as session, session.begin():
                owner = session.scalar(
                    select(AppUser).where(AppUser.bootstrap_marker == "bootstrap-owner").with_for_update()
                )
                if owner is None or owner.status != "pending_setup":
                    raise AuthError("already_initialized")
                if session.scalar(select(PasswordCredential.id).where(PasswordCredential.user_id == owner.id)) is not None:
                    raise AuthError("already_initialized")
                claimed = session.execute(
                    update(AppUser)
                    .where(AppUser.id == owner.id, AppUser.status == "pending_setup")
                    .values(status="active", handle=normalized, initialized_at=now)
                )
                if claimed.rowcount != 1:
                    raise AuthError("already_initialized")
                owner.version_id += 1
                session.add(
                    PasswordCredential(
                        user_id=owner.id,
                        password_hash=password_hash,
                        algorithm="argon2id",
                        created_at=now,
                        updated_at=now,
                    )
                )
                return owner.id
        except IntegrityError as exc:
            raise AuthError("already_initialized") from exc

    def login(
        self,
        *,
        handle: str,
        password: str,
        client_fingerprint: str,
        device_name: str,
        platform: str,
        now: datetime,
    ) -> SessionTokens:
        now = _utc(now)
        normalized = handle.strip().lower()
        key = (normalized, client_fingerprint)
        self._limiter.check(key, now)
        self.validate_device(device_name, platform)
        valid = False
        credential: PasswordCredential | None = None
        user: AppUser | None = None
        with self._sessions() as session, session.begin():
            if _HANDLE_PATTERN.fullmatch(normalized):
                user = session.scalar(select(AppUser).where(AppUser.handle == normalized).with_for_update())
            if user is not None:
                credential = session.scalar(select(PasswordCredential).where(PasswordCredential.user_id == user.id))
            if user is not None and user.status == "active" and credential is not None:
                valid, updated_hash = self._passwords.verify_and_update(password, credential.password_hash)
                if valid and updated_hash is not None:
                    credential.password_hash = updated_hash
                    credential.updated_at = now
            else:
                self._passwords.verify(password, self._dummy_hash)
            if not valid or user is None:
                # The transaction has no externally visible mutation on failure.
                pass
            else:
                active_count = session.scalar(
                    select(func.count(DeviceSession.id)).where(
                        DeviceSession.user_id == user.id,
                        DeviceSession.revoked_at.is_(None),
                        DeviceSession.absolute_expires_at > now,
                    )
                )
                if int(active_count or 0) >= MAX_ACTIVE_SESSIONS:
                    raise AuthError("active_session_limit")
                result = self._issue_session(
                    session,
                    user_id=user.id,
                    device_id=uuid.uuid4(),
                    device_name=device_name,
                    platform=platform,
                    now=now,
                )
        if not valid or user is None:
            self._limiter.fail(key, now)
            raise AuthError("invalid_credentials")
        self._limiter.success(key)
        return result

    def _issue_session(
        self,
        session: Session,
        *,
        user_id: uuid.UUID,
        device_id: uuid.UUID,
        device_name: str,
        platform: str,
        now: datetime,
    ) -> SessionTokens:
        access = _token(self._random_bytes(32))
        refresh = _token(self._random_bytes(32))
        row = DeviceSession(
            user_id=user_id,
            device_id=device_id,
            device_name=device_name,
            platform=platform,
            access_digest=_digest(access),
            access_expires_at=now + ACCESS_TTL,
            absolute_expires_at=now + SESSION_TTL,
            rotation_counter=0,
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        session.flush()
        session.add(
            SessionRefreshToken(
                user_id=user_id,
                session_id=row.id,
                token_digest=_digest(refresh),
                rotation=0,
                status="active",
                created_at=now,
            )
        )
        return SessionTokens(
            session_id=row.id,
            device_id=device_id,
            access_token=access,
            refresh_token=refresh,
            access_expires_at=row.access_expires_at,
            refresh_expires_at=row.absolute_expires_at,
        )

    def authenticate_access(self, access_token: str, *, now: datetime) -> AuthenticatedSession:
        now = _utc(now)
        with self._sessions() as session:
            row = session.scalar(select(DeviceSession).where(DeviceSession.access_digest == _digest(access_token)))
            if row is None or row.revoked_at is not None:
                raise AuthError("session_revoked")
            if now >= _utc(row.access_expires_at) or now >= _utc(row.absolute_expires_at):
                raise AuthError("session_expired")
            user = session.get(AppUser, row.user_id)
            if user is None or user.status != "active":
                raise AuthError("session_revoked")
            return AuthenticatedSession(
                user_id=row.user_id,
                session_id=row.id,
                device_id=row.device_id,
                authenticated_at=_utc(row.created_at),
            )

    def refresh(self, refresh_token: str, *, now: datetime) -> SessionTokens:
        now = _utc(now)
        token_digest = _digest(refresh_token)
        error: AuthError | None = None
        result: SessionTokens | None = None
        with self._sessions() as session:
            with session.begin():
                token_row = session.scalar(
                    select(SessionRefreshToken)
                    .where(SessionRefreshToken.token_digest == token_digest)
                    .with_for_update()
                )
                if token_row is None:
                    error = AuthError("invalid_refresh_token")
                else:
                    device = session.scalar(
                        select(DeviceSession).where(DeviceSession.id == token_row.session_id).with_for_update()
                    )
                    if device is None:
                        error = AuthError("session_revoked")
                    elif token_row.status != "active":
                        self._revoke_session_rows(session, device, now)
                        error = AuthError("session_refresh_replayed")
                    elif device.revoked_at is not None:
                        error = AuthError("session_revoked")
                    elif now >= _utc(device.absolute_expires_at):
                        self._revoke_session_rows(session, device, now)
                        error = AuthError("session_expired")
                    else:
                        claimed = session.execute(
                            update(SessionRefreshToken)
                            .where(SessionRefreshToken.id == token_row.id, SessionRefreshToken.status == "active")
                            .values(status="rotated", used_at=now)
                        )
                        if claimed.rowcount != 1:
                            self._revoke_session_rows(session, device, now)
                            error = AuthError("session_refresh_replayed")
                        else:
                            access = _token(self._random_bytes(32))
                            refresh = _token(self._random_bytes(32))
                            rotation = device.rotation_counter + 1
                            device.access_digest = _digest(access)
                            device.access_expires_at = min(now + ACCESS_TTL, _utc(device.absolute_expires_at))
                            device.rotation_counter = rotation
                            device.updated_at = now
                            session.add(
                                SessionRefreshToken(
                                    user_id=device.user_id,
                                    session_id=device.id,
                                    token_digest=_digest(refresh),
                                    rotation=rotation,
                                    status="active",
                                    created_at=now,
                                )
                            )
                            result = SessionTokens(
                                session_id=device.id,
                                device_id=device.device_id,
                                access_token=access,
                                refresh_token=refresh,
                                access_expires_at=device.access_expires_at,
                                refresh_expires_at=_utc(device.absolute_expires_at),
                            )
        if error is not None:
            raise error
        assert result is not None
        return result

    @staticmethod
    def _revoke_session_rows(session: Session, row: DeviceSession, now: datetime) -> None:
        if row.revoked_at is None:
            row.revoked_at = now
            row.updated_at = now
        session.execute(
            update(SessionRefreshToken)
            .where(SessionRefreshToken.session_id == row.id, SessionRefreshToken.status != "revoked")
            .values(status="revoked", used_at=now)
        )

    def logout(self, access_token: str, *, now: datetime) -> None:
        now = _utc(now)
        with self._sessions() as session, session.begin():
            row = session.scalar(
                select(DeviceSession).where(DeviceSession.access_digest == _digest(access_token)).with_for_update()
            )
            if row is None or row.revoked_at is not None:
                raise AuthError("session_revoked")
            self._revoke_session_rows(session, row, now)

    def list_sessions(self, principal: AuthenticatedSession, *, now: datetime) -> list[DeviceSessionView]:
        now = _utc(now)
        with self._sessions() as session:
            rows = session.scalars(
                select(DeviceSession)
                .where(
                    DeviceSession.user_id == principal.user_id,
                    DeviceSession.revoked_at.is_(None),
                    DeviceSession.absolute_expires_at > now,
                )
                .order_by(DeviceSession.created_at.desc(), DeviceSession.id.asc())
            ).all()
            return [
                DeviceSessionView(
                    session_id=row.id,
                    device_id=row.device_id,
                    device_name=row.device_name,
                    platform=row.platform,
                    created_at=_utc(row.created_at),
                    expires_at=_utc(row.absolute_expires_at),
                    current=row.id == principal.session_id,
                )
                for row in rows
            ]

    def revoke_session(
        self, principal: AuthenticatedSession, session_id: uuid.UUID, *, now: datetime
    ) -> None:
        now = _utc(now)
        with self._sessions() as session, session.begin():
            row = session.scalar(
                select(DeviceSession)
                .where(DeviceSession.id == session_id, DeviceSession.user_id == principal.user_id)
                .with_for_update()
            )
            if row is None or row.revoked_at is not None:
                raise AuthError("session_not_found")
            self._revoke_session_rows(session, row, now)

    def change_password(
        self,
        access_token: str,
        *,
        old_password: str,
        new_password: str,
        now: datetime,
    ) -> SessionTokens:
        now = _utc(now)
        self.validate_password(new_password)
        new_hash = self._passwords.hash(new_password)
        with self._sessions() as session, session.begin():
            current = session.scalar(
                select(DeviceSession).where(DeviceSession.access_digest == _digest(access_token)).with_for_update()
            )
            if current is None or current.revoked_at is not None or now >= _utc(current.absolute_expires_at):
                raise AuthError("session_revoked")
            credential = session.scalar(
                select(PasswordCredential).where(PasswordCredential.user_id == current.user_id).with_for_update()
            )
            if credential is None or not self._passwords.verify(old_password, credential.password_hash):
                raise AuthError("invalid_credentials")
            credential.password_hash = new_hash
            credential.updated_at = now
            rows = session.scalars(
                select(DeviceSession).where(DeviceSession.user_id == current.user_id).with_for_update()
            ).all()
            for row in rows:
                self._revoke_session_rows(session, row, now)
            return self._issue_session(
                session,
                user_id=current.user_id,
                device_id=current.device_id,
                device_name=current.device_name,
                platform=current.platform,
                now=now,
            )

    def deactivate_account(self, user_id: uuid.UUID, *, now: datetime) -> None:
        now = _utc(now)
        with self._sessions() as session, session.begin():
            user = session.scalar(select(AppUser).where(AppUser.id == user_id).with_for_update())
            if user is None:
                raise AuthError("account_not_found")
            user.status = "deactivated"
            user.version_id += 1
            user.deactivated_at = now
            rows = session.scalars(select(DeviceSession).where(DeviceSession.user_id == user_id).with_for_update()).all()
            for row in rows:
                self._revoke_session_rows(session, row, now)

    def create_binding_code(
        self, principal: AuthenticatedSession, *, channel: str, now: datetime
    ) -> BindingCodeResult:
        now = _utc(now)
        if not channel or len(channel) > 32:
            raise AuthError("invalid_channel")
        raw = self._random_bytes(5)
        # Five bytes map exactly to eight 5-bit symbols.
        number = int.from_bytes(raw, "big")
        symbols = [_BINDING_ALPHABET[(number >> (5 * offset)) & 31] for offset in reversed(range(8))]
        compact = "".join(symbols)
        code = f"{compact[:4]}-{compact[4:]}"
        expires_at = now + BINDING_CODE_TTL
        with self._sessions() as session, session.begin():
            row = ChannelBindingCode(
                user_id=principal.user_id,
                channel=channel,
                code_digest=self._binding_digest(b"code", code),
                attempts=0,
                expires_at=expires_at,
                created_at=now,
            )
            session.add(row)
            session.flush()
            return BindingCodeResult(code_id=row.id, code=code, expires_at=expires_at)

    def _binding_digest(self, purpose: bytes, value: str) -> str:
        message = BINDING_HMAC_DOMAIN + b"\x00" + purpose + b"\x00" + value.encode("utf-8")
        return hmac.new(self._binding_hmac_key, message, hashlib.sha256).hexdigest()

    def _check_adapter(self, supplied: bytes) -> None:
        digest = hashlib.sha256(supplied).digest()
        if not hmac.compare_digest(digest, self._adapter_digest):
            raise AuthError("channel_adapter_unauthorized")

    def consume_binding_code(
        self,
        *,
        adapter_token: bytes,
        channel: str,
        provider_account: str,
        external_subject: str,
        code: str,
        now: datetime,
    ) -> BindingView:
        self._check_adapter(adapter_token)
        now = _utc(now)
        provider_digest = self._binding_digest(b"provider-account", provider_account)
        subject_digest = self._binding_digest(b"external-subject", external_subject)
        code_digest = self._binding_digest(b"code", code)
        deferred_error: AuthError | None = None
        result: BindingView | None = None
        try:
            with self._sessions() as session:
                with session.begin():
                    row = session.scalar(
                        select(ChannelBindingCode)
                        .where(ChannelBindingCode.code_digest == code_digest)
                        .with_for_update()
                    )
                    if row is None or row.channel != channel:
                        deferred_error = AuthError("binding_code_invalid")
                    elif row.consumed_at is not None:
                        deferred_error = AuthError("binding_code_consumed")
                    elif now >= _utc(row.expires_at):
                        deferred_error = AuthError("binding_code_expired")
                    elif row.attempts >= MAX_BINDING_ATTEMPTS:
                        deferred_error = AuthError("binding_code_attempts_exceeded")
                    else:
                        conflict = session.scalar(
                            select(ChannelIdentityBinding.id).where(
                                ChannelIdentityBinding.channel == channel,
                                ChannelIdentityBinding.external_subject_digest == subject_digest,
                                ChannelIdentityBinding.status == "active",
                            )
                        )
                        if conflict is not None:
                            row.attempts += 1
                            deferred_error = AuthError("channel_identity_conflict")
                        else:
                            claimed = session.execute(
                                update(ChannelBindingCode)
                                .where(
                                    ChannelBindingCode.id == row.id,
                                    ChannelBindingCode.consumed_at.is_(None),
                                    ChannelBindingCode.attempts < MAX_BINDING_ATTEMPTS,
                                    ChannelBindingCode.expires_at > now,
                                )
                                .values(consumed_at=now)
                                .execution_options(synchronize_session=False)
                            )
                            if claimed.rowcount != 1:
                                deferred_error = AuthError("binding_code_consumed")
                            else:
                                binding = ChannelIdentityBinding(
                                    user_id=row.user_id,
                                    channel=channel,
                                    provider_account_digest=provider_digest,
                                    external_subject_digest=subject_digest,
                                    status="active",
                                    version_id=1,
                                    created_at=now,
                                )
                                session.add(binding)
                                session.flush()
                                session.add(
                                    ChannelBindingAudit(
                                        user_id=row.user_id,
                                        binding_id=binding.id,
                                        action="bound",
                                        channel=channel,
                                        provider_account_digest=provider_digest,
                                        external_subject_digest=subject_digest,
                                        created_at=now,
                                    )
                                )
                                result = BindingView(binding.id, channel, now)
        except IntegrityError as exc:
            raise AuthError("channel_identity_conflict") from exc
        if deferred_error is not None:
            raise deferred_error
        assert result is not None
        return result

    def list_bindings(self, user_id: uuid.UUID) -> list[BindingView]:
        with self._sessions() as session:
            rows = session.scalars(
                select(ChannelIdentityBinding)
                .where(ChannelIdentityBinding.user_id == user_id, ChannelIdentityBinding.status == "active")
                .order_by(ChannelIdentityBinding.created_at.desc(), ChannelIdentityBinding.id.asc())
            ).all()
            return [BindingView(row.id, row.channel, _utc(row.created_at)) for row in rows]

    def revoke_binding(self, user_id: uuid.UUID, binding_id: uuid.UUID, *, now: datetime) -> None:
        now = _utc(now)
        with self._sessions() as session, session.begin():
            row = session.scalar(
                select(ChannelIdentityBinding)
                .where(
                    ChannelIdentityBinding.id == binding_id,
                    ChannelIdentityBinding.user_id == user_id,
                    ChannelIdentityBinding.status == "active",
                )
                .with_for_update()
            )
            if row is None:
                raise AuthError("binding_not_found")
            row.status = "revoked"
            row.revoked_at = now
            row.version_id += 1
            session.add(
                ChannelBindingAudit(
                    user_id=user_id,
                    binding_id=row.id,
                    action="revoked",
                    channel=row.channel,
                    provider_account_digest=row.provider_account_digest,
                    external_subject_digest=row.external_subject_digest,
                    created_at=now,
                )
            )
