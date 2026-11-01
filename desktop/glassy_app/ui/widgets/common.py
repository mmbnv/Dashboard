"""Reusable widgets: stat cards, charts, section headers, form helpers."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .. import theme


def clear_layout(layout):
    """Remove and delete every child of ``layout``."""
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        else:
            child = item.layout()
            if child is not None:
                clear_layout(child)


class Card(QFrame):
    """A rounded surface panel."""

    def __init__(self, parent=None, alt=False, padding=16):
        super().__init__(parent)
        self.setObjectName("CardAlt" if alt else "Card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(padding, padding, padding, padding)
        self._layout.setSpacing(10)

    def body(self):
        return self._layout

    def add(self, widget):
        self._layout.addWidget(widget)
        return widget


class StatCard(Card):
    """A small metric tile: caption, big value and optional hint."""

    def __init__(self, title, value="\u2014", hint="", accent=None, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setMinimumHeight(96)

        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("CardTitle")

        self.value_label = QLabel(value)
        self.value_label.setObjectName("CardValue")
        if accent:
            self.value_label.setStyleSheet(f"color: {accent};")

        self.hint_label = QLabel(hint)
        self.hint_label.setObjectName("Muted")
        self.hint_label.setWordWrap(True)
        self.hint_label.setVisible(bool(hint))

        self._layout.addWidget(self.title_label)
        self._layout.addWidget(self.value_label)
        self._layout.addWidget(self.hint_label)
        self._layout.addStretch(1)

    def set_value(self, value, hint=None, accent=None):
        self.value_label.setText(str(value))
        if accent:
            self.value_label.setStyleSheet(f"color: {accent};")
        else:
            self.value_label.setStyleSheet("")
        if hint is not None:
            self.hint_label.setText(hint)
            self.hint_label.setVisible(bool(hint))


class SectionHeader(QWidget):
    """A page title with an optional subtitle and a right-hand widget row."""

    def __init__(self, title, subtitle="", parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        row = QHBoxLayout()
        row.setSpacing(10)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("PageTitle")
        text_col.addWidget(self.title_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("PageSubtitle")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setVisible(bool(subtitle))
        text_col.addWidget(self.subtitle_label)

        row.addLayout(text_col, 1)
        self.actions = QHBoxLayout()
        self.actions.setSpacing(8)
        row.addLayout(self.actions, 0)
        outer.addLayout(row)

    def add_action(self, widget):
        self.actions.addWidget(widget)
        return widget

    def set_subtitle(self, text):
        self.subtitle_label.setText(text)
        self.subtitle_label.setVisible(bool(text))


class BarChart(QWidget):
    """Minimal grouped bar chart (two series) drawn with QPainter.

    Deliberately dependency-free: no matplotlib in the frozen build.
    """

    def __init__(self, parent=None, labels=None, height=160):
        super().__init__(parent)
        self.labels = labels or []
        self.series_a = []
        self.series_b = []
        self.name_a = "A"
        self.name_b = "B"
        self.setMinimumHeight(height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_data(self, labels, series_a, series_b=None, name_a="A", name_b="B"):
        self.labels = list(labels)
        self.series_a = list(series_a)
        self.series_b = list(series_b or [])
        self.name_a = name_a
        self.name_b = name_b
        self.update()

    def paintEvent(self, event):  # noqa: N802 - Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pal = theme.palette(self.property("themeName") or "dark")

        rect = self.rect().adjusted(8, 8, -8, -24)
        if not self.labels or not self.series_a:
            painter.setPen(QColor(pal["text_dim"]))
            painter.drawText(self.rect(), Qt.AlignCenter, "No data yet")
            painter.end()
            return

        values = list(self.series_a) + list(self.series_b)
        peak = max(values) if values else 0
        if peak <= 0:
            peak = 1

        count = len(self.labels)
        slot = rect.width() / max(1, count)
        bar_width = max(4.0, min(22.0, slot / 3.2))
        gap = 4.0

        # baseline
        painter.setPen(QPen(QColor(pal["border"]), 1))
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

        for index, label in enumerate(self.labels):
            centre = rect.left() + slot * (index + 0.5)
            a_value = self.series_a[index] if index < len(self.series_a) else 0
            height_a = (a_value / peak) * rect.height()

            painter.setBrush(QColor(theme.SERIES[0]))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(
                QRectF(centre - bar_width - gap / 2, rect.bottom() - height_a,
                       bar_width, height_a),
                3, 3,
            )

            if self.series_b:
                b_value = self.series_b[index] if index < len(self.series_b) else 0
                height_b = (b_value / peak) * rect.height()
                painter.setBrush(QColor(theme.SERIES[3]))
                painter.drawRoundedRect(
                    QRectF(centre + gap / 2, rect.bottom() - height_b,
                           bar_width, height_b),
                    3, 3,
                )

            painter.setPen(QColor(pal["text_dim"]))
            font = QFont(painter.font())
            font.setPointSizeF(max(7.0, font.pointSizeF() - 2))
            painter.setFont(font)
            painter.drawText(
                QRectF(centre - slot / 2, rect.bottom() + 3, slot, 18),
                Qt.AlignHCenter | Qt.AlignTop,
                str(label),
            )
        painter.end()


class DonutChart(QWidget):
    """A donut/ring chart with a legend, drawn with QPainter."""

    def __init__(self, parent=None, height=180):
        super().__init__(parent)
        self.slices = []  # list of (label, value, colour)
        self.centre_text = ""
        self.centre_sub = ""
        self.setMinimumHeight(height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_data(self, slices, centre_text="", centre_sub=""):
        self.slices = list(slices)
        self.centre_text = centre_text
        self.centre_sub = centre_sub
        self.update()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pal = theme.palette(self.property("themeName") or "dark")

        total = sum(max(0, value) for _, value, _ in self.slices)
        if not self.slices or total <= 0:
            painter.setPen(QColor(pal["text_dim"]))
            painter.drawText(self.rect(), Qt.AlignCenter, "No data yet")
            painter.end()
            return

        size = min(self.height() - 16, self.width() * 0.45)
        size = max(60, size)
        left = 8
        top = (self.height() - size) / 2
        ring = QRectF(left, top, size, size)

        start = 90 * 16
        for index, (_, value, colour) in enumerate(self.slices):
            span = -int(round(max(0, value) / total * 360 * 16))
            if span == 0:
                continue
            painter.setBrush(QColor(colour or theme.SERIES[index % len(theme.SERIES)]))
            painter.setPen(Qt.NoPen)
            painter.drawPie(ring, start, span)
            start += span

        # punch the hole
        inner = ring.adjusted(size * 0.28, size * 0.28, -size * 0.28, -size * 0.28)
        painter.setBrush(QColor(pal["surface"]))
        painter.drawEllipse(inner)

        if self.centre_text:
            painter.setPen(QColor(pal["text"]))
            font = QFont(painter.font())
            font.setPointSizeF(font.pointSizeF() + 2)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(
                QRectF(ring.left(), ring.center().y() - 20, size, 22),
                Qt.AlignCenter,
                self.centre_text,
            )
            if self.centre_sub:
                font.setBold(False)
                font.setPointSizeF(max(7.0, font.pointSizeF() - 4))
                painter.setFont(font)
                painter.setPen(QColor(pal["text_dim"]))
                painter.drawText(
                    QRectF(ring.left(), ring.center().y() + 2, size, 18),
                    Qt.AlignCenter,
                    self.centre_sub,
                )

        # legend
        legend_x = left + size + 18
        legend_y = top + 4
        font = QFont(painter.font())
        font.setBold(False)
        font.setPointSizeF(max(7.0, font.pointSizeF() - 1))
        painter.setFont(font)
        for index, (label, value, colour) in enumerate(self.slices[:9]):
            share = value / total * 100 if total else 0
            painter.setBrush(QColor(colour or theme.SERIES[index % len(theme.SERIES)]))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(legend_x, legend_y + 4, 10, 10), 2, 2)
            painter.setPen(QColor(pal["text"]))
            painter.drawText(
                QRectF(legend_x + 16, legend_y, self.width() - legend_x - 20, 18),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"{label}  \u00b7  {share:.0f}%",
            )
            legend_y += 19
        painter.end()


class ProgressRow(QWidget):
    """A labelled progress bar, used for budgets and course progress."""

    def __init__(self, label, value_text="", percent=0.0, colour=None, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QProgressBar

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(4)

        row = QHBoxLayout()
        self.label = QLabel(label)
        self.value_label = QLabel(value_text)
        self.value_label.setObjectName("Muted")
        row.addWidget(self.label, 1)
        row.addWidget(self.value_label, 0)
        layout.addLayout(row)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(int(max(0.0, min(100.0, percent))))
        self.bar.setTextVisible(False)
        if colour:
            self.bar.setStyleSheet(
                f"QProgressBar::chunk {{ background: {colour}; border-radius: 6px; }}"
            )
        layout.addWidget(self.bar)


class TagLabel(QLabel):
    """A small pill used for tags and statuses."""

    def __init__(self, text, colour=None, parent=None):
        super().__init__(text, parent)
        pal = theme.palette("dark")
        colour = colour or pal["accent"]
        self.setStyleSheet(
            f"background: {colour}22; color: {colour};"
            "border-radius: 9px; padding: 2px 9px; font-size: 11px;"
        )
        self.setAlignment(Qt.AlignCenter)


def money_label(minor, currency="RUB", signed=False):
    """Return a QLabel styled green/red according to the sign."""
    from ..core import money

    text = money.format_amount(minor, currency, sign=signed)
    label = QLabel(text)
    if signed and minor > 0:
        label.setObjectName("Positive")
    elif signed and minor < 0:
        label.setObjectName("Negative")
    return label
