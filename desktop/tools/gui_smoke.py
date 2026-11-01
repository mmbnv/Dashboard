"""Drive the real GUI headlessly and capture a screenshot of every page.

Run with a display available (Xvfb in CI):

    DISPLAY=:99 python tools/gui_smoke.py /tmp/shots

The script fails loudly if a page raises while building or refreshing, which
is exactly the class of bug that import-only checks miss.
"""

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from glassy_app.__main__ import build_application  # noqa: E402
from glassy_app.ui.main_window import NAV_ITEMS  # noqa: E402


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/glassy-shots")
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else out_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    qt_app, window, ledger = build_application(
        ["gui-smoke"], data_dir=str(data_dir)
    )
    window.resize(1360, 880)
    window.show()

    failures = []

    def capture():
        for key, label, _icon in NAV_ITEMS:
            try:
                window.show_page(key)
                QApplication.processEvents()
                pixmap = window.grab()
                target = out_dir / f"{key}.png"
                if not pixmap.save(str(target)):
                    raise RuntimeError(f"could not save {target}")
                print(f"captured {label:<12} -> {target} "
                      f"({pixmap.width()}x{pixmap.height()})")
            except Exception:  # noqa: BLE001
                failures.append(key)
                print(f"FAILED on page {key!r}")
                traceback.print_exc()

        # exercise a write through the UI layer, then confirm it persisted
        try:
            before = ledger.counts()["tasks"]
            ledger.tasks.create_task("Smoke test task", priority="high")
            after = ledger.counts()["tasks"]
            assert after == before + 1, "task was not persisted"
            window.show_page("tasks")
            QApplication.processEvents()
            window.grab().save(str(out_dir / "tasks-after-write.png"))
            print(f"write check: tasks {before} -> {after}")
        except Exception:  # noqa: BLE001
            failures.append("write")
            traceback.print_exc()

        ledger.close()
        qt_app.quit()

    QTimer.singleShot(600, capture)
    qt_app.exec()

    if failures:
        print(f"GUI SMOKE FAILED: {failures}")
        return 1
    print("GUI SMOKE OK - every page rendered and a write persisted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
