"""Dashboard page: the aggregated home screen."""

from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ... import terms
from ...core import money
from ...core.models import INCOME
from ..base_page import BasePage
from ..widgets.common import (
    BarChart,
    Card,
    DonutChart,
    ProgressRow,
    SectionHeader,
    StatCard,
    TagLabel,
    clear_layout,
    muted_label,
    title_label,
    wrap,
)


class DashboardPage(BasePage):
    title = terms.SECTION_TITLES["dashboard"]
    subtitle = terms.SECTION_SUBTITLES["dashboard"]

    def build(self):
        self.header = SectionHeader(self.title, self.subtitle)
        self.refresh_button = QPushButton("Обновить")
        self.refresh_button.setObjectName("Ghost")
        self.refresh_button.clicked.connect(self.refresh)
        self.header.add_action(self.refresh_button)
        self.add(self.header)

        # -- KPI row ----------------------------------------------------
        self.kpi_row = QHBoxLayout()
        self.kpi_row.setSpacing(12)
        self.kpi_cards = {}
        for key, title in (
            ("net_worth", "Капитал"),
            ("month_income", "Доход за месяц"),
            ("month_expense", "Расходы за месяц"),
            ("tasks", "Открытых задач"),
        ):
            card = StatCard(title)
            self.kpi_cards[key] = card
            self.kpi_row.addWidget(card)
        self.add(wrap(self.kpi_row))

        # -- charts -----------------------------------------------------
        charts = QHBoxLayout()
        charts.setSpacing(12)

        cashflow_card = Card()
        cashflow_card.add(title_label("Движение средств, 6 месяцев"))
        self.cashflow = BarChart()
        cashflow_card.add(self.cashflow)
        cashflow_card.add(
            _legend([(terms.KINDS["income"], "#7c3aed"),
                     (terms.KINDS["expense"], "#f59e0b")])
        )
        charts.addWidget(cashflow_card, 3)

        spend_card = Card()
        spend_card.add(title_label("Расходы по категориям"))
        self.donut = DonutChart()
        spend_card.add(self.donut)
        charts.addWidget(spend_card, 2)
        self.add(wrap(charts))

        # -- accounts + recent ------------------------------------------
        middle = QHBoxLayout()
        middle.setSpacing(12)

        accounts_card = Card()
        accounts_card.add(title_label("Счета"))
        self.accounts_box = QVBoxLayout()
        self.accounts_box.setSpacing(8)
        accounts_card.body().addLayout(self.accounts_box)
        middle.addWidget(accounts_card, 2)

        recent_card = Card()
        recent_card.add(title_label("Последние операции"))
        self.recent_box = QVBoxLayout()
        self.recent_box.setSpacing(8)
        recent_card.body().addLayout(self.recent_box)
        middle.addWidget(recent_card, 3)
        self.add(wrap(middle))

        # -- module summary ---------------------------------------------
        summary = QGridLayout()
        summary.setSpacing(12)
        self.learning_card = StatCard(terms.SECTION_TITLES["learning"])
        self.registry_card = StatCard(terms.SECTION_TITLES["registries"])
        self.workbook_card = StatCard(terms.SECTION_TITLES["workbook"])
        self.budget_card = Card()
        self.budget_card.add(title_label("Бюджеты на месяц"))
        self.budget_box = QVBoxLayout()
        self.budget_box.setSpacing(6)
        self.budget_card.body().addLayout(self.budget_box)
        summary.addWidget(self.learning_card, 0, 0)
        summary.addWidget(self.registry_card, 0, 1)
        summary.addWidget(self.workbook_card, 0, 2)
        summary.addWidget(self.budget_card, 1, 0, 1, 3)
        self.add(wrap(summary))

        self.add_stretch()

    def add_stretch(self):
        self.layout.addStretch(1)

    def refresh(self):
        data = self.app.dashboard.overview()
        currency = self.app.currency

        self.kpi_cards["net_worth"].set_value(
            money.format_amount(data["net_worth"], currency)
        )
        month = data["month"]
        self.kpi_cards["month_income"].set_value(
            money.format_amount(month["income"], currency),
            accent="#22c55e",
        )
        self.kpi_cards["month_expense"].set_value(
            money.format_amount(month["expense"], currency),
            accent="#ef4444",
        )
        tasks = data["tasks"]
        self.kpi_cards["tasks"].set_value(
            str(tasks["open"]),
            hint=f"просрочено: {tasks['overdue']}" if tasks["overdue"] else
                 f"готово: {tasks['done']}",
        )

        # cash flow
        series = data["cashflow"]
        if series:
            self.cashflow.set_data(
                [row["period"][5:] + "/" + row["period"][2:4] for row in series],
                [row["income"] / 100.0 for row in series],
                [row["expense"] / 100.0 for row in series],
                terms.KINDS["income"], terms.KINDS["expense"],
            )
        else:
            self.cashflow.set_data([], [], [])

        # spending donut
        slices = [
            (row["category_name"], row["total_minor"] / 100.0,
             row["category_color"])
            for row in data["expense_by_category"]
        ]
        total_expense = money.sum_minor(
            row["total_minor"] for row in data["expense_by_category"]
        )
        self.donut.set_data(
            slices,
            money.format_amount(total_expense, currency, with_symbol=False),
            "израсходовано за месяц",
        )

        # accounts
        clear_layout(self.accounts_box)
        accounts = data["accounts"]
        if not accounts:
            self.accounts_box.addWidget(muted_label("Пока нет счетов."))
        for account in accounts:
            row = QWidget()
            line = QHBoxLayout(row)
            line.setContentsMargins(0, 0, 0, 0)
            name = QLabel(account["name"])
            kind = TagLabel(terms.label(terms.ACCOUNT_KINDS, account["kind"]))
            amount = QLabel(
                money.format_amount(account["balance"], account["currency"])
            )
            amount.setStyleSheet(
                "font-weight: 600; color: "
                + ("#22c55e" if account["balance"] >= 0 else "#ef4444")
            )
            line.addWidget(name)
            line.addWidget(kind)
            line.addStretch(1)
            line.addWidget(amount)
            self.accounts_box.addWidget(row)

        # recent transactions
        clear_layout(self.recent_box)
        recent = data["recent_transactions"]
        if not recent:
            self.recent_box.addWidget(muted_label("Пока нет операций."))
        for tx in recent:
            row = QWidget()
            line = QHBoxLayout(row)
            line.setContentsMargins(0, 0, 0, 0)
            left = QVBoxLayout()
            left.setSpacing(1)
            caption = QLabel(tx["payee"] or tx["category_name"] or "Операция")
            meta = QLabel(f"{tx['occurred_on']}  \u00b7  {tx['account_name'] or ''}")
            meta.setObjectName("Muted")
            left.addWidget(caption)
            left.addWidget(meta)
            line.addLayout(left, 1)
            amount = QLabel(
                money.format_amount(
                    tx["amount"], currency, sign=True
                )
                if tx["kind"] == INCOME
                else money.format_amount(tx["amount"], currency)
            )
            amount.setStyleSheet(
                "font-weight: 600; color: "
                + ("#22c55e" if tx["kind"] == INCOME else "#ef4444")
            )
            line.addWidget(amount)
            self.recent_box.addWidget(row)

        # module summaries
        learning = data["learning"]
        self.learning_card.set_value(
            f"{learning['hours']} h",
            hint=f"в процессе: {learning['active']} \u00b7 "
                 f"завершено: {learning['finished']}",
        )
        registries = data["registries"]
        self.registry_card.set_value(
            str(registries["tables"]),
            hint=f"записей: {registries['records']}",
        )
        self.workbook_card.set_value(
            str(data["workbook"]["entries"]), hint="записей в заметках"
        )

        # budgets
        clear_layout(self.budget_box)
        start, _ = self.app.wallet.month_bounds()
        period = start[:7]
        budgets = self.app.wallet.list_budgets(period)
        if not budgets:
            self.budget_box.addWidget(
                muted_label("На этот месяц бюджеты не заданы. Добавьте их в разделе «Кошелёк».")
            )
        for budget in budgets:
            limit = budget["limit_minor"] or 0
            spent = budget["spent_minor"] or 0
            percent = (spent / limit * 100.0) if limit else 0.0
            colour = "#22c55e"
            if percent > 100:
                colour = "#ef4444"
            elif percent > 80:
                colour = "#f59e0b"
            self.budget_box.addWidget(
                ProgressRow(
                    budget["category_name"],
                    f"{money.format_amount(spent, currency, with_symbol=False)}"
                    f" / {money.format_amount(limit, currency, with_symbol=False)}",
                    percent,
                    colour,
                )
            )



def _legend(items):
    widget = QWidget()
    row = QHBoxLayout(widget)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(14)
    for name, colour in items:
        chip = QLabel(f"\u25cf  {name}")
        chip.setStyleSheet(f"color: {colour}; font-size: 11px;")
        row.addWidget(chip)
    row.addStretch(1)
    return widget

