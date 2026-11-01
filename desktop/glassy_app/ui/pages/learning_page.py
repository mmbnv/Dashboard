"""Learning page: courses and study sessions."""

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...core import money
from ...core.errors import AppError
from ..base_page import BasePage
from ..dialogs import confirm, show_error, show_info
from ..widgets.common import BarChart, SectionHeader, StatCard

STATUS_LABELS = {
    "planned": "Planned",
    "active": "Active",
    "paused": "Paused",
    "done": "Done",
    "dropped": "Dropped",
}


class LearningPage(BasePage):
    title = "Learning"
    subtitle = "Courses, progress and study time"

    def build(self):
        self.header = SectionHeader(self.title, self.subtitle)
        self.add(self.header)

        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(12)
        self.kpi = {}
        for key, label in (
            ("courses", "Courses"),
            ("active", "Active"),
            ("hours", "Study time"),
            ("spend", "Spent on learning"),
        ):
            card = StatCard(label)
            self.kpi[key] = card
            self.kpi_row.addWidget(card)
        self.add(_wrap(self.kpi_row))

        self.chart_card = BarChart()
        self.weekly = BarChart()
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_courses_tab(), "Courses")
        self.tabs.addTab(self._build_sessions_tab(), "Study log")
        self.tabs.currentChanged.connect(lambda _: self.refresh())
        self.add(self.tabs)

    # -- courses --------------------------------------------------------
    def _build_courses_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        row = QHBoxLayout()
        add = QPushButton("Add course")
        add.setObjectName("Primary")
        add.clicked.connect(self._add_course)
        log = QPushButton("Log study session")
        log.clicked.connect(self._log_session)
        edit = QPushButton("Edit selected")
        edit.clicked.connect(self._edit_course)
        delete = QPushButton("Delete selected")
        delete.setObjectName("Danger")
        delete.clicked.connect(self._delete_course)
        row.addWidget(add)
        row.addWidget(log)
        row.addWidget(edit)
        row.addWidget(delete)
        row.addStretch(1)
        layout.addLayout(row)

        self.courses_table = QTableWidget(0, 8)
        self.courses_table.setHorizontalHeaderLabels(
            ["Title", "Provider", "Status", "Progress", "Units",
             "Hours", "Sessions", "Cost"]
        )
        self.courses_table.setAlternatingRowColors(True)
        self.courses_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.courses_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.courses_table.verticalHeader().setVisible(False)
        self.courses_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.courses_table.doubleClicked.connect(self._edit_course)
        layout.addWidget(self.courses_table, 1)

        chart_label = QLabel("Study time by week (minutes)")
        chart_label.setObjectName("SectionTitle")
        layout.addWidget(chart_label)
        layout.addWidget(self.weekly)
        return page

    def _load_courses(self):
        rows = self.app.learning.summary_rows()
        self.courses_table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            values = [
                row["title"],
                row["provider"],
                STATUS_LABELS.get(row["status"], row["status"]),
                f"{row['progress']:.0f}%",
                row["units"],
                str(row["hours"]),
                str(row["sessions"]),
                row["cost"],
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if col in (3, 4, 5, 6, 7):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.courses_table.setItem(index, col, item)
            self.courses_table.item(index, 0).setData(Qt.UserRole, row["id"])

        weekly = self.app.learning.weekly_minutes(8)
        self.weekly.set_data(
            [row["week"][-2:] for row in weekly],
            [row["minutes"] for row in weekly],
            [],
            "Minutes", "",
        )

    def _selected_course_id(self):
        row = self.courses_table.currentRow()
        if row < 0:
            return None
        item = self.courses_table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _add_course(self):
        if CourseDialog(self.app, self).exec() == QDialog.Accepted:
            self.refresh()

    def _edit_course(self):
        course_id = self._selected_course_id()
        if not course_id:
            show_info(self, "Select a course first.")
            return
        if CourseDialog(self.app, self, course_id).exec() == QDialog.Accepted:
            self.refresh()

    def _delete_course(self):
        course_id = self._selected_course_id()
        if not course_id:
            show_info(self, "Select a course first.")
            return
        if confirm(self, "Delete this course and all its study sessions?"):
            self.app.learning.delete_course(course_id)
            self.refresh()

    def _log_session(self):
        course_id = self._selected_course_id()
        if not course_id:
            show_info(self, "Select a course first.")
            return
        if SessionDialog(self.app, self, course_id).exec() == QDialog.Accepted:
            self.refresh()

    # -- sessions -------------------------------------------------------
    def _build_sessions_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        row = QHBoxLayout()
        remove = QPushButton("Delete selected session")
        remove.setObjectName("Danger")
        remove.clicked.connect(self._delete_session)
        row.addWidget(remove)
        row.addStretch(1)
        layout.addLayout(row)

        self.sessions_table = QTableWidget(0, 5)
        self.sessions_table.setHorizontalHeaderLabels(
            ["Date", "Course", "Minutes", "Units", "Note"]
        )
        self.sessions_table.setAlternatingRowColors(True)
        self.sessions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sessions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.sessions_table.verticalHeader().setVisible(False)
        self.sessions_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.Stretch
        )
        layout.addWidget(self.sessions_table, 1)
        return page

    def _load_sessions(self):
        rows = self.app.learning.list_sessions(limit=200)
        self.sessions_table.setRowCount(len(rows))
        for index, session in enumerate(rows):
            values = [
                session["occurred_on"],
                session["course_title"],
                str(session["minutes"]),
                str(session["units_done"]),
                session["note"],
            ]
            for col, value in enumerate(values):
                self.sessions_table.setItem(index, col, QTableWidgetItem(value))
            self.sessions_table.item(index, 0).setData(
                Qt.UserRole, session["id"]
            )

    def _delete_session(self):
        row = self.sessions_table.currentRow()
        if row < 0:
            show_info(self, "Select a session first.")
            return
        session_id = self.sessions_table.item(row, 0).data(Qt.UserRole)
        if confirm(self, "Delete this study session?"):
            self.app.learning.delete_session(session_id)
            self.refresh()

    # -- refresh --------------------------------------------------------
    def refresh(self):
        self._load_courses()
        self._load_sessions()
        totals = self.app.learning.totals()
        self.kpi["courses"].set_value(str(totals["courses"]))
        self.kpi["active"].set_value(str(totals["active"]))
        self.kpi["hours"].set_value(
            f"{totals['hours']} h", hint=f"{totals['total_minutes']} minutes logged"
        )
        self.kpi["spend"].set_value(
            money.format_amount(totals["spend_minor"], self.app.currency)
        )


