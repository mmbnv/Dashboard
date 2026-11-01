"""Base page class shared by every module page."""

from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from .widgets.common import clear_layout


class BasePage(QWidget):
    """A scrollable page with a title header and a refresh hook.

    ``on_show`` is called every time the page becomes visible, so data is
    always re-read from the database instead of going stale behind the UI.
    """

    title = "Раздел"
    subtitle = ""

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self._built = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        outer.addWidget(self.scroll)

        self.container = QWidget()
        self.container.setObjectName("PageContainer")
        self.scroll.setWidget(self.container)

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(24, 20, 24, 24)
        self.layout.setSpacing(16)

        self.build()

    # -- overridables ----------------------------------------------------
    def build(self):
        """Create the static widget tree. Called once."""

    def refresh(self):
        """Reload data from the database. Called on every show."""

    def on_show(self):
        if not self._built:
            self._built = True
        self.refresh()

    # -- helpers ---------------------------------------------------------
    def add(self, widget):
        self.layout.addWidget(widget)
        return widget

    def reset(self):
        clear_layout(self.layout)
