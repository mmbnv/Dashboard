"""Settings page: appearance, data location, backup and export."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ... import APP_NAME, __version__
from ...core.errors import AppError
from ..base_page import BasePage
from ..dialogs import confirm, show_error, show_info
from ..widgets.common import Card, SectionHeader, clear_layout


class SettingsPage(BasePage):
    title = "Settings"
    subtitle = "Appearance, data and backups"

    def build(self):
        self.header = SectionHeader(self.title, self.subtitle)
        self.add(self.header)

        # -- appearance --------------------------------------------------
        appearance = Card()
        appearance.body().addWidget(_title("Appearance"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Theme"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.currentIndexChanged.connect(self._change_theme)
        row.addWidget(self.theme_combo)

        row.addWidget(QLabel("Currency"))
        self.currency_combo = QComboBox()
        for code in ("RUB", "USD", "EUR", "KZT", "UAH"):
            self.currency_combo.addItem(code, code)
        self.currency_combo.currentIndexChanged.connect(self._change_currency)
        row.addWidget(self.currency_combo)
        row.addStretch(1)
        appearance.body().addLayout(row)
        self.add(appearance)

        # -- storage ------------------------------------------------------
        storage = Card()
        storage.body().addWidget(_title("Data"))
        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        storage.body().addWidget(self.path_label)

        self.counts_label = QLabel()
        self.counts_label.setObjectName("Muted")
        self.counts_label.setWordWrap(True)
        storage.body().addWidget(self.counts_label)

        buttons = QHBoxLayout()
        backup = QPushButton("Back up now")
        backup.setObjectName("Primary")
        backup.clicked.connect(self._backup)
        restore = QPushButton("Restore from file\u2026")
        restore.clicked.connect(self._restore)
        open_folder = QPushButton("Open data folder")
        open_folder.setObjectName("Ghost")
        open_folder.clicked.connect(self._open_folder)
        buttons.addWidget(backup)
        buttons.addWidget(restore)
        buttons.addWidget(open_folder)
        buttons.addStretch(1)
        storage.body().addLayout(buttons)

        self.backups_box = QVBoxLayout()
        self.backups_box.setSpacing(4)
        storage.body().addLayout(self.backups_box)
        self.add(storage)

        # -- export --------------------------------------------------------
        export = Card()
        export.body().addWidget(_title("Export"))
        export_row = QHBoxLayout()
        csv_button = QPushButton("Export transactions (CSV)")
        csv_button.clicked.connect(self._export_csv)
        json_button = QPushButton("Export everything (JSON)")
        json_button.clicked.connect(self._export_json)
        all_csv = QPushButton("Export every table (CSV folder)")
        all_csv.clicked.connect(self._export_all_csv)
        export_row.addWidget(csv_button)
        export_row.addWidget(json_button)
        export_row.addWidget(all_csv)
        export_row.addStretch(1)
        export.body().addLayout(export_row)
        self.add(export)

        # -- danger zone -----------------------------------------------------
        danger = Card()
        danger.body().addWidget(_title("Danger zone"))
        note = QLabel(
            "Erasing removes every account, transaction, course, registry and "
            "note from this database. Take a backup first."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)
        danger.body().addWidget(note)
        wipe = QPushButton("Erase all data")
        wipe.setObjectName("Danger")
        wipe.clicked.connect(self._wipe)
        danger_row = QHBoxLayout()
        danger_row.addWidget(wipe)
        danger_row.addStretch(1)
        danger.body().addLayout(danger_row)
        self.add(danger)

        # -- about ------------------------------------------------------------
        about = Card()
        about.body().addWidget(_title("About"))
        about_label = QLabel(
            f"{APP_NAME} {__version__}\n"
            "A local desktop application for personal record keeping. "
            "All data stays on this computer in a single SQLite file."
        )
        about_label.setObjectName("Muted")
        about_label.setWordWrap(True)
        about.body().addWidget(about_label)
        self.add(about)
        self.layout.addStretch(1)

    # -- appearance -----------------------------------------------------
    def _change_theme(self):
        theme_name = self.theme_combo.currentData()
        self.app.theme = theme_name
        window = self.window()
        if hasattr(window, "apply_theme"):
            window.apply_theme(theme_name)

    def _change_currency(self):
        self.app.currency = self.currency_combo.currentData()
        show_info(
            self,
            "Currency updated. Amounts are shown in the new currency; "
            "existing values are not converted.",
        )
        window = self.window()
        if hasattr(window, "refresh_current_page"):
            window.refresh_current_page()

    # -- data -------------------------------------------------------------
    def _backup(self):
        try:
            path = self.app.backup()
        except Exception as exc:  # noqa: BLE001 - report any failure to user
            show_error(self, f"Backup failed: {exc}")
            return
        show_info(self, f"Backup written to:\n{path}")
        self.refresh()

    def _restore(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose a backup", str(self.app.backup_dir),
            "Database files (*.db);;All files (*)",
        )
        if not path:
            return
        if not confirm(
            self,
            "Replace the current database with this backup? "
            "Unsaved changes to the current data will be lost.",
        ):
            return
        try:
            self.app.restore(path)
        except AppError as exc:
            show_error(self, str(exc))
            return
        show_info(self, "Backup restored.")
        window = self.window()
        if hasattr(window, "apply_theme"):
            window.apply_theme(self.app.theme)
        self.refresh()

    def _open_folder(self):
        import subprocess
        import sys

        path = str(self.app.data_dir)
        try:
            if sys.platform.startswith("win"):
                import os

                os.startfile(path)  # noqa: S606 - opening a folder is intended
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as exc:  # noqa: BLE001
            show_error(self, f"Could not open the folder: {exc}\n\n{path}")

    # -- exports -----------------------------------------------------------
    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export transactions", "transactions.csv", "CSV (*.csv)"
        )
        if not path:
            return
        count = self.app.export_transactions_csv(path)
        show_info(self, f"Exported {count} transactions to:\n{path}")

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export everything", "glassy-ledger.json", "JSON (*.json)"
        )
        if not path:
            return
        self.app.export_all_json(path)
        show_info(self, f"Full export written to:\n{path}")

    def _export_all_csv(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Choose a folder for the CSV files"
        )
        if not directory:
            return
        files = self.app.export_all_csv(directory)
        show_info(self, f"Wrote {len(files)} files into:\n{directory}")

    def _wipe(self):
        if not confirm(
            self,
            "Erase ALL data? This cannot be undone. "
            "Type-free confirmation: press Yes to continue.",
        ):
            return
        if not confirm(self, "Really erase everything? Last chance."):
            return
        self.app.wipe()
        show_info(self, "All data erased.")
        window = self.window()
        if hasattr(window, "refresh_current_page"):
            window.refresh_current_page()
        self.refresh()

    def refresh(self):
        self.theme_combo.blockSignals(True)
        index = self.theme_combo.findData(self.app.theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        self.theme_combo.blockSignals(False)

        self.currency_combo.blockSignals(True)
        index = self.currency_combo.findData(self.app.currency)
        if index >= 0:
            self.currency_combo.setCurrentIndex(index)
        self.currency_combo.blockSignals(False)

        self.path_label.setText(f"Database: {self.app.database_path}")
        counts = self.app.counts()
        self.counts_label.setText(
            "  \u00b7  ".join(f"{name}: {value}" for name, value in counts.items())
        )

        clear_layout(self.backups_box)
        backups = self.app.list_backups()
        if not backups:
            label = QLabel("No backups yet.")
            label.setObjectName("Muted")
            self.backups_box.addWidget(label)
            return
        label = QLabel(f"Recent backups ({len(backups)}):")
        label.setObjectName("Muted")
        self.backups_box.addWidget(label)
        for path in backups[:5]:
            row = QWidget()
            line = QHBoxLayout(row)
            line.setContentsMargins(0, 0, 0, 0)
            name = QLabel(path.name)
            name.setObjectName("Muted")
            size = QLabel(f"{path.stat().st_size / 1024:.0f} KB")
            size.setObjectName("Muted")
            restore = QPushButton("Restore")
            restore.setObjectName("Ghost")
            restore.clicked.connect(
                lambda _, p=path: self._restore_specific(p)
            )
            line.addWidget(name, 1)
            line.addWidget(size)
            line.addWidget(restore)
            self.backups_box.addWidget(row)

    def _restore_specific(self, path):
        if not confirm(self, f"Restore from {path.name}?"):
            return
        try:
            self.app.restore(path)
        except AppError as exc:
            show_error(self, str(exc))
            return
        show_info(self, "Backup restored.")
        window = self.window()
        if hasattr(window, "apply_theme"):
            window.apply_theme(self.app.theme)
        self.refresh()


def _title(text):
    label = QLabel(text)
    label.setObjectName("SectionTitle")
    return label
