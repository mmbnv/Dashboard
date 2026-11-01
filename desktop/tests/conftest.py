"""Shared pytest fixtures. Tests run against a real SQLite file, no mocks."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from glassy_app.app import Application  # noqa: E402
from glassy_app.core.database import Database  # noqa: E402


@pytest.fixture()
def data_dir(tmp_path):
    path = tmp_path / "data"
    path.mkdir()
    return path


@pytest.fixture()
def app(data_dir):
    """A fully seeded application backed by a temporary database."""
    instance = Application(data_dir=data_dir)
    yield instance
    instance.close()


@pytest.fixture()
def empty_app(data_dir):
    """An application with the schema but no seeded example rows."""
    instance = Application(data_dir=data_dir, seed=False)
    yield instance
    instance.close()


@pytest.fixture()
def db(data_dir):
    instance = Database(data_dir / "raw.db")
    yield instance
    instance.close()
