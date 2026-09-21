"""P4 manifest and thin Host bindings for the existing finance tools."""

from __future__ import annotations

from typing import cast

from wife_system.agent.finance_tools import (
    FinanceToolAdapter,
    GetAccountBalanceInput,
    GetMonthlySnapshotInput,
    ListAccountsInput,
    ListCategoriesInput,
    ListTransactionsInput,
    RecordExpenseToolInput,
)
from wife_system.agent.prompts import FINANCE_SYSTEM_PROMPT_V1
from wife_system.host.contracts import (
    AgentProfile,
    MemoryGrant,
    ModuleManifest,
    ProfileLimits,
    SettingContract,
    ToolContract,
)
from wife_system.host.registry import ModuleDefinition
from wife_system.host.tools import CatalogTool
from wife_system.tools import Tool


def _tool(
    adapter: FinanceToolAdapter,
    *,
    local_name: str,
    alias: str,
    description: str,
    arguments_model: object,
    handler_name: str,
    permission: str,
    is_write: bool = False,
) -> tuple[ToolContract, CatalogTool]:
    contract = ToolContract(
        canonical_id=f"daily_finance.{local_name}@1",
        alias=alias,
        description=description,
        required_permission=permission,
        is_write=is_write,
    )
    implementation = Tool(
        name=alias,
        description=description,
        arguments_model=arguments_model,  # type: ignore[arg-type]
        handler=getattr(adapter, handler_name),
        requires_context=True,
        is_write=is_write,
        required_permission=permission,
    )
    return contract, CatalogTool("daily_finance", contract, implementation)


def daily_finance_definition(adapter: object) -> ModuleDefinition:
    """Bind existing deterministic finance handlers without copying domain logic."""

    finance_adapter = cast(FinanceToolAdapter, adapter)
    rows = (
        _tool(
            finance_adapter,
            local_name="list_accounts",
            alias="finance_list_accounts",
            description="List active finance accounts.",
            arguments_model=ListAccountsInput,
            handler_name="list_accounts",
            permission="finance:read",
        ),
        _tool(
            finance_adapter,
            local_name="list_categories",
            alias="finance_list_categories",
            description="List active finance categories.",
            arguments_model=ListCategoriesInput,
            handler_name="list_categories",
            permission="finance:read",
        ),
        _tool(
            finance_adapter,
            local_name="get_account_balance",
            alias="finance_get_account_balance",
            description="Get an account balance at a bounded time.",
            arguments_model=GetAccountBalanceInput,
            handler_name="account_balance",
            permission="finance:read",
        ),
        _tool(
            finance_adapter,
            local_name="list_transactions",
            alias="finance_list_transactions",
            description="List transactions in a bounded time range.",
            arguments_model=ListTransactionsInput,
            handler_name="list_transactions",
            permission="finance:read",
        ),
        _tool(
            finance_adapter,
            local_name="get_monthly_snapshot",
            alias="finance_get_monthly_snapshot",
            description="Get the deterministic monthly finance snapshot.",
            arguments_model=GetMonthlySnapshotInput,
            handler_name="monthly_snapshot",
            permission="finance:read",
        ),
        _tool(
            finance_adapter,
            local_name="record_expense",
            alias="finance_record_expense",
            description="Create a single expense candidate that requires confirmation.",
            arguments_model=RecordExpenseToolInput,
            handler_name="record_expense",
            permission="finance:write",
            is_write=True,
        ),
    )
    contracts = tuple(row[0] for row in rows)
    tools = tuple(row[1] for row in rows)
    profile = AgentProfile(
        profile_id="daily_finance.assistant@1",
        module_id="daily_finance",
        version="1.0.0",
        display_name="日常财务助手",
        system_prompt=FINANCE_SYSTEM_PROMPT_V1,
        tool_grants=tuple(contract.canonical_id for contract in contracts),
        memory_grants=(
            MemoryGrant(namespace="daily_finance.confirmed"),
            MemoryGrant(namespace="shared.confirmed"),
        ),
        limits=ProfileLimits(),
    )
    manifest = ModuleManifest(
        module_id="daily_finance",
        version="1.0.0",
        host_api_major=1,
        display_name="日常财务",
        enabled_by_default=True,
        profiles=(profile,),
        tools=contracts,
        permissions=frozenset({"finance:read", "finance:write"}),
        api_prefixes=("/api/v1/finance",),
        memory_namespaces=(
            "daily_finance.confirmed",
            "daily_finance.candidates",
        ),
        settings_schema_version=1,
        settings=(SettingContract(key="assistant_mode", schema_version=1),),
        published_events=(),
        subscribed_events=(),
        migration_owner="daily_finance",
    )
    return ModuleDefinition(manifest=manifest, tools=tools)
