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

    def __init__(self, account: AccountRecord, checked: bool) -> None:
        super().__init__()
        self.account = account
        self.setObjectName("AccountCard")
        self.setProperty("selected", "true" if checked else "false")
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(78)
        self.setMaximumHeight(78)
        self.clicked.connect(self.toggle_selection)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

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
        self.meta_label = ElidedLabel(f"{account.category_label} · {account.source}{phone_text}{tag_text} · {account.last_status}")
        self.meta_label.setObjectName("AccountMeta")
        self.meta_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        text_box.addWidget(self.meta_label)

        layout.addWidget(text_host, 1)

        actions_host = QtWidgets.QWidget()
        actions_host.setFixedWidth(116)
        actions_host.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        actions = QtWidgets.QGridLayout(actions_host)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setHorizontalSpacing(8)
        actions.setVerticalSpacing(6)

        self.mail_button = pill_button("邮箱", role="mini-action")
        self.mail_button.setFixedSize(54, 28)
        self.mail_button.setProperty("compact", "true")
        self.mail_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.mail_button.setToolTip(f"获取邮箱验证码：{account.email}")
        self.mail_button.clicked.connect(lambda: self.mail_code_requested.emit(self.account.email))
        actions.addWidget(self.mail_button, 0, 1)

        self.phone_button = pill_button("手机", role="mini-action")
        self.phone_button.setFixedSize(54, 28)
        self.phone_button.setProperty("compact", "true")
        self.phone_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.phone_button.setEnabled(bool(account.phone))
        self.phone_button.setToolTip(f"获取手机号验证码：{account.phone}" if account.phone else "未绑定手机号")
        self.phone_button.clicked.connect(lambda: self.phone_code_requested.emit(self.account.email))
        actions.addWidget(self.phone_button, 0, 0)

        tag_button_text = compact_text(account.tag, 6) if account.tag else "标签"
        tag_button_role = "tagged" if account.tag else "mini-action"
        self.tag_button = pill_button(tag_button_text, role=tag_button_role)
        self.tag_button.setFixedSize(54, 28)
        self.tag_button.setProperty("compact", "true")
        self.tag_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.tag_button.setToolTip(f"编辑标签：{account.tag}" if account.tag else "添加自定义标签")
        self.tag_button.clicked.connect(lambda: self.tag_requested.emit(self.account.email))
        actions.addWidget(self.tag_button, 1, 0)

        self.copy_button = pill_button("复制", role="mini-action")
        self.copy_button.setFixedSize(54, 28)
        self.copy_button.setProperty("compact", "true")
        self.copy_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.copy_button.clicked.connect(lambda: self.copy_requested.emit(self.account.email))
        actions.addWidget(self.copy_button, 1, 1)
        layout.addWidget(actions_host, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)

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
