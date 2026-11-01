"""GUI tests. These drive the real widgets, not mocks.

They require a display; run under Xvfb:

    DISPLAY=:99 python -m pytest tests/test_gui.py

A missing display skips the whole module rather than failing, so the data
tests still run on a headless machine.
"""

import os
from datetime import date

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from glassy_app.app import Application  # noqa: E402
from glassy_app.core.models import EXPENSE  # noqa: E402
from glassy_app.ui.main_window import NAV_ITEMS, MainWindow  # noqa: E402

pytestmark = pytest.mark.skipif(
    not os.environ.get("DISPLAY") and os.name != "nt",
    reason="no display available; run under Xvfb",
)


@pytest.fixture(scope="session")
def qt_app():
    application = QApplication.instance() or QApplication([])
    yield application


@pytest.fixture()
def window(qt_app, data_dir):
    ledger = Application(data_dir=data_dir)
    win = MainWindow(ledger)
    win.resize(1280, 820)
    win.show()
    qt_app.processEvents()
    yield win
    win.close()
    ledger.close()


def test_every_nav_item_has_a_page(window):
    for key, _label, _icon in NAV_ITEMS:
        assert key in window.pages, key


def test_every_page_builds_and_refreshes(window, qt_app):
    """The real regression net: build + refresh each page in order."""
    for key, label, _icon in NAV_ITEMS:
        window.show_page(key)
        qt_app.processEvents()
        assert window.stack.currentWidget() is window.pages[key], label


def test_pages_render_something(window, qt_app):
    """A page that paints nothing is a bug, so check the grab is not blank."""
    for key, _label, _icon in NAV_ITEMS:
        window.show_page(key)
        qt_app.processEvents()
        image = window.grab().toImage()
        width, height = image.width(), image.height()
        assert width > 400 and height > 300
        # Count distinct colours on a coarse grid. A blank page yields 1.
        colours = {
            image.pixel(x, y)
            for x in range(0, width, 17)
            for y in range(0, height, 17)
        }
        assert len(colours) > 5, f"page {key} looks blank ({len(colours)} colours)"


def test_navigation_updates_the_checked_button(window, qt_app):
    window.show_page("wallet")
    qt_app.processEvents()
    assert window.nav_buttons["wallet"].isChecked()
    assert not window.nav_buttons["dashboard"].isChecked()


def test_last_page_is_remembered(window, qt_app, data_dir):
    window.show_page("calculator")
    qt_app.processEvents()
    assert window.app.last_page == "calculator"
    window.close()

    ledger = Application(data_dir=data_dir)
    again = MainWindow(ledger)
    assert again.stack.currentWidget() is again.pages["calculator"]
    again.close()
    ledger.close()


def test_theme_switch_applies_to_every_page(window, qt_app):
    for theme_name in ("light", "dark"):
        window.app.theme = theme_name
        window.apply_theme(theme_name)
        qt_app.processEvents()
        assert window.styleSheet()
    # Both stylesheets must actually differ.
    window.apply_theme("dark")
    dark = window.styleSheet()
    window.apply_theme("light")
    light = window.styleSheet()
    assert dark != light


def test_adding_a_transaction_through_the_service_updates_the_table(window, qt_app):
    wallet = window.pages["wallet"]
    window.show_page("wallet")
    qt_app.processEvents()

    account = window.app.wallet.list_accounts(with_balances=False)[0]["id"]
    groceries = [
        c for c in window.app.wallet.list_categories(EXPENSE)
        if c["name"] == "Продукты"
    ][0]["id"]
    window.app.wallet.add_transaction(
        account, EXPENSE, "123,45", date.today().isoformat(), groceries, "Test shop"
    )
    wallet.refresh()
    qt_app.processEvents()

    rows = wallet.tx_table.rowCount()
    assert rows >= 1
    found = any(
        wallet.tx_table.item(row, 5)
        and wallet.tx_table.item(row, 5).text() == "Test shop"
        for row in range(rows)
    )
    assert found, "the new transaction is not in the table"