class CourseDialog(QDialog):
    def __init__(self, app, parent=None, course_id=None):
        super().__init__(parent)
        self.app = app
        self.course_id = course_id
        self.setWindowTitle("Edit course" if course_id else "New course")
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_input = QLineEdit()
        form.addRow("Title", self.title_input)

        self.provider = QLineEdit()
        form.addRow("Provider", self.provider)

        self.url = QLineEdit()
        form.addRow("Link", self.url)

        self.status = QComboBox()
        for value in ("planned", "active", "paused", "done", "dropped"):
            self.status.addItem(STATUS_LABELS[value], value)
        self.status.setCurrentIndex(1)
        form.addRow("Status", self.status)

        self.total_units = QSpinBox()
        self.total_units.setRange(0, 100000)
        form.addRow("Total units", self.total_units)

        self.done_units = QSpinBox()
        self.done_units.setRange(0, 100000)
        form.addRow("Completed units", self.done_units)

        self.cost = QLineEdit("0")
        form.addRow("Cost", self.cost)

        self.started = QDateEdit()
        self.started.setCalendarPopup(True)
        self.started.setDisplayFormat("yyyy-MM-dd")
        self.started.setSpecialValueText("\u2014")
        self.started.setDate(QDate.currentDate())
        form.addRow("Started", self.started)

        self.rating = QSpinBox()
        self.rating.setRange(0, 5)
        form.addRow("Rating (0\u20135)", self.rating)

        self.note = QTextEdit()
        self.note.setFixedHeight(70)
        form.addRow("Notes", self.note)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if course_id:
            course = self.app.learning.get_course(course_id)
            self.title_input.setText(course["title"])
            self.provider.setText(course["provider"])
            self.url.setText(course["url"])
            index = self.status.findData(course["status"])
            if index >= 0:
                self.status.setCurrentIndex(index)
            self.total_units.setValue(int(course["total_units"] or 0))
            self.done_units.setValue(int(course["done_units"] or 0))
            self.cost.setText(str(money.to_decimal(course["cost"])))
            if course["started_on"]:
                self.started.setDate(
                    QDate.fromString(course["started_on"], "yyyy-MM-dd")
                )
            self.rating.setValue(int(course["rating"] or 0))
            self.note.setPlainText(course["note"])

    def _save(self):
        try:
            payload = dict(
                title=self.title_input.text(),
                provider=self.provider.text(),
                url=self.url.text(),
                status=self.status.currentData(),
                total_units=self.total_units.value(),
                done_units=self.done_units.value(),
                cost=money.to_minor(self.cost.text() or "0"),
                currency=self.app.currency,
                started_on=self.started.date().toString("yyyy-MM-dd"),
                rating=self.rating.value(),
                note=self.note.toPlainText(),
            )
            if self.course_id:
                self.app.learning.update_course(self.course_id, **payload)
            else:
                self.app.learning.create_course(**payload)
        except AppError as exc:
            show_error(self, str(exc))
            return
        self.accept()


class SessionDialog(QDialog):
    def __init__(self, app, parent=None, course_id=None):
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("Log study session")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.course = QComboBox()
        for course in app.learning.list_courses():
            self.course.addItem(course["title"], course["id"])
        if course_id:
            index = self.course.findData(course_id)
            if index >= 0:
                self.course.setCurrentIndex(index)
        form.addRow("Course", self.course)

        self.minutes = QSpinBox()
        self.minutes.setRange(0, 100000)
        self.minutes.setValue(30)
        form.addRow("Minutes", self.minutes)

        self.units = QSpinBox()
        self.units.setRange(0, 100000)
        form.addRow("Units completed", self.units)

        self.occurred = QDateEdit()
        self.occurred.setCalendarPopup(True)
        self.occurred.setDisplayFormat("yyyy-MM-dd")
        self.occurred.setDate(QDate.currentDate())
        form.addRow("Date", self.occurred)

        self.note = QLineEdit()
        form.addRow("Note", self.note)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        try:
            self.app.learning.log_session(
                course_id=self.course.currentData(),
                minutes=self.minutes.value(),
                units_done=self.units.value(),
                occurred_on=self.occurred.date().toString("yyyy-MM-dd"),
                note=self.note.text(),
            )
        except AppError as exc:
            show_error(self, str(exc))
            return
        self.accept()


def _wrap(layout):
    widget = QWidget()
    widget.setLayout(layout)
    return widget
