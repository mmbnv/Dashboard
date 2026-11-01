"""Visual theme: colour palettes and Qt stylesheets.

The app ships a dark and a light palette. Both are defined here and applied
through a single stylesheet so every page looks consistent without per-widget
styling.
"""

DARK = {
    "name": "dark",
    "bg": "#0f1117",
    "surface": "#171a23",
    "surface_alt": "#1e222d",
    "border": "#2a2f3d",
    "text": "#e8eaf0",
    "text_dim": "#9aa2b5",
    "accent": "#7c3aed",
    "accent_hover": "#8b5cf6",
    "accent_soft": "#241b3d",
    "success": "#22c55e",
    "danger": "#ef4444",
    "warning": "#f59e0b",
    "info": "#38bdf8",
    "selection": "#2d2450",
}

LIGHT = {
    "name": "light",
    "bg": "#f4f5f9",
    "surface": "#ffffff",
    "surface_alt": "#eef0f6",
    "border": "#d8dce8",
    "text": "#1c1f2a",
    "text_dim": "#5b6376",
    "accent": "#7c3aed",
    "accent_hover": "#6d28d9",
    "accent_soft": "#ede9fe",
    "success": "#15803d",
    "danger": "#dc2626",
    "warning": "#b45309",
    "info": "#0284c7",
    "selection": "#ddd6fe",
}

PALETTES = {"dark": DARK, "light": LIGHT}

# Chart series colours, used by the bar and donut widgets.
SERIES = [
    "#7c3aed", "#38bdf8", "#22c55e", "#f59e0b",
    "#ef4444", "#a855f7", "#14b8a6", "#f472b6",
]


def palette(name):
    return PALETTES.get(name, DARK)


def qt_palette(name):
    """Build a QPalette for the theme.

    Setting this as well as the stylesheet matters: widgets that draw
    themselves with the palette (scroll area viewports, tooltips, the text
    caret) would otherwise keep the platform default and show white patches on
    a dark theme.
    """
    from PySide6.QtGui import QColor, QPalette

    c = palette(name)
    result = QPalette()
    result.setColor(QPalette.Window, QColor(c["bg"]))
    result.setColor(QPalette.WindowText, QColor(c["text"]))
    result.setColor(QPalette.Base, QColor(c["surface"]))
    result.setColor(QPalette.AlternateBase, QColor(c["surface_alt"]))
    result.setColor(QPalette.Text, QColor(c["text"]))
    result.setColor(QPalette.PlaceholderText, QColor(c["text_dim"]))
    result.setColor(QPalette.Button, QColor(c["surface_alt"]))
    result.setColor(QPalette.ButtonText, QColor(c["text"]))
    result.setColor(QPalette.ToolTipBase, QColor(c["surface_alt"]))
    result.setColor(QPalette.ToolTipText, QColor(c["text"]))
    result.setColor(QPalette.Highlight, QColor(c["accent"]))
    result.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    result.setColor(QPalette.Link, QColor(c["accent_hover"]))
    disabled = QColor(c["text_dim"])
    result.setColor(QPalette.Disabled, QPalette.Text, disabled)
    result.setColor(QPalette.Disabled, QPalette.ButtonText, disabled)
    result.setColor(QPalette.Disabled, QPalette.WindowText, disabled)
    return result


