import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import QtCore, QtWidgets

from mail_fetcher.dialogs import PhoneDialog
from mail_fetcher.models import PhoneRecord
from mail_fetcher.ui import app_stylesheet


class FakePhoneStore:
    max_emails_per_phone = 3

    def __init__(self) -> None:
        self.phones = [
            PhoneRecord(
                phone="+12638883107",
                api_url="https://api.sms8.net/api/record?token=test",
                emails=["bound@example.com"],
                last_status="成功",
            )
        ]

    def get(self, phone_number: str):
        return next((phone for phone in self.phones if phone.phone == phone_number), None)


class PhoneDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self) -> None:
        self.dialog = PhoneDialog(FakePhoneStore(), ["bound@example.com"])
        self.dialog.setStyleSheet(app_stylesheet("light"))
        self.dialog.show()
        self.app.processEvents()

    def tearDown(self) -> None:
        self.dialog.close()

    def test_bound_email_cell_tracks_row_selection(self) -> None:
        cell = self.dialog.table.cellWidget(0, 2)
        self.assertEqual(cell.property("selected"), "true")
        selected_color = cell.grab().toImage().pixelColor(cell.width() // 2, cell.height() // 2)
        self.assertEqual(selected_color.name(), "#dbe7ff")

        self.dialog.table.clearSelection()
        self.app.processEvents()
        self.assertEqual(cell.property("selected"), "false")

    def test_copy_phone_uses_button_and_context_menu_is_disabled(self) -> None:
        self.assertEqual(
            self.dialog.table.contextMenuPolicy(),
            QtCore.Qt.ContextMenuPolicy.NoContextMenu,
        )
        copy_button = next(
            button
            for button in self.dialog.findChildren(QtWidgets.QPushButton)
            if button.text() == "复制手机号"
        )
        copy_button.click()
        self.assertEqual(
            QtWidgets.QApplication.clipboard().text(),
            "+12638883107",
        )


if __name__ == "__main__":
    unittest.main()
