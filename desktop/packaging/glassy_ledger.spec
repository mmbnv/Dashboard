# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Glassy Ledger.

Build with:

    pyinstaller packaging/glassy_ledger.spec --noconfirm

Produces a one-folder build in dist/GlassyLedger. A one-folder build starts
faster than one-file and keeps the Qt plugins on disk, which is what an
installed desktop app wants. Set GLASSY_ONE_FILE=1 for a single executable.

The database is never bundled: it is created on first run under the user's
application data directory, so an installed copy works for every user and the
program directory can stay read-only.
"""

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).resolve().parent

datas = []
binaries = []
hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    # Qt loads the SQL driver lazily, so it must be named explicitly.
    "sqlite3",
]

# The window icon is loaded at runtime by name, so PyInstaller cannot see it.
_icon_png = ROOT / "glassy_app" / "assets" / "app.png"
if _icon_png.exists():
    datas.append((str(_icon_png), "glassy_app/assets"))

# Keep image plugins available even in a minimal Qt build.
for package in ("PySide6",):
    try:
        datas += collect_data_files(package, includes=["**/*.png", "**/*.svg"])
    except Exception:  # noqa: BLE001 - optional, the Qt hook covers the rest
        pass

hiddenimports += collect_submodules("glassy_app")

one_file = os.environ.get("GLASSY_ONE_FILE") == "1"

_icon = ROOT / "packaging" / "app.ico"

a = Analysis(
    [str(ROOT / "run.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim the build: none of these are used and each adds megabytes.
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.Qt3DCore",
        "PySide6.QtMultimedia",
        "PySide6.QtQuick",
        "PySide6.QtQml",
        "PySide6.QtNetwork",
        "PySide6.QtOpenGL",
        "PySide6.QtCharts",
        "PySide6.QtTest",
        "PySide6.QtBluetooth",
        "PySide6.QtPositioning",
        "PySide6.QtSerialPort",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

if one_file:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="GlassyLedger",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(_icon) if _icon.exists() else None,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="GlassyLedger",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(_icon) if _icon.exists() else None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="GlassyLedger",
    )
