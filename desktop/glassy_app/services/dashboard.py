"""Dashboard service: the aggregated view shown on the home page.

It reads from every other module and returns one dictionary, so the dashboard
page performs a single call instead of five.
"""

from datetime import date, timedelta

from ..core import money
from ..repositories.ledger import AccountRepository, TransactionRepository


class DashboardService:
    def __init__(self, db):
        self.db = db
        self.accounts = AccountRepository(db)
        self.transactions = TransactionRepository(db)

    def overview(self):
        today = date.today()
        month_start = today.replace(day=1).isoformat()
        month_end = today.isoformat()

        month = self.transactions.totals(month_start, month_end)
        all_time = self.transactions.totals()
        net_worth, account_rows = self._net_worth()

        return {
            "today": today.isoformat(),
            "net_worth": net_worth,
            "accounts": account_rows,
            "month": month,
            "all_time": all_time,
            "tasks": self._task_stats(),
            "learning": self._learning_stats(),
            "registries": self._registry_stats(),
            "workbook": self._workbook_stats(),
            "recent_transactions": self._recent_transactions(6),
            "expense_by_category": self._top_categories(month_start, month_end),
            "cashflow": self._cashflow_series(),
        }

    def _net_worth(self):
        rows = self.accounts.with_balances()
        return money.sum_minor(r["balance"] for r in rows), rows

    def _task_stats(self):
        row = self.db.query_one(
            """
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(CASE WHEN status='todo'  THEN 1 END), 0) AS todo,
                   COALESCE(SUM(CASE WHEN status='doing' THEN 1 END), 0) AS doing,
                   COALESCE(SUM(CASE WHEN status='done'  THEN 1 END), 0) AS done
            FROM tasks
            """
        ) or {"total": 0, "todo": 0, "doing": 0, "done": 0}
        overdue = self.db.query_one(
            """
            SELECT COUNT(*) AS n FROM tasks
            WHERE status != 'done' AND due_on != '' AND due_on < date('now')
            """
        )
        row["overdue"] = overdue["n"] if overdue else 0
        row["open"] = row["todo"] + row["doing"]
        row["percent"] = money.percent(row["done"], row["total"])
        return row

    def _learning_stats(self):
        row = self.db.query_one(
            """
            SELECT COUNT(*) AS courses,
                   COALESCE(SUM(CASE WHEN status='active' THEN 1 END), 0) AS active,
                   COALESCE(SUM(CASE WHEN status='done'   THEN 1 END), 0) AS finished,
                   COALESCE(SUM(cost), 0) AS spend_minor
            FROM courses
            """
        ) or {}
        minutes = self.db.query_one(
            "SELECT COALESCE(SUM(minutes), 0) AS m FROM study_sessions"
        )
        row["minutes"] = minutes["m"] if minutes else 0
        row["hours"] = round(row["minutes"] / 60.0, 1)

        week_start = (date.today() - timedelta(days=6)).isoformat()
        week = self.db.query_one(
            "SELECT COALESCE(SUM(minutes), 0) AS m FROM study_sessions "
            "WHERE occurred_on >= ?",
            (week_start,),
        )
        row["week_minutes"] = week["m"] if week else 0
        row["week_hours"] = round(row["week_minutes"] / 60.0, 1)
        return row

    def _registry_stats(self):
        row = self.db.query_one(
            """
            SELECT COUNT(*) AS tables,
                   (SELECT COUNT(*) FROM registry_records) AS records
            FROM registries
            """
        )
        return row or {"tables": 0, "records": 0}

    def _workbook_stats(self):
        row = self.db.query_one(
            "SELECT COUNT(*) AS entries FROM workbook_entries"
        )
        return row or {"entries": 0}

    def _recent_transactions(self, limit=6):
        return self.transactions.search(limit=limit)

    def _top_categories(self, date_from, date_to):
        rows = self.transactions.by_category("expense", date_from, date_to)
        total = money.sum_minor(r["total_minor"] for r in rows)
        for row in rows:
            row["percent"] = money.percent(row["total_minor"], total)
        return rows[:6]

    def _cashflow_series(self, months=6):
        return self.transactions.by_month(months)
