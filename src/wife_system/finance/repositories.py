from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Account, Category, FinancialTransaction, TransactionEntry


class FinanceRepository:
    """Persistence primitives. Transaction ownership stays with the service."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def account(self, account_id: uuid.UUID, *, for_update: bool = False) -> Account | None:
        statement = select(Account).where(Account.id == account_id)
        if for_update and self.session.bind is not None and self.session.bind.dialect.name == "postgresql":
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def category(self, category_id: uuid.UUID) -> Category | None:
        return self.session.get(Category, category_id)

    def transaction(self, transaction_id: uuid.UUID, *, for_update: bool = False) -> FinancialTransaction | None:
        statement = select(FinancialTransaction).where(FinancialTransaction.id == transaction_id)
        if for_update and self.session.bind is not None and self.session.bind.dialect.name == "postgresql":
            statement = statement.with_for_update()
        return self.session.scalar(statement)

    def transaction_entries(self, transaction_id: uuid.UUID) -> list[TransactionEntry]:
        return list(self.session.scalars(
            select(TransactionEntry)
            .where(TransactionEntry.transaction_id == transaction_id)
            .order_by(TransactionEntry.line_no)
        ).all())

    def add(self, value: object) -> None:
        self.session.add(value)

    def flush(self) -> None:
        self.session.flush()
