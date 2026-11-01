"""Registry service: user-defined tables for arbitrary data arrays.

A registry is a named table whose columns the user creates at runtime. Values
are validated against the declared field type before they are stored, so a
money column always holds a parseable amount and a date column a real date.
"""

import csv
import io
import json

from ..core import money
from ..core.errors import ConflictError, NotFoundError, ValidationError
from ..core.models import Registry, RegistryField, validate_iso_date
from ..repositories.library import RegistryRepository

BUILTIN_TEMPLATES = {
    "inventory": {
        "title": "Инвентарь",
        "description": "Вещи с количеством и стоимостью.",
        "icon": "box",
        "fields": [
            {"key": "name", "label": "Название", "type": "text", "required": True},
            {"key": "qty", "label": "Кол-во", "type": "number"},
            {"key": "price", "label": "Цена за единицу", "type": "money"},
            {"key": "place", "label": "Место", "type": "text"},
            {"key": "bought", "label": "Куплено", "type": "date"},
        ],
    },
    "contacts": {
        "title": "Контакты",
        "description": "Люди и способы связи с ними.",
        "icon": "user",
        "fields": [
            {"key": "name", "label": "Имя", "type": "text", "required": True},
            {"key": "phone", "label": "Телефон", "type": "text"},
            {"key": "email", "label": "Почта", "type": "text"},
            {"key": "note", "label": "Заметка", "type": "multiline"},
        ],
    },
    "readings": {
        "title": "Показания счётчиков",
        "description": "Коммунальные счётчики по датам.",
        "icon": "gauge",
        "fields": [
            {"key": "meter", "label": "Счётчик", "type": "text", "required": True},
            {"key": "value", "label": "Показание", "type": "number"},
            {"key": "taken_on", "label": "Дата снятия", "type": "date"},
        ],
    },
    "vehicles": {
        "title": "Журнал автомобиля",
        "description": "Топливо, обслуживание и пробег.",
        "icon": "car",
        "fields": [
            {"key": "vehicle", "label": "Автомобиль", "type": "text", "required": True},
            {"key": "odometer", "label": "Пробег", "type": "number"},
            {"key": "litres", "label": "Литров", "type": "number"},
            {"key": "cost", "label": "Стоимость", "type": "money"},
            {"key": "serviced_on", "label": "Дата", "type": "date"},
            {"key": "done", "label": "Оплачено", "type": "bool"},
        ],
    },
}


