from __future__ import annotations

from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from .models import ImportRecord, PhoneRecord
from .parsing import parse_import_text, parse_phone_import_text
from .services import SmsService
from .storage import PhoneStore
from .widgets.common import pill_button


class ImportDialog(QtWidgets.QDialog):
    import_requested = QtCore.pyqtSignal(object, int)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("批量导入邮箱")
        self.resize(880, 620)
        self.setMinimumSize(760, 560)
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("批量导入邮箱")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        desc = QtWidgets.QLabel("每行格式：email----password----client_id----graph_refresh_token。导出文件会多一段分类，也会保留绑定手机号和短信API。")
        desc.setObjectName("DialogText")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setObjectName("ImportEditor")
        self.editor.setPlaceholderText("每行一个账号，四段或五段用 ---- 分隔")
        layout.addWidget(self.editor, 1)

        actions = QtWidgets.QHBoxLayout()
        actions.setSpacing(10)
        self.load_button = pill_button("从文件载入", role="secondary")
        self.load_button.clicked.connect(self.load_file)
        actions.addWidget(self.load_button)

        actions.addStretch(1)
        cancel_button = pill_button("取消", role="secondary")
        cancel_button.clicked.connect(self.reject)
        actions.addWidget(cancel_button)

        import_button = pill_button("导入并取件", role="primary")
        import_button.clicked.connect(self.submit)
        actions.addWidget(import_button)
        layout.addLayout(actions)

    def load_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择账号文本",
            "",
            "Text files (*.txt *.csv);;All files (*.*)",
        )
        if not path:
            return
        self.editor.setPlainText(Path(path).read_text(encoding="utf-8", errors="ignore"))

    def submit(self) -> None:
        records, invalid = parse_import_text(self.editor.toPlainText())
        if not records:
            QtWidgets.QMessageBox.warning(self, "没有账号", "没有识别到有效邮箱。")
            return
        self.import_requested.emit(records, invalid)
        self.accept()


class MailDetailDialog(QtWidgets.QDialog):
    def __init__(self, row: dict, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.row = row
        self.setWindowTitle("邮件详情")
        self.resize(920, 620)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)

        subject = QtWidgets.QLabel(row.get("subject") or "(无主题)")
        subject.setObjectName("DialogTitle")
        subject.setWordWrap(True)
        layout.addWidget(subject)

        meta = QtWidgets.QLabel(
            f"{row.get('sender', '')}    {row.get('time', '')}    {row.get('protocol', '')}    {row.get('account', '')}"
        )
        meta.setObjectName("DialogText")
        meta.setWordWrap(True)
        layout.addWidget(meta)

        self.viewer = QtWidgets.QTextEdit()
        self.viewer.setObjectName("DetailViewer")
        self.viewer.setReadOnly(True)
        self.viewer.setPlainText(row.get("preview") or "")
        self.viewer.moveCursor(QtGui.QTextCursor.MoveOperation.Start)
        self.viewer.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        layout.addWidget(self.viewer, 1)

        actions = QtWidgets.QHBoxLayout()
        actions.addStretch(1)
        if row.get("webLink"):
            open_button = pill_button("打开网页版", role="primary")
            open_button.clicked.connect(self.open_link)
            actions.addWidget(open_button)
        close_button = pill_button("关闭", role="secondary")
        close_button.clicked.connect(self.accept)
        actions.addWidget(close_button)
        layout.addLayout(actions)

    def open_link(self) -> None:
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.row["webLink"]))


class PhoneCodeWorker(QtCore.QThread):
    result_ready = QtCore.pyqtSignal(object)
    error_ready = QtCore.pyqtSignal(str)

    def __init__(self, phone: PhoneRecord) -> None:
        super().__init__()
        self.phone = phone

    def run(self) -> None:
        try:
            row = SmsService().fetch_phone_row(self.phone, concise_mode=False)
            self.result_ready.emit(row)
        except Exception as exc:
            self.error_ready.emit(str(exc))


