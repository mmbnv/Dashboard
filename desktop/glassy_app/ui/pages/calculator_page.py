"""Calculator page: expression evaluation, percentages and loan maths.

Every computation here is pure; the history is kept in memory only.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ... import terms
from ...core import calculator, money
from ...core.errors import AppError
from ..base_page import BasePage
from ..dialogs import show_error
from ..widgets.common import Card, SectionHeader, clear_layout, title_label

BUTTONS = [
    ["C", "(", ")", "\u00f7"],
    ["7", "8", "9", "\u00d7"],
    ["4", "5", "6", "\u2212"],
    ["1", "2", "3", "+"],
    ["0", ".", "\u2190", "="],
]


class CalculatorPage(BasePage):
    title = terms.SECTION_TITLES["calculator"]
    subtitle = terms.SECTION_SUBTITLES["calculator"]

    def build(self):
        self.header = SectionHeader(self.title, self.subtitle)
        self.add(self.header)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_basic_tab(), "Вычисления")
        self.tabs.addTab(self._build_percent_tab(), "Проценты")
        self.tabs.addTab(self._build_loan_tab(), "Кредит")
        self.add(self.tabs)
        self.history = []

    # -- basic -----------------------------------------------------------
    def _build_basic_tab(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        left = Card()
        self.expression = QLineEdit()
        self.expression.setPlaceholderText("Введите выражение, например (1200+350)*1.2")
        self.expression.setStyleSheet("font-size: 18px; padding: 12px;")
        self.expression.returnPressed.connect(self._evaluate)
        left.body().addWidget(self.expression)

        self.result = QLabel("\u2014")
        self.result.setObjectName("CardValue")
        self.result.setAlignment(Qt.AlignRight)
        left.body().addWidget(self.result)

        grid = QGridLayout()
        grid.setSpacing(8)
        for row, keys in enumerate(BUTTONS):
            for col, key in enumerate(keys):
                button = QPushButton(key)
                button.setMinimumHeight(46)
                button.setStyleSheet("font-size: 16px;")
                if key == "=":
                    button.setObjectName("Primary")
                button.clicked.connect(
                    lambda _, k=key: self._press(k)
                )
                grid.addWidget(button, row, col)
        left.body().addLayout(grid)

        hint = QLabel(
            "Функции: sqrt, log, sin, cos, abs, round, min, max. "
            "Константы: pi, e."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        left.body().addWidget(hint)
        left.body().addStretch(1)
        layout.addWidget(left, 3)

        right = Card()
        right.body().addWidget(title_label("История"))
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self._reuse_history)
        right.body().addWidget(self.history_list, 1)
        clear_history = QPushButton("Очистить историю")
        clear_history.setObjectName("Ghost")
        clear_history.clicked.connect(self._clear_history)
        right.body().addWidget(clear_history)
        layout.addWidget(right, 2)
        return page

    def _press(self, key):
        if key == "C":
            self.expression.clear()
            self.result.setText("\u2014")
        elif key == "\u2190":
            self.expression.setText(self.expression.text()[:-1])
        elif key == "=":
            self._evaluate()
        else:
            self.expression.setText(self.expression.text() + key)

    def _evaluate(self):
        try:
            value = calculator.evaluate(self.expression.text())
        except AppError as exc:
            self.result.setText("ошибка")
            self.result.setStyleSheet("color: #ef4444;")
            show_error(self, str(exc), title="Не удалось вычислить")
            return
        text = calculator.format_result(value)
        self.result.setText(text)
        self.result.setStyleSheet("")
        entry = f"{self.expression.text()} = {text}"
        self.history.insert(0, entry)
        self.history_list.insertItem(0, entry)

    def _reuse_history(self, item):
        expression = item.text().split(" = ")[0]
        self.expression.setText(expression)

    def _clear_history(self):
        self.history.clear()
        self.history_list.clear()

    # -- percentages ------------------------------------------------------
    def _build_percent_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        card = Card()
        card.body().addWidget(title_label("Процент от числа"))
        row = QHBoxLayout()
        self.pct_of_base = QLineEdit("1000")
        self.pct_of_base.setPlaceholderText("Число")
        self.pct_of_value = QLineEdit("15")
        self.pct_of_value.setPlaceholderText("Процент")
        compute = QPushButton("Вычислить")
        compute.setObjectName("Primary")
        compute.clicked.connect(self._percent_of)
        row.addWidget(QLabel("Число"))
        row.addWidget(self.pct_of_base)
        row.addWidget(QLabel("Процент %"))
        row.addWidget(self.pct_of_value)
        row.addWidget(compute)
        card.body().addLayout(row)
        self.pct_of_result = QLabel("\u2014")
        self.pct_of_result.setObjectName("CardValue")
        card.body().addWidget(self.pct_of_result)
        layout.addWidget(card)

        card2 = Card()
        card2.body().addWidget(title_label("Изменение в процентах"))
        row2 = QHBoxLayout()
        self.change_from = QLineEdit("100")
        self.change_to = QLineEdit("150")
        compute2 = QPushButton("Вычислить")
        compute2.setObjectName("Primary")
        compute2.clicked.connect(self._percent_change)
        row2.addWidget(QLabel("Было"))
        row2.addWidget(self.change_from)
        row2.addWidget(QLabel("Стало"))
        row2.addWidget(self.change_to)
        row2.addWidget(compute2)
        card2.body().addLayout(row2)
        self.change_result = QLabel("\u2014")
        self.change_result.setObjectName("CardValue")
        card2.body().addWidget(self.change_result)
        layout.addWidget(card2)

        card3 = Card()
        card3.body().addWidget(title_label("Разделить счёт"))
        row3 = QHBoxLayout()
        self.bill_total = QLineEdit("1000")
        self.bill_people = QSpinBox()
        self.bill_people.setRange(1, 100)
        self.bill_people.setValue(2)
        compute3 = QPushButton("Разделить")
        compute3.setObjectName("Primary")
        compute3.clicked.connect(self._split_bill)
        row3.addWidget(QLabel("Всего"))
        row3.addWidget(self.bill_total)
        row3.addWidget(QLabel("Человек"))
        row3.addWidget(self.bill_people)
        row3.addWidget(compute3)
        card3.body().addLayout(row3)
        self.bill_result = QLabel("\u2014")
        self.bill_result.setObjectName("CardValue")
        card3.body().addWidget(self.bill_result)
        layout.addWidget(card3)
        layout.addStretch(1)
        return page

    def _percent_of(self):
        try:
            base = float(self.pct_of_base.text().replace(",", "."))
            pct = float(self.pct_of_value.text().replace(",", "."))
        except ValueError:
            show_error(self, "Введите корректные числа.")
            return
        self.pct_of_result.setText(calculator.format_result(
            calculator.percent_of(base, pct)
        ))

    def _percent_change(self):
        try:
            old = float(self.change_from.text().replace(",", "."))
            new = float(self.change_to.text().replace(",", "."))
        except ValueError:
            show_error(self, "Введите корректные числа.")
            return
        value = calculator.percent_change(old, new)
        if value == float("inf"):
            self.change_result.setText("\u2014")
            return
        sign = "+" if value > 0 else ""
        self.change_result.setText(f"{sign}{value:.2f}%")

    def _split_bill(self):
        try:
            total = money.to_minor(self.bill_total.text())
        except AppError as exc:
            show_error(self, str(exc))
            return
        people = self.bill_people.value() or 1
        each = total // people
        remainder = total - each * people
        text = money.format_amount(each, self.app.currency)
        if remainder:
            text += (
                f"  (+{money.format_amount(remainder, self.app.currency)} остаток)"
            )
        self.bill_result.setText(text)

    # -- loan -------------------------------------------------------------
    def _build_loan_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        card = Card()
        card.body().addWidget(title_label("Аннуитетный платёж"))
        form = QGridLayout()
        form.setSpacing(10)

        self.loan_amount = QLineEdit("1000000")
        self.loan_rate = QLineEdit("12")
        self.loan_months = QSpinBox()
        self.loan_months.setRange(1, 600)
        self.loan_months.setValue(24)

        form.addWidget(QLabel("Сумма"), 0, 0)
        form.addWidget(self.loan_amount, 0, 1)
        form.addWidget(QLabel("Ставка, % годовых"), 1, 0)
        form.addWidget(self.loan_rate, 1, 1)
        form.addWidget(QLabel("Срок, месяцев"), 2, 0)
        form.addWidget(self.loan_months, 2, 1)

        compute = QPushButton("Вычислить")
        compute.setObjectName("Primary")
        compute.clicked.connect(self._compute_loan)
        form.addWidget(compute, 3, 0, 1, 2)
        card.body().addLayout(form)

        self.loan_output = QVBoxLayout()
        self.loan_output.setSpacing(6)
        card.body().addLayout(self.loan_output)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _compute_loan(self):
        clear_layout(self.loan_output)
        try:
            principal = float(money.to_minor(self.loan_amount.text())) / 100.0
            rate = float(self.loan_rate.text().replace(",", "."))
        except (AppError, ValueError) as exc:
            show_error(self, str(exc) if str(exc) else "Введите корректные числа.")
            return
        try:
            payment, total, overpay = calculator.loan_payment(
                principal, rate, self.loan_months.value()
            )
        except AppError as exc:
            show_error(self, str(exc))
            return
        currency = self.app.currency
        for label, value in (
            ("Ежемесячный платёж",
             money.format_amount(int(round(payment * 100)), currency)),
            ("Всего выплат", money.format_amount(int(round(total * 100)), currency)),
            ("Переплата",
             money.format_amount(int(round(overpay * 100)), currency)),
        ):
            row = QWidget()
            line = QHBoxLayout(row)
            line.setContentsMargins(0, 0, 0, 0)
            caption = QLabel(label)
            caption.setObjectName("Muted")
            amount = QLabel(value)
            amount.setStyleSheet("font-weight: 600;")
            line.addWidget(caption, 1)
            line.addWidget(amount)
            self.loan_output.addWidget(row)

    def refresh(self):
        pass

