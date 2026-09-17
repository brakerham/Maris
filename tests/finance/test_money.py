from decimal import Decimal

import pytest

from wife_system.finance.errors import FinanceError
from wife_system.finance.money import MAX_MINOR, parse_minor, round_minor


@pytest.mark.parametrize(("value", "expected"), [("0.01", 1), ("1", 100), ("001.20", 120), ("9999999999.99", MAX_MINOR)])
def test_parse_minor_exact(value: str, expected: int) -> None:
    assert parse_minor(value) == expected


@pytest.mark.parametrize(("value", "code"), [("1.001", "invalid_amount_precision"), ("0", "amount_out_of_range"), ("10000000000", "amount_out_of_range"), ("1e2", "validation_error"), (" 1", "validation_error")])
def test_parse_minor_rejects_invalid(value: str, code: str) -> None:
    with pytest.raises(FinanceError) as raised:
        parse_minor(value)
    assert raised.value.code == code


def test_round_half_up_for_predictions() -> None:
    assert round_minor(Decimal("1.005")) == 101
