"""Trusted tool catalog with schema-time and execution-time authorization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol

from wife_system.host.contracts import AgentProfile, ToolContract
from wife_system.tools import Tool


class PrincipalLike(Protocol):
    user_id: Any
    permissions: frozenset[str]


class ToolNotAllowedError(PermissionError):
    code = "tool_not_allowed"

    def __init__(self) -> None:
        super().__init__("The requested tool is not allowed.")


@dataclass(frozen=True)
class CatalogTool:
    module_id: str
    contract: ToolContract
    implementation: Tool[Any]

    def __post_init__(self) -> None:
        if self.implementation.name != self.contract.alias:
            raise ValueError("tool implementation name must equal its declared alias")
        if self.implementation.is_write != self.contract.is_write:
            raise ValueError("tool implementation write flag differs from its contract")
        if self.implementation.required_permission != self.contract.required_permission:
            raise ValueError("tool implementation permission differs from its contract")


class ToolCatalog:
    """Immutable process catalog from which trusted per-profile views are bound."""

    def __init__(self, tools: tuple[CatalogTool, ...] | list[CatalogTool]) -> None:
        by_canonical: dict[str, CatalogTool] = {}
        by_alias: dict[str, CatalogTool] = {}
        for tool in tools:
            if tool.contract.canonical_id in by_canonical:
                raise ValueError("duplicate canonical tool id")
            if tool.contract.alias in by_alias:
                raise ValueError("duplicate tool alias")
            by_canonical[tool.contract.canonical_id] = tool
            by_alias[tool.contract.alias] = tool
        self._by_canonical = by_canonical
        self._by_alias = by_alias

    @property
    def canonical_ids(self) -> tuple[str, ...]:
        return tuple(self._by_canonical)

    def bind(
        self,
        profile: AgentProfile,
        principal: PrincipalLike | Callable[[], PrincipalLike],
        module_enabled: Callable[[Any, str], bool],
    ) -> "BoundToolRegistry":
        missing = set(profile.tool_grants).difference(self._by_canonical)
        if missing:
            raise ValueError("profile grants an unknown tool")
        principal_provider = principal if callable(principal) else lambda: principal
        return BoundToolRegistry(
            catalog=self,
            profile=profile,
            principal_provider=principal_provider,
            module_enabled=module_enabled,
        )


class BoundToolRegistry:
    """A profile view that rechecks all authorization at each operation."""

    def __init__(
        self,
        *,
        catalog: ToolCatalog,
        profile: AgentProfile,
        principal_provider: Callable[[], PrincipalLike],
        module_enabled: Callable[[Any, str], bool],
    ) -> None:
        self._catalog = catalog
        self.profile = profile
        self._principal_provider = principal_provider
        self._module_enabled = module_enabled

    def _resolve(self, name: str) -> CatalogTool:
        tool = self._catalog._by_alias.get(name) or self._catalog._by_canonical.get(name)
        if tool is None or tool.contract.canonical_id not in self.profile.tool_grants:
            raise ToolNotAllowedError()
        principal = self._principal_provider()
        if not self._module_enabled(principal.user_id, tool.module_id):
            raise ToolNotAllowedError()
        if tool.contract.required_permission not in principal.permissions:
            raise ToolNotAllowedError()
        return tool

    def schemas(self, context: Any = None) -> tuple[dict[str, Any], ...]:
        del context
        schemas: list[dict[str, Any]] = []
        for canonical_id in self.profile.tool_grants:
            tool = self._catalog._by_canonical[canonical_id]
            try:
                self._resolve(canonical_id)
            except ToolNotAllowedError:
                continue
            schemas.append(tool.implementation.schema())
        return tuple(schemas)

    def contains(self, name: str) -> bool:
        try:
            self._resolve(name)
        except ToolNotAllowedError:
            return False
        return True

    def invoke(self, name: str, arguments: dict[str, Any], context: Any = None) -> Any:
        tool = self._resolve(name)
        return tool.implementation.invoke(arguments, context)

    def is_write(self, name: str) -> bool:
        return self._resolve(name).contract.is_write
