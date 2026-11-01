"""Glassy Ledger - a desktop application for personal record keeping.

Modules: wallet (income/expense), learning, arbitrary data registries,
calculator, workbook (notes) and tasks.
"""

import sys
from pathlib import Path

__version__ = "1.0.0"
APP_NAME = "Glassy Ledger"


def resource_path(*parts):
    """Locate a bundled file both in development and in a frozen build.

    PyInstaller unpacks data next to the executable (one-folder) or into a
    temporary directory (one-file) and exposes it as ``sys._MEIPASS``.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base).joinpath(*parts)
    return Path(__file__).resolve().parent.joinpath(*parts)


def app_icon_path():
    """Return the path to the window icon, or ``None`` if it is missing."""
    candidate = resource_path("assets", "app.png")
    return candidate if candidate.exists() else None
