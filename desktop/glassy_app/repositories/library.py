"""Repositories for learning, registries, workbook, tasks and settings."""

import json

from .base import BaseRepository


class CourseRepository(BaseRepository):
    table = "courses"
    columns = (
        "title", "provider", "url", "status", "total_units", "done_units",
        "cost", "currency", "started_on", "finished_on", "rating", "note",
        "created_at", "updated_at",
    )

    def create(self, course):
        course.validate()
        return self._insert(self._payload(course))

    def update(self, course):
        course.validate()
        return self._update(course.id, self._payload(course))

    @staticmethod
    def _payload(course):
        return {
            "title": course.title,
            "provider": course.provider,
            "url": course.url,
            "status": course.status,
            "total_units": course.total_units,
            "done_units": course.done_units,
            "cost": course.cost,
            "currency": course.currency,
            "started_on": course.started_on,
            "finished_on": course.finished_on,
            "rating": course.rating,
            "note": course.note,
        }

    def with_stats(self):
        """Courses plus logged study time and session count."""
        return self.db.query(
            """
            SELECT c.*,
                   COALESCE(SUM(s.minutes), 0) AS total_minutes,
                   COUNT(s.id) AS session_count,
                   MAX(s.occurred_on) AS last_session
            FROM courses c
            LEFT JOIN study_sessions s ON s.course_id = c.id
            GROUP BY c.id
            ORDER BY
                CASE c.status
                    WHEN 'active' THEN 0
                    WHEN 'planned' THEN 1
                    WHEN 'paused' THEN 2
                    WHEN 'done' THEN 3
                    ELSE 4
                END,
                c.title COLLATE NOCASE
            """
        )

    def totals(self):
        row = self.db.query_one(
            """
            SELECT COUNT(*) AS courses,
                   COALESCE(SUM(CASE WHEN status='active' THEN 1 END), 0) AS active,
                   COALESCE(SUM(CASE WHEN status='done' THEN 1 END), 0) AS finished,
                   COALESCE(SUM(cost), 0) AS spend_minor
            FROM courses
            """
        )
        minutes = self.db.query_one(
            "SELECT COALESCE(SUM(minutes), 0) AS m FROM study_sessions"
        )
        row["total_minutes"] = minutes["m"] if minutes else 0
        return row


class StudySessionRepository(BaseRepository):
    table = "study_sessions"
    columns = (
        "course_id", "minutes", "units_done", "occurred_on", "note",
        "created_at", "updated_at",
    )

    def create(self, session):
        session.validate()
        return self._insert(self._payload(session))

    def update(self, session):
        session.validate()
        return self._update(session.id, self._payload(session))

    @staticmethod
    def _payload(session):
        return {
            "course_id": session.course_id,
            "minutes": session.minutes,
            "units_done": session.units_done,
            "occurred_on": session.occurred_on,
            "note": session.note,
        }

    def for_course(self, course_id):
        return self.db.query(
            "SELECT * FROM study_sessions WHERE course_id=? "
            "ORDER BY occurred_on DESC, id DESC",
            (course_id,),
        )

    def recent(self, limit=20):
        return self.db.query(
            """
            SELECT s.*, c.title AS course_title
            FROM study_sessions s
            JOIN courses c ON c.id = s.course_id
            ORDER BY s.occurred_on DESC, s.id DESC
            LIMIT ?
            """,
            (limit,),
        )

    def daily_minutes(self, days=30):
        return self.db.query(
            """
            SELECT occurred_on, COALESCE(SUM(minutes), 0) AS minutes
            FROM study_sessions
            GROUP BY occurred_on
            ORDER BY occurred_on DESC
            LIMIT ?
            """,
            (days,),
        )[::-1]


