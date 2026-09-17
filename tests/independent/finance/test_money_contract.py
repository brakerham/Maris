from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from wife_system.finance.errors import FinanceError
from wife_system.finance.money import MAX_MINOR, parse_minor, round_minor
from wife_system.finance.schemas import (
    BudgetAllocationInput,
    CreateAccount,
    CreateBudgetPlan,
    PublishBudgetVersion,
    RecordExpense,
    RecordIncome,
)

from conftest import TZ, WHEN


@pytest.mark.c3("AMT-01", "AMT-02", "AMT-05", "LED-01")
def test_decimal_strings_remain_exact_through_ledger(service, virtual) -> None:
    account = virtual.account()
    income = virtual.category("income", "虚拟收入")
    service.record_income(
        RecordIncome(**virtual.source(), account_id=account, category_id=income, amount="0.10", occurred_at=WHEN)
    )
    service.record_income(
        RecordIncome(**virtual.source(), account_id=account, category_id=income, amount="0.20", occurred_at=WHEN)
    )
    service.record_income(
        RecordIncome(**virtual.source(), account_id=account, category_id=income, amount="0.01", occurred_at=WHEN)
    )
    assert service.account_balance(account) == 31


@pytest.mark.c3("AMT-03", "LED-03", "INC-06", "BUD-04")
@pytest.mark.parametrize(
    ("value", "allow_zero", "code"),
    [
        ("0", False, "amount_out_of_range"),
        ("-0.01", False, "validation_error"),
        ("9999999999.99", False, None),
        ("10000000000.00", False, "amount_out_of_range"),
        ("0", True, None),
        ("-0.01", True, "validation_error"),
    ],
)
def test_amount_boundaries(value: str, allow_zero: bool, code: str | None) -> None:
    if code is None:
        assert 0 <= parse_minor(value, allow_zero=allow_zero) <= MAX_MINOR
        return
    with pytest.raises(FinanceError) as raised:
        parse_minor(value, allow_zero=allow_zero)
    assert raised.value.code == code


@pytest.mark.c3("AMT-04", "AMT-06", "LED-03", "INC-06", "BUD-04")
@pytest.mark.parametrize(
    ("value", "code"),
    [
        ("1.001", "invalid_amount_precision"),
        ("NaN", "validation_error"),
        ("Infinity", "validation_error"),
        ("-Infinity", "validation_error"),
        ("1e2", "validation_error"),
        (" 1.00", "validation_error"),
        ("1.00 ", "validation_error"),
    ],
)
def test_invalid_fact_amounts_are_rejected_without_rounding(value: str, code: str) -> None:
    with pytest.raises(FinanceError) as raised:
        parse_minor(value)
    assert raised.value.code == code


@pytest.mark.c3("AMT-06")
@pytest.mark.parametrize("value", [0.1, 1, Decimal("1.00")])
def test_non_string_amount_types_are_rejected_at_command_boundary(value: object) -> None:
    with pytest.raises(ValidationError):
        RecordExpense(
            source_system="p1-c4",
            source_event_id="virtual-float",
            account_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            amount=value,  # type: ignore[arg-type]
            occurred_at=WHEN,
        )


@pytest.mark.c3("AMT-04", "AMT-05")
def test_prediction_rounding_is_half_up_and_bounded() -> None:
    assert round_minor(Decimal("1.004")) == 100
    assert round_minor(Decimal("1.005")) == 101
    assert round_minor(Decimal("-1.005")) == -101
    with pytest.raises(FinanceError, match="amount out of range"):
        round_minor(Decimal("10000000000.00"))


@pytest.mark.c3("AMT-07", "TRF-05")
def test_currency_defaults_to_cny_and_non_cny_is_rejected(service) -> None:
    created = service.create_account(
        CreateAccount(source_system="p1-c4", source_event_id="currency-default", name="虚拟人民币账户")
    )
    assert service.list_accounts()[0].id == created.result_id
    assert service.list_accounts()[0].currency == "CNY"

    for currency in ("USD", "cny"):
        with pytest.raises(FinanceError) as raised:
            service.create_account(
                CreateAccount(
                    source_system="p1-c4",
                    source_event_id=f"currency-{currency}",
                    name="虚拟外币账户",
                    currency=currency,
                )
            )
        assert raised.value.code == "unsupported_currency"


@pytest.mark.c3("BUD-01", "BUD-04")
def test_budget_allocation_accepts_zero_but_rejects_negative(service, virtual) -> None:
    category = virtual.category("expense", "虚拟零额度分类")
    plan = service.create_budget_plan(CreateBudgetPlan(**virtual.source(), name="虚拟预算"))
    result = service.publish_budget_version(
        PublishBudgetVersion(
            **virtual.source(),
            plan_id=plan.result_id,
            expected_version=1,
            period="2026-09",
            allocations=[BudgetAllocationInput(category_id=category, limit="0")],
            published_at=WHEN,
        )
    )
    assert service.list_budget_versions(plan.result_id)[0].id == result.result_id

    with pytest.raises(FinanceError) as raised:
        service.publish_budget_version(
            PublishBudgetVersion(
                **virtual.source(),
                plan_id=plan.result_id,
                expected_version=2,
                period="2026-10",
                allocations=[BudgetAllocationInput(category_id=category, limit="-0.01")],
                published_at=WHEN.replace(month=10),
            )
        )
    assert raised.value.code == "validation_error"
