"""Domain models.

Plain dataclasses with light validation. They are deliberately free of any
database or Qt dependency so they can be unit tested in isolation and reused
by importers/exporters.
"""

from dataclasses import dataclass, field, asdict
from datetime import date, datetime

from .errors import ValidationError

INCOME = "income"
EXPENSE = "expense"
KINDS = (INCOME, EXPENSE)

TASK_STATUSES = ("todo", "doing", "done")
TASK_PRIORITIES = ("low", "medium", "high")
COURSE_STATUSES = ("planned", "active", "paused", "done", "dropped")

FIELD_TYPES = (
    "text",
    "number",
    "money",
    "date",
    "bool",
    "select",
    "multiline",
)


def today_iso():
    return date.today().isoformat()


def now_iso():
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def _clean_str(value, default=""):
    if value is None:
        return default
    return str(value).strip()


def validate_iso_date(value, field_name="date", allow_empty=True):
    """Return a normalised ``YYYY-MM-DD`` string or raise ValidationError."""
    text = _clean_str(value)
    if not text:
        if allow_empty:
            return ""
        raise ValidationError(f"Поле «{field_name}» обязательно", field=field_name)
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(
            f"{field_name}: нужна дата в виде ГГГГ-ММ-ДД, получено {text!r}",
            field=field_name,
        )
    return parsed.isoformat()


def validate_period(value):
    """Return a normalised ``YYYY-MM`` string or raise ValidationError."""
    text = _clean_str(value)
    try:
        datetime.strptime(text, "%Y-%m")
    except ValueError:
        raise ValidationError(
            f"Период должен быть в виде ГГГГ-ММ, получено {text!r}", field="period"
        )
    return text


@dataclass
class Account:
    name: str
    kind: str = "cash"
    currency: str = "RUB"
    opening: int = 0
    archived: bool = False
    note: str = ""
    id: int | None = None
    created_at: str = ""
    updated_at: str = ""

    def validate(self):
        self.name = _clean_str(self.name)
        if not self.name:
            raise ValidationError("Укажите название счёта", field="name")
        self.kind = _clean_str(self.kind, "cash") or "cash"
        self.currency = (_clean_str(self.currency, "RUB") or "RUB").upper()
        self.note = _clean_str(self.note)
        # An int is already minor units; anything else ("1000", 1000.5) is a
        # major-unit amount the caller typed and must be parsed exactly.
        if not isinstance(self.opening, int) or isinstance(self.opening, bool):
            from . import money

            self.opening = money.to_minor(self.opening or 0)
        return self


@dataclass
class Category:
    name: str
    kind: str = EXPENSE
    color: str = "#7c3aed"
    parent_id: int | None = None
    archived: bool = False
    id: int | None = None
    created_at: str = ""
    updated_at: str = ""

    def validate(self):
        self.name = _clean_str(self.name)
        if not self.name:
            raise ValidationError("Укажите название категории", field="name")
        if self.kind not in KINDS:
            raise ValidationError(
                f"Тип категории должен быть одним из: {KINDS}", field="kind"
            )
        return self


@dataclass
class Transaction:
    account_id: int
    kind: str
    amount: int
    occurred_on: str = field(default_factory=today_iso)
    category_id: int | None = None
    payee: str = ""
    note: str = ""
    id: int | None = None
    created_at: str = ""
    updated_at: str = ""

    def validate(self):
        if self.kind not in KINDS:
            raise ValidationError(
                f"Transaction kind must be one of {KINDS}", field="kind"
            )
        if not self.account_id:
            raise ValidationError("Выберите счёт", field="account_id")
        self.amount = int(self.amount or 0)
        if self.amount <= 0:
            raise ValidationError("Сумма должна быть больше нуля", field="amount")
        self.occurred_on = validate_iso_date(
            self.occurred_on, "Дата", allow_empty=False
        )
        self.payee = _clean_str(self.payee)
        self.note = _clean_str(self.note)
        return self


@dataclass
class Budget:
    category_id: int
    period: str
    limit_minor: int
    id: int | None = None
    created_at: str = ""
    updated_at: str = ""

    def validate(self):
        if not self.category_id:
            raise ValidationError("Выберите категорию", field="category_id")
        self.period = validate_period(self.period)
        self.limit_minor = int(self.limit_minor or 0)
        if self.limit_minor < 0:
            raise ValidationError("Лимит бюджета не может быть отрицательным", field="limit_minor")
        return self


