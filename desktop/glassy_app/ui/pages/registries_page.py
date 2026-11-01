"""Registries page: user-defined tables for arbitrary data arrays.

The user picks a template or defines their own columns, then records rows.
Columns can be added later without losing data, because values live in a JSON
document per row.
"""


from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from ... import terms
from ...core.errors import AppError
from ...services.registries import BUILTIN_TEMPLATES
from ..base_page import BasePage
from ..dialogs import confirm, show_error, show_info
from ..widgets.common import Card, SectionHeader, title_label


class RegistriesPage(BasePage):
    title = terms.SECTION_TITLES["registries"]
    subtitle = terms.SECTION_SUBTITLES["registries"]

    def build(self):
        self.header = SectionHeader(self.title, self.subtitle)
        new_button = QPushButton("Новая таблица")
        new_button.setObjectName("Primary")
        new_button.clicked.connect(self._new_registry)
        self.header.add_action(new_button)
        self.add(self.header)

        splitter = QSplitter(Qt.Horizontal)

        # -- left: registry list ----------------------------------------
        left = Card(padding=12)
        left.body().addWidget(title_label("Таблицы"))
        self.registry_list = QListWidget()
        self.registry_list.currentItemChanged.connect(self._on_registry_selected)
        left.body().addWidget(self.registry_list, 1)

        left_actions = QHBoxLayout()
        rename = QPushButton("Переименовать")
        rename.setObjectName("Ghost")
        rename.clicked.connect(self._rename_registry)
        remove = QPushButton("Удалить")
        remove.setObjectName("Danger")
        remove.clicked.connect(self._delete_registry)
        left_actions.addWidget(rename)
        left_actions.addWidget(remove)
        left.body().addLayout(left_actions)
        splitter.addWidget(left)

        # -- right: records ---------------------------------------------
        right = Card(padding=12)
        self.registry_title = QLabel("Выберите таблицу")
        self.registry_title.setObjectName("SectionTitle")
        self.registry_description = QLabel("")
        self.registry_description.setObjectName("Muted")
        self.registry_description.setWordWrap(True)
        right.body().addWidget(self.registry_title)
        right.body().addWidget(self.registry_description)

        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск записей\u2026")
        self.search.textChanged.connect(self._load_records)
        controls.addWidget(self.search, 1)

        add_record = QPushButton("Добавить запись")
        add_record.setObjectName("Primary")
        add_record.clicked.connect(self._add_record)
        controls.addWidget(add_record)

        edit_record = QPushButton("Изменить")
        edit_record.clicked.connect(self._edit_record)
        controls.addWidget(edit_record)

        delete_record = QPushButton("Удалить")
        delete_record.setObjectName("Danger")
        delete_record.clicked.connect(self._delete_record)
        controls.addWidget(delete_record)

        columns = QPushButton("Колонки\u2026")
        columns.clicked.connect(self._manage_columns)
        controls.addWidget(columns)

        export = QPushButton("Экспорт")
        export.clicked.connect(self._export)
        controls.addWidget(export)
        right.body().addLayout(controls)

        self.records_table = QTableWidget(0, 0)
        self.records_table.setAlternatingRowColors(True)
        self.records_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.records_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.records_table.verticalHeader().setVisible(False)
        self.records_table.doubleClicked.connect(self._edit_record)
        right.body().addWidget(self.records_table, 1)

        self.summary_label = QLabel()
        self.summary_label.setObjectName("Muted")
        right.body().addWidget(self.summary_label)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([260, 720])
        self.add(splitter)

        self.current_registry_id = None
        self.current_fields = []

    # -- registry list ---------------------------------------------------
    def _load_registries(self, select_id=None):
        registries = self.app.registries.list_registries()
        self.registry_list.blockSignals(True)
        self.registry_list.clear()
        for registry in registries:
            item = QListWidgetItem(
                f"{registry['title']}  ({registry['record_count']})"
            )
            item.setData(Qt.UserRole, registry["id"])
            self.registry_list.addItem(item)
        self.registry_list.blockSignals(False)

        if not registries:
            self.current_registry_id = None
            self.registry_title.setText("Пока нет таблиц")
            self.registry_description.setText(
                "Создайте таблицу или возьмите шаблон: инвентарь, контакты, "
                "показания счётчиков, журнал автомобиля."
            )
            self.records_table.setRowCount(0)
            self.records_table.setColumnCount(0)
            self.summary_label.clear()
            return

        target = select_id or self.current_registry_id
        index = 0
        if target:
            for row in range(self.registry_list.count()):
                if self.registry_list.item(row).data(Qt.UserRole) == target:
                    index = row
                    break
        self.registry_list.setCurrentRow(index)
        self._on_registry_selected(self.registry_list.currentItem())

    def _on_registry_selected(self, item):
        if item is None:
            return
        self.current_registry_id = item.data(Qt.UserRole)
        registry = self.app.registries.get_registry(self.current_registry_id)
        self.current_fields = registry["fields"]
        self.registry_title.setText(registry["title"])
        self.registry_description.setText(registry["description"] or "")
        self._load_records()

    def _new_registry(self):
        if NewRegistryDialog(self.app, self).exec() == QDialog.Accepted:
            self.refresh()

    def _rename_registry(self):
        if not self.current_registry_id:
            return
        registry = self.app.registries.get_registry(self.current_registry_id)
        text, ok = QInputDialog.getText(
            self, "Переименовать таблицу", "Название", text=registry["title"]
        )
        if not ok or not text.strip():
            return
        self.app.registries.update_registry(
            self.current_registry_id, title=text.strip()
        )
        self.refresh(self.current_registry_id)

    def _delete_registry(self):
        if not self.current_registry_id:
            return
        if not confirm(self, "Удалить таблицу и все её записи?"):
            return
        self.app.registries.delete_registry(self.current_registry_id)
        self.current_registry_id = None
        self.refresh()

    # -- records ---------------------------------------------------------
    def _load_records(self):
        if not self.current_registry_id:
            return
        registry, rows = self.app.registries.display_rows(
            self.current_registry_id, search=self.search.text().strip() or None
        )
        fields = registry["fields"]
        self.current_fields = fields

        self.records_table.setColumnCount(len(fields) + 1)
        self.records_table.setHorizontalHeaderLabels(
            [f["label"] for f in fields] + ["Обновлено"]
        )
        self.records_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col, field in enumerate(fields):
                item = QTableWidgetItem(row["display"].get(field["key"], ""))
                self.records_table.setItem(row_index, col, item)
            self.records_table.setItem(
                row_index, len(fields), QTableWidgetItem(row["updated_at"][:10])
            )
            self.records_table.item(row_index, 0).setData(Qt.UserRole, row["id"])
        header = self.records_table.horizontalHeader()
        for col in range(len(fields)):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        if fields:
            header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(len(fields), QHeaderView.ResizeToContents)

        self.summary_label.setText(f"записей: {len(rows)}")

    def _add_record(self):
        if not self.current_registry_id:
            show_info(self, "Сначала создайте или выберите таблицу.")
            return
        dialog = RecordDialog(self.app, self.current_registry_id, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh(self.current_registry_id)

    def _edit_record(self):
        record_id = self._selected_record_id()
        if not record_id:
            show_info(self, "Сначала выберите запись.")
            return
        dialog = RecordDialog(
            self.app, self.current_registry_id, self, record_id=record_id
        )
        if dialog.exec() == QDialog.Accepted:
            self.refresh(self.current_registry_id)

    def _selected_record_id(self):
        row = self.records_table.currentRow()
        if row < 0:
            return None
        item = self.records_table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _delete_record(self):
        record_id = self._selected_record_id()
        if not record_id:
            show_info(self, "Сначала выберите запись.")
            return
        if confirm(self, "Удалить эту запись?"):
            self.app.registries.delete_record(record_id)
            self.refresh(self.current_registry_id)

    def _manage_columns(self):
        if not self.current_registry_id:
            return
        if ColumnsDialog(self.app, self.current_registry_id, self).exec() == (
            QDialog.Accepted
        ):
            self.refresh(self.current_registry_id)

    def _export(self):
        if not self.current_registry_id:
            return
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт таблицы", "registry.csv",
            "Файлы CSV (*.csv);;Файлы JSON (*.json)",
        )
        if not path:
            return
        if path.lower().endswith(".json"):
            content = self.app.registries.export_json(self.current_registry_id)
        else:
            content = self.app.registries.export_csv(self.current_registry_id)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        show_info(self, f"Экспортировано в:\n{path}")

    def refresh(self, select_id=None):
        self._load_registries(select_id)


