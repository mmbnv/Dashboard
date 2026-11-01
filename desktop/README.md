# Glassy Ledger

A native desktop application for personal record keeping, written in Python
with PySide6 (Qt 6). It is a real Windows program — not a browser extension and
not a web page in a shell — and it ships as a genuine `GlassyLedger.exe`.

Everything runs and is stored locally. There is no server, no account and no
network access. The database is a single SQLite file on your own computer.

## What is inside

| Page | What it does |
| --- | --- |
| **Dashboard** | Net worth, monthly income and spending, cash-flow chart, spending donut, account balances, recent transactions, budgets and module summaries — all on one screen. |
| **Wallet** | Accounts, transactions, categories, budgets and transfers, with monthly summaries. |
| **Tasks** | A three-column board (to do / in progress / done) plus a filterable list, priorities, due dates, tags, notes and an overdue count. |
| **Learning** | Courses and study sessions with progress, time logged and ratings. |
| **Registries** | User-defined tables: create your own columns and store arbitrary records. |
| **Workbook** | Free-form notes and entries with a simple editor. |
| **Calculator** | An expression calculator with history. |
| **Settings** | Theme, currency, database path, backup and restore, data export and reset. |

## Highlights

- **Native desktop chrome** — a real menu bar (File / View / Go / Help), a status
  bar, keyboard shortcuts and a window that remembers its size and position
  between runs.
- **Dark and light themes**, switchable from the View menu or Settings.
- **Local SQLite database** with 13 tables, created automatically on first run
  and seeded with example data so the app is never empty.
- **Backups and export** — one-click database backup, full JSON export and
  transactions to CSV.
- **Offline and private** — nothing leaves the machine.

## Running from source

Requires Python 3.11 or newer.

```bash
cd desktop
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
python -m glassy_app
```

On a headless Linux machine, run it under a virtual display:

```bash
xvfb-run -a python -m glassy_app
```

## Building the Windows executable

The build produces a one-folder distribution in `dist/GlassyLedger`, which
contains `GlassyLedger.exe` and the Qt runtime it needs.

```bash
pip install -r requirements-dev.txt
pyinstaller packaging/glassy_ledger.spec --noconfirm
```

Set `GLASSY_ONE_FILE=1` to build a single self-contained executable instead.
The icon in `packaging/app.ico` is embedded automatically.

## Where your data lives

The application picks its data directory in this order:

1. `GLASSY_LEDGER_HOME`, if set — useful for portable installs.
2. `%APPDATA%\GlassyLedger` on Windows, or
   `~/.local/share/glassy-ledger` on Linux (honouring `XDG_DATA_HOME`).

The database is `ledger.db` inside that directory, alongside a `backups`
folder. Back up that folder and you have backed up everything.

## Tests

The suite drives the real widgets rather than mocks, and includes a regression
test that samples painted pixels to prove the page background follows the
theme.

```bash
python -m pytest tests -q          # needs a display for the GUI tests
DISPLAY=:99 python -m pytest tests -q
```

`tools/gui_smoke.py` goes further: it opens every page, takes a screenshot of
each one, writes a task through the service layer and confirms it persisted.

```bash
DISPLAY=:99 python tools/gui_smoke.py /tmp/shots
```

## Project layout

```
glassy_app/
  app.py              application object: database + one service per module
  core/               database, models, money handling, calculator, errors
  repositories/       data access, one per table group
  services/           business logic per module
  ui/                 main window, theme, shared widgets, pages, dialogs
  assets/             runtime icon
packaging/            PyInstaller spec and the .ico
tests/                data and GUI tests
tools/gui_smoke.py    end-to-end GUI smoke run
run.py                entry point used by the frozen build
```