def stylesheet(name):
    """Return the Qt stylesheet for the given theme name."""
    c = palette(name)
    return f"""
    * {{
        font-family: "Segoe UI", "Inter", "DejaVu Sans", sans-serif;
        font-size: 13px;
        color: {c['text']};
    }}
    QWidget#Root {{
        background: {c['bg']};
    }}
    /* The stacked page area, the scroll viewports and every page container
       must paint the theme background. Without this Qt falls back to the
       platform default (white) behind the cards. */
    QStackedWidget, QScrollArea, QScrollArea > QWidget > QWidget {{
        background: {c['bg']};
    }}
    QScrollArea > QWidget > QWidget > QWidget {{
        background: {c['bg']};
    }}
    QMainWindow, QDialog {{
        background: {c['bg']};
    }}
    QWidget#PageContainer {{
        background: {c['bg']};
    }}

    /* ---- sidebar ---- */
    QFrame#Sidebar {{
        background: {c['surface']};
        border-right: 1px solid {c['border']};
    }}
    QLabel#Brand {{
        font-size: 18px;
        font-weight: 700;
        padding: 4px 0 2px 0;
    }}
    QLabel#BrandSub {{
        color: {c['text_dim']};
        font-size: 11px;
    }}
    QPushButton#NavButton {{
        text-align: left;
        padding: 10px 14px;
        border: none;
        border-radius: 10px;
        background: transparent;
        color: {c['text_dim']};
        font-size: 14px;
    }}
    QPushButton#NavButton:hover {{
        background: {c['surface_alt']};
        color: {c['text']};
    }}
    QPushButton#NavButton:checked {{
        background: {c['accent_soft']};
        color: {c['text']};
        font-weight: 600;
    }}

    /* ---- cards ---- */
    QFrame#Card {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 14px;
    }}
    QFrame#CardAlt {{
        background: {c['surface_alt']};
        border: 1px solid {c['border']};
        border-radius: 12px;
    }}
    QLabel#CardTitle {{
        font-size: 12px;
        color: {c['text_dim']};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    QLabel#CardValue {{
        font-size: 24px;
        font-weight: 700;
    }}
    QLabel#PageTitle {{
        font-size: 22px;
        font-weight: 700;
    }}
    QLabel#PageSubtitle {{
        color: {c['text_dim']};
    }}
    QLabel#Muted {{
        color: {c['text_dim']};
    }}
    QLabel#SectionTitle {{
        font-size: 15px;
        font-weight: 600;
    }}
    QLabel#Positive {{ color: {c['success']}; font-weight: 600; }}
    QLabel#Negative {{ color: {c['danger']}; font-weight: 600; }}
    QLabel#Warning  {{ color: {c['warning']}; font-weight: 600; }}

    /* ---- buttons ---- */
    QPushButton {{
        background: {c['surface_alt']};
        border: 1px solid {c['border']};
        border-radius: 9px;
        padding: 8px 14px;
    }}
    QPushButton:hover {{
        border-color: {c['accent']};
    }}
    QPushButton:disabled {{
        color: {c['text_dim']};
        background: {c['surface']};
    }}
    QPushButton#Primary {{
        background: {c['accent']};
        border: 1px solid {c['accent']};
        color: #ffffff;
        font-weight: 600;
    }}
    QPushButton#Primary:hover {{
        background: {c['accent_hover']};
        border-color: {c['accent_hover']};
    }}
    QPushButton#Danger {{
        background: transparent;
        border: 1px solid {c['danger']};
        color: {c['danger']};
    }}
    QPushButton#Danger:hover {{
        background: {c['danger']};
        color: #ffffff;
    }}
    QPushButton#Ghost {{
        background: transparent;
        border: 1px solid transparent;
        color: {c['text_dim']};
    }}
    QPushButton#Ghost:hover {{
        color: {c['text']};
        background: {c['surface_alt']};
    }}
    QPushButton#Chip {{
        border-radius: 14px;
        padding: 5px 12px;
        font-size: 12px;
    }}
    QPushButton#Chip:checked {{
        background: {c['accent']};
        border-color: {c['accent']};
        color: #ffffff;
    }}

    /* ---- inputs ---- */
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QDateEdit, QTimeEdit {{
        background: {c['surface_alt']};
        border: 1px solid {c['border']};
        border-radius: 9px;
        padding: 8px 10px;
        selection-background-color: {c['accent']};
        selection-color: #ffffff;
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
    QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
    QDateEdit:focus {{
        border: 1px solid {c['accent']};
    }}
    QLineEdit:disabled, QComboBox:disabled {{
        color: {c['text_dim']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 22px;
    }}
    QComboBox QAbstractItemView {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        selection-background-color: {c['accent']};
        selection-color: #ffffff;
        outline: none;
    }}
    QDateEdit::drop-down, QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
        border: none;
        background: transparent;
    }}

    /* ---- tables ---- */
    QTableWidget, QTableView {{
        background: {c['surface']};
        alternate-background-color: {c['surface_alt']};
        border: 1px solid {c['border']};
        border-radius: 12px;
        gridline-color: {c['border']};
        selection-background-color: {c['selection']};
        selection-color: {c['text']};
        outline: none;
    }}
    QTableWidget::item, QTableView::item {{
        padding: 6px 8px;
        border: none;
    }}
    QHeaderView::section {{
        background: {c['surface_alt']};
        color: {c['text_dim']};
        border: none;
        border-bottom: 1px solid {c['border']};
        padding: 8px;
        font-weight: 600;
    }}
    QTableCornerButton::section {{
        background: {c['surface_alt']};
        border: none;
    }}

    /* ---- tabs ---- */
    QTabWidget::pane {{
        border: 1px solid {c['border']};
        border-radius: 12px;
        background: {c['surface']};
        top: -1px;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {c['text_dim']};
        padding: 9px 16px;
        border: none;
        border-bottom: 2px solid transparent;
        margin-right: 4px;
    }}
    QTabBar::tab:hover {{ color: {c['text']}; }}
    QTabBar::tab:selected {{
        color: {c['text']};
        border-bottom: 2px solid {c['accent']};
        font-weight: 600;
    }}

    /* ---- scrollbars ---- */
    QScrollBar:vertical {{
        background: transparent; width: 10px; margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {c['border']}; border-radius: 5px; min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {c['accent']}; }}
    QScrollBar:horizontal {{
        background: transparent; height: 10px; margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {c['border']}; border-radius: 5px; min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{ background: {c['accent']}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

    /* ---- misc ---- */
    QProgressBar {{
        background: {c['surface_alt']};
        border: none;
        border-radius: 6px;
        height: 10px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background: {c['accent']};
        border-radius: 6px;
    }}
    QListWidget {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 12px;
        outline: none;
        padding: 4px;
    }}
    QListWidget::item {{
        padding: 8px 10px;
        border-radius: 8px;
    }}
    QListWidget::item:selected {{
        background: {c['selection']};
        color: {c['text']};
    }}
    QListWidget::item:hover {{ background: {c['surface_alt']}; }}
    QMenu {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{ padding: 7px 22px 7px 14px; border-radius: 6px; }}
    QMenu::item:selected {{ background: {c['accent']}; color: #ffffff; }}
    QToolTip {{
        background: {c['surface_alt']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 5px 8px;
    }}
    QSplitter::handle {{ background: {c['border']}; }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 16px; height: 16px;
        border: 1px solid {c['border']};
        border-radius: 4px;
        background: {c['surface_alt']};
    }}
    QCheckBox::indicator:checked {{
        background: {c['accent']};
        border-color: {c['accent']};
    }}
    QGroupBox {{
        border: 1px solid {c['border']};
        border-radius: 12px;
        margin-top: 14px;
        padding-top: 10px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {c['text_dim']};
    }}
    QStatusBar {{
        background: {c['surface']};
        border-top: 1px solid {c['border']};
        color: {c['text_dim']};
    }}
    QMessageBox {{ background: {c['surface']}; }}
    """
