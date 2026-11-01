"""Shared dialog helpers so every page reports errors the same way."""

from PySide6.QtWidgets import QMessageBox


def show_error(parent, message, title="Что-то пошло не так"):
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning)
    box.setWindowTitle(title)
    box.setText(str(message))
    box.exec()


def show_info(parent, message, title="Готово"):
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Information)
    box.setWindowTitle(title)
    box.setText(str(message))
    box.exec()


def confirm(parent, message, title="Подтвердите действие"):
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Question)
    box.setWindowTitle(title)
    box.setText(str(message))
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.setButtonText(QMessageBox.Yes, "Да")
    box.setButtonText(QMessageBox.No, "Нет")
    box.setDefaultButton(QMessageBox.No)
    return box.exec() == QMessageBox.Yes
