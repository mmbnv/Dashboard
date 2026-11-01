"""The main application window: sidebar navigation plus a stacked page area."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .. import APP_NAME, __version__, app_icon_path, terms
from . import theme
from .dialogs import show_error, show_info
from .pages.calculator_page import CalculatorPage
from .pages.dashboard_page import DashboardPage
from .pages.learning_page import LearningPage
from .pages.registries_page import RegistriesPage
from .pages.settings_page import SettingsPage
from .pages.tasks_page import TasksPage
from .pages.wallet_page import WalletPage
from .pages.workbook_page import WorkbookPage

NAV_ITEMS = list(terms.SECTIONS)

PAGE_CLASSES = {
    "dashboard": DashboardPage,
    "wallet": WalletPage,
    "tasks": TasksPage,
    "learning": LearningPage,
    "registries": RegistriesPage,
    "workbook": WorkbookPage,
    "calculator": CalculatorPage,
    "settings": SettingsPage,
}


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle(f"{APP_NAME} {__version__}")
        self.resize(1280, 820)
        self.setMinimumSize(980, 640)

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        self.pages = {}
        for key, _, _ in NAV_ITEMS:
            page = PAGE_CLASSES[key](self.app)
            self.pages[key] = page
            self.stack.addWidget(page)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Готово")

        self._build_menu()
        self.apply_theme(self.app.theme)
        self._restore_window_state()

        start = self.app.last_page
        self.show_page(start if start in self.pages else "dashboard")

    # -- window state ------------------------------------------------------
    def _restore_window_state(self):
        state = self.app.window_state or {}
        geometry = state.get("geometry")
        if isinstance(geometry, list) and len(geometry) == 4:
            x, y, width, height = (int(v) for v in geometry)
            self.setGeometry(x, y, max(width, self.minimumWidth()),
                             max(height, self.minimumHeight()))
        if state.get("maximized"):
            self.showMaximized()

    def closeEvent(self, event):  # noqa: N802
        # The application may already be shut down (for example when a test or
        # the smoke tool closes it first); saving then would write through a
        # closed connection.
        if not getattr(self.app, "_closed", False):
            geometry = self.geometry()
            self.app.window_state = {
                "geometry": [geometry.x(), geometry.y(),
                             geometry.width(), geometry.height()],
                "maximized": self.isMaximized(),
            }
        self.app.close()
        super().closeEvent(event)

    # -- menu --------------------------------------------------------------
    def _build_menu(self):
        """A native menu bar, as expected of a desktop application."""
        bar = self.menuBar()

        file_menu = bar.addMenu("&Файл")
        self._action(file_menu, "&Новая задача\u2026", self._new_task,
                     QKeySequence("Ctrl+N"))
        self._action(file_menu, "&Обновить", self.refresh_current_page,
                     QKeySequence("F5"))
        file_menu.addSeparator()
        self._action(file_menu, "Создать &резервную копию\u2026", self._backup)
        self._action(file_menu, "&Экспорт всех данных (JSON)\u2026",
                     self._export_json)
        self._action(file_menu, "Экспорт операций (CSV)\u2026",
                     self._export_csv)
        file_menu.addSeparator()
        self._action(file_menu, "В&ыход", self.close,
                     QKeySequence("Ctrl+Q"))

        view_menu = bar.addMenu("&Вид")
        self._action(view_menu, "&Тёмная тема", lambda: self._set_theme("dark"),
                     QKeySequence("Ctrl+Shift+D"))
        self._action(view_menu, "&Светлая тема", lambda: self._set_theme("light"),
                     QKeySequence("Ctrl+Shift+L"))
        view_menu.addSeparator()
        self._action(view_menu, "Во весь &экран", self._toggle_fullscreen,
                     QKeySequence("F11"))

        go_menu = bar.addMenu("&Переход")
        for index, (key, label, _) in enumerate(NAV_ITEMS, start=1):
            self._action(go_menu, label, lambda k=key: self.show_page(k),
                         QKeySequence(f"Ctrl+{index}"))

        help_menu = bar.addMenu("&Справка")
        self._action(help_menu, "&О программе", self._about)

    @staticmethod
    def _action(menu, text, slot, shortcut=None):
        action = QAction(text, menu)
        action.triggered.connect(lambda _=False: slot())
        if shortcut is not None:
            action.setShortcut(shortcut)
        menu.addAction(action)
        return action

    # -- menu handlers -----------------------------------------------------
    def _new_task(self):
        self.show_page("tasks")
        page = self.pages["tasks"]
        if hasattr(page, "_new_task"):
            page._new_task()

    def _set_theme(self, name):
        self.app.theme = name
        self.apply_theme(name)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _backup(self):
        try:
            path = self.app.backup()
        except Exception as exc:  # noqa: BLE001 - report and keep running
            show_error(self, f"Не удалось создать копию: {exc}")
            return
        show_info(self, f"Копия сохранена:\n{path}")

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт всех данных", "glassy-ledger-export.json",
            "Файлы JSON (*.json)",
        )
        if not path:
            return
        try:
            self.app.export_all_json(path)
        except Exception as exc:  # noqa: BLE001
            show_error(self, f"Не удалось экспортировать: {exc}")
            return
        show_info(self, f"Экспортировано в:\n{path}")

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт операций", "transactions.csv",
            "Файлы CSV (*.csv)",
        )
        if not path:
            return
        try:
            self.app.export_transactions_csv(path)
        except Exception as exc:  # noqa: BLE001
            show_error(self, f"Не удалось экспортировать: {exc}")
            return
        show_info(self, f"Экспортировано в:\n{path}")

    def _about(self):
        box = QMessageBox(self)
        box.setWindowTitle(f"О программе {APP_NAME}")
        box.setText(f"<h3>{APP_NAME} {__version__}</h3>"
                    f"<p>{terms.APP_TAGLINE}.</p>")
        box.setInformativeText(
            "Кошелёк, задачи, обучение, таблицы, заметки и калькулятор "
            "в одной программе.\n\n"
            f"База данных: {self.app.database_path}\n"
            "Все данные остаются на этом компьютере."
        )
        icon_file = app_icon_path()
        if icon_file:
            box.setIconPixmap(QPixmap(str(icon_file)))
        box.exec()

    # -- chrome -----------------------------------------------------------
    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(224)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(6)

        brand = QLabel(APP_NAME)
        brand.setObjectName("Brand")
        layout.addWidget(brand)
        sub = QLabel(terms.APP_TAGLINE.lower())
        sub.setObjectName("BrandSub")
        layout.addWidget(sub)
        layout.addSpacing(14)

        self.nav_buttons = {}
        for key, label, icon in NAV_ITEMS:
            button = QPushButton(f"  {icon}   {label}")
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setMinimumHeight(40)
            button.clicked.connect(lambda _, k=key: self.show_page(k))
            layout.addWidget(button)
            self.nav_buttons[key] = button

        layout.addStretch(1)

        version = QLabel(f"v{__version__}\nЛокальная база")
        version.setObjectName("BrandSub")
        version.setAlignment(Qt.AlignLeft)
        layout.addWidget(version)
        return sidebar

    # -- navigation -------------------------------------------------------
    def show_page(self, key):
        if key not in self.pages:
            key = "dashboard"
        page = self.pages[key]
        self.stack.setCurrentWidget(page)
        button = self.nav_buttons.get(key)
        if button:
            button.setChecked(True)
        page.on_show()
        self.app.last_page = key
        self.status.showMessage(f"{page.title} \u2014 {page.subtitle}")

    def refresh_current_page(self):
        current = self.stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()

    # -- theme -------------------------------------------------------------
    def apply_theme(self, name):
        app = QApplication.instance()
        if app is not None:
            # The palette covers widgets the stylesheet does not reach.
            app.setPalette(theme.qt_palette(name))
        self.setStyleSheet(theme.stylesheet(name))
        for page in self.pages.values():
            page.setProperty("themeName", name)
            for child in page.findChildren(QWidget):
                child.setProperty("themeName", name)
            page.update()
        self.update()

    def sizeHint(self):  # noqa: N802
        return QSize(1280, 820)
