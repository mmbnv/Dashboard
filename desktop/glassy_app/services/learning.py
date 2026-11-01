"""Learning service: courses and logged study sessions."""

from ..core import money
from ..core.errors import NotFoundError, ValidationError
from ..core.models import Course, StudySession
from ..repositories.library import CourseRepository, StudySessionRepository


class LearningService:
    def __init__(self, db):
        self.db = db
        self.courses = CourseRepository(db)
        self.sessions = StudySessionRepository(db)

    # -- courses --------------------------------------------------------
    def list_courses(self):
        return self.courses.with_stats()

    def get_course(self, course_id):
        row = self.courses.get(course_id)
        if not row:
            raise NotFoundError("Курс не найден")
        return row

    def create_course(self, **kwargs):
        return self.courses.create(Course(**kwargs))

    def update_course(self, course_id, **kwargs):
        return self.courses.update(Course(id=course_id, **kwargs))

    def delete_course(self, course_id):
        self.courses.delete(course_id)

    def seed_defaults(self):
        if self.courses.count() == 0:
            self.courses.create(
                Course(
                    title="С чего начать",
                    provider="Glassy Ledger",
                    status="active",
                    total_units=5,
                    note="Пример курса. Запишите занятие или удалите его.",
                )
            )

    # -- sessions -------------------------------------------------------
    def log_session(self, course_id, minutes=0, units_done=0, occurred_on=None,
                    note=""):
        """Record study time and, when units are supplied, advance progress.

        Progress is stored on the course row so the list view stays a single
        query. The two writes share one transaction.
        """
        session = StudySession(
            course_id=course_id,
            minutes=minutes,
            units_done=units_done,
            occurred_on=occurred_on or "",
            note=note,
        )
        if not session.occurred_on:
            from ..core.models import today_iso

            session.occurred_on = today_iso()
        session.validate()

        course = self.get_course(course_id)
        new_done = int(course["done_units"] or 0) + int(session.units_done or 0)
        total = int(course["total_units"] or 0)
        if total and new_done > total:
            raise ValidationError(
                f"На курсе осталось единиц: {total - int(course['done_units'] or 0)}",
                field="units_done",
            )

        with self.db.transaction():
            session_id = self.sessions.create(session)
            fields = ["done_units=?"]
            params = [new_done]
            if total and new_done >= total and course["status"] != "done":
                fields.append("status='done'")
            fields.append("updated_at=?")
            from ..core.models import now_iso

            params.append(now_iso())
            params.append(course_id)
            self.db.execute(
                f"UPDATE courses SET {', '.join(fields)} WHERE id=?", params
            )
        return session_id

    def list_sessions(self, course_id=None, limit=None):
        if course_id:
            return self.sessions.for_course(course_id)
        return self.sessions.recent(limit or 50)

    def delete_session(self, session_id):
        """Delete a session and roll the logged units back off the course."""
        row = self.sessions.get(session_id)
        if not row:
            raise NotFoundError("Занятие не найдено")
        course = self.courses.get(row["course_id"])
        with self.db.transaction():
            self.sessions.delete(session_id)
            if course:
                from ..core.models import now_iso

                new_done = max(
                    0, int(course["done_units"] or 0) - int(row["units_done"] or 0)
                )
                self.db.execute(
                    "UPDATE courses SET done_units=?, updated_at=? WHERE id=?",
                    (new_done, now_iso(), course["id"]),
                )

    # -- reports --------------------------------------------------------
    def totals(self):
        data = self.courses.totals()
        data["hours"] = round(data["total_minutes"] / 60.0, 1)
        return data

    def summary_rows(self):
        """One row per course with progress, time and spend, for the table."""
        rows = []
        for course in self.list_courses():
            minutes = int(course["total_minutes"] or 0)
            total_units = int(course["total_units"] or 0)
            done_units = int(course["done_units"] or 0)
            rows.append(
                {
                    "id": course["id"],
                    "title": course["title"],
                    "provider": course["provider"],
                    "status": course["status"],
                    "progress": (done_units / total_units * 100.0)
                    if total_units
                    else (100.0 if course["status"] == "done" else 0.0),
                    "units": f"{done_units}/{total_units}" if total_units else "\u2014",
                    "hours": round(minutes / 60.0, 1),
                    "sessions": int(course["session_count"] or 0),
                    "last_session": course["last_session"] or "\u2014",
                    "cost": money.format_amount(
                        course["cost"] or 0, course["currency"]
                    ),
                    "rating": course["rating"],
                }
            )
        return rows

    def weekly_minutes(self, weeks=8):
        """Study minutes bucketed by ISO week, oldest first."""
        rows = self.db.query(
            """
            SELECT strftime('%Y-W%W', occurred_on) AS week,
                   COALESCE(SUM(minutes), 0) AS minutes
            FROM study_sessions
            GROUP BY week
            ORDER BY week DESC
            LIMIT ?
            """,
            (weeks,),
        )
        return rows[::-1]
