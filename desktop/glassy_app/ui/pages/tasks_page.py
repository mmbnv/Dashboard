"""Tasks page: a three-column board plus a filterable list."""

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...core.errors import AppError
from ...core.models import TASK_PRIORITIES, TASK_STATUSES
from ..base_page import BasePage
from ..dialogs import confirm, show_error
from ..widgets.common import Card, SectionHeader, StatCard, TagLabel, clear_layout

STATUS_LABELS = {"todo": "To do", "doing": "In progress", "done": "Done"}
PRIORITY_COLOURS = {"high": "#ef4444", "medium": "#f59e0b", "low": "#38bdf8"}


class TasksPage(BasePage):
    title = "Tasks"
    subtitle = "A board and a list for everything you need to do"

    def build(self):
        self.header = SectionHeader(self.title, self.subtitle)
        add = QPushButton("New task")
        add.setObjectName("Primary")
        add.clicked.connect(self._new_task)
        self.header.add_action(add)
        self.add(self.header)

        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(12)
        self.kpi = {}
        for key, label in (
            ("total", "Total"),
            ("todo", "To do"),
            ("doing", "In progress"),
            ("done", "Done"),
            ("overdue", "Overdue"),
        ):
            card = StatCard(label)
            self.kpi[key] = card
            self.kpi_row.addWidget(card)
        self.add(_wrap(self.kpi_row))

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_board_tab(), "Board")
        self.tabs.addTab(self._build_list_tab(), "List")
        self.tabs.currentChanged.connect(lambda _: self.refresh())
        self.add(self.tabs)

    # -- board -------------------------------------------------------------
    def _build_board_tab(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        self.columns = {}
        for status in TASK_STATUSES:
            column = Card(padding=12)
            header = QHBoxLayout()
            title = QLabel(STATUS_LABELS[status])
            title.setObjectName("SectionTitle")
            count = QLabel("0")
            count.setObjectName("Muted")
            header.addWidget(title)
            header.addStretch(1)
            header.addWidget(count)
            column.body().addLayout(header)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QScrollArea.NoFrame)
            holder = QWidget()
            box = QVBoxLayout(holder)
            box.setContentsMargins(0, 0, 0, 0)
            box.setSpacing(8)
            box.addStretch(1)
            scroll.setWidget(holder)
            column.body().addWidget(scroll, 1)
            self.columns[status] = (box, count)
            layout.addWidget(column, 1)
        return page

    def _load_board(self):
        tasks = self.app.tasks.list_tasks()
        for status, (box, count_label) in self.columns.items():
            clear_layout(box)
            matching = [t for t in tasks if t["status"] == status]
            count_label.setText(str(len(matching)))
            for task in matching:
                box.addWidget(self._task_card(task))
            box.addStretch(1)

    def _task_card(self, task):
        card = Card(alt=True, padding=10)
        title = QLabel(task["title"])
        title.setWordWrap(True)
        title.setStyleSheet("font-weight: 600;")
        card.add(title)

        if task["notes"]:
            notes = QLabel(task["notes"])
            notes.setObjectName("Muted")
            notes.setWordWrap(True)
            card.add(notes)

        tags = QHBoxLayout()
        tags.setSpacing(6)
        priority = TagLabel(
            task["priority"], PRIORITY_COLOURS.get(task["priority"], "#64748b")
        )
        tags.addWidget(priority)
        if task["due_on"]:
            due = TagLabel(task["due_on"], "#64748b")
            if task["due_on"] < QDate.currentDate().toString("yyyy-MM-dd") and (
                task["status"] != "done"
            ):
                due = TagLabel(f"overdue {task['due_on']}", "#ef4444")
            tags.addWidget(due)
        if task["tags"]:
            tags.addWidget(TagLabel(task["tags"], "#a855f7"))
        tags.addStretch(1)
        card.body().addLayout(tags)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        move = QComboBox()
        for status in TASK_STATUSES:
            move.addItem(STATUS_LABELS[status], status)
        index = move.findData(task["status"])
        if index >= 0:
            move.setCurrentIndex(index)
        move.currentIndexChanged.connect(
            lambda _, tid=task["id"], combo=move: self._move_task(
                tid, combo.currentData()
            )
        )
        actions.addWidget(move, 1)
        edit = QPushButton("Edit")
        edit.setObjectName("Ghost")
        edit.clicked.connect(lambda _, tid=task["id"]: self._edit_task(tid))
        actions.addWidget(edit)
        delete = QPushButton("\u2715")
        delete.setObjectName("Ghost")
        delete.clicked.connect(lambda _, tid=task["id"]: self._delete_task(tid))
        actions.addWidget(delete)
        card.body().addLayout(actions)
        return card

    # -- list ---------------------------------------------------------------
    def _build_list_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search tasks\u2026")
        self.search.textChanged.connect(self._load_list)
        row.addWidget(self.search, 2)

        self.status_filter = QComboBox()
        self.status_filter.addItem("All statuses", None)
        for status in TASK_STATUSES:
            self.status_filter.addItem(STATUS_LABELS[status], status)
        self.status_filter.currentIndexChanged.connect(self._load_list)
        row.addWidget(self.status_filter)

        self.priority_filter = QComboBox()
        self.priority_filter.addItem("All priorities", None)
        for priority in TASK_PRIORITIES:
            self.priority_filter.addItem(priority.capitalize(), priority)
        self.priority_filter.currentIndexChanged.connect(self._load_list)
        row.addWidget(self.priority_filter)
        layout.addLayout(row)

        self.list_box = QVBoxLayout()
        self.list_box.setSpacing(8)
        layout.addLayout(self.list_box)
        layout.addStretch(1)
        return page

    def _load_list(self):
        clear_layout(self.list_box)
        tasks = self.app.tasks.list_tasks(
            text=self.search.text().strip() or None,
            status=self.status_filter.currentData(),
            priority=self.priority_filter.currentData(),
        )
        if not tasks:
            label = QLabel("No tasks match these filters.")
            label.setObjectName("Muted")
            self.list_box.addWidget(label)
            return
        for task in tasks:
            self.list_box.addWidget(self._task_card(task))

    # -- actions ------------------------------------------------------------
    def _move_task(self, task_id, status):
        self.app.tasks.set_status(task_id, status)
        self.refresh()

    def _new_task(self):
        if TaskDialog(self.app, self).exec() == QDialog.Accepted:
            self.refresh()

    def _edit_task(self, task_id):
        if TaskDialog(self.app, self, task_id).exec() == QDialog.Accepted:
            self.refresh()

    def _delete_task(self, task_id):
        if confirm(self, "Delete this task?"):
            self.app.tasks.delete_task(task_id)
            self.refresh()

    def refresh(self):
        self._load_board()
        self._load_list()
        stats = self.app.tasks.stats()
        self.kpi["total"].set_value(str(stats["total"]))
        self.kpi["todo"].set_value(str(stats["todo"]))
        self.kpi["doing"].set_value(str(stats["doing"]))
        self.kpi["done"].set_value(str(stats["done"]))
        self.kpi["overdue"].set_value(
            str(stats["overdue"]),
            accent="#ef4444" if stats["overdue"] else None,
        )