def test_task_board_shows_seeded_task(window, qt_app):
    window.show_page("tasks")
    qt_app.processEvents()
    board = window.pages["tasks"]
    total = sum(
        box.count() for box, _ in board.columns.values()
    )
    assert total >= 1


def test_moving_a_task_changes_its_column(window, qt_app):
    board = window.pages["tasks"]
    window.show_page("tasks")
    qt_app.processEvents()

    task_id = window.app.tasks.create_task("Move me")
    board.refresh()
    qt_app.processEvents()

    def card_titles(status):
        titles = []
        box, _count = board.columns[status]
        for index in range(box.count()):
            widget = box.itemAt(index).widget()
            if widget is None:
                continue
            from PySide6.QtWidgets import QLabel

            for label in widget.findChildren(QLabel):
                titles.append(label.text())
        return titles

    assert "Move me" in card_titles("todo")

    window.app.tasks.set_status(task_id, "done")
    board.refresh()
    qt_app.processEvents()

    assert "Move me" not in card_titles("todo")
    assert "Move me" in card_titles("done")


def test_calculator_button_press_computes(window, qt_app):
    page = window.pages["calculator"]
    window.show_page("calculator")
    qt_app.processEvents()
    page.expression.setText("12*12")
    page._evaluate()
    qt_app.processEvents()
    assert page.result.text() == "144"
    assert page.history_list.count() == 1


def test_registry_page_can_create_and_show_a_record(window, qt_app):
    page = window.pages["registries"]
    window.show_page("registries")
    qt_app.processEvents()

    registry_id = window.app.registries.create_from_template("inventory")
    window.app.registries.add_record(
        registry_id, {"name": "Wrench", "qty": "3", "price": "12.50"}
    )
    page.refresh(registry_id)
    qt_app.processEvents()

    assert page.records_table.rowCount() == 1
    assert page.records_table.item(0, 0).text() == "Wrench"
    assert "12.50" in page.records_table.item(0, 2).text()


def test_workbook_editor_round_trip(window, qt_app):
    page = window.pages["workbook"]
    window.show_page("workbook")
    qt_app.processEvents()

    page._new_entry()
    page.title_input.setText("GUI note")
    page.body_edit.setPlainText("written from the test")
    page._save()
    qt_app.processEvents()

    titles = [
        page.entry_list.item(row).text()
        for row in range(page.entry_list.count())
    ]
    assert any("GUI note" in title for title in titles)
    entries = window.app.workbook.list_entries(text="GUI note")
    assert entries[0]["body"] == "written from the test"


def test_settings_page_shows_the_database_path(window, qt_app):
    page = window.pages["settings"]
    window.show_page("settings")
    qt_app.processEvents()
    assert str(window.app.database_path) in page.path_label.text()
    assert "accounts" in page.counts_label.text()


def test_window_state_is_saved_and_restored(window, qt_app, data_dir):
    """Geometry must survive a restart, like any real desktop application."""
    window.setGeometry(120, 90, 1100, 700)
    qt_app.processEvents()
    window.close()  # closeEvent persists the state

    ledger = Application(data_dir=data_dir)
    restored = MainWindow(ledger)
    geometry = restored.geometry()
    assert (geometry.width(), geometry.height()) == (1100, 700), (
        f"window size not restored: {geometry.width()}x{geometry.height()}"
    )
    assert (geometry.x(), geometry.y()) == (120, 90)
    restored.close()


def test_menu_bar_has_expected_menus(window):
    """A desktop application needs a menu bar, not just sidebar buttons."""
    menus = [a.menu().title().replace("&", "") for a in window.menuBar().actions()
             if a.menu()]
    for expected in ("Файл", "Вид", "Переход", "Справка"):
        assert expected in menus, f"missing {expected} menu: {menus}"


def test_menu_actions_are_wired(window):
    """Every menu entry must have a target, and shortcuts must not collide."""
    shortcuts = []
    action_count = 0
    for top in window.menuBar().actions():
        menu = top.menu()
        if menu is None:
            continue
        for action in menu.actions():
            if action.isSeparator():
                continue
            action_count += 1
            assert not action.text().startswith("&") or len(action.text()) > 1
            key = action.shortcut().toString()
            if key:
                shortcuts.append(key)
    assert action_count >= 10, f"only {action_count} menu actions"
    assert len(shortcuts) == len(set(shortcuts)), (
        f"duplicate shortcuts: {sorted(shortcuts)}"
    )


