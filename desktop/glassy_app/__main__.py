"""Entry point: build the QApplication and show the main window.

``main()`` is the single entry point used by ``python -m glassy_app``, by the
PyInstaller build and by the GUI tests.
"""

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from . import APP_NAME, __version__, app_icon_path
from .app import Application
from .ui.main_window import MainWindow


def build_application(argv=None, data_dir=None, seed=True):
    """Create the Qt application and the window without entering the loop.

    Returned as a tuple so tests can drive the window and then call
    ``app.exec()`` themselves, or simply inspect it.
    """
    qt_app = QApplication.instance()
    if qt_app is None:
        qt_app = QApplication(argv if argv is not None else sys.argv)
    qt_app.setApplicationName(APP_NAME)
    qt_app.setApplicationVersion(__version__)
    qt_app.setOrganizationName("GlassyLedger")

    icon_file = app_icon_path()
    if icon_file:
        qt_app.setWindowIcon(QIcon(str(icon_file)))

    ledger = Application(data_dir=data_dir, seed=seed)
    window = MainWindow(ledger)
    if icon_file:
        window.setWindowIcon(QIcon(str(icon_file)))
    return qt_app, window, ledger


def main(argv=None):
    argv = list(sys.argv if argv is None else argv)
    try:
        qt_app, window, _ledger = build_application(argv)
    except Exception as exc:  # noqa: BLE001 - last-resort startup guard
        # A failure here usually means the data directory is not writable.
        fallback = QApplication.instance() or QApplication(argv)
        QMessageBox.critical(
            None,
            f"{APP_NAME} could not start",
            f"{exc}\n\nSet GLASSY_LEDGER_HOME to a writable folder and retry.",
        )
        del fallback
        return 1

    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    sys.exit(main())
