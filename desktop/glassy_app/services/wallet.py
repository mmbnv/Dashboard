"""Wallet service: accounts, categories, transactions, budgets, reports.

This is the only object the wallet UI talks to. It composes repositories,
enforces business rules and returns plain dicts ready for display.
"""

from datetime import date, timedelta

from ..core import money
from ..core.errors import ConflictError, NotFoundError
from ..core.models import (
    EXPENSE,
    INCOME,
    Account,
    Category,
    Transaction,
    validate_period,
    now_iso,
)
from ..repositories.ledger import (
    AccountRepository,
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)

DEFAULT_EXPENSE_CATEGORIES = [
    ("Groceries", "#22c55e"),
    ("Transport", "#38bdf8"),
    ("Housing", "#f97316"),
    ("Health", "#ef4444"),
    ("Entertainment", "#a855f7"),
    ("Education", "#eab308"),
    ("Other", "#64748b"),
]

DEFAULT_INCOME_CATEGORIES = [
    ("Salary", "#22c55e"),
    ("Freelance", "#38bdf8"),
    ("Gifts", "#a855f7"),
    ("Other income", "#64748b"),
]


class WalletService:
    def __init__(self, db):
        self.db = db
        self.accounts = AccountRepository(db)
        self.categories = CategoryRepository(db)
        self.transactions = TransactionRepository(db)
        self.budgets = BudgetRepository(db)

    # -- seeding --------------------------------------------------------
    def seed_defaults(self):
        """Create a starter account and category set on first run."""
        if self.accounts.count() == 0:
            self.accounts.create(Account(name="Cash", kind="cash"))
        if self.categories.count() == 0:
            for name, color in DEFAULT_EXPENSE_CATEGORIES:
                self.categories.create(
                    Category(name=name, kind=EXPENSE, color=color)
                )
            for name, color in DEFAULT_INCOME_CATEGORIES:
                self.categories.create(
                    Category(name=name, kind=INCOME, color=color)
                )

    # -- accounts -------------------------------------------------------
    def list_accounts(self, with_balances=True):
        if with_balances:
            return self.accounts.with_balances()
        return self.accounts.active()

    def get_account(self, account_id):
        row = self.accounts.get(account_id)
        if not row:
            raise NotFoundError("Account not found")
        return row

    def create_account(self, **kwargs):
        return self.accounts.create(Account(**kwargs))

    def update_account(self, account_id, **kwargs):
        account = Account(id=account_id, **kwargs)
        return self.accounts.update(account)

    def archive_account(self, account_id):
        self.db.execute(
            "UPDATE accounts SET archived=1, updated_at=? WHERE id=?",
            (now_iso(), account_id),
        )

    def delete_account(self, account_id):
        """Delete an account. Refuses when transactions would be destroyed."""
        balance_row = self.db.query_one(
            "SELECT COUNT(*) AS n FROM transactions WHERE account_id=?",
            (account_id,),
        )
        if balance_row and balance_row["n"]:
            raise ConflictError(
                f"This account has {balance_row['n']} transactions. "
                "Archive it instead, or delete the transactions first."
            )
        self.accounts.delete(account_id)

    # -- categories -----------------------------------------------------
    def list_categories(self, kind=None):
        if kind:
            return self.categories.by_kind(kind)
        return self.categories.with_usage()

    def get_category(self, category_id):
        row = self.categories.get(category_id)
        if not row:
            raise NotFoundError("Category not found")
        return row

    def create_category(self, **kwargs):
        return self.categories.create(Category(**kwargs))

    def update_category(self, category_id, **kwargs):
        return self.categories.update(Category(id=category_id, **kwargs))

    def delete_category(self, category_id):
        used = self.db.query_one(
            "SELECT COUNT(*) AS n FROM transactions WHERE category_id=?",
            (category_id,),
        )
        if used and used["n"]:
            raise ConflictError(
                f"This category is used by {used['n']} transactions. "
                "Archive it instead."
            )
        self.categories.delete(category_id)

    # -- transactions ---------------------------------------------------
    def list_transactions(self, **filters):
        return self.transactions.search(**filters)

    def get_transaction(self, tx_id):
        row = self.transactions.get(tx_id)
        if not row:
            raise NotFoundError("Transaction not found")
        return row

    def add_transaction(
        self, account_id, kind, amount, occurred_on=None, category_id=None,
        payee="", note="",
    ):
        """Add a transaction. ``amount`` may be text and is parsed exactly."""
        minor = money.to_minor(amount)
        tx = Transaction(
            account_id=account_id,
            category_id=category_id,
            kind=kind,
            amount=minor,
            occurred_on=occurred_on or date.today().isoformat(),
            payee=payee,
            note=note,
        )
        return self.transactions.create(tx)

    def update_transaction(self, tx_id, account_id, kind, amount, occurred_on,
                           category_id=None, payee="", note=""):
        tx = Transaction(
            id=tx_id,
            account_id=account_id,
            category_id=category_id,
            kind=kind,
            amount=money.to_minor(amount),
            occurred_on=occurred_on,
            payee=payee,
            note=note,
        )
        return self.transactions.update(tx)

    def delete_transaction(self, tx_id):
        self.transactions.delete(tx_id)

    # -- budgets --------------------------------------------------------
    def list_budgets(self, period):
        return self.budgets.for_period(validate_period(period))

    def set_budget(self, category_id, period, amount):
        return self.budgets.upsert(
            category_id, validate_period(period), money.to_minor(amount)
        )

    def delete_budget(self, budget_id):
        self.budgets.delete(budget_id)

    # -- reports --------------------------------------------------------
    def summary(self, date_from=None, date_to=None, account_id=None):
        return self.transactions.totals(
            date_from=date_from, date_to=date_to, account_id=account_id
        )

    def month_bounds(self, reference=None):
        """First and last day of the month containing ``reference``."""
        ref = reference or date.today()
        if isinstance(ref, str):
            ref = date.fromisoformat(ref)
        first = ref.replace(day=1)
        if first.month == 12:
            nxt = first.replace(year=first.year + 1, month=1)
        else:
            nxt = first.replace(month=first.month + 1)
        return first.isoformat(), (nxt - timedelta(days=1)).isoformat()

    def monthly_summary(self, reference=None):
        start, end = self.month_bounds(reference)
        data = self.summary(date_from=start, date_to=end)
        data["period"] = start[:7]
        data["date_from"] = start
        data["date_to"] = end
        return data

    def category_breakdown(self, kind=EXPENSE, date_from=None, date_to=None):
        rows = self.transactions.by_category(kind, date_from, date_to)
        total = money.sum_minor(r["total_minor"] for r in rows)
        for row in rows:
            row["percent"] = money.percent(row["total_minor"], total)
        return rows, total

    def monthly_series(self, months=12):
        return self.transactions.by_month(months)

    def net_worth(self):
        rows = self.accounts.with_balances()
        total = money.sum_minor(r["balance"] for r in rows)
        return total, rows

    def export_rows(self, **filters):
        """Rows shaped for CSV export, with human readable amounts."""
        rows = self.transactions.search(**filters)
        out = []
        for row in rows:
            out.append(
                {
                    "date": row["occurred_on"],
                    "kind": row["kind"],
                    "amount": money.format_amount(
                        row["amount"], with_symbol=False
                    ).replace("\u00a0", ""),
                    "account": row["account_name"] or "",
                    "category": row["category_name"] or "",
                    "payee": row["payee"],
                    "note": row["note"],
                }
            )
        return out
