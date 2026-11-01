"""Workbook and task services."""

from ..core.errors import NotFoundError
from ..core.models import Task, WorkbookEntry, now_iso
from ..repositories.library import TaskRepository, WorkbookRepository

DEFAULT_TASK_STATUSES = ("todo", "doing", "done")


class WorkbookService:
    """Free-form notes, journals and reference pages."""

    def __init__(self, db):
        self.db = db
        self.entries = WorkbookRepository(db)

    def list_entries(self, text=None, kind=None):
        return self.entries.search(text=text, kind=kind)

    def get_entry(self, entry_id):
        row = self.entries.get(entry_id)
        if not row:
            raise NotFoundError("Запись не найдена")
        return row

    def create_entry(self, title, body="", kind="note", tags="", pinned=False):
        return self.entries.create(
            WorkbookEntry(
                title=title, body=body, kind=kind, tags=tags, pinned=pinned
            )
        )

    def update_entry(self, entry_id, title, body="", kind="note", tags="",
                     pinned=False):
        entry = WorkbookEntry(
            id=entry_id, title=title, body=body, kind=kind, tags=tags,
            pinned=pinned,
        )
        return self.entries.update(entry)

    def toggle_pin(self, entry_id):
        row = self.get_entry(entry_id)
        self.db.execute(
            "UPDATE workbook_entries SET pinned=?, updated_at=? WHERE id=?",
            (0 if row["pinned"] else 1, now_iso(), entry_id),
        )

    def delete_entry(self, entry_id):
        self.entries.delete(entry_id)

    def seed_defaults(self):
        if self.entries.count() == 0:
            self.entries.create(
                WorkbookEntry(
                    title="Добро пожаловать в заметки",
                    body=(
                        "Здесь можно хранить что угодно: планы, списки дел, "
                        "записи встреч или дневник.\n\n"
                        "Запись сохраняется сразу после нажатия «Сохранить» и "
                        "хранится в той же базе, что и остальные данные."
                    ),
                    kind="note",
                    tags="с-чего-начать",
                    pinned=True,
                )
            )


class TaskService:
    """Lightweight task tracker, also surfaced on the dashboard."""

    def __init__(self, db):
        self.db = db
        self.tasks = TaskRepository(db)

    def list_tasks(self, text=None, status=None, priority=None):
        return self.tasks.search(text=text, status=status, priority=priority)

    def get_task(self, task_id):
        row = self.tasks.get(task_id)
        if not row:
            raise NotFoundError("Задача не найдена")
        return row

    def create_task(self, title, notes="", status="todo", priority="medium",
                    due_on="", tags=""):
        return self.tasks.create(
            Task(
                title=title, notes=notes, status=status, priority=priority,
                due_on=due_on, tags=tags,
            )
        )

    def update_task(self, task_id, **kwargs):
        current = self.get_task(task_id)
        merged = {k: current.get(k) for k in ("title", "notes", "status",
                                              "priority", "due_on", "tags",
                                              "completed_at")}
        merged.update({k: v for k, v in kwargs.items() if v is not None})
        task = Task(id=task_id, **merged)
        return self.tasks.update(task)

    def set_status(self, task_id, status):
        current = self.get_task(task_id)
        completed = now_iso() if status == "done" else None
        self.db.execute(
            "UPDATE tasks SET status=?, completed_at=?, updated_at=? WHERE id=?",
            (status, completed, now_iso(), task_id),
        )
        return current

    def delete_task(self, task_id):
        self.tasks.delete(task_id)

    def stats(self):
        return self.tasks.stats()

    def due_soon(self, days=7):
        return self.db.query(
            """
            SELECT * FROM tasks
            WHERE status != 'done'
              AND due_on != ''
              AND due_on <= date('now', ?)
            ORDER BY due_on
            """,
            (f"+{int(days)} days",),
        )

    def seed_defaults(self):
        if self.tasks.count() == 0:
            self.tasks.create(
                Task(
                    title="Создайте первую таблицу",
                    notes=(
                        "Откройте раздел «Таблицы» и выберите шаблон, "
                        "например «Инвентарь» или «Показания счётчиков»."
                    ),
                    priority="medium",
                )
            )
