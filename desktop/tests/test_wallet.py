"""Wallet service behaviour, exercised against a real database."""

import pytest

from glassy_app.core.errors import ConflictError, ValidationError
from glassy_app.core.models import EXPENSE, INCOME


def _account(app):
    return app.wallet.list_accounts(with_balances=False)[0]["id"]


def _category(app, name):
    for cat in app.wallet.list_categories():
        if cat["name"] == name:
            return cat["id"]
    raise AssertionError(f"category {name} missing")


def test_seeding_creates_starting_data(app):
    assert app.wallet.list_accounts(with_balances=False)
    assert len(app.wallet.list_categories()) >= 10


def test_seeding_runs_only_once(data_dir):
    from glassy_app.app import Application

    first = Application(data_dir=data_dir)
    count = len(first.wallet.list_categories())
    first.close()
    second = Application(data_dir=data_dir)
    assert len(second.wallet.list_categories()) == count
    second.close()


def test_balance_maths(app):
    account = _account(app)
    groceries = _category(app, "Продукты")
    app.wallet.add_transaction(account, EXPENSE, "100,25", "2026-05-01", groceries)
    app.wallet.add_transaction(account, EXPENSE, "0.75", "2026-05-02", groceries)
    app.wallet.add_transaction(account, INCOME, "500", "2026-05-03")

    balance = app.wallet.list_accounts()[0]["balance"]
    assert balance == 50000 - 10025 - 75  # exact, no float drift
    assert app.wallet.summary() == {
        "income": 50000, "expense": 10100, "net": 39900
    }


def test_opening_balance_is_included(app):
    app.wallet.create_account(name="Savings", opening="1000")
    account = [a for a in app.wallet.list_accounts() if a["name"] == "Savings"][0]
    assert account["balance"] == 100000


def test_transaction_requires_positive_amount(app):
    account = _account(app)
    with pytest.raises(ValidationError):
        app.wallet.add_transaction(account, EXPENSE, "0")
    with pytest.raises(ValidationError):
        app.wallet.add_transaction(account, EXPENSE, "-5")


def test_transaction_rejects_bad_date(app):
    account = _account(app)
    with pytest.raises(ValidationError):
        app.wallet.add_transaction(account, EXPENSE, "10", "31/12/2026")


def test_delete_account_with_transactions_is_blocked(app):
    account = _account(app)
    app.wallet.add_transaction(account, EXPENSE, "10", "2026-05-01")
    with pytest.raises(ConflictError):
        app.wallet.delete_account(account)


def test_delete_category_in_use_is_blocked(app):
    account = _account(app)
    groceries = _category(app, "Продукты")
    app.wallet.add_transaction(account, EXPENSE, "10", "2026-05-01", groceries)
    with pytest.raises(ConflictError):
        app.wallet.delete_category(groceries)


def test_update_transaction_changes_balance(app):
    account = _account(app)
    tx_id = app.wallet.add_transaction(account, EXPENSE, "100", "2026-05-01")
    assert app.wallet.list_accounts()[0]["balance"] == -10000
    app.wallet.update_transaction(
        tx_id, account_id=account, kind=EXPENSE, amount="250",
        occurred_on="2026-05-01",
    )
    assert app.wallet.list_accounts()[0]["balance"] == -25000


def test_filters_are_applied(app):
    account = _account(app)
    groceries = _category(app, "Продукты")
    transport = _category(app, "Транспорт")
    app.wallet.add_transaction(account, EXPENSE, "10", "2026-05-01", groceries, "Lenta")
    app.wallet.add_transaction(account, EXPENSE, "20", "2026-05-02", transport, "Metro")
    app.wallet.add_transaction(account, INCOME, "30", "2026-05-03", payee="Boss")

    assert len(app.wallet.list_transactions(text="Lenta")) == 1
    assert len(app.wallet.list_transactions(kind=INCOME)) == 1
    assert len(app.wallet.list_transactions(category_id=groceries)) == 1
    assert len(app.wallet.list_transactions(account_id=account)) == 3
    assert len(
        app.wallet.list_transactions(date_from="2026-05-02", date_to="2026-05-02")
    ) == 1
    assert len(app.wallet.list_transactions(limit=2)) == 2


def test_category_breakdown_percentages(app):
    account = _account(app)
    groceries = _category(app, "Продукты")
    transport = _category(app, "Транспорт")
    app.wallet.add_transaction(account, EXPENSE, "75", "2026-05-01", groceries)
    app.wallet.add_transaction(account, EXPENSE, "25", "2026-05-02", transport)
    rows, total = app.wallet.category_breakdown(
        EXPENSE, "2026-05-01", "2026-05-31"
    )
    assert total == 10000
    assert rows[0]["percent"] == 75.0
    assert rows[1]["percent"] == 25.0
    assert sum(r["percent"] for r in rows) == pytest.approx(100.0)


def test_budgets_track_spending(app):
    account = _account(app)
    groceries = _category(app, "Продукты")
    app.wallet.add_transaction(account, EXPENSE, "120", "2026-05-04", groceries)
    app.wallet.set_budget(groceries, "2026-05", "500")
    rows = app.wallet.list_budgets("2026-05")
    assert len(rows) == 1
    assert rows[0]["limit_minor"] == 50000
    assert rows[0]["spent_minor"] == 12000

    # setting again updates rather than duplicating
    app.wallet.set_budget(groceries, "2026-05", "600")
    rows = app.wallet.list_budgets("2026-05")
    assert len(rows) == 1 and rows[0]["limit_minor"] == 60000


def test_budget_ignores_other_months(app):
    account = _account(app)
    groceries = _category(app, "Продукты")
    app.wallet.add_transaction(account, EXPENSE, "120", "2026-06-04", groceries)
    app.wallet.set_budget(groceries, "2026-05", "500")
    assert app.wallet.list_budgets("2026-05")[0]["spent_minor"] == 0


def test_month_bounds(app):
    start, end = app.wallet.month_bounds("2026-02-15")
    assert start == "2026-02-01"
    assert end == "2026-02-28"
    start, end = app.wallet.month_bounds("2024-02-10")
    assert end == "2024-02-29"  # leap year


def test_monthly_series_is_chronological(app):
    account = _account(app)
    app.wallet.add_transaction(account, EXPENSE, "10", "2026-03-01")
    app.wallet.add_transaction(account, EXPENSE, "10", "2026-01-01")
    app.wallet.add_transaction(account, EXPENSE, "10", "2026-02-01")
    series = app.wallet.monthly_series(12)
    assert [row["period"] for row in series] == ["2026-01", "2026-02", "2026-03"]


def test_archived_account_disappears_from_lists(app):
    account = _account(app)
    app.wallet.archive_account(account)
    assert all(a["id"] != account for a in app.wallet.list_accounts())


def test_export_rows_have_expected_shape(app):
    account = _account(app)
    app.wallet.add_transaction(account, EXPENSE, "12.34", "2026-05-01", payee="X")
    rows = app.wallet.export_rows()
    assert set(rows[0]) == {
        "дата", "вид", "сумма", "счёт", "категория", "получатель", "заметка"
    }
    assert rows[0]["сумма"] == "12.34"
