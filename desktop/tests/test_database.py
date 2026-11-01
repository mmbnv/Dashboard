"""Schema, migrations and the concurrency guard."""

import sqlite3
import threading

import pytest

from glassy_app.core.database import MIGRATIONS, SCHEMA_VERSION, Database

EXPECTED_TABLES = {
    "accounts", "categories", "transactions", "budgets", "courses",
    "study_sessions", "registries", "registry_fields", "registry_records",
    "workbook_entries", "tasks", "settings",
}


def test_fresh_database_has_every_table_and_version(db):
    tables = {
        row["name"]
        for row in db.query("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert EXPECTED_TABLES <= tables
    assert db.query_one("PRAGMA user_version")["user_version"] == SCHEMA_VERSION


def test_foreign_keys_are_enforced(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO transactions (account_id, kind, amount, occurred_on, "
            "created_at, updated_at) VALUES (9999, 'expense', 1, '2026-01-01', "
            "'now', 'now')"
        )


def test_cascade_delete_removes_children(db):
    account_id = db.insert(
        "INSERT INTO accounts (name, kind, currency, opening, archived, note, "
        "created_at, updated_at) VALUES ('A','cash','RUB',0,0,'','n','n')"
    )
    db.insert(
        "INSERT INTO transactions (account_id, kind, amount, occurred_on, "
        "created_at, updated_at) VALUES (?, 'expense', 100, '2026-01-01', "
        "'n', 'n')",
        (account_id,),
    )
    db.execute("DELETE FROM accounts WHERE id=?", (account_id,))
    assert db.query("SELECT * FROM transactions") == []


def test_migration_is_idempotent(data_dir):
    path = data_dir / "m.db"
    first = Database(path)
    version = first.query_one("PRAGMA user_version")["user_version"]
    first.close()
    second = Database(path)
    assert second.query_one("PRAGMA user_version")["user_version"] == version
    second.close()


def test_migration_preserves_rows(data_dir):
    path = data_dir / "p.db"
    handle = Database(path)
    handle.insert(
        "INSERT INTO accounts (name, kind, currency, opening, archived, note, "
        "created_at, updated_at) VALUES ('Keep','cash','RUB',0,0,'','n','n')"
    )
    handle.close()
    again = Database(path)
    assert again.query("SELECT name FROM accounts")[0]["name"] == "Keep"
    again.close()


def test_every_migration_version_is_defined():
    for version in range(1, SCHEMA_VERSION + 1):
        assert version in MIGRATIONS
        assert MIGRATIONS[version]


def test_newer_schema_is_refused(data_dir):
    path = data_dir / "future.db"
    handle = Database(path)
    handle.execute(f"PRAGMA user_version={SCHEMA_VERSION + 5}")
    handle.close()
    with pytest.raises(RuntimeError):
        Database(path)


def test_transaction_rolls_back_on_error(db):
    db.execute(
        "INSERT INTO accounts (name, kind, currency, opening, archived, note, "
        "created_at, updated_at) VALUES ('T','cash','RUB',0,0,'','n','n')"
    )
    with pytest.raises(sqlite3.IntegrityError):
        with db.transaction():
            db.execute(
                "INSERT INTO categories (name, kind, color, archived, "
                "created_at, updated_at) VALUES ('ok','expense','#000',0,'n','n')"
            )
            # duplicate primary key forces a failure inside the transaction
            db.execute(
                "INSERT INTO categories (id, name, kind, color, archived, "
                "created_at, updated_at) "
                "VALUES (1,'dup','expense','#000',0,'n','n')"
            )
            db.execute(
                "INSERT INTO categories (id, name, kind, color, archived, "
                "created_at, updated_at) "
                "VALUES (1,'dup2','expense','#000',0,'n','n')"
            )
    assert db.query("SELECT * FROM categories") == []


def test_concurrent_writes_do_not_corrupt(db):
    """The connection is shared across threads; the lock must serialise it."""
    db.execute(
        "INSERT INTO accounts (name, kind, currency, opening, archived, note, "
        "created_at, updated_at) VALUES ('C','cash','RUB',0,0,'','n','n')"
    )
    errors = []

    def writer(index):
        try:
            for i in range(20):
                db.execute(
                    "INSERT INTO tasks (title, notes, status, priority, due_on, "
                    "tags, created_at, updated_at) "
                    "VALUES (?, '', 'todo', 'low', '', '', 'n', 'n')",
                    (f"t{index}-{i}",),
                )
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert not errors, errors
    assert db.query_one("SELECT COUNT(*) AS n FROM tasks")["n"] == 120
