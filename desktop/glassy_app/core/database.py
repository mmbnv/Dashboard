"""SQLite connection handling and schema migrations.

The schema is versioned through ``PRAGMA user_version``. Each migration is a
plain list of statements applied in order, so an existing user database is
upgraded in place instead of being recreated.
"""

import os
import sqlite3
import threading
from pathlib import Path

SCHEMA_VERSION = 1

# Every table carries created_at/updated_at as ISO-8601 text. Dates that a
# user reasons about (transaction date, due date) are stored as 'YYYY-MM-DD'
# text so that SQLite string comparison is also chronological comparison.
MIGRATIONS = {
    1: [
        """
        CREATE TABLE accounts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            kind        TEXT    NOT NULL DEFAULT 'cash',
            currency    TEXT    NOT NULL DEFAULT 'RUB',
            opening     INTEGER NOT NULL DEFAULT 0,
            archived    INTEGER NOT NULL DEFAULT 0,
            note        TEXT    NOT NULL DEFAULT '',
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        )
        """,
        """
        CREATE TABLE categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            kind        TEXT    NOT NULL,          -- 'income' | 'expense'
            color       TEXT    NOT NULL DEFAULT '#7c3aed',
            parent_id   INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            archived    INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        )
        """,
        """
        CREATE TABLE transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id  INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            kind        TEXT    NOT NULL,          -- 'income' | 'expense'
            amount      INTEGER NOT NULL,          -- minor units, always positive
            occurred_on TEXT    NOT NULL,          -- YYYY-MM-DD
            payee       TEXT    NOT NULL DEFAULT '',
            note        TEXT    NOT NULL DEFAULT '',
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        )
        """,
        "CREATE INDEX idx_tx_date    ON transactions(occurred_on)",
        "CREATE INDEX idx_tx_account ON transactions(account_id)",
        "CREATE INDEX idx_tx_cat     ON transactions(category_id)",
        """
        CREATE TABLE budgets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
            period      TEXT    NOT NULL,          -- YYYY-MM
            limit_minor INTEGER NOT NULL,
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL,
            UNIQUE(category_id, period)
        )
        """,
        """
        CREATE TABLE courses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            provider    TEXT    NOT NULL DEFAULT '',
            url         TEXT    NOT NULL DEFAULT '',
            status      TEXT    NOT NULL DEFAULT 'planned',
            total_units INTEGER NOT NULL DEFAULT 0,
            done_units  INTEGER NOT NULL DEFAULT 0,
            cost        INTEGER NOT NULL DEFAULT 0,
            currency    TEXT    NOT NULL DEFAULT 'RUB',
            started_on  TEXT    NOT NULL DEFAULT '',
            finished_on TEXT    NOT NULL DEFAULT '',
            rating      INTEGER NOT NULL DEFAULT 0,
            note        TEXT    NOT NULL DEFAULT '',
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        )
        """,
        """
        CREATE TABLE study_sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id   INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            minutes     INTEGER NOT NULL DEFAULT 0,
            units_done  INTEGER NOT NULL DEFAULT 0,
            occurred_on TEXT    NOT NULL,
            note        TEXT    NOT NULL DEFAULT '',
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        )
        """,
        "CREATE INDEX idx_sessions_course ON study_sessions(course_id)",
        """
        CREATE TABLE registries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            title       TEXT    NOT NULL,
            description TEXT    NOT NULL DEFAULT '',
            icon        TEXT    NOT NULL DEFAULT 'table',
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        )
        """,
        """
        CREATE TABLE registry_fields (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            registry_id INTEGER NOT NULL REFERENCES registries(id) ON DELETE CASCADE,
            key         TEXT    NOT NULL,
            label       TEXT    NOT NULL,
            type        TEXT    NOT NULL DEFAULT 'text',
            required    INTEGER NOT NULL DEFAULT 0,
            options     TEXT    NOT NULL DEFAULT '',
            position    INTEGER NOT NULL DEFAULT 0,
            UNIQUE(registry_id, key)
        )
        """,
        """
        CREATE TABLE registry_records (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            registry_id INTEGER NOT NULL REFERENCES registries(id) ON DELETE CASCADE,
            data        TEXT    NOT NULL DEFAULT '{}',
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        )
        """,
        "CREATE INDEX idx_regrec_registry ON registry_records(registry_id)",
        """
        CREATE TABLE workbook_entries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            body        TEXT    NOT NULL DEFAULT '',
            kind        TEXT    NOT NULL DEFAULT 'note',
            tags        TEXT    NOT NULL DEFAULT '',
            pinned      INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        )
        """,
        """
        CREATE TABLE tasks (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT    NOT NULL,
            notes        TEXT    NOT NULL DEFAULT '',
            status       TEXT    NOT NULL DEFAULT 'todo',
            priority     TEXT    NOT NULL DEFAULT 'medium',
            due_on       TEXT    NOT NULL DEFAULT '',
            tags         TEXT    NOT NULL DEFAULT '',
            created_at   TEXT    NOT NULL,
            updated_at   TEXT    NOT NULL,
            completed_at TEXT
        )
        """,
        "CREATE INDEX idx_tasks_status ON tasks(status)",
        """
        CREATE TABLE settings (
            key        TEXT PRIMARY KEY,
            value      TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
    ]
}


class Database:
    """A thin, thread-safe wrapper around one SQLite connection.

    Qt runs UI on one thread and background work on others, so the connection
    is opened with ``check_same_thread=False`` and every statement is
    serialised through a re-entrant lock.
    """

    def __init__(self, path):
        self.path = str(path)
        self._lock = threading.RLock()
        self._depth = 0  # >0 while a transaction() block is active
        parent = Path(self.path).parent
        if str(parent) and not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._configure()
        self.migrate()

    def _configure(self):
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.execute("PRAGMA synchronous=NORMAL")
            self._conn.commit()

    @property
    def connection(self):
        return self._conn

    def migrate(self):
        """Bring the database up to ``SCHEMA_VERSION``."""
        with self._lock:
            cur = self._conn.cursor()
            current = cur.execute("PRAGMA user_version").fetchone()[0]
            if current > SCHEMA_VERSION:
                raise RuntimeError(
                    f"Database schema v{current} is newer than this build "
                    f"supports (v{SCHEMA_VERSION}). Update the application."
                )
            for version in range(current + 1, SCHEMA_VERSION + 1):
                for statement in MIGRATIONS[version]:
                    cur.execute(statement)
                cur.execute(f"PRAGMA user_version={version}")
            self._conn.commit()
            return current

    def execute(self, sql, params=()):
        with self._lock:
            cur = self._conn.execute(sql, params)
            # Inside a transaction() block the caller owns the commit. Committing
            # here would make the block unable to roll back.
            if self._depth == 0:
                self._conn.commit()
            return cur

    def executemany(self, sql, seq):
        with self._lock:
            cur = self._conn.executemany(sql, seq)
            if self._depth == 0:
                self._conn.commit()
            return cur

    def query(self, sql, params=()):
        with self._lock:
            return [dict(row) for row in self._conn.execute(sql, params).fetchall()]

    def query_one(self, sql, params=()):
        with self._lock:
            row = self._conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    def insert(self, sql, params=()):
        """Run an INSERT and return the new row id."""
        with self._lock:
            cur = self._conn.execute(sql, params)
            if self._depth == 0:
                self._conn.commit()
            return cur.lastrowid

    def transaction(self):
        """Context manager wrapping several statements in one transaction.

        Re-entrant: a nested ``transaction()`` joins the outer one and only the
        outermost block commits or rolls back.
        """
        return _Transaction(self)

    def close(self):
        with self._lock:
            self._conn.close()


class _Transaction:
    def __init__(self, db):
        self.db = db
        self._outermost = False

    def __enter__(self):
        self.db._lock.acquire()
        if self.db._depth == 0:
            self._outermost = True
            self.db._conn.execute("BEGIN")
        self.db._depth += 1
        return self.db

    def __exit__(self, exc_type, exc, tb):
        try:
            self.db._depth -= 1
            if self._outermost:
                if exc_type is None:
                    self.db._conn.commit()
                else:
                    self.db._conn.rollback()
        finally:
            self.db._lock.release()
        return False


def default_data_dir():
    """Return the per-user directory where the database and backups live.

    On Windows this is ``%APPDATA%\\GlassyLedger``; on Linux/macOS the XDG or
    home based equivalent. The application never writes next to its own
    executable, which keeps an installed build working for all users.
    """
    override = os.environ.get("GLASSY_LEDGER_HOME")
    if override:
        return Path(override)
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return Path(base) / "GlassyLedger"
    if os.environ.get("XDG_DATA_HOME"):
        return Path(os.environ["XDG_DATA_HOME"]) / "glassy-ledger"
    return Path(os.path.expanduser("~")) / ".local" / "share" / "glassy-ledger"


def open_default_database():
    """Open (creating if needed) the database in the user data directory."""
    return Database(default_data_dir() / "ledger.db")
