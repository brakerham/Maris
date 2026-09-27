"""Explicit composition root for trusted builtin Host modules."""

from sqlalchemy.orm import Session, sessionmaker

from wife_system.host.registry import ModuleRegistry
from wife_system.modules.daily_finance import daily_finance_definition


def build_builtin_registry(
    finance_adapter: object,
    *,
    sessions: sessionmaker[Session] | None = None,
) -> ModuleRegistry:
    """Build production registry without filesystem or entry-point discovery."""

    return ModuleRegistry((daily_finance_definition(finance_adapter),), sessions=sessions)


__all__ = ["build_builtin_registry", "daily_finance_definition"]