class RegistryRepository(BaseRepository):
    table = "registries"
    columns = ("name", "title", "description", "icon", "created_at", "updated_at")

    def create(self, registry):
        registry.validate()
        registry_id = self._insert(
            {
                "name": registry.name,
                "title": registry.title,
                "description": registry.description,
                "icon": registry.icon,
            }
        )
        for position, field in enumerate(registry.fields or []):
            field.position = position
            self.add_field(registry_id, field)
        return registry_id

    def update(self, registry):
        registry.validate()
        return self._update(
            registry.id,
            {
                "name": registry.name,
                "title": registry.title,
                "description": registry.description,
                "icon": registry.icon,
            },
        )

    def by_name(self, name):
        return self.db.query_one("SELECT * FROM registries WHERE name=?", (name,))

    # -- fields ---------------------------------------------------------
    def add_field(self, registry_id, field):
        field.validate()
        return self.db.insert(
            """
            INSERT INTO registry_fields
                (registry_id, key, label, type, required, options, position)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                registry_id,
                field.key,
                field.label,
                field.type,
                int(bool(field.required)),
                json.dumps(list(field.options or []), ensure_ascii=False),
                field.position,
            ),
        )

    def update_field(self, field_id, field):
        field.validate()
        self.db.execute(
            """
            UPDATE registry_fields
            SET key=?, label=?, type=?, required=?, options=?, position=?
            WHERE id=?
            """,
            (
                field.key,
                field.label,
                field.type,
                int(bool(field.required)),
                json.dumps(list(field.options or []), ensure_ascii=False),
                field.position,
                field_id,
            ),
        )

    def delete_field(self, field_id):
        self.db.execute("DELETE FROM registry_fields WHERE id=?", (field_id,))

    def fields(self, registry_id):
        rows = self.db.query(
            "SELECT * FROM registry_fields WHERE registry_id=? "
            "ORDER BY position, id",
            (registry_id,),
        )
        for row in rows:
            row["required"] = bool(row["required"])
            try:
                row["options"] = json.loads(row["options"] or "[]")
            except (ValueError, TypeError):
                row["options"] = []
        return rows

    # -- records --------------------------------------------------------
    def add_record(self, registry_id, data):
        return self.db.insert(
            "INSERT INTO registry_records (registry_id, data, created_at, updated_at) "
            "VALUES (?, ?, datetime('now'), datetime('now'))",
            (registry_id, json.dumps(data or {}, ensure_ascii=False)),
        )

    def update_record(self, record_id, data):
        self.db.execute(
            "UPDATE registry_records SET data=?, updated_at=datetime('now') "
            "WHERE id=?",
            (json.dumps(data or {}, ensure_ascii=False), record_id),
        )

    def delete_record(self, record_id):
        self.db.execute("DELETE FROM registry_records WHERE id=?", (record_id,))

    def records(self, registry_id, search=None, limit=None, offset=0):
        where = ["registry_id = ?"]
        params = [registry_id]
        if search:
            where.append("data LIKE ?")
            params.append(f"%{search}%")
        sql = (
            "SELECT * FROM registry_records "
            f"WHERE {' AND '.join(where)} ORDER BY id DESC"
        )
        if limit:
            sql += " LIMIT ? OFFSET ?"
            params += [limit, offset]
        rows = self.db.query(sql, params)
        for row in rows:
            try:
                row["data"] = json.loads(row["data"] or "{}")
            except (ValueError, TypeError):
                row["data"] = {}
        return rows

    def record_count(self, registry_id):
        row = self.db.query_one(
            "SELECT COUNT(*) AS n FROM registry_records WHERE registry_id=?",
            (registry_id,),
        )
        return row["n"] if row else 0

    def all_with_counts(self):
        return self.db.query(
            """
            SELECT r.*, COUNT(rec.id) AS record_count
            FROM registries r
            LEFT JOIN registry_records rec ON rec.registry_id = r.id
            GROUP BY r.id
            ORDER BY r.title COLLATE NOCASE
            """
        )


class WorkbookRepository(BaseRepository):
    table = "workbook_entries"
    columns = (
        "title", "body", "kind", "tags", "pinned", "created_at", "updated_at",
    )

    def create(self, entry):
        entry.validate()
        return self._insert(self._payload(entry))

    def update(self, entry):
        entry.validate()
        return self._update(entry.id, self._payload(entry))

    @staticmethod
    def _payload(entry):
        return {
            "title": entry.title,
            "body": entry.body,
            "kind": entry.kind,
            "tags": entry.tags,
            "pinned": int(bool(entry.pinned)),
        }

    def search(self, text=None, kind=None):
        where = ["1=1"]
        params = []
        if text:
            where.append("(title LIKE ? OR body LIKE ? OR tags LIKE ?)")
            like = f"%{text}%"
            params += [like, like, like]
        if kind:
            where.append("kind = ?")
            params.append(kind)
        return self.db.query(
            f"""
            SELECT * FROM workbook_entries
            WHERE {' AND '.join(where)}
            ORDER BY pinned DESC, updated_at DESC
            """,
            params,
        )

    def kinds(self):
        return [
            r["kind"]
            for r in self.db.query(
                "SELECT DISTINCT kind FROM workbook_entries ORDER BY kind"
            )
        ]


class TaskRepository(BaseRepository):
    table = "tasks"
    columns = (
        "title", "notes", "status", "priority", "due_on", "tags",
        "created_at", "updated_at", "completed_at",
    )

    def create(self, task):
        task.validate()
        return self._insert(self._payload(task))

    def update(self, task):
        task.validate()
        return self._update(task.id, self._payload(task))

    @staticmethod
    def _payload(task):
        return {
            "title": task.title,
            "notes": task.notes,
            "status": task.status,
            "priority": task.priority,
            "due_on": task.due_on,
            "tags": task.tags,
            "completed_at": task.completed_at,
        }

    def search(self, text=None, status=None, priority=None):
        where = ["1=1"]
        params = []
        if text:
            where.append("(title LIKE ? OR notes LIKE ? OR tags LIKE ?)")
            like = f"%{text}%"
            params += [like, like, like]
        if status:
            where.append("status = ?")
            params.append(status)
        if priority:
            where.append("priority = ?")
            params.append(priority)
        return self.db.query(
            f"""
            SELECT * FROM tasks
            WHERE {' AND '.join(where)}
            ORDER BY
                CASE status WHEN 'doing' THEN 0 WHEN 'todo' THEN 1 ELSE 2 END,
                CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
                CASE WHEN due_on = '' THEN 1 ELSE 0 END,
                due_on,
                id DESC
            """,
            params,
        )

    def stats(self):
        row = self.db.query_one(
            """
            SELECT
              COUNT(*) AS total,
              COALESCE(SUM(CASE WHEN status='todo'  THEN 1 END), 0) AS todo,
              COALESCE(SUM(CASE WHEN status='doing' THEN 1 END), 0) AS doing,
              COALESCE(SUM(CASE WHEN status='done'  THEN 1 END), 0) AS done
            FROM tasks
            """
        )
        overdue = self.db.query_one(
            """
            SELECT COUNT(*) AS n FROM tasks
            WHERE status != 'done' AND due_on != '' AND due_on < date('now')
            """
        )
        row["overdue"] = overdue["n"] if overdue else 0
        return row


class SettingsRepository:
    """Key/value settings store. Values are JSON encoded."""

    def __init__(self, db):
        self.db = db

    def get(self, key, default=None):
        row = self.db.query_one("SELECT value FROM settings WHERE key=?", (key,))
        if not row:
            return default
        try:
            return json.loads(row["value"])
        except (ValueError, TypeError):
            return default

    def set(self, key, value):
        self.db.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET value=excluded.value,
                                           updated_at=excluded.updated_at
            """,
            (key, json.dumps(value, ensure_ascii=False)),
        )

    def all(self):
        result = {}
        for row in self.db.query("SELECT key, value FROM settings"):
            try:
                result[row["key"]] = json.loads(row["value"])
            except (ValueError, TypeError):
                result[row["key"]] = None
        return result