@dataclass
class Course:
    title: str
    provider: str = ""
    url: str = ""
    status: str = "planned"
    total_units: int = 0
    done_units: int = 0
    cost: int = 0
    currency: str = "RUB"
    started_on: str = ""
    finished_on: str = ""
    rating: int = 0
    note: str = ""
    id: int | None = None
    created_at: str = ""
    updated_at: str = ""

    def validate(self):
        self.title = _clean_str(self.title)
        if not self.title:
            raise ValidationError("Укажите название курса", field="title")
        if self.status not in COURSE_STATUSES:
            raise ValidationError(
                f"Статус должен быть одним из: {COURSE_STATUSES}", field="status"
            )
        self.total_units = max(0, int(self.total_units or 0))
        self.done_units = max(0, int(self.done_units or 0))
        if self.total_units and self.done_units > self.total_units:
            raise ValidationError(
                "Пройдено не может быть больше, чем всего", field="done_units"
            )
        self.cost = max(0, int(self.cost or 0))
        self.rating = int(self.rating or 0)
        if not 0 <= self.rating <= 5:
            raise ValidationError("Оценка должна быть от 0 до 5", field="rating")
        self.started_on = validate_iso_date(self.started_on, "Дата начала")
        self.finished_on = validate_iso_date(self.finished_on, "Дата окончания")
        self.provider = _clean_str(self.provider)
        self.url = _clean_str(self.url)
        self.note = _clean_str(self.note)
        self.currency = (_clean_str(self.currency, "RUB") or "RUB").upper()
        return self

    @property
    def progress_percent(self):
        if not self.total_units:
            return 100.0 if self.status == "done" else 0.0
        return min(100.0, self.done_units / self.total_units * 100.0)


@dataclass
class StudySession:
    course_id: int
    minutes: int = 0
    units_done: int = 0
    occurred_on: str = field(default_factory=today_iso)
    note: str = ""
    id: int | None = None
    created_at: str = ""
    updated_at: str = ""

    def validate(self):
        if not self.course_id:
            raise ValidationError("Выберите курс", field="course_id")
        self.minutes = max(0, int(self.minutes or 0))
        self.units_done = max(0, int(self.units_done or 0))
        if self.minutes == 0 and self.units_done == 0:
            raise ValidationError(
                "Укажите минуты или пройденные единицы", field="minutes"
            )
        self.occurred_on = validate_iso_date(
            self.occurred_on, "Дата", allow_empty=False
        )
        self.note = _clean_str(self.note)
        return self


@dataclass
class RegistryField:
    key: str
    label: str
    type: str = "text"
    required: bool = False
    options: list = field(default_factory=list)
    position: int = 0
    id: int | None = None

    def validate(self):
        self.key = _clean_str(self.key)
        self.label = _clean_str(self.label) or self.key
        if not self.key:
            raise ValidationError("Укажите имя поля", field="key")
        if not self.key.replace("_", "").isalnum():
            raise ValidationError(
                "Имя поля может содержать только буквы, цифры и подчёркивания",
                field="key",
            )
        if self.type not in FIELD_TYPES:
            raise ValidationError(
                f"Тип поля должен быть одним из: {FIELD_TYPES}", field="type"
            )
        return self


@dataclass
class Registry:
    name: str
    title: str = ""
    description: str = ""
    icon: str = "table"
    fields: list = field(default_factory=list)
    id: int | None = None
    created_at: str = ""
    updated_at: str = ""

    def validate(self):
        self.name = _clean_str(self.name)
        if not self.name:
            raise ValidationError("Укажите название таблицы", field="name")
        if not self.name.replace("_", "").replace("-", "").isalnum():
            raise ValidationError(
                "Название таблицы может содержать только буквы, цифры, дефисы "
                "и подчёркивания",
                field="name",
            )
        self.title = _clean_str(self.title) or self.name
        self.description = _clean_str(self.description)
        return self


@dataclass
class WorkbookEntry:
    title: str
    body: str = ""
    kind: str = "note"
    tags: str = ""
    pinned: bool = False
    id: int | None = None
    created_at: str = ""
    updated_at: str = ""

    def validate(self):
        self.title = _clean_str(self.title)
        if not self.title:
            raise ValidationError("Укажите заголовок", field="title")
        self.body = self.body or ""
        self.kind = _clean_str(self.kind, "note") or "note"
        self.tags = _clean_str(self.tags)
        return self


@dataclass
class Task:
    title: str
    notes: str = ""
    status: str = "todo"
    priority: str = "medium"
    due_on: str = ""
    tags: str = ""
    id: int | None = None
    created_at: str = ""
    updated_at: str = ""
    completed_at: str | None = None

    def validate(self):
        self.title = _clean_str(self.title)
        if not self.title:
            raise ValidationError("Укажите название задачи", field="title")
        if self.status not in TASK_STATUSES:
            raise ValidationError(
                f"Статус должен быть одним из: {TASK_STATUSES}", field="status"
            )
        if self.priority not in TASK_PRIORITIES:
            raise ValidationError(
                f"Приоритет должен быть одним из: {TASK_PRIORITIES}", field="priority"
            )
        self.due_on = validate_iso_date(self.due_on, "Срок")
        self.notes = _clean_str(self.notes)
        self.tags = _clean_str(self.tags)
        return self

    @property
    def is_overdue(self):
        if self.status == "done" or not self.due_on:
            return False
        return self.due_on < today_iso()

    def to_dict(self):
        data = asdict(self)
        data["is_overdue"] = self.is_overdue
        return data