class TaskDialog(QDialog):
    def __init__(self, app, parent=None, task_id=None):
        super().__init__(parent)
        self.app = app
        self.task_id = task_id
        self.setWindowTitle("Edit task" if task_id else "New task")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_input = QLineEdit()
        form.addRow("Title", self.title_input)

        self.status = QComboBox()
        for status in TASK_STATUSES:
            self.status.addItem(STATUS_LABELS[status], status)
        form.addRow("Status", self.status)

        self.priority = QComboBox()
        for priority in TASK_PRIORITIES:
            self.priority.addItem(priority.capitalize(), priority)
        self.priority.setCurrentIndex(1)
        form.addRow("Priority", self.priority)

        self.due = QDateEdit()
        self.due.setCalendarPopup(True)
        self.due.setDisplayFormat("yyyy-MM-dd")
        self.due.setDate(QDate.currentDate().addDays(7))
        form.addRow("Due date", self.due)

        self.tags = QLineEdit()
        form.addRow("Tags", self.tags)

        self.notes = QPlainTextEdit()
        self.notes.setFixedHeight(80)
        form.addRow("Notes", self.notes)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if task_id:
            task = app.tasks.get_task(task_id)
            self.title_input.setText(task["title"])
            index = self.status.findData(task["status"])
            if index >= 0:
                self.status.setCurrentIndex(index)
            index = self.priority.findData(task["priority"])
            if index >= 0:
                self.priority.setCurrentIndex(index)
            if task["due_on"]:
                self.due.setDate(QDate.fromString(task["due_on"], "yyyy-MM-dd"))
            self.tags.setText(task["tags"])
            self.notes.setPlainText(task["notes"])

    def _save(self):
        payload = dict(
            title=self.title_input.text(),
            status=self.status.currentData(),
            priority=self.priority.currentData(),
            due_on=self.due.date().toString("yyyy-MM-dd"),
            tags=self.tags.text().strip(),
            notes=self.notes.toPlainText(),
        )
        try:
            if self.task_id:
                self.app.tasks.update_task(self.task_id, **payload)
            else:
                self.app.tasks.create_task(**payload)
        except AppError as exc:
            show_error(self, str(exc))
            return
        self.accept()


def _wrap(layout):
    widget = QWidget()
    widget.setLayout(layout)
    return widget
