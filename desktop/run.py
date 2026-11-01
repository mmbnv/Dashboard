#!/usr/bin/env python3
"""Launcher for the packaged build.

PyInstaller needs a plain script as its entry point. This one keeps the
frozen build working the same way as ``python -m glassy_app``.
"""

import multiprocessing
import sys


def main():
    # Required before any Qt import in a frozen build, otherwise a spawned
    # child process would re-run the whole application.
    multiprocessing.freeze_support()

    from glassy_app.__main__ import main as app_main

    return app_main(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
