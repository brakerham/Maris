"""Injected P4-A Host runtime and readiness checks."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from wife_system.host.auth.service import AuthService
from wife_system.host.cursor import CursorCodec
from wife_system.host.registry import ModuleRegistry
from wife_system.host.state import ConversationService, HostCommandService, MemoryService, ModuleSettingService


@dataclass(frozen=True)
class HostRuntime:
    sessions: sessionmaker[Session]
    auth: AuthService
    registry: ModuleRegistry
    conversations: ConversationService
    memories: MemoryService
    settings: ModuleSettingService
    commands: HostCommandService
    cursor: CursorCodec
    alembic_head: str
    owner_permissions: frozenset[str]

    def readiness(self) -> tuple[bool, str | None]:
        try:
            if not self.registry.module_ids:
                return False, "registry_unavailable"
            with self.sessions() as session:
                session.execute(text("SELECT 1"))
                revision = session.scalar(text("SELECT version_num FROM alembic_version"))
            if revision != self.alembic_head:
                return False, "migration_not_current"
            return True, None
        except Exception:
            return False, "database_unavailable"
