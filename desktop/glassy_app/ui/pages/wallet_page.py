"""Wallet page: transactions, accounts, categories and budgets."""

from datetime import date

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
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ... import terms
from ...core import money
from ...core.errors import AppError
from ...core.models import EXPENSE, INCOME
from ..base_page import BasePage
from ..dialogs import confirm, show_error, show_info
from ..widgets.common import (
    ProgressRow,
    SectionHeader,
    StatCard,
    clear_layout,
    wrap,
)

KIND_LABELS = terms.KINDS


class WalletPage(BasePage):
    title = terms.SECTION_TITLES["wallet"]
    subtitle = terms.SECTION_SUBTITLES["wallet"]

    def build(self):
        self.header = SectionHeader(self.title, self.subtitle)
        self.add(self.header)

        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(12)
        self.kpi = {}
        for key, label in (
            ("balance", "Общий баланс"),
            ("income", "Доход (по фильтру)"),
            ("expense", "Расход (по фильтру)"),
            ("net", "Итог (по фильтру)"),
        ):
            card = StatCard(label)
            self.kpi[key] = card
            self.kpi_row.addWidget(card)
        self.add(wrap(self.kpi_row))

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_transactions_tab(), "Операции")
        self.tabs.addTab(self._build_accounts_tab(), "Счета")
        self.tabs.addTab(self._build_categories_tab(), "Категории")
        self.tabs.addTab(self._build_budgets_tab(), "Бюджеты")
        self.tabs.currentChanged.connect(lambda _: self.refresh())
        self.add(self.tabs)

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------
    def _build_transactions_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.tx_search = QLineEdit()
        self.tx_search.setPlaceholderText("Поиск по получателю, заметке или категории\u2026")
        self.tx_search.textChanged.connect(self._load_transactions)
        controls.addWidget(self.tx_search, 2)

        self.tx_kind = QComboBox()
        self.tx_kind.addItem("Все виды", None)
        self.tx_kind.addItem(KIND_LABELS[INCOME], INCOME)
        self.tx_kind.addItem(KIND_LABELS[EXPENSE], EXPENSE)
        self.tx_kind.currentIndexChanged.connect(self._load_transactions)
        controls.addWidget(self.tx_kind)

        self.tx_account = QComboBox()
        self.tx_account.currentIndexChanged.connect(self._load_transactions)
        controls.addWidget(self.tx_account)

        self.tx_category = QComboBox()
        self.tx_category.currentIndexChanged.connect(self._load_transactions)
        controls.addWidget(self.tx_category)

        add_button = QPushButton("Добавить операцию")
        add_button.setObjectName("Primary")
        add_button.clicked.connect(self._add_transaction)
        controls.addWidget(add_button)
        layout.addLayout(controls)

        date_row = QHBoxLayout()
        date_row.setSpacing(8)
        self.tx_from = QDateEdit()
        self.tx_from.setCalendarPopup(True)
        self.tx_from.setDisplayFormat("dd.MM.yyyy")
        self.tx_from.setDate(QDate.currentDate().addMonths(-1))
        self.tx_from.dateChanged.connect(self._load_transactions)
        self.tx_to = QDateEdit()
        self.tx_to.setCalendarPopup(True)
        self.tx_to.setDisplayFormat("dd.MM.yyyy")
        self.tx_to.setDate(QDate.currentDate())
        self.tx_to.dateChanged.connect(self._load_transactions)

        clear_button = QPushButton("Сбросить фильтры")
        clear_button.setObjectName("Ghost")
        clear_button.clicked.connect(self._clear_filters)
        export_button = QPushButton("Экспорт в CSV")
        export_button.setObjectName("Ghost")
        export_button.clicked.connect(self._export_csv)

        date_row.addWidget(QLabel("С"))
        date_row.addWidget(self.tx_from)
        date_row.addWidget(QLabel("По"))
        date_row.addWidget(self.tx_to)
        date_row.addWidget(clear_button)
        date_row.addStretch(1)
        date_row.addWidget(export_button)
        layout.addLayout(date_row)

        self.tx_table = QTableWidget(0, 7)
        self.tx_table.setHorizontalHeaderLabels(
            ["Дата", "Вид", "Сумма", "Счёт", "Категория", "Получатель", "Заметка"]
        )
        self.tx_table.setAlternatingRowColors(True)
        self.tx_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tx_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tx_table.verticalHeader().setVisible(False)
        self.tx_table.setSortingEnabled(True)
        header = self.tx_table.horizontalHeader()
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        for col in (0, 1, 2, 3, 4, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.tx_table.doubleClicked.connect(self._edit_transaction)
        layout.addWidget(self.tx_table, 1)

        actions = QHBoxLayout()
        edit_button = QPushButton("Изменить")
        edit_button.clicked.connect(self._edit_transaction)
        delete_button = QPushButton("Удалить")
        delete_button.setObjectName("Danger")
        delete_button.clicked.connect(self._delete_transaction)
        actions.addWidget(edit_button)
        actions.addWidget(delete_button)
        actions.addStretch(1)
        self.tx_count = QLabel()
        self.tx_count.setObjectName("Muted")
        actions.addWidget(self.tx_count)
        layout.addLayout(actions)
        return page

    def _load_transactions(self):
        filters = {
            "text": self.tx_search.text().strip() or None,
            "kind": self.tx_kind.currentData(),
            "account_id": self.tx_account.currentData(),
            "category_id": self.tx_category.currentData(),
            "date_from": self.tx_from.date().toString("yyyy-MM-dd"),
            "date_to": self.tx_to.date().toString("yyyy-MM-dd"),
        }
        rows = self.app.wallet.list_transactions(**filters)
        currency = self.app.currency

        self.tx_table.setSortingEnabled(False)
        self.tx_table.setRowCount(len(rows))
        for index, tx in enumerate(rows):
            values = [
                tx["occurred_on"],
                KIND_LABELS.get(tx["kind"], tx["kind"]),
                money.format_amount(tx["amount"], currency),
                tx["account_name"] or "",
                tx["category_name"] or "\u2014",
                tx["payee"] or "",
                tx["note"] or "",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 2:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    item.setForeground(
                        Qt.green if tx["kind"] == INCOME else Qt.red
                    )
                self.tx_table.setItem(index, col, item)
            self.tx_table.item(index, 0).setData(Qt.UserRole, tx["id"])
        self.tx_table.setSortingEnabled(True)

        self.tx_count.setText(f"операций: {len(rows)}")

        totals = self.app.wallet.summary(
            date_from=filters["date_from"], date_to=filters["date_to"],
            account_id=filters["account_id"],
        )
        self.kpi["income"].set_value(
            money.format_amount(totals["income"], currency), accent="#22c55e"
        )
        self.kpi["expense"].set_value(
            money.format_amount(totals["expense"], currency), accent="#ef4444"
        )
        net = totals["net"]
        self.kpi["net"].set_value(
            money.format_amount(net, currency),
            accent="#22c55e" if net >= 0 else "#ef4444",
        )

    def _clear_filters(self):
        self.tx_search.clear()
        self.tx_kind.setCurrentIndex(0)
        self.tx_account.setCurrentIndex(0)
        self.tx_category.setCurrentIndex(0)
        self.tx_from.setDate(QDate.currentDate().addMonths(-1))
        self.tx_to.setDate(QDate.currentDate())

    def _selected_tx_id(self):
        row = self.tx_table.currentRow()
        if row < 0:
            return None
        item = self.tx_table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _add_transaction(self):
        dialog = TransactionDialog(self.app, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh()

    def _edit_transaction(self):
        tx_id = self._selected_tx_id()
        if not tx_id:
            show_info(self, "Сначала выберите операцию.")
            return
        dialog = TransactionDialog(self.app, self, tx_id=tx_id)
        if dialog.exec() == QDialog.Accepted:
            self.refresh()

    def _delete_transaction(self):
        tx_id = self._selected_tx_id()
        if not tx_id:
            show_info(self, "Сначала выберите операцию.")
            return
        if confirm(self, "Удалить эту операцию? Действие необратимо."):
            self.app.wallet.delete_transaction(tx_id)
            self.refresh()

    def _export_csv(self):
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт операций", "transactions.csv", "Файлы CSV (*.csv)"
        )
        if not path:
            return
        count = self.app.export_transactions_csv(
            path,
            text=self.tx_search.text().strip() or None,
            kind=self.tx_kind.currentData(),
            account_id=self.tx_account.currentData(),
            category_id=self.tx_category.currentData(),
            date_from=self.tx_from.date().toString("yyyy-MM-dd"),
            date_to=self.tx_to.date().toString("yyyy-MM-dd"),
        )
        show_info(self, f"Экспортировано операций: {count}\n{path}")

    # ------------------------------------------------------------------
    # Accounts
    # ------------------------------------------------------------------
    def _build_accounts_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        row = QHBoxLayout()
        add = QPushButton("Добавить счёт")
        add.setObjectName("Primary")
        add.clicked.connect(self._add_account)
        edit = QPushButton("Изменить")
        edit.clicked.connect(self._edit_account)
        delete = QPushButton("Удалить")
        delete.setObjectName("Danger")
        delete.clicked.connect(self._delete_account)
        row.addWidget(add)
        row.addWidget(edit)
        row.addWidget(delete)
        row.addStretch(1)
        layout.addLayout(row)

        self.accounts_table = QTableWidget(0, 5)
        self.accounts_table.setHorizontalHeaderLabels(
            ["Название", "Вид", "Валюта", "Баланс", "Операций"]
        )
        self.accounts_table.setAlternatingRowColors(True)
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.accounts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.accounts_table.verticalHeader().setVisible(False)
        self.accounts_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.accounts_table.doubleClicked.connect(self._edit_account)
        layout.addWidget(self.accounts_table, 1)
        return page

    def _load_accounts(self):
        rows = self.app.wallet.list_accounts()
        self.accounts_table.setRowCount(len(rows))
        for index, account in enumerate(rows):
            values = [
                account["name"],
                terms.label(terms.ACCOUNT_KINDS, account["kind"]),
                account["currency"],
                money.format_amount(account["balance"], account["currency"]),
                str(account["tx_count"]),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 3:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.accounts_table.setItem(index, col, item)
            self.accounts_table.item(index, 0).setData(Qt.UserRole, account["id"])
        total = money.sum_minor(r["balance"] for r in rows)
        self.kpi["balance"].set_value(
            money.format_amount(total, self.app.currency)
        )

    def _selected_account_id(self):
        row = self.accounts_table.currentRow()
        if row < 0:
            return None
        item = self.accounts_table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _add_account(self):
        dialog = AccountDialog(self.app, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh()

    def _edit_account(self):
        account_id = self._selected_account_id()
        if not account_id:
            show_info(self, "Сначала выберите счёт.")
            return
        dialog = AccountDialog(self.app, self, account_id=account_id)
        if dialog.exec() == QDialog.Accepted:
            self.refresh()

    def _delete_account(self):
        account_id = self._selected_account_id()
        if not account_id:
            show_info(self, "Сначала выберите счёт.")
            return
        if not confirm(self, "Удалить этот счёт?"):
            return
        try:
            self.app.wallet.delete_account(account_id)
        except AppError as exc:
            show_error(self, str(exc))
            return
        self.refresh()

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------
    def _build_categories_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        row = QHBoxLayout()
        add = QPushButton("Добавить категорию")
        add.setObjectName("Primary")
        add.clicked.connect(self._add_category)
        edit = QPushButton("Изменить")
        edit.clicked.connect(self._edit_category)
        delete = QPushButton("Удалить")
        delete.setObjectName("Danger")
        delete.clicked.connect(self._delete_category)
        row.addWidget(add)
        row.addWidget(edit)
        row.addWidget(delete)
        row.addStretch(1)
        layout.addLayout(row)

        self.categories_table = QTableWidget(0, 5)
        self.categories_table.setHorizontalHeaderLabels(
            ["Название", "Вид", "Цвет", "Операций", "Итого"]
        )
        self.categories_table.setAlternatingRowColors(True)
        self.categories_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.categories_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.categories_table.verticalHeader().setVisible(False)
        self.categories_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.categories_table.doubleClicked.connect(self._edit_category)
        layout.addWidget(self.categories_table, 1)
        return page

    def _load_categories(self):
        rows = self.app.wallet.list_categories()
        self.categories_table.setRowCount(len(rows))
        for index, cat in enumerate(rows):
            values = [
                cat["name"],
                KIND_LABELS.get(cat["kind"], cat["kind"]),
                cat["color"],
                str(cat["tx_count"]),
                money.format_amount(cat["total_minor"], self.app.currency),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 2:
                    item.setForeground(Qt.GlobalColor.gray)
                self.categories_table.setItem(index, col, item)
            self.categories_table.item(index, 0).setData(Qt.UserRole, cat["id"])

    def _selected_category_id(self):
        row = self.categories_table.currentRow()
        if row < 0:
            return None
        item = self.categories_table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _add_category(self):
        dialog = CategoryDialog(self.app, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh()

    def _edit_category(self):
        category_id = self._selected_category_id()
        if not category_id:
            show_info(self, "Сначала выберите категорию.")
            return
        dialog = CategoryDialog(self.app, self, category_id=category_id)
        if dialog.exec() == QDialog.Accepted:
            self.refresh()

    def _delete_category(self):
        category_id = self._selected_category_id()
        if not category_id:
            show_info(self, "Сначала выберите категорию.")
            return
        if not confirm(self, "Удалить эту категорию?"):
            return
        try:
            self.app.wallet.delete_category(category_id)
        except AppError as exc:
            show_error(self, str(exc))
            return
        self.refresh()

    # ------------------------------------------------------------------
    # Budgets
    # ------------------------------------------------------------------
    def _build_budgets_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        row = QHBoxLayout()
        row.addWidget(QLabel("Месяц"))
        self.budget_period = QComboBox()
        self.budget_period.currentIndexChanged.connect(self._load_budgets)
        row.addWidget(self.budget_period)
        add = QPushButton("Задать бюджет")
        add.setObjectName("Primary")
        add.clicked.connect(self._set_budget)
        remove = QPushButton("Убрать")
        remove.setObjectName("Danger")
        remove.clicked.connect(self._remove_budget)
        row.addWidget(add)
        row.addWidget(remove)
        row.addStretch(1)
        layout.addLayout(row)

        self.budgets_box = QVBoxLayout()
        self.budgets_box.setSpacing(8)
        layout.addLayout(self.budgets_box)
        layout.addStretch(1)
        return page

    def _load_budget_periods(self):
        current = self.budget_period.currentData()
        today = date.today()
        periods = []
        year, month = today.year, today.month
        for offset in range(-6, 7):
            m = month + offset
            y = year
            while m < 1:
                m += 12
                y -= 1
            while m > 12:
                m -= 12
                y += 1
            periods.append(f"{y:04d}-{m:02d}")
        self.budget_period.blockSignals(True)
        self.budget_period.clear()
        for period in periods:
            self.budget_period.addItem(period, period)
        target = current if current in periods else today.strftime("%Y-%m")
        index = self.budget_period.findData(target)
        if index >= 0:
            self.budget_period.setCurrentIndex(index)
        self.budget_period.blockSignals(False)

    def _load_budgets(self):
        clear_layout(self.budgets_box)
        period = self.budget_period.currentData() or date.today().strftime("%Y-%m")
        rows = self.app.wallet.list_budgets(period)
        currency = self.app.currency
        if not rows:
            label = QLabel("На этот месяц бюджетов пока нет.")
            label.setObjectName("Muted")
            self.budgets_box.addWidget(label)
            return
        for budget in rows:
            limit = budget["limit_minor"] or 0
            spent = budget["spent_minor"] or 0
            percent = (spent / limit * 100.0) if limit else 0.0
            colour = "#22c55e"
            if percent > 100:
                colour = "#ef4444"
            elif percent > 80:
                colour = "#f59e0b"
            remaining = limit - spent
            widget = ProgressRow(
                budget["category_name"],
                f"{money.format_amount(spent, currency, with_symbol=False)}"
                f" / {money.format_amount(limit, currency, with_symbol=False)}"
                f"   (осталось {money.format_amount(remaining, currency, with_symbol=False)})",
                percent,
                colour,
            )
            widget.setProperty("budget_id", budget["id"])
            self.budgets_box.addWidget(widget)

    def _set_budget(self):
        dialog = BudgetDialog(self.app, self, self.budget_period.currentData())
        if dialog.exec() == QDialog.Accepted:
            self.refresh()

    def _remove_budget(self):
        selected = None
        for index in range(self.budgets_box.count()):
            widget = self.budgets_box.itemAt(index).widget()
            if widget is not None and widget.property("budget_id"):
                selected = widget.property("budget_id")
                break
        if not selected:
            show_info(self, "За этот месяц убирать нечего.")
            return
        if confirm(self, "Убрать этот бюджет?"):
            self.app.wallet.delete_budget(selected)
            self.refresh()

    # ------------------------------------------------------------------
    # Shared refresh
    # ------------------------------------------------------------------
    def refresh(self):
        currency = self.app.currency
        self._reload_filter_combos()
        self._load_transactions()
        self._load_accounts()
        self._load_categories()
        self._load_budget_periods()
        self._load_budgets()

        net_worth, accounts = self.app.wallet.net_worth()
        self.kpi["balance"].set_value(
            money.format_amount(net_worth, currency)
        )
        _ = accounts

    def _reload_filter_combos(self):
        """Repopulate the filter dropdowns without losing the selection."""
        for combo, items, all_label in (
            (
                self.tx_account,
                [(a["name"], a["id"]) for a in self.app.wallet.list_accounts()],
                "Все счета",
            ),
            (
                self.tx_category,
                [
                    (c["name"], c["id"])
                    for c in self.app.wallet.list_categories()
                ],
                "Все категории",
            ),
        ):
            previous = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(all_label, None)
            for label, value in items:
                combo.addItem(label, value)
            index = combo.findData(previous)
            combo.setCurrentIndex(index if index >= 0 else 0)
            combo.blockSignals(False)


# ----------------------------------------------------------------------
# Dialogs
# ----------------------------------------------------------------------
class TransactionDialog(QDialog):
    def __init__(self, app, parent=None, tx_id=None):
        super().__init__(parent)
        self.app = app
        self.tx_id = tx_id
        self.setWindowTitle("Изменить операцию" if tx_id else "Новая операция")
        self.setMinimumWidth(430)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.kind = QComboBox()
        self.kind.addItem(KIND_LABELS[EXPENSE], EXPENSE)
        self.kind.addItem(KIND_LABELS[INCOME], INCOME)
        self.kind.currentIndexChanged.connect(self._reload_categories)
        form.addRow("Вид", self.kind)

        self.amount = QLineEdit()
        self.amount.setPlaceholderText("например, 1250,50")
        form.addRow("Сумма", self.amount)

        self.account = QComboBox()
        for account in app.wallet.list_accounts(with_balances=False):
            self.account.addItem(account["name"], account["id"])
        form.addRow("Счёт", self.account)

        self.category = QComboBox()
        form.addRow("Категория", self.category)

        self.occurred = QDateEdit()
        self.occurred.setCalendarPopup(True)
        self.occurred.setDisplayFormat("dd.MM.yyyy")
        self.occurred.setDate(QDate.currentDate())
        form.addRow("Дата", self.occurred)

        self.payee = QLineEdit()
        form.addRow("Получатель", self.payee)

        self.note = QLineEdit()
        form.addRow("Заметка", self.note)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._reload_categories()
        if tx_id:
            self._load(tx_id)

    def _reload_categories(self):
        kind = self.kind.currentData()
        previous = self.category.currentData()
        self.category.clear()
        self.category.addItem("\u2014 без категории \u2014", None)
        for cat in self.app.wallet.list_categories(kind):
            self.category.addItem(cat["name"], cat["id"])
        index = self.category.findData(previous)
        self.category.setCurrentIndex(index if index >= 0 else 0)

    def _load(self, tx_id):
        tx = self.app.wallet.get_transaction(tx_id)
        self.kind.setCurrentIndex(max(0, self.kind.findData(tx["kind"])))
        self._reload_categories()
        self.amount.setText(
            money.to_decimal(tx["amount"]).__str__().replace(".", ",")
        )
        account_index = self.account.findData(tx["account_id"])
        if account_index >= 0:
            self.account.setCurrentIndex(account_index)
        category_index = self.category.findData(tx["category_id"])
        if category_index >= 0:
            self.category.setCurrentIndex(category_index)
        self.occurred.setDate(QDate.fromString(tx["occurred_on"], "yyyy-MM-dd"))
        self.payee.setText(tx["payee"])
        self.note.setText(tx["note"])

    def _save(self):
        try:
            if self.tx_id:
                self.app.wallet.update_transaction(
                    self.tx_id,
                    account_id=self.account.currentData(),
                    kind=self.kind.currentData(),
                    amount=self.amount.text(),
                    occurred_on=self.occurred.date().toString("yyyy-MM-dd"),
                    category_id=self.category.currentData(),
                    payee=self.payee.text(),
                    note=self.note.text(),
                )
            else:
                self.app.wallet.add_transaction(
                    account_id=self.account.currentData(),
                    kind=self.kind.currentData(),
                    amount=self.amount.text(),
                    occurred_on=self.occurred.date().toString("yyyy-MM-dd"),
                    category_id=self.category.currentData(),
                    payee=self.payee.text(),
                    note=self.note.text(),
                )
        except AppError as exc:
            show_error(self, str(exc))
            return
        self.accept()


class AccountDialog(QDialog):
    def __init__(self, app, parent=None, account_id=None):
        super().__init__(parent)
        self.app = app
        self.account_id = account_id
        self.setWindowTitle("Изменить счёт" if account_id else "Новый счёт")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name = QLineEdit()
        form.addRow("Название", self.name)

        self.kind = QComboBox()
        for value in ("cash", "bank", "card", "savings", "investment", "other"):
            self.kind.addItem(terms.label(terms.ACCOUNT_KINDS, value, value), value)
        form.addRow("Вид", self.kind)

        self.currency = QComboBox()
        for value in ("RUB", "USD", "EUR", "KZT", "UAH"):
            self.currency.addItem(value, value)
        form.addRow("Валюта", self.currency)

        self.opening = QLineEdit("0")
        form.addRow("Начальный остаток", self.opening)

        self.note = QLineEdit()
        form.addRow("Заметка", self.note)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if account_id:
            account = self.app.wallet.get_account(account_id)
            self.name.setText(account["name"])
            index = self.kind.findData(account["kind"])
            if index >= 0:
                self.kind.setCurrentIndex(index)
            index = self.currency.findData(account["currency"])
            if index >= 0:
                self.currency.setCurrentIndex(index)
            self.opening.setText(str(money.to_decimal(account["opening"])))
            self.note.setText(account["note"])

    def _save(self):
        try:
            opening = money.to_minor(self.opening.text() or "0")
            payload = dict(
                name=self.name.text(),
                kind=self.kind.currentData(),
                currency=self.currency.currentData(),
                opening=opening,
                note=self.note.text(),
            )
            if self.account_id:
                self.app.wallet.update_account(self.account_id, **payload)
            else:
                self.app.wallet.create_account(**payload)
        except AppError as exc:
            show_error(self, str(exc))
            return
        self.accept()


class CategoryDialog(QDialog):
    def __init__(self, app, parent=None, category_id=None):
        super().__init__(parent)
        self.app = app
        self.category_id = category_id
        self.setWindowTitle("Изменить категорию" if category_id else "Новая категория")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name = QLineEdit()
        form.addRow("Название", self.name)

        self.kind = QComboBox()
        self.kind.addItem(KIND_LABELS[EXPENSE], EXPENSE)
        self.kind.addItem(KIND_LABELS[INCOME], INCOME)
        form.addRow("Вид", self.kind)

        self.color = QLineEdit("#7c3aed")
        form.addRow("Цвет", self.color)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if category_id:
            cat = self.app.wallet.get_category(category_id)
            self.name.setText(cat["name"])
            index = self.kind.findData(cat["kind"])
            if index >= 0:
                self.kind.setCurrentIndex(index)
            self.color.setText(cat["color"])

    def _save(self):
        try:
            payload = dict(
                name=self.name.text(),
                kind=self.kind.currentData(),
                color=self.color.text() or "#7c3aed",
            )
            if self.category_id:
                self.app.wallet.update_category(self.category_id, **payload)
            else:
                self.app.wallet.create_category(**payload)
        except AppError as exc:
            show_error(self, str(exc))
            return
        self.accept()


class BudgetDialog(QDialog):
    def __init__(self, app, parent=None, period=None):
        super().__init__(parent)
        self.app = app
        self.period = period or date.today().strftime("%Y-%m")
        self.setWindowTitle(f"Бюджет на {self.period}")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.category = QComboBox()
        for cat in app.wallet.list_categories(EXPENSE):
            self.category.addItem(cat["name"], cat["id"])
        form.addRow("Категория", self.category)

        self.limit = QLineEdit()
        self.limit.setPlaceholderText("например, 20000")
        form.addRow("Лимит на месяц", self.limit)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        try:
            self.app.wallet.set_budget(
                self.category.currentData(), self.period, self.limit.text()
            )
        except AppError as exc:
            show_error(self, str(exc))
            return
        self.accept()