class PhoneDialog(QtWidgets.QDialog):
    changed = QtCore.pyqtSignal()
    sms_result_ready = QtCore.pyqtSignal(object)

    def __init__(
        self,
        phone_store: PhoneStore,
        selected_emails: list[str],
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.phone_store = phone_store
        self.selected_emails = selected_emails
        self.phone_worker: PhoneCodeWorker | None = None
        self.setWindowTitle("手机号管理")
        self.resize(960, 660)
        self.setMinimumSize(840, 580)
        self.setModal(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QtWidgets.QLabel("手机号管理")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        desc = QtWidgets.QLabel("每行格式：+12633008723----https://api.sms8.net/api/record?token=xxx。导出时会附带已绑定邮箱，重新导入会自动恢复绑定。")
        desc.setObjectName("DialogText")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.search = QtWidgets.QLineEdit()
        self.search.setObjectName("SearchField")
        self.search.setPlaceholderText("搜索手机号或绑定邮箱")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh_table)
        layout.addWidget(self.search)

        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["手机号", "邮箱数", "绑定邮箱", "状态"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setObjectName("ImportEditor")
        self.editor.setPlaceholderText("+12633008723----https://api.sms8.net/api/record?token=xxx")
        self.editor.setMaximumHeight(108)
        layout.addWidget(self.editor)

        selected_text = f"当前已勾选邮箱：{len(selected_emails)} 个"
        if selected_emails:
            selected_text += f"（{', '.join(selected_emails[:3])}{'...' if len(selected_emails) > 3 else ''}）"
        self.selected_label = QtWidgets.QLabel(selected_text)
        self.selected_label.setObjectName("DialogText")
        self.selected_label.setWordWrap(True)
        layout.addWidget(self.selected_label)

        self.code_label = QtWidgets.QLabel("验证码：等待获取")
        self.code_label.setObjectName("StatusLabel")
        self.code_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        self.code_label.setMinimumHeight(42)
        layout.addWidget(self.code_label)

        actions = QtWidgets.QHBoxLayout()
        actions.setSpacing(8)
        for text, slot, role in (
            ("从文件载入", self.load_file, "secondary"),
            ("导入手机号", self.import_phones, "primary"),
            ("获取验证码", self.fetch_selected_code, "primary"),
            ("复制手机号", self.copy_selected_phone, "secondary"),
            ("绑定选中邮箱", self.bind_selected_emails, "accent"),
            ("解绑选中邮箱", self.unbind_selected_emails, "secondary"),
            ("导出手机号", self.export_phones, "secondary"),
            ("删除手机号", self.delete_selected_phone, "danger"),
        ):
            button = pill_button(text, role=role)
            button.setFixedHeight(38)
            button.clicked.connect(slot)
            actions.addWidget(button)
        actions.addStretch(1)
        close_button = pill_button("关闭", role="secondary")
        close_button.setFixedHeight(38)
        close_button.clicked.connect(self.accept)
        actions.addWidget(close_button)
        layout.addLayout(actions)

        self.refresh_table()

    def filtered_phones(self):
        needle = self.search.text().strip().lower()
        phones = sorted(self.phone_store.phones, key=lambda item: item.phone.lower())
        if not needle:
            return phones
        return [
            phone
            for phone in phones
            if needle in phone.phone.lower()
            or needle in phone.api_url.lower()
            or any(needle in email.lower() for email in phone.emails)
        ]

    def refresh_table(self) -> None:
        phones = self.filtered_phones()
        self.table.setRowCount(len(phones))
        for row, phone in enumerate(phones):
            values = [
                phone.phone,
                f"{len(phone.emails)}/3",
                ", ".join(phone.emails),
                phone.last_status,
            ]
            for col, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setToolTip(phone.api_url if col == 0 else value)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, phone.phone)
                self.table.setItem(row, col, item)
        if phones:
            self.table.selectRow(0)

    def selected_phone_number(self) -> str:
        row = self.table.currentRow()
        if row < 0:
            return ""
        item = self.table.item(row, 0)
        return item.data(QtCore.Qt.ItemDataRole.UserRole) if item else ""

    def load_file(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择手机号文本",
            "",
            "Text files (*.txt *.csv);;All files (*.*)",
        )
        if path:
            self.editor.setPlainText(Path(path).read_text(encoding="utf-8", errors="ignore"))

    def copy_selected_phone(self) -> None:
        phone_number = self.selected_phone_number()
        if not phone_number:
            QtWidgets.QMessageBox.information(self, "请选择手机号", "请先在列表里选中一个手机号。")
            return
        QtWidgets.QApplication.clipboard().setText(phone_number)
        self.code_label.setText(f"已复制手机号：{phone_number}")

    def import_phones(self) -> None:
        records, invalid = parse_phone_import_text(self.editor.toPlainText())
        if not records:
            QtWidgets.QMessageBox.warning(self, "没有手机号", "没有识别到有效手机号。")
            return
        added, updated, skipped = self.phone_store.upsert_records(records)
        self.editor.clear()
        self.refresh_table()
        self.changed.emit()
        QtWidgets.QMessageBox.information(self, "导入完成", f"新增 {added}，更新 {updated}，重复 {skipped}，无效 {invalid}。")

    def bind_selected_emails(self) -> None:
        phone_number = self.selected_phone_number()
        if not phone_number:
            QtWidgets.QMessageBox.information(self, "请选择手机号", "请先在列表里选中一个手机号。")
            return
        if not self.selected_emails:
            QtWidgets.QMessageBox.information(self, "没有勾选邮箱", "请先在主界面勾选要绑定的邮箱。")
            return
        bound, rejected = self.phone_store.bind_emails(phone_number, set(self.selected_emails))
        self.refresh_table()
        self.changed.emit()
        message = f"已绑定 {bound} 个邮箱。"
        if rejected:
            message += f" 未绑定 {len(rejected)} 个，因为一个手机号最多绑定 3 个邮箱。"
        QtWidgets.QMessageBox.information(self, "绑定完成", message)

    def unbind_selected_emails(self) -> None:
        if not self.selected_emails:
            QtWidgets.QMessageBox.information(self, "没有勾选邮箱", "请先在主界面勾选要解绑的邮箱。")
            return
        removed = self.phone_store.unbind_emails(set(self.selected_emails))
        self.refresh_table()
        self.changed.emit()
        QtWidgets.QMessageBox.information(self, "解绑完成", f"已解绑 {removed} 个邮箱。")

    def export_phones(self) -> None:
        if not self.phone_store.phones:
            QtWidgets.QMessageBox.information(self, "没有手机号", "当前没有可导出的手机号。")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "导出手机号", "", "Text files (*.txt)")
        if not path:
            return
        lines = []
        for phone in sorted(self.phone_store.phones, key=lambda item: item.phone.lower()):
            parts = [phone.phone, phone.api_url]
            if phone.emails:
                parts.append(",".join(phone.emails))
            lines.append("----".join(parts))
        Path(path).write_text("\n".join(lines), encoding="utf-8")
        QtWidgets.QMessageBox.information(self, "导出完成", f"已导出 {len(lines)} 个手机号。")

    def delete_selected_phone(self) -> None:
        phone_number = self.selected_phone_number()
        if not phone_number:
            return
        if QtWidgets.QMessageBox.question(self, "删除手机号", f"确定删除 {phone_number} 吗？") != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        if self.phone_store.remove(phone_number):
            self.refresh_table()
            self.changed.emit()

    def fetch_selected_code(self) -> None:
        phone_number = self.selected_phone_number()
        if not phone_number:
            QtWidgets.QMessageBox.information(self, "请选择手机号", "请先在列表里选中一个手机号。")
            return
        phone = self.phone_store.get(phone_number)
        if not phone:
            QtWidgets.QMessageBox.warning(self, "手机号不存在", "没有找到这个手机号。")
            return
        if self.phone_worker and self.phone_worker.isRunning():
            return
        self.code_label.setText(f"正在获取 {phone.phone} 的验证码...")
        self.set_fetch_buttons_enabled(False)
        self.phone_worker = PhoneCodeWorker(phone)
        self.phone_worker.result_ready.connect(lambda row, current=phone.phone: self.on_code_result(current, row))
        self.phone_worker.error_ready.connect(lambda error, current=phone.phone: self.on_code_error(current, error))
        self.phone_worker.finished.connect(lambda: self.set_fetch_buttons_enabled(True))
        self.phone_worker.start()

    def on_code_result(self, phone_number: str, row: object) -> None:
        data = dict(row)
        code = data.get("code") or "未识别"
        message = data.get("preview", "")
        self.phone_store.mark_fetch_result(
            phone_number,
            "成功" if data.get("code") else "未识别验证码",
            code=data.get("code", ""),
            message=message,
        )
        self.code_label.setText(f"验证码：{code}    手机号：{phone_number}")
        self.refresh_table()
        self.changed.emit()
        self.sms_result_ready.emit(data)

    def on_code_error(self, phone_number: str, error: str) -> None:
        self.phone_store.mark_fetch_result(phone_number, "获取失败", message=error)
        self.code_label.setText(f"获取失败：{error[:180]}")
        self.refresh_table()
        self.changed.emit()

    def set_fetch_buttons_enabled(self, enabled: bool) -> None:
        for button in self.findChildren(QtWidgets.QPushButton):
            button.setEnabled(enabled)
