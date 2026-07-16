from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets

from ..models import AccountRecord
from ..parsing import clean_verification_code, compact_text, extract_verification_code, short_sender
from .common import BadgeLabel, CheckBox, ElidedLabel, pill_button


class ClickableFrame(QtWidgets.QFrame):
    clicked = QtCore.pyqtSignal()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class AccountCard(ClickableFrame):
    selection_changed = QtCore.pyqtSignal(str, bool)
    copy_requested = QtCore.pyqtSignal(str)
    mail_code_requested = QtCore.pyqtSignal(str)
    phone_code_requested = QtCore.pyqtSignal(str)
    tag_requested = QtCore.pyqtSignal(str)

    def __init__(self, account: AccountRecord, checked: bool, category_label: str | None = None) -> None:
        super().__init__()
        self.account = account
        self.setObjectName("AccountCard")
        self.setProperty("selected", "true" if checked else "false")
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(72)
        self.setMaximumHeight(72)
        self.clicked.connect(self.toggle_selection)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 10, 8)
        layout.setSpacing(9)

        self.checkbox = CheckBox()
        self.checkbox.setChecked(checked)
        self.checkbox.toggled.connect(self.on_selection_toggled)
        layout.addWidget(self.checkbox, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)

        text_host = QtWidgets.QWidget()
        text_host.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
        text_host.setMinimumWidth(0)
        text_box = QtWidgets.QVBoxLayout(text_host)
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(1)
        self.email_label = ElidedLabel(account.email)
        self.email_label.setObjectName("AccountEmail")
        self.email_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        text_box.addWidget(self.email_label)

        phone_text = f" · {account.phone}" if account.phone else ""
        tag_text = f" · 标签:{compact_text(account.tag, 18)}" if account.tag else ""
        shown_category = category_label or account.category_label
        self.meta_label = ElidedLabel(f"{shown_category} · {account.source}{phone_text}{tag_text} · {account.last_status}")
        self.meta_label.setObjectName("AccountMeta")
        self.meta_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        text_box.addWidget(self.meta_label)

        layout.addWidget(text_host, 1)

        actions_host = QtWidgets.QWidget()
        actions_host.setFixedSize(104, 54)
        actions = QtWidgets.QGridLayout(actions_host)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setHorizontalSpacing(4)
        actions.setVerticalSpacing(4)

        mail_button = self._action_button("邮箱", "获取这个邮箱的验证码邮件")
        mail_button.clicked.connect(lambda: self.mail_code_requested.emit(self.account.email))
        phone_button = self._action_button("手机", "获取这个邮箱绑定手机号的验证码")
        phone_button.setEnabled(bool(account.phone))
        phone_button.clicked.connect(lambda: self.phone_code_requested.emit(self.account.email))
        tag_text = compact_text(account.tag, 4) if account.tag else "标签"
        tag_role = "account-tagged" if account.tag else "account-action"
        tag_button = self._action_button(tag_text, "编辑账号标签", role=tag_role)
        tag_button.clicked.connect(lambda: self.tag_requested.emit(self.account.email))
        copy_button = self._action_button("复制", "复制邮箱地址")
        copy_button.clicked.connect(lambda: self.copy_requested.emit(self.account.email))

        actions.addWidget(mail_button, 0, 0)
        actions.addWidget(phone_button, 0, 1)
        actions.addWidget(tag_button, 1, 0)
        actions.addWidget(copy_button, 1, 1)
        layout.addWidget(actions_host, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)

    @staticmethod
    def _action_button(text: str, tooltip: str, role: str = "account-action") -> QtWidgets.QPushButton:
        button = pill_button(text, role=role)
        button.setFixedSize(50, 25)
        button.setToolTip(tooltip)
        return button

    def toggle_selection(self) -> None:
        self.checkbox.setChecked(not self.checkbox.isChecked())

    def on_selection_toggled(self, value: bool) -> None:
        self.setProperty("selected", "true" if value else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self.selection_changed.emit(self.account.email, value)


class MailCard(ClickableFrame):
    open_requested = QtCore.pyqtSignal(dict)
    copy_code_requested = QtCore.pyqtSignal(str)

    def __init__(self, row: dict) -> None:
        super().__init__()
        self.row = row
        self.setObjectName("MailCard")
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(116)
        self.clicked.connect(lambda: self.open_requested.emit(self.row))

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(3)

        top_host = QtWidgets.QWidget()
        top_host.setMinimumHeight(28)
        top = QtWidgets.QHBoxLayout(top_host)
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)
        sender_label = QtWidgets.QLabel(short_sender(row.get("sender", "")))
        sender_label.setObjectName("MailSender")
        sender_label.setMinimumHeight(24)
        top.addWidget(sender_label)

        tone = "green" if row.get("protocol") == "GRAPH" else ("blue" if row.get("protocol") == "SMS" else "cyan")
        badge = BadgeLabel(row.get("protocol", ""), tone=tone)
        badge.setFixedWidth(86)
        top.addWidget(badge)
        top.addStretch(1)

        self.code = clean_verification_code(row.get("code") or extract_verification_code(row.get("subject", ""), row.get("preview", "")))
        self.copy_code_button = pill_button("复制码" if self.code else "无码", role="accent")
        self.copy_code_button.setFixedSize(76, 30)
        self.copy_code_button.setProperty("compact", "true")
        self.copy_code_button.setEnabled(bool(self.code))
        self.copy_code_button.setToolTip(f"复制验证码：{self.code}" if self.code else "未识别到验证码")
        self.copy_code_button.clicked.connect(lambda: self.copy_code_requested.emit(self.code))
        top.addWidget(self.copy_code_button)

        time_label = QtWidgets.QLabel(row.get("time", ""))
        time_label.setObjectName("MailMeta")
        time_label.setMinimumHeight(24)
        top.addWidget(time_label)
        layout.addWidget(top_host)

        if row.get("concise"):
            code = clean_verification_code(row.get("code") or "") or "未识别"
            subject_text = code
        elif row.get("protocol") == "SMS" and self.code:
            subject_text = self.code
        else:
            subject_text = row.get("subject") or "(无主题)"
        subject = ElidedLabel(compact_text(subject_text, 80))
        subject.setObjectName("MailSubject")
        subject.setMinimumHeight(24)
        layout.addWidget(subject)

        preview_text = row.get("preview") or ""
        if row.get("concise") and not preview_text:
            preview_text = "只展示最新一条验证码结果"
        preview = ElidedLabel(compact_text(preview_text, 160))
        preview.setObjectName("MailPreview")
        preview.setMinimumHeight(20)
        layout.addWidget(preview)

        account_label = ElidedLabel(f"账号：{row.get('account', '')}")
        account_label.setObjectName("MailMeta")
        account_label.setMinimumHeight(20)
        layout.addWidget(account_label)
