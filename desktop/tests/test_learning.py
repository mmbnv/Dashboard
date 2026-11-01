"""Learning service: course progress and session logging."""

import pytest

from glassy_app.core.errors import NotFoundError, ValidationError


def test_default_course_is_seeded(app):
    assert len(app.learning.list_courses()) == 1


def test_logging_a_session_advances_progress(app):
    course = app.learning.list_courses()[0]
    app.learning.log_session(course["id"], minutes=60, units_done=2)
    updated = app.learning.get_course(course["id"])
    assert updated["done_units"] == 2

    rows = app.learning.summary_rows()
    assert rows[0]["progress"] == pytest.approx(40.0)  # 2 of 5
    assert rows[0]["hours"] == 1.0


def test_cannot_exceed_total_units(app):
    course = app.learning.list_courses()[0]
    with pytest.raises(ValidationError):
        app.learning.log_session(course["id"], units_done=99)
    # the failed attempt must not have changed anything
    assert app.learning.get_course(course["id"])["done_units"] == 0


def test_completing_all_units_marks_course_done(app):
    course = app.learning.list_courses()[0]
    app.learning.log_session(course["id"], units_done=5)
    assert app.learning.get_course(course["id"])["status"] == "done"


def test_session_needs_minutes_or_units(app):
    course = app.learning.list_courses()[0]
    with pytest.raises(ValidationError):
        app.learning.log_session(course["id"], minutes=0, units_done=0)


def test_delete_session_rolls_progress_back(app):
    course = app.learning.list_courses()[0]
    session_id = app.learning.log_session(course["id"], units_done=3)
    assert app.learning.get_course(course["id"])["done_units"] == 3
    app.learning.delete_session(session_id)
    assert app.learning.get_course(course["id"])["done_units"] == 0


def test_totals_aggregate_everything(app):
    course = app.learning.list_courses()[0]
    app.learning.log_session(course["id"], minutes=30)
    app.learning.log_session(course["id"], minutes=45)
    totals = app.learning.totals()
    assert totals["total_minutes"] == 75
    assert totals["hours"] == 1.2
    assert totals["courses"] == 1


def test_delete_course_removes_sessions(app):
    course = app.learning.list_courses()[0]
    app.learning.log_session(course["id"], minutes=10)
    app.learning.delete_course(course["id"])
    assert app.learning.list_courses() == []
    assert app.learning.list_sessions() == []


def test_missing_course_raises(app):
    with pytest.raises(NotFoundError):
        app.learning.get_course(99999)


def test_course_validation(app):
    with pytest.raises(ValidationError):
        app.learning.create_course(title="")
    with pytest.raises(ValidationError):
        app.learning.create_course(title="X", status="bogus")
    with pytest.raises(ValidationError):
        app.learning.create_course(title="X", rating=9)
    with pytest.raises(ValidationError):
        app.learning.create_course(title="X", total_units=2, done_units=5)


def test_weekly_minutes_buckets(app):
    course = app.learning.list_courses()[0]
    app.learning.log_session(course["id"], minutes=20, occurred_on="2026-01-05")
    app.learning.log_session(course["id"], minutes=25, occurred_on="2026-01-06")
    weeks = app.learning.weekly_minutes(8)
    assert len(weeks) == 1
    assert weeks[0]["minutes"] == 45
