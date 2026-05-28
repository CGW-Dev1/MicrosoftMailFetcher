from __future__ import annotations

from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from .models import ImportRecord
from .parsing import parse_import_text
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

        desc = QtWidgets.QLabel("每行格式：email----password----client_id----graph_refresh_token。导出文件会多一段分类：未使用 / Plus / Free / 已封禁。")
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
