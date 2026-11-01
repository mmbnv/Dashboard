"""Tasks and workbook services."""

import pytest

from glassy_app.core.errors import NotFoundError, ValidationError


def test_task_lifecycle(app):
    task_id = app.tasks.create_task("Write report", priority="high")
    task = app.tasks.get_task(task_id)
    assert task["status"] == "todo"
    assert task["priority"] == "high"

    app.tasks.set_status(task_id, "done")
    task = app.tasks.get_task(task_id)
    assert task["status"] == "done"
    assert task["completed_at"]

    app.tasks.set_status(task_id, "todo")
    assert app.tasks.get_task(task_id)["completed_at"] is None


def test_task_stats(app):
    app.tasks.create_task("a")
    app.tasks.create_task("b")
    third = app.tasks.create_task("c")
    app.tasks.set_status(third, "done")
    stats = app.tasks.stats()
    assert stats["total"] == 4  # 3 added plus the seeded one
    assert stats["done"] == 1


def test_overdue_detection(app):
    app.tasks.create_task("late", due_on="2020-01-01")
    assert app.tasks.stats()["overdue"] == 1
    app.tasks.create_task("future", due_on="2999-01-01")
    assert app.tasks.stats()["overdue"] == 1


def test_task_validation(app):
    with pytest.raises(ValidationError):
        app.tasks.create_task("")
    with pytest.raises(ValidationError):
        app.tasks.create_task("x", status="nope")
    with pytest.raises(ValidationError):
        app.tasks.create_task("x", priority="nope")
    with pytest.raises(ValidationError):
        app.tasks.create_task("x", due_on="01.01.2026")


def test_task_filters(app):
    app.tasks.create_task("alpha", priority="high")
    app.tasks.create_task("beta", priority="low")
    assert len(app.tasks.list_tasks(text="alpha")) == 1
    assert len(app.tasks.list_tasks(priority="low")) == 1
    assert len(app.tasks.list_tasks(status="done")) == 0


def test_update_task_partially(app):
    task_id = app.tasks.create_task("x", notes="first")
    app.tasks.update_task(task_id, notes="second")
    task = app.tasks.get_task(task_id)
    assert task["notes"] == "second"
    assert task["title"] == "x"


def test_missing_task_raises(app):
    with pytest.raises(NotFoundError):
        app.tasks.get_task(123456)


def test_workbook_crud(app):
    entry_id = app.workbook.create_entry("Shopping", body="milk", tags="home")
    entry = app.workbook.get_entry(entry_id)
    assert entry["title"] == "Shopping"
    assert entry["pinned"] == 0

    app.workbook.update_entry(entry_id, "Shopping", body="milk, bread")
    assert app.workbook.get_entry(entry_id)["body"] == "milk, bread"

    app.workbook.toggle_pin(entry_id)
    assert app.workbook.get_entry(entry_id)["pinned"] == 1
    app.workbook.toggle_pin(entry_id)
    assert app.workbook.get_entry(entry_id)["pinned"] == 0

    app.workbook.delete_entry(entry_id)
    with pytest.raises(NotFoundError):
        app.workbook.get_entry(entry_id)


def test_workbook_search_and_filter(app):
    app.workbook.create_entry("Alpha note", kind="note")
    app.workbook.create_entry("Beta idea", kind="idea")
    assert len(app.workbook.list_entries(text="Alpha")) == 1
    assert len(app.workbook.list_entries(kind="idea")) == 1


def test_workbook_requires_title(app):
    with pytest.raises(ValidationError):
        app.workbook.create_entry("   ")


def test_workbook_pinned_entries_come_first(app):
    app.workbook.create_entry("Normal")
    pinned = app.workbook.create_entry("Important")
    app.workbook.toggle_pin(pinned)
    entries = app.workbook.list_entries()
    # The seeded welcome entry is also pinned, so both pinned entries must
    # precede the unpinned one.
    titles = [entry["title"] for entry in entries]
    assert titles.index("Important") < titles.index("Normal")
    assert titles.index("Welcome to your workbook") < titles.index("Normal")