def test_theme_can_be_switched_from_the_menu(window, qt_app):
    window._set_theme("light")
    assert window.app.theme == "light"
    assert "background" in window.styleSheet()
    window._set_theme("dark")
    assert window.app.theme == "dark"


def test_about_dialog_builds(window, qt_app, monkeypatch):
    """The About box must open without blocking the test run."""
    from PySide6.QtWidgets import QMessageBox

    seen = {}
    monkeypatch.setattr(
        QMessageBox, "exec", lambda self: seen.setdefault("title", self.windowTitle())
    )
    window._about()
    assert "Glassy Ledger" in seen["title"]


def test_close_saves_window_state(window, data_dir):
    window.setGeometry(200, 150, 1024, 768)
    window.close()
    state = Application(data_dir=data_dir).window_state
    assert state["geometry"] == [200, 150, 1024, 768]
    assert state["maximized"] is False


def test_backup_action_writes_a_file(window, monkeypatch):
    """The File > Backup action must write a real backup file.

    The confirmation dialog is stubbed out; the backup itself runs for real.
    """
    from glassy_app.ui import main_window as mw

    monkeypatch.setattr(mw, "show_info", lambda *a, **k: None)
    window._backup()
    backups = window.app.list_backups()
    assert backups, "backup action produced no file"


def test_closing_the_app_twice_is_safe(data_dir):
    """Regression: closeEvent wrote to the database after it was closed."""
    ledger = Application(data_dir=data_dir)
    ledger.close()
    ledger.close()  # must not raise
    assert ledger._closed is True


def test_window_close_after_app_close_is_safe(window, qt_app):
    """Regression: closing the window after the app must not touch the DB."""
    window.app.close()
    window.close()  # must not raise sqlite3.ProgrammingError


def test_page_background_follows_the_theme(window, qt_app):
    """Regression: the page area used to stay white behind the cards.

    Qt falls back to the platform palette for widgets the stylesheet does not
    name, so this checks the actual painted pixels rather than the stylesheet
    text.
    """
    window.show_page("dashboard")
    qt_app.processEvents()

    def background_pixels():
        image = window.grab().toImage()
        width, height = image.width(), image.height()
        samples = []
        # A grid over the page area, skipping the sidebar on the left.
        for y in range(40, height - 40, 23):
            for x in range(240, width - 40, 97):
                colour = image.pixelColor(x, y)
                samples.append((colour.red(), colour.green(), colour.blue()))
        return samples

    def brightness(rgb):
        return sum(rgb) / 3

    def share_light(samples):
        # The old bug showed up as near-white (239,239,239) regions.
        return sum(1 for s in samples if brightness(s) > 200) / len(samples)

    def share_dark(samples):
        return sum(1 for s in samples if brightness(s) < 60) / len(samples)

    window.apply_theme("dark")
    qt_app.processEvents()
    dark_samples = background_pixels()

    window.apply_theme("light")
    qt_app.processEvents()
    light_samples = background_pixels()

    # Dark theme: the page background must be dark and must not be white.
    assert share_dark(dark_samples) > 0.5, (
        f"dark theme page background is not dark: "
        f"{share_dark(dark_samples):.2f} dark, {share_light(dark_samples):.2f} light"
    )
    assert share_light(dark_samples) < 0.2, (
        f"white background leaked into the dark theme: "
        f"{share_light(dark_samples):.2f} of samples are near-white"
    )
    # Light theme: the page background must be light.
    assert share_light(light_samples) > 0.4, (
        f"light theme page background is not light: "
        f"{share_light(light_samples):.2f} light"
    )

    window.apply_theme("dark")


def test_dashboard_kpis_show_numbers(window, qt_app):
    page = window.pages["dashboard"]
    window.show_page("dashboard")
    qt_app.processEvents()
    value = page.kpi_cards["net_worth"].value_label.text()
    assert value and value != "\u2014"
    assert "0" in value or any(ch.isdigit() for ch in value)
