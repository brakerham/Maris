from __future__ import annotations

from collections.abc import Iterator

import pytest
from wife_system.finance.db import Base, make_engine, make_session_factory
from wife_system.finance.models import *  # noqa: F403 - registers all mapped tables
from wife_system.finance.service import FinanceService, IdempotencyKeys


@pytest.fixture
def service() -> Iterator[FinanceService]:
    engine = make_engine("sqlite://", echo=False)
    Base.metadata.create_all(engine)
    yield FinanceService(make_session_factory(engine), IdempotencyKeys({1: b"virtual-test-secret"}))
    engine.dispose()
