"""Repositories for the wallet module: accounts, categories, transactions, budgets."""

from .base import BaseRepository


class AccountRepository(BaseRepository):
    table = "accounts"
    columns = (
        "name", "kind", "currency", "opening", "archived", "note",
        "created_at", "updated_at",
    )

    def create(self, account):
        account.validate()
        return self._insert(
            {
                "name": account.name,
                "kind": account.kind,
                "currency": account.currency,
                "opening": account.opening,
                "archived": int(bool(account.archived)),
                "note": account.note,
            }
        )

    def update(self, account):
        account.validate()
        return self._update(
            account.id,
            {
                "name": account.name,
                "kind": account.kind,
                "currency": account.currency,
                "opening": account.opening,
                "archived": int(bool(account.archived)),
                "note": account.note,
            },
        )

    def active(self):
        return self.db.query(
            "SELECT * FROM accounts WHERE archived=0 ORDER BY name COLLATE NOCASE"
        )

    def with_balances(self):
        """Return every active account with its computed balance.

        Balance = opening + income - expense. The computation happens in SQL
        with integer arithmetic so the numbers match the transaction list
        exactly.
        """
        return self.db.query(
            """
            SELECT a.*,
                   a.opening
                   + COALESCE(SUM(CASE WHEN t.kind='income'  THEN  t.amount END), 0)
                   - COALESCE(SUM(CASE WHEN t.kind='expense' THEN  t.amount END), 0)
                   AS balance,
                   COUNT(t.id) AS tx_count
            FROM accounts a
            LEFT JOIN transactions t ON t.account_id = a.id
            WHERE a.archived = 0
            GROUP BY a.id
            ORDER BY a.name COLLATE NOCASE
            """
        )

    def balance(self, account_id):
        row = self.db.query_one(
            """
            SELECT a.opening
                   + COALESCE(SUM(CASE WHEN t.kind='income'  THEN  t.amount END), 0)
                   - COALESCE(SUM(CASE WHEN t.kind='expense' THEN  t.amount END), 0)
                   AS balance
            FROM accounts a
            LEFT JOIN transactions t ON t.account_id = a.id
            WHERE a.id = ?
            GROUP BY a.id
            """,
            (account_id,),
        )
        return row["balance"] if row else 0


class CategoryRepository(BaseRepository):
    table = "categories"
    columns = (
        "name", "kind", "color", "parent_id", "archived",
        "created_at", "updated_at",
    )

    def create(self, category):
        category.validate()
        return self._insert(
            {
                "name": category.name,
                "kind": category.kind,
                "color": category.color,
                "parent_id": category.parent_id,
                "archived": int(bool(category.archived)),
            }
        )

    def update(self, category):
        category.validate()
        return self._update(
            category.id,
            {
                "name": category.name,
                "kind": category.kind,
                "color": category.color,
                "parent_id": category.parent_id,
                "archived": int(bool(category.archived)),
            },
        )

    def by_kind(self, kind):
        return self.db.query(
            "SELECT * FROM categories WHERE kind=? AND archived=0 "
            "ORDER BY name COLLATE NOCASE",
            (kind,),
        )

    def with_usage(self):
        """Categories plus how many transactions reference each one."""
        return self.db.query(
            """
            SELECT c.*, COUNT(t.id) AS tx_count,
                   COALESCE(SUM(t.amount), 0) AS total_minor
            FROM categories c
            LEFT JOIN transactions t ON t.category_id = c.id
            WHERE c.archived = 0
            GROUP BY c.id
            ORDER BY c.kind, c.name COLLATE NOCASE
            """
        )


