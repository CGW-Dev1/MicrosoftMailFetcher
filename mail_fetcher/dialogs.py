from __future__ import annotations

from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from .models import ImportRecord, PhoneRecord
from .parsing import parse_import_text, parse_phone_import_text
from .services import SmsService
from .storage import PhoneStore
from .widgets.common import ElidedLabel, pill_button


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
        available_emails: list[str] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.phone_store = phone_store
        self.available_emails = self.normalize_emails(available_emails or selected_emails)
        self.selected_emails = self.normalize_emails(selected_emails)
        if self.available_emails:
            available_set = {email.lower() for email in self.available_emails}
            self.selected_emails = [email for email in self.selected_emails if email.lower() in available_set]
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
        self.table.setHorizontalHeaderLabels(["手机号", "邮箱数", "已绑定邮箱", "状态"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)
        layout.addWidget(self.table, 3)

        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setObjectName("ImportEditor")
        self.editor.setPlaceholderText("+12633008723----https://api.sms8.net/api/record?token=xxx")
        self.editor.setMaximumHeight(72)
        layout.addWidget(self.editor)

        selected_text = f"当前菜单邮箱：{len(self.available_emails)} 个。点击已绑定邮箱后的小三角，可绑定或解绑单个邮箱。"
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
        actions.setSpacing(10)
        action_items = (
            ("从文件载入", self.load_file, "secondary"),
            ("导入手机号", self.import_phones, "primary"),
            ("获取验证码", self.fetch_selected_code, "primary"),
            ("导出手机号", self.export_phones, "secondary"),
            ("清空当前绑定", self.clear_selected_phone_bindings, "secondary"),
            ("删除手机号", self.delete_selected_phone, "danger"),
        )
        for text, slot, role in action_items:
            button = pill_button(text, role=role)
            button.setFixedHeight(40)
            width = max(112, button.fontMetrics().horizontalAdvance(text) + 34)
            button.setMinimumWidth(width)
            button.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Fixed,
            )
            button.clicked.connect(slot)
            actions.addWidget(button, 1)
        layout.addLayout(actions)

        self.refresh_table()

    @staticmethod
    def normalize_emails(emails: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for email in emails:
            clean = str(email).strip()
            key = clean.lower()
            if not clean or key in seen:
                continue
            normalized.append(clean)
            seen.add(key)
        return sorted(normalized, key=str.lower)

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
                "",
                phone.last_status,
            ]
            for col, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setToolTip(phone.api_url if col == 0 else value)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, phone.phone)
                self.table.setItem(row, col, item)
            self.table.setCellWidget(row, 2, self.build_bound_email_cell(phone))
        if phones:
            self.table.selectRow(0)

    def build_bound_email_cell(self, phone: PhoneRecord) -> QtWidgets.QWidget:
        cell = QtWidgets.QWidget()
        cell.setObjectName("BoundEmailCell")
        layout = QtWidgets.QHBoxLayout(cell)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.setSpacing(6)

        text = ", ".join(phone.emails) if phone.emails else "未绑定"
        label = ElidedLabel(text)
        label.setObjectName("BoundEmailText")
        label.setToolTip(text)
        label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        layout.addWidget(label, 1)

        menu_button = QtWidgets.QToolButton()
        menu_button.setObjectName("EmailMenuButton")
        menu_button.setProperty("role", "email-menu")
        menu_button.setArrowType(QtCore.Qt.ArrowType.DownArrow)
        menu_button.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        menu_button.setToolTip("绑定或解绑邮箱")
        menu_button.setFixedSize(28, 28)
        menu_button.clicked.connect(
            lambda _checked=False, phone_number=phone.phone, button=menu_button: self.show_email_action_menu(
                phone_number,
                button.mapToGlobal(QtCore.QPoint(0, button.height())),
                include_copy=False,
            )
        )
        layout.addWidget(menu_button)
        return cell

    def show_email_action_menu(self, phone_number: str, global_pos: QtCore.QPoint, include_copy: bool = False) -> None:
        phone = self.phone_store.get(phone_number)
        if not phone:
            return
        menu = QtWidgets.QMenu(self)
        copy_action = None
        if include_copy:
            copy_action = menu.addAction("复制手机号")
            menu.addSeparator()

        action_payloads: dict[QtGui.QAction, tuple[str, str]] = {}
        phone_email_keys = {email.lower() for email in phone.emails}
        bindable_emails = [email for email in self.available_emails if email.lower() not in phone_email_keys]
        if len(phone.emails) < self.phone_store.max_emails_per_phone and bindable_emails:
            bind_title = menu.addAction("绑定邮箱")
            bind_title.setEnabled(False)
            for email in bindable_emails:
                action = menu.addAction(email)
                action_payloads[action] = ("bind", email)
        elif len(phone.emails) >= self.phone_store.max_emails_per_phone:
            full_action = menu.addAction("已满 3/3，请先解绑")
            full_action.setEnabled(False)
        elif not self.available_emails:
            empty_action = menu.addAction("当前菜单无邮箱")
            empty_action.setEnabled(False)

        if phone.emails:
            if action_payloads:
                menu.addSeparator()
            unbind_title = menu.addAction("解绑邮箱")
            unbind_title.setEnabled(False)
            for email in sorted(phone.emails, key=str.lower):
                action = menu.addAction(email)
                action_payloads[action] = ("unbind", email)

        action = menu.exec(global_pos)
        if copy_action is not None and action == copy_action:
            self.copy_phone_number(phone_number)
            return
        payload = action_payloads.get(action)
        if not payload:
            return
        mode, email = payload
        if mode == "bind":
            bound, rejected = self.phone_store.bind_emails(phone_number, {email})
            self.refresh_table()
            self.changed.emit()
            if bound:
                self.code_label.setText(f"已绑定：{email} -> {phone_number}")
            elif rejected:
                self.code_label.setText("绑定失败：一个手机号最多绑定 3 个邮箱，或邮箱不存在。")
            else:
                self.code_label.setText(f"已存在绑定：{email}")
            return
        removed = self.phone_store.unbind_emails({email})
        self.refresh_table()
        self.changed.emit()
        self.code_label.setText(f"已解绑：{email}" if removed else f"未找到绑定：{email}")

    def selected_phone_number(self) -> str:
        row = self.table.currentRow()
        if row < 0:
            return ""
        item = self.table.item(row, 0)
        return item.data(QtCore.Qt.ItemDataRole.UserRole) if item else ""

    def show_table_context_menu(self, pos: QtCore.QPoint) -> None:
        item = self.table.itemAt(pos)
        if not item:
            return
        self.table.selectRow(item.row())
        phone_item = self.table.item(item.row(), 0)
        phone_number = phone_item.data(QtCore.Qt.ItemDataRole.UserRole) if phone_item else ""
        if not phone_number:
            return
        menu = QtWidgets.QMenu(self)
        copy_action = menu.addAction("复制手机号")
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == copy_action:
            self.copy_phone_number(str(phone_number))

    def copy_phone_number(self, phone_number: str) -> None:
        QtWidgets.QApplication.clipboard().setText(phone_number)
        self.code_label.setText(f"已复制手机号：{phone_number}")

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
        self.copy_phone_number(phone_number)

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

    def clear_selected_phone_bindings(self) -> None:
        phone_number = self.selected_phone_number()
        if not phone_number:
            QtWidgets.QMessageBox.information(self, "请选择手机号", "请先在列表里选中一个手机号。")
            return
        phone = self.phone_store.get(phone_number)
        if not phone or not phone.emails:
            self.code_label.setText("当前手机号没有绑定邮箱。")
            return
        removed = self.phone_store.unbind_emails(set(phone.emails))
        self.refresh_table()
        self.changed.emit()
        self.code_label.setText(f"已清空 {phone_number} 的 {removed} 个绑定邮箱。")

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
