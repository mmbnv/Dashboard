"""Application facade: backup, restore, export and the dashboard aggregate.

These cover the paths where bugs were actually found during development, so a
regression is caught immediately.
"""

import json

import pytest

from glassy_app.app import Application
from glassy_app.core.errors import ValidationError
from glassy_app.core.models import EXPENSE, INCOME


def test_data_dir_is_respected(data_dir):
    app = Application(data_dir=data_dir)
    assert app.database_path.parent == data_dir
    assert app.database_path.exists()
    app.close()


def test_backup_then_restore_reverts_changes(app):
    account = app.wallet.list_accounts(with_balances=False)[0]["id"]
    app.wallet.add_transaction(account, EXPENSE, "100", "2026-05-01")
    backup = app.backup()
    assert backup.exists()

    app.wallet.add_transaction(account, EXPENSE, "999", "2026-05-02")
    assert app.counts()["transactions"] == 2

    app.restore(backup)
    # The write-ahead log must not replay over the restored file.
    assert app.counts()["transactions"] == 1
    assert app.wallet.list_accounts()[0]["balance"] == -10000


def test_services_work_after_restore(app):
    account = app.wallet.list_accounts(with_balances=False)[0]["id"]
    app.wallet.add_transaction(account, EXPENSE, "50", "2026-05-01")
    backup = app.backup()
    app.restore(backup)
    # Every service must have been rewired onto the new connection.
    assert app.wallet.list_transactions()
    assert app.tasks.stats()["total"] >= 1
    assert app.dashboard.overview()["net_worth"] == -5000
    assert app.settings.get("app.seeded") is True


def test_restore_missing_file_is_reported(app, tmp_path):
    with pytest.raises(ValidationError):
        app.restore(tmp_path / "nope.db")


def test_backups_are_listed_newest_first(app):
    first = app.backup()
    second = app.backup()
    listed = app.list_backups()
    assert second in listed and first in listed
    assert listed[0].stat().st_mtime >= listed[-1].stat().st_mtime


def test_transactions_csv_export(app, tmp_path):
    account = app.wallet.list_accounts(with_balances=False)[0]["id"]
    app.wallet.add_transaction(account, INCOME, "1500.50", "2026-05-01", payee="Boss")
    target = tmp_path / "out.csv"
    count = app.export_transactions_csv(target)
    assert count == 1
    text = target.read_text(encoding="utf-8-sig")
    lines = text.strip().splitlines()
    assert lines[0].startswith("date,kind,amount,account,category,payee,note")
    assert "1500.50" in lines[1]
    assert "Boss" in lines[1]


def test_full_json_export_contains_every_table(app, tmp_path):
    target = tmp_path / "all.json"
    app.export_all_json(target)
    payload = json.loads(target.read_text(encoding="utf-8"))
    for table in (
        "accounts", "categories", "transactions", "budgets", "courses",
        "study_sessions", "registries", "registry_fields", "registry_records",
        "workbook_entries", "tasks",
    ):
        assert table in payload, table
    assert payload["accounts"]


def test_all_tables_csv_export(app, tmp_path):
    written = app.export_all_csv(tmp_path / "csvs")
    names = {path.name for path in written}
    assert "transactions.csv" in names
    assert "tasks.csv" in names
    assert (tmp_path / "csvs" / "accounts.csv").exists()


def test_wipe_clears_everything_but_keeps_working(app):
    account = app.wallet.list_accounts(with_balances=False)[0]["id"]
    app.wallet.add_transaction(account, EXPENSE, "10", "2026-05-01")
    app.wipe()
    counts = app.counts()
    assert all(value == 0 for value in counts.values())
    # The app must still be usable: create a fresh account and post to it.
    new_id = app.wallet.create_account(name="Fresh")
    app.wallet.add_transaction(new_id, EXPENSE, "5", "2026-05-01")
    assert app.wallet.list_accounts()[0]["balance"] == -500


def test_seeding_skipped_for_non_empty_database(data_dir):
    first = Application(data_dir=data_dir)
    first.wallet.create_category(name="Custom", kind=EXPENSE)
    first.close()
    second = Application(data_dir=data_dir)
    names = [c["name"] for c in second.wallet.list_categories()]
    assert "Custom" in names
    second.close()


def test_settings_persist_across_restart(data_dir):
    first = Application(data_dir=data_dir)
    first.theme = "light"
    first.currency = "USD"
    first.close()
    second = Application(data_dir=data_dir)
    assert second.theme == "light"
    assert second.currency == "USD"
    second.close()


def test_dashboard_overview_shape(app):
    data = app.dashboard.overview()
    for key in (
        "net_worth", "accounts", "month", "all_time", "tasks", "learning",
        "registries", "workbook", "recent_transactions",
        "expense_by_category", "cashflow",
    ):
        assert key in data, key
    assert set(data["month"]) == {"income", "expense", "net"}


def test_dashboard_reflects_new_data(app):
    account = app.wallet.list_accounts(with_balances=False)[0]["id"]
    groceries = [
        c for c in app.wallet.list_categories(EXPENSE) if c["name"] == "Groceries"
    ][0]["id"]
    from datetime import date

    today = date.today().isoformat()
    app.wallet.add_transaction(account, EXPENSE, "250", today, groceries)
    data = app.dashboard.overview()
    assert data["month"]["expense"] == 25000
    assert data["net_worth"] == -25000
    assert data["expense_by_category"][0]["category_name"] == "Groceries"
    assert data["expense_by_category"][0]["percent"] == 100.0
    assert data["recent_transactions"][0]["amount"] == 25000


def test_dashboard_handles_empty_database(empty_app):
    data = empty_app.dashboard.overview()
    assert data["net_worth"] == 0
    assert data["month"] == {"income": 0, "expense": 0, "net": 0}
    assert data["tasks"]["total"] == 0
    assert data["tasks"]["percent"] == 0.0
    assert data["expense_by_category"] == []


def test_dashboard_cashflow_is_chronological(app):
    account = app.wallet.list_accounts(with_balances=False)[0]["id"]
    app.wallet.add_transaction(account, EXPENSE, "10", "2026-03-01")
    app.wallet.add_transaction(account, EXPENSE, "10", "2026-01-01")
    app.wallet.add_transaction(account, EXPENSE, "10", "2026-02-01")
    series = app.dashboard.overview()["cashflow"]
    assert [row["period"] for row in series] == ["2026-01", "2026-02", "2026-03"]