class TransactionRepository(BaseRepository):
    table = "transactions"
    columns = (
        "account_id", "category_id", "kind", "amount", "occurred_on",
        "payee", "note", "created_at", "updated_at",
    )

    def create(self, tx):
        tx.validate()
        return self._insert(self._payload(tx))

    def update(self, tx):
        tx.validate()
        return self._update(tx.id, self._payload(tx))

    @staticmethod
    def _payload(tx):
        return {
            "account_id": tx.account_id,
            "category_id": tx.category_id,
            "kind": tx.kind,
            "amount": tx.amount,
            "occurred_on": tx.occurred_on,
            "payee": tx.payee,
            "note": tx.note,
        }

    def search(
        self,
        text=None,
        kind=None,
        account_id=None,
        category_id=None,
        date_from=None,
        date_to=None,
        limit=None,
        offset=0,
    ):
        """Filtered, joined listing used by the wallet table view."""
        where = ["1=1"]
        params = []
        if text:
            where.append(
                "(t.payee LIKE ? OR t.note LIKE ? OR c.name LIKE ?)"
            )
            like = f"%{text}%"
            params += [like, like, like]
        if kind:
            where.append("t.kind = ?")
            params.append(kind)
        if account_id:
            where.append("t.account_id = ?")
            params.append(account_id)
        if category_id:
            where.append("t.category_id = ?")
            params.append(category_id)
        if date_from:
            where.append("t.occurred_on >= ?")
            params.append(date_from)
        if date_to:
            where.append("t.occurred_on <= ?")
            params.append(date_to)

        sql = f"""
            SELECT t.*, a.name AS account_name, c.name AS category_name,
                   c.color AS category_color
            FROM transactions t
            LEFT JOIN accounts a   ON a.id = t.account_id
            LEFT JOIN categories c ON c.id = t.category_id
            WHERE {' AND '.join(where)}
            ORDER BY t.occurred_on DESC, t.id DESC
        """
        if limit:
            sql += " LIMIT ? OFFSET ?"
            params += [limit, offset]
        return self.db.query(sql, params)

    def totals(self, date_from=None, date_to=None, account_id=None):
        """Return income, expense and net for the given window."""
        where = ["1=1"]
        params = []
        if date_from:
            where.append("occurred_on >= ?")
            params.append(date_from)
        if date_to:
            where.append("occurred_on <= ?")
            params.append(date_to)
        if account_id:
            where.append("account_id = ?")
            params.append(account_id)
        row = self.db.query_one(
            f"""
            SELECT
              COALESCE(SUM(CASE WHEN kind='income'  THEN amount END), 0) AS income,
              COALESCE(SUM(CASE WHEN kind='expense' THEN amount END), 0) AS expense
            FROM transactions
            WHERE {' AND '.join(where)}
            """,
            params,
        ) or {"income": 0, "expense": 0}
        row["net"] = row["income"] - row["expense"]
        return row

    def by_month(self, months=12):
        """Income/expense grouped by month, oldest first."""
        return self.db.query(
            """
            SELECT substr(occurred_on, 1, 7) AS period,
                   COALESCE(SUM(CASE WHEN kind='income'  THEN amount END), 0) AS income,
                   COALESCE(SUM(CASE WHEN kind='expense' THEN amount END), 0) AS expense
            FROM transactions
            GROUP BY period
            ORDER BY period DESC
            LIMIT ?
            """,
            (months,),
        )[::-1]

    def by_category(self, kind="expense", date_from=None, date_to=None):
        where = ["t.kind = ?", "t.category_id IS NOT NULL"]
        params = [kind]
        if date_from:
            where.append("t.occurred_on >= ?")
            params.append(date_from)
        if date_to:
            where.append("t.occurred_on <= ?")
            params.append(date_to)
        return self.db.query(
            f"""
            SELECT c.name AS category_name, c.color AS category_color,
                   COALESCE(SUM(t.amount), 0) AS total_minor,
                   COUNT(t.id) AS tx_count
            FROM transactions t
            JOIN categories c ON c.id = t.category_id
            WHERE {' AND '.join(where)}
            GROUP BY t.category_id
            ORDER BY total_minor DESC
            """,
            params,
        )

    def daily_series(self, date_from, date_to):
        return self.db.query(
            """
            SELECT occurred_on,
                   COALESCE(SUM(CASE WHEN kind='income'  THEN amount END), 0) AS income,
                   COALESCE(SUM(CASE WHEN kind='expense' THEN amount END), 0) AS expense
            FROM transactions
            WHERE occurred_on BETWEEN ? AND ?
            GROUP BY occurred_on
            ORDER BY occurred_on
            """,
            (date_from, date_to),
        )


class BudgetRepository(BaseRepository):
    table = "budgets"
    columns = ("category_id", "period", "limit_minor", "created_at", "updated_at")

    def create(self, budget):
        budget.validate()
        return self._insert(
            {
                "category_id": budget.category_id,
                "period": budget.period,
                "limit_minor": budget.limit_minor,
            }
        )

    def update(self, budget):
        budget.validate()
        return self._update(
            budget.id,
            {
                "category_id": budget.category_id,
                "period": budget.period,
                "limit_minor": budget.limit_minor,
            },
        )

    def upsert(self, category_id, period, limit_minor):
        existing = self.db.query_one(
            "SELECT * FROM budgets WHERE category_id=? AND period=?",
            (category_id, period),
        )
        if existing:
            self.db.execute(
                "UPDATE budgets SET limit_minor=?, updated_at=datetime('now') "
                "WHERE id=?",
                (limit_minor, existing["id"]),
            )
            return existing["id"]
        from ..core.models import Budget

        return self.create(
            Budget(category_id=category_id, period=period, limit_minor=limit_minor)
        )

    def for_period(self, period):
        """Budgets for a month with actual spend and remaining headroom."""
        return self.db.query(
            """
            SELECT b.*, c.name AS category_name, c.color AS category_color,
                   COALESCE((
                       SELECT SUM(t.amount) FROM transactions t
                       WHERE t.category_id = b.category_id
                         AND t.kind = 'expense'
                         AND substr(t.occurred_on, 1, 7) = b.period
                   ), 0) AS spent_minor
            FROM budgets b
            JOIN categories c ON c.id = b.category_id
            WHERE b.period = ?
            ORDER BY c.name COLLATE NOCASE
            """,
            (period,),
        )