class RegistryService:
    def __init__(self, db):
        self.db = db
        self.repo = RegistryRepository(db)

    # -- registries -----------------------------------------------------
    def list_registries(self):
        return self.repo.all_with_counts()

    def get_registry(self, registry_id):
        row = self.repo.get(registry_id)
        if not row:
            raise NotFoundError("Таблица не найдена")
        row["fields"] = self.repo.fields(registry_id)
        return row

    def get_by_name(self, name):
        row = self.repo.by_name(name)
        if not row:
            return None
        row["fields"] = self.repo.fields(row["id"])
        return row

    def create_registry(self, name, title="", description="", icon="table",
                        fields=None, template=None):
        if template:
            spec = BUILTIN_TEMPLATES.get(template)
            if spec is None:
                raise ValidationError(f"Неизвестный шаблон: {template!r}")
            title = title or spec["title"]
            description = description or spec["description"]
            icon = spec.get("icon", icon)
            fields = [
                RegistryField(**f) for f in spec["fields"]
            ] if fields is None else fields
        if self.repo.by_name(name):
            raise ConflictError(f"Таблица с именем {name!r} уже есть")
        registry = Registry(
            name=name,
            title=title or name,
            description=description,
            icon=icon,
            fields=list(fields or []),
        )
        return self.repo.create(registry)

    def create_from_template(self, template, name=None):
        return self.create_registry(
            name=name or template, template=template
        )

    def update_registry(self, registry_id, **kwargs):
        current = self.get_registry(registry_id)
        registry = Registry(
            id=registry_id,
            name=kwargs.get("name", current["name"]),
            title=kwargs.get("title", current["title"]),
            description=kwargs.get("description", current["description"]),
            icon=kwargs.get("icon", current["icon"]),
        )
        return self.repo.update(registry)

    def delete_registry(self, registry_id):
        self.repo.delete(registry_id)

    # -- fields ---------------------------------------------------------
    def add_field(self, registry_id, key, label, type_="text", required=False,
                  options=None):
        field = RegistryField(
            key=key, label=label or key, type=type_, required=required,
            options=options or [],
        )
        try:
            return self.repo.add_field(registry_id, field)
        except Exception as exc:
            if "UNIQUE" in str(exc):
                raise ConflictError(f"Поле с именем {key!r} уже есть")
            raise

    def update_field(self, field_id, **kwargs):
        current = self.db.query_one(
            "SELECT * FROM registry_fields WHERE id=?", (field_id,)
        )
        if not current:
            raise NotFoundError("Поле не найдено")
        try:
            options = json.loads(current["options"] or "[]")
        except (ValueError, TypeError):
            options = []
        field = RegistryField(
            key=kwargs.get("key", current["key"]),
            label=kwargs.get("label", current["label"]),
            type=kwargs.get("type", current["type"]),
            required=kwargs.get("required", bool(current["required"])),
            options=kwargs.get("options", options),
            position=kwargs.get("position", current["position"]),
        )
        self.repo.update_field(field_id, field)

    def delete_field(self, field_id):
        self.repo.delete_field(field_id)

    # -- records --------------------------------------------------------
    def validate_record(self, registry_id, data):
        """Coerce and check a record against the registry field definitions.

        Returns a cleaned dict. Money is stored as an integer string of minor
        units so that totals can be summed exactly later.
        """
        fields = self.repo.fields(registry_id)
        cleaned = {}
        for field in fields:
            key = field["key"]
            raw = data.get(key)
            ftype = field["type"]
            if ftype == "bool":
                cleaned[key] = bool(raw)
                continue
            text = "" if raw is None else str(raw).strip()
            if not text:
                if field["required"]:
                    raise ValidationError(
                        f"Поле «{field['label']}» обязательно", field=key
                    )
                cleaned[key] = ""
                continue
            if ftype == "money":
                try:
                    cleaned[key] = str(money.to_minor(text))
                except ValidationError:
                    raise ValidationError(
                        f"Поле «{field['label']}» должно быть суммой", field=key
                    )
            elif ftype == "number":
                try:
                    cleaned[key] = str(float(text.replace(",", ".")))
                except ValueError:
                    raise ValidationError(
                        f"Поле «{field['label']}» должно быть числом", field=key
                    )
            elif ftype == "date":
                cleaned[key] = validate_iso_date(text, field["label"])
            elif ftype == "select":
                options = field.get("options") or []
                if options and text not in options:
                    raise ValidationError(
                        f"Поле «{field['label']}» должно быть одним из: {', '.join(options)}",
                        field=key,
                    )
                cleaned[key] = text
            else:
                cleaned[key] = text
        return cleaned

    def add_record(self, registry_id, data):
        cleaned = self.validate_record(registry_id, data)
        return self.repo.add_record(registry_id, cleaned)

    def update_record(self, registry_id, record_id, data):
        cleaned = self.validate_record(registry_id, data)
        self.repo.update_record(record_id, cleaned)

    def delete_record(self, record_id):
        self.repo.delete_record(record_id)

    def list_records(self, registry_id, search=None):
        return self.repo.records(registry_id, search=search)

    def display_rows(self, registry_id, search=None):
        """Records rendered as strings according to their field types."""
        registry = self.get_registry(registry_id)
        fields = registry["fields"]
        rows = []
        for record in self.list_records(registry_id, search=search):
            display = {}
            for field in fields:
                value = record["data"].get(field["key"], "")
                display[field["key"]] = self._display_value(value, field)
            rows.append({
                "id": record["id"],
                "data": record["data"],
                "display": display,
                "created_at": record.get("created_at", ""),
                "updated_at": record.get("updated_at", ""),
            })
        return registry, rows

    @staticmethod
    def _display_value(value, field):
        if field["type"] == "money" and value not in ("", None):
            try:
                return money.format_amount(int(value))
            except (TypeError, ValueError):
                return str(value)
        if field["type"] == "bool":
            return "\u2713" if value else "\u2014"
        if field["type"] == "number" and value not in ("", None):
            try:
                number = float(value)
                if number.is_integer():
                    return str(int(number))
                return f"{number:g}"
            except (TypeError, ValueError):
                return str(value)
        return str(value)

    def numeric_total(self, registry_id, field_key):
        """Sum a money or number column across a registry."""
        field = self.db.query_one(
            "SELECT * FROM registry_fields WHERE registry_id=? AND key=?",
            (registry_id, field_key),
        )
        if not field:
            return 0
        rows = self.repo.records(registry_id)
        total = 0
        for row in rows:
            value = row["data"].get(field_key)
            if value in ("", None):
                continue
            try:
                total += float(value)
            except (TypeError, ValueError):
                continue
        if field["type"] == "money":
            return int(total)
        return total

    # -- import / export ------------------------------------------------
    def export_csv(self, registry_id):
        registry, rows = self.display_rows(registry_id)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([f["label"] for f in registry["fields"]])
        for row in rows:
            writer.writerow(
                [row["display"].get(f["key"], "") for f in registry["fields"]]
            )
        return buffer.getvalue()

    def export_json(self, registry_id):
        registry = self.get_registry(registry_id)
        rows = self.repo.records(registry_id)
        return json.dumps(
            {
                # Money values are already integer minor units in the store.
                # This flag tells the importer not to re-parse them.
                "normalized": True,
                "registry": {
                    "name": registry["name"],
                    "title": registry["title"],
                    "description": registry["description"],
                    "fields": [
                        {
                            "key": f["key"],
                            "label": f["label"],
                            "type": f["type"],
                            "required": f["required"],
                            "options": f["options"],
                        }
                        for f in registry["fields"]
                    ],
                },
                "records": [r["data"] for r in rows],
            },
            ensure_ascii=False,
            indent=2,
        )

    def import_json(self, payload):
        """Import a registry previously produced by :meth:`export_json`."""
        if isinstance(payload, str):
            payload = json.loads(payload)
        spec = payload.get("registry") or {}
        name = spec.get("name")
        if not name:
            raise ValidationError("В импортируемых данных нет имени таблицы")
        existing = self.get_by_name(name)
        if existing:
            registry_id = existing["id"]
        else:
            registry_id = self.create_registry(
                name=name,
                title=spec.get("title", name),
                description=spec.get("description", ""),
                fields=[RegistryField(**f) for f in spec.get("fields", [])],
            )
        # A file we produced ourselves is already normalised, so its money
        # values must be stored verbatim. Parsing them again would multiply
        # every amount by 100.
        already_normalized = bool(payload.get("normalized"))
        imported = 0
        for record in payload.get("records", []):
            try:
                if already_normalized:
                    self._store_normalized(registry_id, record)
                else:
                    self.add_record(registry_id, record)
                imported += 1
            except ValidationError:
                continue
        return registry_id, imported

    def _store_normalized(self, registry_id, record):
        """Store an already-typed record, checking required fields only."""
        fields = self.repo.fields(registry_id)
        cleaned = {}
        for field in fields:
            key = field["key"]
            value = record.get(key)
            if field["type"] == "bool":
                cleaned[key] = bool(value)
                continue
            text = "" if value is None else str(value).strip()
            if not text:
                if field["required"]:
                    raise ValidationError(
                        f"Поле «{field['label']}» обязательно", field=key
                    )
                cleaned[key] = ""
                continue
            if field["type"] == "money":
                try:
                    cleaned[key] = str(int(value))
                except (TypeError, ValueError):
                    raise ValidationError(
                        f"Поле «{field['label']}» должно быть суммой", field=key
                    )
            elif field["type"] == "date":
                cleaned[key] = validate_iso_date(text, field["label"])
            else:
                cleaned[key] = text
        self.repo.add_record(registry_id, cleaned)