class NewRegistryDialog(QDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("Новая таблица")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.template = QComboBox()
        self.template.addItem("С нуля", None)
        for key, spec in BUILTIN_TEMPLATES.items():
            self.template.addItem(spec["title"], key)
        form.addRow("Шаблон", self.template)

        self.name = QLineEdit()
        self.name.setPlaceholderText("короткое_имя, буквы и подчёркивания")
        form.addRow("Имя", self.name)

        self.title_input = QLineEdit()
        form.addRow("Название", self.title_input)

        self.description = QLineEdit()
        form.addRow("Описание", self.description)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save(self):
        template = self.template.currentData()
        name = self.name.text().strip() or (template or "")
        if not name:
            show_error(self, "Укажите короткое имя таблицы, например «tools».")
            return
        try:
            if template and not self.name.text().strip():
                self.app.registries.create_from_template(template, name=name)
            else:
                self.app.registries.create_registry(
                    name=name,
                    title=self.title_input.text().strip() or name,
                    description=self.description.text().strip(),
                    template=template,
                )
        except AppError as exc:
            show_error(self, str(exc))
            return
        self.accept()


class ColumnsDialog(QDialog):
    """Add, rename and remove columns of a registry."""

    def __init__(self, app, registry_id, parent=None):
        super().__init__(parent)
        self.app = app
        self.registry_id = registry_id
        self.setWindowTitle("Колонки")
        self.setMinimumWidth(560)
        self.setMinimumHeight(420)

        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Имя", "Подпись", "Тип", "Обязательное"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table, 1)

        row = QHBoxLayout()
        add = QPushButton("Добавить колонку")
        add.setObjectName("Primary")
        add.clicked.connect(self._add)
        remove = QPushButton("Удалить")
        remove.setObjectName("Danger")
        remove.clicked.connect(self._remove)
        row.addWidget(add)
        row.addWidget(remove)
        row.addStretch(1)
        layout.addLayout(row)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self._load()

    def _load(self):
        fields = self.app.registries.get_registry(self.registry_id)["fields"]
        self.table.setRowCount(len(fields))
        for index, field in enumerate(fields):
            key_item = QTableWidgetItem(field["key"])
            key_item.setData(Qt.UserRole, field["id"])
            self.table.setItem(index, 0, key_item)
            self.table.setItem(index, 1, QTableWidgetItem(field["label"]))
            type_combo = QComboBox()
            for value in ("text", "number", "money", "date", "bool", "select",
                          "multiline"):
                type_combo.addItem(terms.label(terms.FIELD_TYPES, value, value), value)
            pos = type_combo.findData(field["type"])
            if pos >= 0:
                type_combo.setCurrentIndex(pos)
            type_combo.currentIndexChanged.connect(
                lambda _, fid=field["id"], combo=type_combo: self._change_type(
                    fid, combo.currentData()
                )
            )
            self.table.setCellWidget(index, 2, type_combo)
            check = QCheckBox()
            check.setChecked(bool(field["required"]))
            check.stateChanged.connect(
                lambda _, fid=field["id"], box=check: self._change_required(
                    fid, box.isChecked()
                )
            )
            self.table.setCellWidget(index, 3, check)

    def _add(self):
        dialog = FieldDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            self.app.registries.add_field(
                self.registry_id,
                dialog.key.text(),
                dialog.label.text(),
                dialog.type.currentData(),
                dialog.required.isChecked(),
            )
        except AppError as exc:
            show_error(self, str(exc))
            return
        self._load()

    def _remove(self):
        row = self.table.currentRow()
        if row < 0:
            return
        field_id = self.table.item(row, 0).data(Qt.UserRole)
        if not confirm(
            self,
            "Удалить колонку? Значения останутся в базе, но перестанут "
            "показываться.",
        ):
            return
        self.app.registries.delete_field(field_id)
        self._load()

    def _change_type(self, field_id, type_value):
        self.app.registries.update_field(field_id, type=type_value)

    def _change_required(self, field_id, required):
        self.app.registries.update_field(field_id, required=required)


class FieldDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новая колонка")
        self.setMinimumWidth(340)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.key = QLineEdit()
        form.addRow("Имя", self.key)

        self.label = QLineEdit()
        form.addRow("Подпись", self.label)

        self.type = QComboBox()
        for value in ("text", "number", "money", "date", "bool", "select",
                      "multiline"):
            self.type.addItem(terms.label(terms.FIELD_TYPES, value, value), value)
        form.addRow("Тип", self.type)

        self.required = QCheckBox("Обязательное")
        form.addRow("", self.required)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class RecordDialog(QDialog):
    """Add or edit one row, rendering a widget per column type."""

    def __init__(self, app, registry_id, parent=None, record_id=None):
        super().__init__(parent)
        self.app = app
        self.registry_id = registry_id
        self.record_id = record_id
        self.widgets = {}
        self.setWindowTitle("Изменить запись" if record_id else "Новая запись")
        self.setMinimumWidth(430)

        registry = app.registries.get_registry(registry_id)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        existing = {}
        if record_id:
            for record in app.registries.list_records(registry_id):
                if record["id"] == record_id:
                    existing = record["data"]
                    break

        for field in registry["fields"]:
            value = existing.get(field["key"], "")
            if field["type"] == "bool":
                widget = QCheckBox()
                widget.setChecked(bool(value))
            elif field["type"] == "date":
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                widget.setDisplayFormat("dd.MM.yyyy")
                widget.setDate(QDate.currentDate())
                if value:
                    widget.setDate(QDate.fromString(value, "yyyy-MM-dd"))
            elif field["type"] == "money":
                widget = QLineEdit()
                if value not in ("", None):
                    from ...core import money

                    widget.setText(str(money.to_decimal(int(value))))
            elif field["type"] == "multiline":
                widget = QTextEdit()
                widget.setFixedHeight(70)
                widget.setPlainText(str(value or ""))
            elif field["type"] == "select":
                widget = QComboBox()
                for option in field.get("options") or []:
                    widget.addItem(option, option)
            else:
                widget = QLineEdit(str(value or ""))
            label = field["label"] + (" *" if field["required"] else "")
            self.widgets[field["key"]] = (widget, field)
            form.addRow(label, widget)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _collect(self):
        data = {}
        for key, (widget, field) in self.widgets.items():
            if field["type"] == "bool":
                data[key] = widget.isChecked()
            elif field["type"] == "date":
                data[key] = widget.date().toString("yyyy-MM-dd")
            elif field["type"] == "multiline":
                data[key] = widget.toPlainText()
            elif field["type"] == "select":
                data[key] = widget.currentData()
            else:
                data[key] = widget.text()
        return data

    def _save(self):
        data = self._collect()
        try:
            if self.record_id:
                self.app.registries.update_record(
                    self.registry_id, self.record_id, data
                )
            else:
                self.app.registries.add_record(self.registry_id, data)
        except AppError as exc:
            show_error(self, str(exc))
            return
        self.accept()
