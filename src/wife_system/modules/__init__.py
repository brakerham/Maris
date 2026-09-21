"""Explicit composition root for trusted builtin Host modules."""

from wife_system.host.registry import ModuleRegistry
from wife_system.modules.daily_finance import daily_finance_definition


def build_builtin_registry(finance_adapter: object) -> ModuleRegistry:
    """Build production registry without filesystem or entry-point discovery."""

    return ModuleRegistry((daily_finance_definition(finance_adapter),))


__all__ = ["build_builtin_registry", "daily_finance_definition"]
