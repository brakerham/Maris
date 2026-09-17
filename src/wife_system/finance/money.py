from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .errors import FinanceError

MAX_MINOR = 999_999_999_999
_MONEY_RE = re.compile(r"^[+]?[0-9]+(?:\.[0-9]+)?$")


def require_cny(currency: str | None) -> str:
    normalized = currency or "CNY"
    if normalized != "CNY":
        raise FinanceError("unsupported_currency")
    return normalized


def parse_minor(value: str, *, allow_zero: bool = False) -> int:
    if not isinstance(value, str) or not _MONEY_RE.fullmatch(value):
        raise FinanceError("validation_error", "amount must be a decimal string")
    fraction = value.partition(".")[2]
    if len(fraction) > 2:
        raise FinanceError("invalid_amount_precision")
    try:
        decimal = Decimal(value)
    except InvalidOperation as exc:
        raise FinanceError("validation_error") from exc
    if not decimal.is_finite():
        raise FinanceError("validation_error")
    minor = int(decimal * 100)
    minimum = 0 if allow_zero else 1
    if minor < minimum or minor > MAX_MINOR:
        raise FinanceError("amount_out_of_range")
    return minor


def round_minor(value: Decimal) -> int:
    if not value.is_finite():
        raise FinanceError("validation_error")
    minor = int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if abs(minor) > MAX_MINOR:
        raise FinanceError("amount_out_of_range")
    return minor


def ensure_aggregate(value: int) -> int:
    if abs(value) > MAX_MINOR:
        raise FinanceError("amount_out_of_range")
    return value
