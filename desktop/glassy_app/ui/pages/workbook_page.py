"""Workbook page: a split view of entries and an editor."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
)

from ...core.errors import AppError
from ..base_page import BasePage
from ..dialogs import confirm, show_error, show_info
from ..widgets.common import Card, SectionHeader

KINDS = ["note", "journal", "checklist", "reference", "idea"]


class WorkbookPage(BasePage):
    title = "Workbook"
    subtitle = "Notes, journals and reference pages"

    def build(self):
        self.header = SectionHeader(self.title, self.subtitle)
        new_button = QPushButton("New entry")
        new_button.setObjectName("Primary")
        new_button.clicked.connect(self._new_entry)
        self.header.add_action(new_button)
        self.add(self.header)

        self.count_label = QLabel()
        self.count_label.setObjectName("Muted")
        self.add(self.count_label)

        splitter = QSplitter(Qt.Horizontal)

        # -- list ---------------------------------------------------------
        left = Card(padding=12)
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search\u2026")
        self.search.textChanged.connect(self._load_list)
        search_row.addWidget(self.search, 1)
        left.body().addLayout(search_row)

        self.kind_filter = QComboBox()
        self.kind_filter.addItem("All kinds", None)
        for kind in KINDS:
            self.kind_filter.addItem(kind.capitalize(), kind)
        self.kind_filter.currentIndexChanged.connect(self._load_list)
        left.body().addWidget(self.kind_filter)

        self.entry_list = QListWidget()
        self.entry_list.currentItemChanged.connect(self._on_select)
        left.body().addWidget(self.entry_list, 1)

        list_actions = QHBoxLayout()
        pin = QPushButton("Pin / unpin")
        pin.setObjectName("Ghost")
        pin.clicked.connect(self._toggle_pin)
        delete = QPushButton("Delete")
        delete.setObjectName("Danger")
        delete.clicked.connect(self._delete)
        list_actions.addWidget(pin)
        list_actions.addWidget(delete)
        left.body().addLayout(list_actions)
        splitter.addWidget(left)

        # -- editor -------------------------------------------------------
        right = Card(padding=16)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Title")
        self.title_input.setStyleSheet("font-size: 17px; font-weight: 600;")
        right.body().addWidget(self.title_input)

        meta_row = QHBoxLayout()
        self.kind_input = QComboBox()
        for kind in KINDS:
            self.kind_input.addItem(kind.capitalize(), kind)
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("tags, comma separated")
        meta_row.addWidget(QLabel("Kind"))
        meta_row.addWidget(self.kind_input)
        meta_row.addWidget(QLabel("Tags"))
        meta_row.addWidget(self.tags_input, 1)
        right.body().addLayout(meta_row)

        self.body_edit = QPlainTextEdit()
        self.body_edit.setPlaceholderText("Write here\u2026")
        right.body().addWidget(self.body_edit, 1)

        actions = QHBoxLayout()
        save = QPushButton("Save")
        save.setObjectName("Primary")
        save.clicked.connect(self._save)
        revert = QPushButton("Revert")
        revert.setObjectName("Ghost")
        revert.clicked.connect(self._on_select_current)
        actions.addWidget(save)
        actions.addWidget(revert)
        actions.addStretch(1)
        self.status = QLabel("")
        self.status.setObjectName("Muted")
        actions.addWidget(self.status)
        right.body().addLayout(actions)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([280, 700])
        self.add(splitter)

        self.current_id = None

    # -- list -------------------------------------------------------------
    def _load_list(self):
        entries = self.app.workbook.list_entries(
            text=self.search.text().strip() or None,
            kind=self.kind_filter.currentData(),
        )
        previous = self.current_id
        self.entry_list.blockSignals(True)
        self.entry_list.clear()
        for entry in entries:
            prefix = "\u2605 " if entry["pinned"] else ""
            item = QListWidgetItem(f"{prefix}{entry['title']}")
            item.setData(Qt.UserRole, entry["id"])
            self.entry_list.addItem(item)
        self.entry_list.blockSignals(False)
        self.count_label.setText(f"{len(entries)} entries")

        if previous:
            for row in range(self.entry_list.count()):
                if self.entry_list.item(row).data(Qt.UserRole) == previous:
                    self.entry_list.setCurrentRow(row)
                    break
        elif self.entry_list.count():
            self.entry_list.setCurrentRow(0)
        else:
            self._clear_editor()

    def _on_select(self, item):
        if item is None:
            return
        self.current_id = item.data(Qt.UserRole)
        entry = self.app.workbook.get_entry(self.current_id)
        self.title_input.setText(entry["title"])
        self.body_edit.setPlainText(entry["body"])
        self.tags_input.setText(entry["tags"])
        index = self.kind_input.findData(entry["kind"])
        if index >= 0:
            self.kind_input.setCurrentIndex(index)
        self.status.setText(f"Updated {entry['updated_at'][:16]}")

    def _on_select_current(self):
        if self.current_id:
            entry = self.app.workbook.get_entry(self.current_id)
            self.title_input.setText(entry["title"])
            self.body_edit.setPlainText(entry["body"])
            self.tags_input.setText(entry["tags"])
            self.status.setText("Reverted")

    def _clear_editor(self):
        self.current_id = None
        self.title_input.clear()
        self.body_edit.clear()
        self.tags_input.clear()
        self.status.clear()

    # -- actions -----------------------------------------------------------
    def _new_entry(self):
        self.entry_list.setCurrentItem(None)
        self._clear_editor()
        self.title_input.setFocus()
        self.status.setText("New entry \u2014 press Save to store it")

    def _save(self):
        title = self.title_input.text().strip()
        if not title:
            show_info(self, "Give the entry a title before saving.")
            return
        payload = dict(
            title=title,
            body=self.body_edit.toPlainText(),
            kind=self.kind_input.currentData(),
            tags=self.tags_input.text().strip(),
        )
        try:
            if self.current_id:
                existing = self.app.workbook.get_entry(self.current_id)
                self.app.workbook.update_entry(
                    self.current_id, pinned=bool(existing["pinned"]), **payload
                )
                self.status.setText("Saved")
            else:
                new_id = self.app.workbook.create_entry(**payload)
                self.current_id = new_id
                self.status.setText("Created")
        except AppError as exc:
            show_error(self, str(exc))
            return
        self._load_list()

    def _toggle_pin(self):
        if not self.current_id:
            show_info(self, "Select an entry first.")
            return
        self.app.workbook.toggle_pin(self.current_id)
        self._load_list()

    def _delete(self):
        if not self.current_id:
            show_info(self, "Select an entry first.")
            return
        if not confirm(self, "Delete this entry?"):
            return
        self.app.workbook.delete_entry(self.current_id)
        self.current_id = None
        self._clear_editor()
        self._load_list()

    def refresh(self):
        self._load_list()
