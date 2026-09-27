from __future__ import annotations

import inspect
import uuid
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from wife_system.host.contracts import (
    AgentProfile,
    ModuleManifest,
    ProfileLimits,
    ToolExecutionResult,
    canonical_parts,
)
from wife_system.host.factory import build_host_runtime
from wife_system.host.registry import ModuleRegistry, RegistryStartupError
from wife_system.host.tools import ToolNotAllowedError
from wife_system.modules.daily_finance import daily_finance_definition
from wife_system.modules import build_builtin_registry


class Adapter:
    def __getattr__(self, name):
        return lambda *_args, **_kwargs: {"name": name}


def definition():
    return daily_finance_definition(Adapter())


@pytest.mark.parametrize(
    "value",
    ["Daily_Finance.tool@1", " daily_finance.tool@1", "daily_finance.tool@01", "财务.tool@1"],
)
def test_c11_ids_are_exact_ascii_and_never_normalized(value: str) -> None:
    with pytest.raises(ValueError):
        canonical_parts(value)


def test_c11_contracts_are_strict_frozen_and_limit_profiles() -> None:
    manifest = definition().manifest
    assert ModuleManifest.model_validate(manifest.model_dump()) == manifest
    with pytest.raises(ValidationError):
        ModuleManifest.model_validate({**manifest.model_dump(), "import_path": "private.plugin"})
    for field, value in (
        ("max_model_turns", 5), ("max_tool_calls", 9), ("max_write_calls", 2),
        ("provider_timeout_seconds", 16), ("tool_timeout_seconds", 11),
    ):
        with pytest.raises(ValidationError):
            ProfileLimits.model_validate({field: value})


def test_c11_registry_is_atomic_and_builtin_composition_is_explicit() -> None:
    item = definition()
    with pytest.raises(RegistryStartupError) as duplicate:
        ModuleRegistry((item, item))
    assert duplicate.value.code == "duplicate_module"
    with pytest.raises(RegistryStartupError) as incompatible:
        ModuleRegistry((item,), host_api_major=2)
    assert incompatible.value.code == "host_api_incompatible"
    source = inspect.getsource(build_builtin_registry)
    assert "daily_finance_definition" in source
    for forbidden in ("entry_points", "pkgutil", "walk_packages", "import_module"):
        assert forbidden not in source


def test_c11_bound_registry_rechecks_permission_and_module_state() -> None:
    item = definition()
    registry = ModuleRegistry((item,))
    profile = item.manifest.profiles[0]
    principal = SimpleNamespace(
        user_id=uuid.uuid4(), permissions=frozenset({"finance:read"})
    )
    enabled = True
    bound = registry.tool_catalog.bind(profile, principal, lambda *_: enabled)
    schemas = bound.schemas()
    assert schemas and all(schema["function"]["name"] != "finance_record_expense" for schema in schemas)
    with pytest.raises(ToolNotAllowedError):
        bound.invoke("finance_record_expense", {}, None)
    principal.permissions = frozenset({"finance:read", "finance:write"})
    enabled = False
    with pytest.raises(ToolNotAllowedError):
        bound.contains("daily_finance.record_expense@1")


def test_c11_profile_ownership_and_tool_results_reject_invalid_unions() -> None:
    profile = definition().manifest.profiles[0]
    with pytest.raises(ValidationError):
        AgentProfile.model_validate({**profile.model_dump(), "module_id": "other"})
    with pytest.raises(ValidationError):
        ToolExecutionResult.model_validate({"status": "ok", "data": {}, "error": {}})


def test_c11_no_arbitrary_execution_or_mcp_surface_is_registered() -> None:
    item = definition()
    aliases = {tool.alias for tool in item.manifest.tools}
    corpus = " ".join(aliases).lower()
    for forbidden in ("sql", "python", "shell", "file", "mcp"):
        assert forbidden not in corpus
    assert set(item.manifest.api_prefixes) == {"/api/v1/finance"}
