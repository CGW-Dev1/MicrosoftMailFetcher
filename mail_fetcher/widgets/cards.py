from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets

from ..models import AccountRecord
from ..parsing import compact_text, short_sender
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

    def __init__(self, account: AccountRecord, checked: bool) -> None:
        super().__init__()
        self.account = account
        self.setObjectName("AccountCard")
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(46)
        self.setMaximumHeight(46)
        self.clicked.connect(self.toggle_selection)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setSpacing(6)

        self.checkbox = CheckBox()
        self.checkbox.setChecked(checked)
        self.checkbox.toggled.connect(lambda value: self.selection_changed.emit(self.account.email, value))
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

        self.meta_label = ElidedLabel(f"{account.category_label} · {account.source} · {account.last_status}")
        self.meta_label.setObjectName("AccountMeta")
        self.meta_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        text_box.addWidget(self.meta_label)

        layout.addWidget(text_host, 1)

        self.copy_button = pill_button("复制", role="ghost")
        self.copy_button.setFixedSize(54, 32)
        self.copy_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        self.copy_button.clicked.connect(lambda: self.copy_requested.emit(self.account.email))
        layout.addWidget(self.copy_button, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)

    def toggle_selection(self) -> None:
        self.checkbox.setChecked(not self.checkbox.isChecked())


class MailCard(ClickableFrame):
    open_requested = QtCore.pyqtSignal(dict)

    def __init__(self, row: dict) -> None:
        super().__init__()
        self.row = row
        self.setObjectName("MailCard")
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(96)
        self.clicked.connect(lambda: self.open_requested.emit(self.row))

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 9, 14, 9)
        layout.setSpacing(4)

        top = QtWidgets.QHBoxLayout()
        top.setSpacing(8)
        sender_label = QtWidgets.QLabel(short_sender(row.get("sender", "")))
        sender_label.setObjectName("MailSender")
        top.addWidget(sender_label)

        tone = "green" if row.get("protocol") == "GRAPH" else "cyan"
        top.addWidget(BadgeLabel(row.get("protocol", ""), tone=tone))
        top.addStretch(1)

        time_label = QtWidgets.QLabel(row.get("time", ""))
        time_label.setObjectName("MailMeta")
        top.addWidget(time_label)
        layout.addLayout(top)

        if row.get("concise"):
            code = row.get("code") or "未识别"
            subject_text = f"验证码：{code}"
        else:
            subject_text = row.get("subject") or "(无主题)"
        subject = ElidedLabel(compact_text(subject_text, 80))
        subject.setObjectName("MailSubject")
        layout.addWidget(subject)

        preview_text = row.get("preview") or ""
        if row.get("concise") and not preview_text:
            preview_text = "只展示最新一条验证码结果"
        preview = ElidedLabel(compact_text(preview_text, 160))
        preview.setObjectName("MailPreview")
        layout.addWidget(preview)

        account_label = ElidedLabel(f"账号：{row.get('account', '')}")
        account_label.setObjectName("MailMeta")
        layout.addWidget(account_label)
