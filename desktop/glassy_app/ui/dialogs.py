"""Shared dialog helpers so every page reports errors the same way."""

from PySide6.QtWidgets import QMessageBox


def show_error(parent, message, title="Something went wrong"):
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning)
    box.setWindowTitle(title)
    box.setText(str(message))
    box.exec()


def show_info(parent, message, title="Done"):
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Information)
    box.setWindowTitle(title)
    box.setText(str(message))
    box.exec()


def confirm(parent, message, title="Please confirm"):
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Question)
    box.setWindowTitle(title)
    box.setText(str(message))
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.setDefaultButton(QMessageBox.No)
    return box.exec() == QMessageBox.Yes
