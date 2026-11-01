"""Application container and backup helpers.

``Application`` wires the database and every service together and is the single
object passed to the UI. It also owns the settings store and the backup /
restore / CSV / JSON export routines.
"""

import csv
import json
import shutil
from datetime import datetime
from pathlib import Path

from .core.database import Database, default_data_dir
from .core.errors import ValidationError
from .repositories.library import SettingsRepository
from .services.dashboard import DashboardService
from .services.learning import LearningService
from .services.registries import RegistryService
from .services.wallet import WalletService
from .services.workspace import TaskService, WorkbookService

SETTING_THEME = "ui.theme"
SETTING_CURRENCY = "ui.currency"
SETTING_LAST_PAGE = "ui.last_page"
SETTING_SEEDED = "app.seeded"
SETTING_WINDOW = "ui.window"


class Application:
    """Owns the database and exposes one service per module."""

    def __init__(self, db=None, data_dir=None, seed=True):
        self.data_dir = Path(data_dir) if data_dir else default_data_dir()
        if db is not None:
            self.db = db
        else:
            # Honour data_dir here: callers (tests, portable mode) rely on the
            # database landing inside the directory they passed.
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.db = Database(self.data_dir / "ledger.db")
        self.settings = SettingsRepository(self.db)
        self._closed = False

        self.wallet = WalletService(self.db)
        self.learning = LearningService(self.db)
        self.registries = RegistryService(self.db)
        self.workbook = WorkbookService(self.db)
        self.tasks = TaskService(self.db)
        self.dashboard = DashboardService(self.db)

        if seed:
            self.seed_if_empty()

    # -- lifecycle ------------------------------------------------------
    def seed_if_empty(self):
        """Populate example data exactly once, on a brand new database."""
        if self.settings.get(SETTING_SEEDED):
            return False
        self.wallet.seed_defaults()
        self.learning.seed_defaults()
        self.workbook.seed_defaults()
        self.tasks.seed_defaults()
        self.settings.set(SETTING_SEEDED, True)
        return True

    def close(self):
        """Close the database. Safe to call more than once.

        ``close`` is called both by the tests and by the window's
        ``closeEvent``; without the guard the second call would try to write
        through an already closed connection.
        """
        if getattr(self, "_closed", False):
            return
        self._closed = True
        self.db.close()

    # -- settings -------------------------------------------------------
    @property
    def theme(self):
        return self.settings.get(SETTING_THEME, "dark")

    @theme.setter
    def theme(self, value):
        self.settings.set(SETTING_THEME, value)

    @property
    def currency(self):
        return self.settings.get(SETTING_CURRENCY, "RUB")

    @currency.setter
    def currency(self, value):
        self.settings.set(SETTING_CURRENCY, value)

    @property
    def last_page(self):
        return self.settings.get(SETTING_LAST_PAGE, "dashboard")

    @last_page.setter
    def last_page(self, value):
        self.settings.set(SETTING_LAST_PAGE, value)

    @property
    def window_state(self):
        """Saved geometry and maximised flag, or ``None`` on first run."""
        return self.settings.get(SETTING_WINDOW)

    @window_state.setter
    def window_state(self, value):
        self.settings.set(SETTING_WINDOW, value)

    # -- paths ----------------------------------------------------------
    @property
    def database_path(self):
        return Path(self.db.path)

    @property
    def backup_dir(self):
        path = self.data_dir / "backups"
        path.mkdir(parents=True, exist_ok=True)
        return path

    # -- backup / restore ------------------------------------------------
    def backup(self, target=None):
        """Copy the database to a timestamped file and return its path."""
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = Path(target) if target else self.backup_dir / f"ledger-{stamp}.db"
        target.parent.mkdir(parents=True, exist_ok=True)
        # Flush WAL contents into the main file first, otherwise the copy can
        # miss the most recent writes.
        self.db.execute("PRAGMA wal_checkpoint(FULL)")
        shutil.copy2(self.database_path, target)
        return target

    def list_backups(self):
        if not self.backup_dir.exists():
            return []
        files = sorted(
            self.backup_dir.glob("ledger-*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return files

    def restore(self, source):
        """Replace the live database with a backup file."""
        source = Path(source)
        if not source.exists():
            raise ValidationError(f"Резервная копия не найдена: {source}")

        # Close the connection first so the OS releases the file, then drop the
        # write-ahead log and shared-memory files. Without this the stale -wal
        # is replayed on reopen and silently undoes the restore.
        self.db.close()
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(self.database_path) + suffix)
            if sidecar.exists():
                sidecar.unlink()

        shutil.copy2(source, self.database_path)

        self.db = Database(self.database_path)
        self._rewire_services()
        return True

    def _rewire_services(self):
        self.settings = SettingsRepository(self.db)
        self.wallet = WalletService(self.db)
        self.learning = LearningService(self.db)
        self.registries = RegistryService(self.db)
        self.workbook = WorkbookService(self.db)
        self.tasks = TaskService(self.db)
        self.dashboard = DashboardService(self.db)

    # -- exports ---------------------------------------------------------
    def export_transactions_csv(self, path, **filters):
        rows = self.wallet.export_rows(**filters)
        with open(path, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["дата", "вид", "сумма", "счёт", "категория",
                            "получатель", "заметка"],
            )
            writer.writeheader()
            writer.writerows(rows)
        return len(rows)

    def export_all_json(self, path):
        payload = {
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "version": 1,
            "accounts": self.db.query("SELECT * FROM accounts"),
            "categories": self.db.query("SELECT * FROM categories"),
            "transactions": self.db.query("SELECT * FROM transactions"),
            "budgets": self.db.query("SELECT * FROM budgets"),
            "courses": self.db.query("SELECT * FROM courses"),
            "study_sessions": self.db.query("SELECT * FROM study_sessions"),
            "registries": self.db.query("SELECT * FROM registries"),
            "registry_fields": self.db.query("SELECT * FROM registry_fields"),
            "registry_records": self.db.query("SELECT * FROM registry_records"),
            "workbook_entries": self.db.query("SELECT * FROM workbook_entries"),
            "tasks": self.db.query("SELECT * FROM tasks"),
        }
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        return path

    def export_all_csv(self, directory):
        """Write one CSV per table into ``directory`` and return the file list."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        tables = [
            "accounts", "categories", "transactions", "budgets", "courses",
            "study_sessions", "registries", "registry_records",
            "workbook_entries", "tasks",
        ]
        written = []
        for table in tables:
            rows = self.db.query(f"SELECT * FROM {table}")
            path = directory / f"{table}.csv"
            with open(path, "w", newline="", encoding="utf-8-sig") as handle:
                if rows:
                    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
                else:
                    handle.write("")
            written.append(path)
        return written

    # -- maintenance ------------------------------------------------------
    def counts(self):
        """Row counts per table, used by the settings page and by tests."""
        result = {}
        for table in (
            "accounts", "categories", "transactions", "budgets", "courses",
            "study_sessions", "registries", "registry_records",
            "workbook_entries", "tasks",
        ):
            row = self.db.query_one(f"SELECT COUNT(*) AS n FROM {table}")
            result[table] = row["n"] if row else 0
        return result

    def wipe(self):
        """Delete every record but keep the schema. Used by Settings."""
        tables = [
            "transactions", "budgets", "accounts", "categories", "courses",
            "study_sessions", "registry_records", "registry_fields",
            "registries", "workbook_entries", "tasks", "settings",
        ]
        with self.db.transaction():
            for table in tables:
                self.db.execute(f"DELETE FROM {table}")
        return True
