from __future__ import annotations

from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from .constants import APP_VERSION, DISPLAY_NAME, EXPORT_TOP_OPTIONS
from .dialogs import ImportDialog, MailDetailDialog
from .models import AccountRecord, ImportRecord
from .parsing import compact_text
from .services import MailService
from .storage import AccountStore, ConfigStore
from .widgets import AccountCard, BadgeLabel, CheckBox, CountSelector, MailCard, SearchField, pill_button
from .workers import FetchWorker

SURFACE = "#ffffff"
SURFACE_SOFT = "#f8fbff"
BORDER = "#d7e4f4"
BG = "#eef4fa"
TEXT = "#16304d"
MUTED = "#6f84a0"
BLUE = "#2f6fed"
BLUE_DARK = "#2456d8"
TEAL = "#14b8a6"
GREEN = "#0f9f75"
GREEN_SOFT = "#dcf8f0"
CYAN_SOFT = "#e7f5ff"
CYAN_TEXT = "#1183c8"
BLUE_SOFT = "#dfe9ff"
RED_SOFT = "#fff3f2"
RED = "#e25353"


def app_stylesheet() -> str:
    return f"""
    QWidget {{
        color: {TEXT};
        font-family: "Segoe UI", "Microsoft YaHei UI";
        font-size: 14px;
    }}
    QLabel {{
        background: transparent;
    }}
    QMainWindow, QWidget#CentralRoot {{
        background: {BG};
    }}
    QFrame#HeaderCard, QFrame#SidebarCard, QFrame#ControlsCard, QFrame#MailCard, QFrame#AccountCard, QFrame#StatCard {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 20px;
    }}
    QFrame#CountSelect {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 18px;
    }}
    QFrame#SidebarCard {{
        background: {SURFACE_SOFT};
    }}
    QFrame#AccountCard {{
        min-height: 52px;
    }}
    QFrame#MailCard {{
        min-height: 112px;
    }}
    QLabel#HeroTitle {{
        font-size: 26px;
        font-weight: 700;
        color: {TEXT};
    }}
    QLabel#HeroSubTitle {{
        font-size: 15px;
        font-weight: 600;
        color: {MUTED};
    }}
    QLabel#SectionTitle {{
        font-size: 20px;
        font-weight: 700;
        color: {TEXT};
    }}
    QLabel#AccountEmail {{
        font-size: 11px;
        font-weight: 600;
        color: {TEXT};
    }}
    QLabel#AccountMeta, QLabel#MailMeta, QLabel#DialogText {{
        color: {MUTED};
        font-size: 11px;
    }}
    QLabel#MailSender {{
        font-size: 13px;
        font-weight: 700;
        color: {TEXT};
    }}
    QLabel#MailSubject {{
        font-size: 15px;
        font-weight: 700;
        color: {TEXT};
    }}
    QLabel#MailPreview {{
        color: {MUTED};
        font-size: 12px;
        font-weight: 500;
    }}
    QLabel#ProgressText {{
        color: {MUTED};
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel#DialogTitle {{
        font-size: 24px;
        font-weight: 700;
        color: {TEXT};
    }}
    QLabel#StatusLabel {{
        background: {GREEN_SOFT};
        border: 1px solid transparent;
        border-radius: 14px;
        color: {GREEN};
        font-weight: 700;
        padding: 10px 14px;
    }}
    QLabel#SidebarCount {{
        background: {BLUE_SOFT};
        color: {BLUE};
        border-radius: 12px;
        padding: 6px 12px;
        font-weight: 700;
    }}
    QLabel#BadgeLabel {{
        border-radius: 12px;
        padding: 4px 10px;
        font-weight: 700;
        min-width: 74px;
    }}
    QLabel#BadgeLabel[tone="green"] {{
        background: {GREEN_SOFT};
        color: {GREEN};
    }}
    QLabel#BadgeLabel[tone="cyan"] {{
        background: {CYAN_SOFT};
        color: {CYAN_TEXT};
    }}
    QLabel#BadgeLabel[tone="blue"] {{
        background: {BLUE_SOFT};
        color: {BLUE};
    }}
    QLineEdit#SearchField, QPlainTextEdit#ImportEditor, QTextEdit#DetailViewer, QComboBox#CountCombo {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 12px 14px;
        color: {TEXT};
        selection-background-color: #dbeafe;
    }}
    QLineEdit#SearchField:focus, QPlainTextEdit#ImportEditor:focus, QTextEdit#DetailViewer:focus, QComboBox#CountCombo:focus {{
        border: 1px solid {BLUE};
    }}
    QComboBox#CountCombo {{
        padding-right: 32px;
        min-height: 24px;
        font-weight: 700;
    }}
    QComboBox#CountCombo::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border: none;
        background: transparent;
    }}
    QComboBox#CountCombo::down-arrow {{
        width: 12px;
        height: 12px;
    }}
    QPushButton {{
        border-radius: 14px;
        padding: 9px 16px;
        font-weight: 700;
        border: 1px solid transparent;
    }}
    QPushButton[role="primary"] {{
        background: {BLUE};
        color: white;
    }}
    QPushButton[role="primary"]:hover {{
        background: {BLUE_DARK};
    }}
    QPushButton[role="secondary"] {{
        background: {SURFACE};
        color: {TEXT};
        border: 1px solid {BORDER};
    }}
    QPushButton[role="secondary"]:hover {{
        border: 1px solid {BLUE};
        color: {BLUE};
    }}
    QPushButton[role="accent"] {{
        background: {BLUE_SOFT};
        color: {BLUE};
    }}
    QPushButton[role="accent"]:hover {{
        background: #d2e0ff;
    }}
    QPushButton[role="danger"] {{
        background: {RED_SOFT};
        color: {RED};
    }}
    QPushButton[role="ghost"] {{
        background: {SURFACE};
        color: {BLUE};
        border: 1px solid {BORDER};
        padding: 8px 14px;
    }}
    QPushButton[role="dropdown-value"] {{
        background: #f3f7ff;
        color: {TEXT};
        border: 1px solid #d6e3f5;
        border-radius: 12px;
        padding: 8px 10px;
        font-weight: 700;
    }}
    QToolButton[role="dropdown-arrow"] {{
        background: transparent;
        border: none;
        color: {MUTED};
        font-size: 16px;
        padding: 0;
    }}
    QPushButton[role="tab"] {{
        background: #edf3fb;
        color: {TEXT};
        border: 1px solid transparent;
    }}
    QPushButton[role="tab"]:checked, QPushButton[role="protocol"]:checked {{
        background: {BLUE};
        color: white;
    }}
    QPushButton[role="protocol"] {{
        background: #edf3fb;
        color: {TEXT};
    }}
    QPushButton:disabled {{
        background: #e8eef6;
        color: #a2b2c5;
        border-color: transparent;
    }}
    QProgressBar {{
        background: #e7eef8;
        border-radius: 7px;
        border: none;
        min-height: 10px;
    }}
    QProgressBar::chunk {{
        background: {TEAL};
        border-radius: 7px;
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        width: 11px;
        background: transparent;
        margin: 4px 0 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: #cfe0f6;
        border-radius: 5px;
        min-height: 36px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    """


def enable_qt_dpi() -> None:
    try:
        import ctypes

        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        pass
    QtGui.QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{DISPLAY_NAME} {APP_VERSION} | IMAP + Graph API")
        self.resize(1520, 920)
        self.setMinimumSize(1260, 760)
        self.setStyleSheet(app_stylesheet())

        icon_path = Path(__file__).resolve().parent.parent / "assets" / "mail.ico"
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))

        self.account_store = AccountStore()
        self.config_store = ConfigStore()
        self.mail_service = MailService(self.config_store, self.account_store)

        self.fetch_worker: FetchWorker | None = None
        self.fetch_running = False
        self.account_states: dict[str, bool] = {account.email: True for account in self.account_store.accounts}
        self.mail_rows: list[dict] = []
        self.logs: list[str] = []

        self.build_ui(icon_path)
        self.refresh_accounts()
        self.render_results(reset_scroll=True)
        self.update_protocol_buttons()
        self.update_status("就绪")

    def build_ui(self, icon_path: Path) -> None:
        root = QtWidgets.QWidget()
        root.setObjectName("CentralRoot")
        self.setCentralWidget(root)

        outer = QtWidgets.QVBoxLayout(root)
        outer.setContentsMargins(18, 14, 18, 14)
        outer.setSpacing(12)

        header = self.make_header(icon_path)
        outer.addWidget(header)

        body = QtWidgets.QHBoxLayout()
        body.setSpacing(16)
        outer.addLayout(body, 1)

        self.sidebar = self.make_sidebar()
        body.addWidget(self.sidebar, 0)

        self.main_panel = self.make_main_panel()
        body.addWidget(self.main_panel, 1)

    def make_header(self, icon_path: Path) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("HeaderCard")
        layout = QtWidgets.QHBoxLayout(frame)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(14)

        icon_box = QtWidgets.QLabel()
        icon_box.setFixedSize(48, 48)
        icon_box.setStyleSheet(f"background:{BLUE}; border-radius:18px;")
        icon_box.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        if icon_path.exists():
            icon = QtGui.QIcon(str(icon_path))
            pixmap = icon.pixmap(QtCore.QSize(30, 30))
            icon_box.setPixmap(pixmap)
        else:
            icon_box.setText("✉")
            icon_box.setStyleSheet(
                f"background:{BLUE}; border-radius:18px; color:white; font-size:24px; font-weight:700;"
            )
        layout.addWidget(icon_box)

        titles = QtWidgets.QVBoxLayout()
        titles.setSpacing(4)
        title = QtWidgets.QLabel(f"{DISPLAY_NAME} {APP_VERSION}")
        title.setObjectName("HeroTitle")
        titles.addWidget(title)
        subtitle = QtWidgets.QLabel("IMAP OAuth2 + Graph API 双协议")
        subtitle.setObjectName("HeroSubTitle")
        titles.addWidget(subtitle)
        layout.addLayout(titles, 1)

        self.status_label = QtWidgets.QLabel("就绪")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumWidth(340)
        self.status_label.setMinimumHeight(44)
        layout.addWidget(self.status_label, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        return frame

    def make_sidebar(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("SidebarCard")
        frame.setFixedWidth(410)

        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

        top = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("邮箱列表")
        title.setObjectName("SectionTitle")
        top.addWidget(title)
        top.addStretch(1)
        self.account_count_label = QtWidgets.QLabel("0/0")
        self.account_count_label.setObjectName("SidebarCount")
        top.addWidget(self.account_count_label)
        layout.addLayout(top)

        self.account_search = SearchField("邮箱搜索")
        self.account_search.textChanged.connect(lambda: self.refresh_accounts(reset_scroll=True))
        layout.addWidget(self.account_search)

        group_line = QtWidgets.QHBoxLayout()
        group_line.setSpacing(8)
        self.unused_button = pill_button("未使用", role="tab", checkable=True)
        self.used_button = pill_button("已使用", role="tab", checkable=True)
        self.unused_button.setChecked(True)
        self.unused_button.clicked.connect(lambda: self.set_account_group("unused"))
        self.used_button.clicked.connect(lambda: self.set_account_group("used"))
        group_line.addWidget(self.unused_button)
        group_line.addWidget(self.used_button)
        layout.addLayout(group_line)

        import_button = pill_button("+  批量导入邮箱", role="primary")
        import_button.clicked.connect(self.open_import_dialog)
        layout.addWidget(import_button)

        export_button = pill_button("⇩  导出邮箱", role="secondary")
        export_button.clicked.connect(self.export_accounts)
        layout.addWidget(export_button)

        select_line = QtWidgets.QHBoxLayout()
        self.select_all_box = CheckBox("全选")
        self.select_all_box.setChecked(True)
        self.select_all_box.toggled.connect(self.toggle_all_accounts)
        select_line.addWidget(self.select_all_box)
        select_line.addStretch(1)
        delete_button = pill_button("删除选中", role="danger")
        delete_button.clicked.connect(self.remove_selected)
        select_line.addWidget(delete_button)
        layout.addLayout(select_line)

        usage_line = QtWidgets.QHBoxLayout()
        usage_line.setSpacing(8)
        mark_button = pill_button("标记已使用", role="accent")
        mark_button.clicked.connect(self.mark_selected_used)
        usage_line.addWidget(mark_button)
        unmark_button = pill_button("取消标记", role="secondary")
        unmark_button.clicked.connect(self.mark_selected_unused)
        usage_line.addWidget(unmark_button)
        layout.addLayout(usage_line)

        self.account_scroll = QtWidgets.QScrollArea()
        self.account_scroll.setWidgetResizable(True)
        self.account_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.account_container = QtWidgets.QWidget()
        self.account_layout = QtWidgets.QVBoxLayout(self.account_container)
        self.account_layout.setContentsMargins(0, 0, 0, 0)
        self.account_layout.setSpacing(8)
        self.account_layout.addStretch(1)
        self.account_scroll.setWidget(self.account_container)
        layout.addWidget(self.account_scroll, 1)

        footer = QtWidgets.QHBoxLayout()
        clear_button = pill_button("清空全部", role="secondary")
        clear_button.clicked.connect(self.clear_accounts)
        footer.addWidget(clear_button)
        footer.addStretch(1)
        layout.addLayout(footer)
        return frame

    def make_main_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        controls = QtWidgets.QFrame()
        controls.setObjectName("ControlsCard")
        controls_layout = QtWidgets.QVBoxLayout(controls)
        controls_layout.setContentsMargins(16, 14, 16, 14)
        controls_layout.setSpacing(10)

        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(12)
        self.keyword_search = SearchField("邮件搜索")
        self.keyword_search.textChanged.connect(lambda: self.render_results())
        top_row.addWidget(self.keyword_search, 1)
        self.sender_search = SearchField("发件人搜索")
        self.sender_search.textChanged.connect(lambda: self.render_results())
        top_row.addWidget(self.sender_search, 1)
        self.count_card = self.make_count_card()
        top_row.addWidget(self.count_card, 1)
        controls_layout.addLayout(top_row)

        middle_row = QtWidgets.QHBoxLayout()
        middle_row.setSpacing(10)
        self.imap_button = pill_button("IMAP令牌", role="protocol", checkable=True)
        self.graph_button = pill_button("Graph令牌", role="protocol", checkable=True)
        self.imap_button.clicked.connect(lambda: self.set_protocol("IMAP"))
        self.graph_button.clicked.connect(lambda: self.set_protocol("Graph"))
        middle_row.addWidget(self.imap_button)
        middle_row.addWidget(self.graph_button)

        self.auto_fetch_box = CheckBox("导入后自动取件")
        self.auto_fetch_box.setChecked(self.config_store.auto_fetch_after_import)
        self.auto_fetch_box.toggled.connect(self.save_config)
        middle_row.addWidget(self.auto_fetch_box)

        self.concise_mode_box = CheckBox("简洁模式")
        self.concise_mode_box.setChecked(self.config_store.concise_mode)
        self.concise_mode_box.toggled.connect(self.save_config)
        middle_row.addWidget(self.concise_mode_box)
        middle_row.addStretch(1)
        controls_layout.addLayout(middle_row)

        action_row = QtWidgets.QHBoxLayout()
        action_row.setSpacing(10)
        export_csv_button = pill_button("导出CSV", role="secondary")
        export_csv_button.clicked.connect(self.export_csv)
        action_row.addWidget(export_csv_button)
        self.stop_button = pill_button("停止", role="secondary")
        self.stop_button.clicked.connect(self.request_stop)
        action_row.addWidget(self.stop_button)
        action_row.addStretch(1)
        self.fetch_selected_button = pill_button("⇩  选中取件", role="primary")
        self.fetch_selected_button.clicked.connect(self.fetch_selected)
        action_row.addWidget(self.fetch_selected_button)
        self.fetch_all_button = pill_button("⇩  全部取件", role="primary")
        self.fetch_all_button.clicked.connect(self.fetch_all)
        self.fetch_all_button.setStyleSheet("")
        action_row.addWidget(self.fetch_all_button)
        controls_layout.addLayout(action_row)

        layout.addWidget(controls)

        self.progress_text = QtWidgets.QLabel("等待操作")
        self.progress_text.setObjectName("ProgressText")
        layout.addWidget(self.progress_text)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("取件结果")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        self.graph_badge = BadgeLabel("Graph: 0", tone="green")
        self.imap_badge = BadgeLabel("IMAP: 0", tone="cyan")
        self.total_badge = BadgeLabel("共 0 封", tone="blue")
        header.addWidget(self.graph_badge)
        header.addWidget(self.imap_badge)
        header.addWidget(self.total_badge)
        layout.addLayout(header)

        self.result_scroll = QtWidgets.QScrollArea()
        self.result_scroll.setWidgetResizable(True)
        self.result_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.result_container = QtWidgets.QWidget()
        self.result_layout = QtWidgets.QVBoxLayout(self.result_container)
        self.result_layout.setContentsMargins(0, 0, 0, 0)
        self.result_layout.setSpacing(8)
        self.result_layout.addStretch(1)
        self.result_scroll.setWidget(self.result_container)
        layout.addWidget(self.result_scroll, 1)
        return panel

    def make_count_card(self) -> QtWidgets.QFrame:
        selector = CountSelector("每个邮箱最大取件数", EXPORT_TOP_OPTIONS, str(self.config_store.top))
        selector.currentTextChanged.connect(self.save_config)
        return selector

    def update_status(self, text: str) -> None:
        self.status_label.setText(text)

    def save_config(self) -> None:
        try:
            top = int(self.count_card.currentText())
        except ValueError:
            top = 10
        self.config_store.protocol = self.protocol
        self.config_store.top = max(1, min(top, 50))
        self.config_store.auto_fetch_after_import = self.auto_fetch_box.isChecked()
        self.config_store.concise_mode = self.concise_mode_box.isChecked()
        self.config_store.save()

    @property
    def protocol(self) -> str:
        return "IMAP" if self.imap_button.isChecked() else "Graph"

    def set_protocol(self, protocol: str) -> None:
        self.graph_button.setChecked(protocol == "Graph")
        self.imap_button.setChecked(protocol == "IMAP")
        self.update_protocol_buttons()
        self.save_config()

    def update_protocol_buttons(self) -> None:
        if not self.graph_button.isChecked() and not self.imap_button.isChecked():
            self.graph_button.setChecked(True)
        for name, button in (("IMAP", self.imap_button), ("Graph", self.graph_button)):
            active = button.isChecked()
            label = f"{name}令牌"
            button.setText(f"当前 {label}" if active else label)

    def current_group(self) -> str:
        return "used" if self.used_button.isChecked() else "unused"

    def set_account_group(self, group: str) -> None:
        self.unused_button.setChecked(group == "unused")
        self.used_button.setChecked(group == "used")
        self.refresh_accounts(reset_scroll=True)

    def filtered_accounts(self) -> list[AccountRecord]:
        needle = self.account_search.text().strip().lower()
        show_used = self.current_group() == "used"
        pool = [account for account in self.account_store.accounts if account.used == show_used]
        if not needle:
            return pool
        starts = [account for account in pool if account.email.lower().startswith(needle)]
        contains = [account for account in pool if needle in account.email.lower() and account not in starts]
        return starts + contains

    def visible_account_emails(self) -> set[str]:
        return {account.email for account in self.filtered_accounts()}

    def selected_emails(self) -> list[str]:
        visible = self.visible_account_emails()
        return [email for email, checked in self.account_states.items() if checked and email in visible and self.account_store.get(email)]

    def on_account_checked(self, email: str, checked: bool) -> None:
        self.account_states[email] = checked
        self.sync_select_all_box()

    def refresh_accounts(self, reset_scroll: bool = False) -> None:
        accounts = self.filtered_accounts()
        self.account_count_label.setText(f"{len(accounts)}/{len(self.account_store.accounts)}")
        self.rebuild_list(
            self.account_layout,
            [
                self.build_account_card(account)
                for account in accounts
            ],
        )
        self.sync_select_all_box()
        if reset_scroll:
            self.account_scroll.verticalScrollBar().setValue(0)

    def build_account_card(self, account: AccountRecord) -> QtWidgets.QWidget:
        checked = self.account_states.setdefault(account.email, True)
        card = AccountCard(account, checked)
        card.selection_changed.connect(self.on_account_checked)
        card.copy_requested.connect(self.copy_email)
        return card

    def toggle_all_accounts(self, checked: bool) -> None:
        visible = self.visible_account_emails()
        for email in visible:
            self.account_states[email] = checked
        self.refresh_accounts()

    def sync_select_all_box(self) -> None:
        visible = list(self.visible_account_emails())
        all_checked = bool(visible) and all(self.account_states.get(email, False) for email in visible)
        self.select_all_box.blockSignals(True)
        self.select_all_box.setChecked(all_checked)
        self.select_all_box.blockSignals(False)

    def copy_email(self, email_address: str) -> None:
        QtWidgets.QApplication.clipboard().setText(email_address)
        self.update_status(f"已复制邮箱：{email_address}")

    def open_import_dialog(self) -> None:
        dialog = ImportDialog(self)
        dialog.setStyleSheet(self.styleSheet())
        dialog.import_requested.connect(self.handle_import)
        dialog.exec()

    def handle_import(self, records: list[ImportRecord], invalid: int) -> None:
        added, updated, skipped = self.account_store.upsert_records(records)
        for record in records:
            self.account_states.setdefault(record.email, True)
        self.set_account_group("unused")
        self.refresh_accounts(reset_scroll=True)
        self.update_status(f"导入完成：新增 {added}，重复 {skipped}")
        if invalid:
            self.logs.append(f"跳过 {invalid} 行无效邮箱。")
        if self.auto_fetch_box.isChecked():
            self.fetch_accounts([record.email for record in records])

    def export_accounts(self) -> None:
        if not self.account_store.accounts:
            QtWidgets.QMessageBox.information(self, "没有邮箱", "当前没有可导出的邮箱。")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "导出邮箱", "", "Text files (*.txt)")
        if not path:
            return
        accounts = sorted(self.account_store.accounts, key=lambda account: account.email.lower())
        lines = [
            "----".join([account.email, account.password, account.client_id, account.refresh_token])
            for account in accounts
        ]
        Path(path).write_text("\n".join(lines), encoding="utf-8")
        self.update_status(f"已导出 {len(lines)} 个邮箱")

    def remove_selected(self) -> None:
        selected = set(self.selected_emails())
        if not selected:
            return
        if QtWidgets.QMessageBox.question(self, "删除选中", f"确定删除选中的 {len(selected)} 个邮箱吗？") != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        removed = self.account_store.remove(selected)
        for email in selected:
            self.account_states.pop(email, None)
        self.refresh_accounts()
        self.update_status(f"已删除 {removed} 个邮箱")

    def mark_selected_used(self) -> None:
        self.set_selected_usage(True)

    def mark_selected_unused(self) -> None:
        self.set_selected_usage(False)

    def set_selected_usage(self, used: bool) -> None:
        selected = set(self.selected_emails())
        if not selected:
            return
        changed = self.account_store.set_used(selected, used)
        for email in selected:
            self.account_states[email] = False
        self.refresh_accounts(reset_scroll=True)
        target = "已使用" if used else "未使用"
        self.update_status(f"已将 {changed} 个邮箱移动到{target}")

    def clear_accounts(self) -> None:
        if not self.account_store.accounts:
            return
        if QtWidgets.QMessageBox.question(self, "清空全部", "确定清空全部邮箱吗？") != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        total = self.account_store.clear()
        self.account_states.clear()
        self.refresh_accounts()
        self.update_status(f"已清空 {total} 个邮箱")

    def fetch_selected(self) -> None:
        selected = self.selected_emails()
        if not selected:
            QtWidgets.QMessageBox.information(self, "请选择邮箱", "请先勾选要取件的邮箱。")
            return
        self.fetch_accounts(selected)

    def fetch_all(self) -> None:
        self.fetch_accounts([account.email for account in self.account_store.accounts])

    def fetch_accounts(self, emails: list[str]) -> None:
        accounts = [account for email in emails if (account := self.account_store.get(email))]
        if not accounts:
            QtWidgets.QMessageBox.information(self, "没有邮箱", "请先导入邮箱。")
            return
        self.save_config()
        self.fetch_running = True
        self.update_fetch_buttons()
        self.mail_rows.clear()
        self.render_results(reset_scroll=True)
        self.progress_text.setText("准备取件...")
        self.progress_bar.setRange(0, len(accounts))
        self.progress_bar.setValue(0)

        top = 1 if self.concise_mode_box.isChecked() else self.config_store.top
        self.fetch_worker = FetchWorker(
            self.mail_service,
            self.account_store,
            accounts,
            self.protocol,
            top,
            self.concise_mode_box.isChecked(),
        )
        self.fetch_worker.status_changed.connect(self.update_status)
        self.fetch_worker.progress_changed.connect(self.on_progress)
        self.fetch_worker.results_ready.connect(self.on_result_chunk)
        self.fetch_worker.log_message.connect(self.logs.append)
        self.fetch_worker.accounts_changed.connect(lambda: self.refresh_accounts())
        self.fetch_worker.finished_summary.connect(self.on_fetch_finished)
        self.fetch_worker.start()

    def request_stop(self) -> None:
        if self.fetch_worker is not None:
            self.fetch_worker.request_stop()
            self.progress_text.setText("正在停止...")
            self.update_status("正在停止取件")

    def on_progress(self, done: int, total: int, account: str, messages: int) -> None:
        self.progress_bar.setRange(0, max(total, 1))
        self.progress_bar.setValue(done)
        self.progress_text.setText(f"[{done}/{total}] {compact_text(account, 44)}，已取 {messages} 封")

    def on_result_chunk(self, rows: object) -> None:
        self.mail_rows.extend(list(rows))
        self.update_result_badges()

    def on_fetch_finished(self, success: int, total_accounts: int, total_messages: int, stopped: bool) -> None:
        self.fetch_running = False
        self.update_fetch_buttons()
        if stopped:
            self.update_status(f"已停止 | 已完成 {success}/{total_accounts} | {total_messages} 封")
            self.progress_text.setText("已停止")
        else:
            self.update_status(f"完成 {success}/{total_accounts} | {total_messages} 封邮件")
            self.progress_text.setText(f"完成：{success}/{total_accounts} 个账号，{total_messages} 封邮件")
        self.render_results(reset_scroll=True)
        self.fetch_worker = None

    def update_fetch_buttons(self) -> None:
        running = self.fetch_running
        self.fetch_selected_button.setDisabled(running)
        self.fetch_all_button.setDisabled(running)
        self.stop_button.setEnabled(running)

    def filtered_results(self) -> list[dict]:
        keyword = self.keyword_search.text().strip().lower()
        sender_filter = self.sender_search.text().strip().lower()
        rows: list[dict] = []
        for row in self.mail_rows:
            haystack = f"{row.get('subject', '')} {row.get('preview', '')}".lower()
            sender = row.get("sender", "").lower()
            if keyword and keyword not in haystack:
                continue
            if sender_filter and sender_filter not in sender:
                continue
            rows.append(row)
        return rows

    def update_result_badges(self) -> None:
        rows = self.filtered_results()
        graph_count = sum(1 for row in rows if row.get("protocol") == "GRAPH")
        imap_count = sum(1 for row in rows if row.get("protocol") == "IMAP")
        self.total_badge.setText(f"共 {len(rows)} 封")
        self.graph_badge.setText(f"Graph: {graph_count}")
        self.imap_badge.setText(f"IMAP: {imap_count}")

    def render_results(self, reset_scroll: bool = False) -> None:
        rows = self.filtered_results()
        cards = [self.build_mail_card(row) for row in rows]
        self.rebuild_list(self.result_layout, cards)
        self.update_result_badges()
        if reset_scroll:
            self.result_scroll.verticalScrollBar().setValue(0)

    def build_mail_card(self, row: dict) -> QtWidgets.QWidget:
        card = MailCard(row)
        card.open_requested.connect(self.open_mail_detail)
        return card

    def open_mail_detail(self, row: dict) -> None:
        dialog = MailDetailDialog(row, self)
        dialog.setStyleSheet(self.styleSheet())
        dialog.exec()

    def export_csv(self) -> None:
        rows = self.filtered_results()
        if not rows:
            QtWidgets.QMessageBox.information(self, "没有结果", "当前没有可导出的邮件结果。")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "导出结果", "", "CSV files (*.csv)")
        if not path:
            return
        import csv

        with open(path, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["account", "protocol", "time", "sender", "subject", "code", "read", "preview", "webLink", "concise"],
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(rows)
        self.update_status(f"已导出 {len(rows)} 条结果")

    @staticmethod
    def rebuild_list(layout: QtWidgets.QVBoxLayout, widgets: list[QtWidgets.QWidget]) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                while child_layout.count():
                    child_item = child_layout.takeAt(0)
                    if child_item.widget():
                        child_item.widget().deleteLater()
        for widget in widgets:
            layout.addWidget(widget)
        layout.addStretch(1)


def run_app() -> int:
    enable_qt_dpi()
    app = QtWidgets.QApplication([])
    app.setApplicationDisplayName(DISPLAY_NAME)
    app.setStyle("Fusion")
    font = QtGui.QFont("Microsoft YaHei UI", 11)
    font.setHintingPreference(QtGui.QFont.HintingPreference.PreferFullHinting)
    font.setStyleStrategy(
        QtGui.QFont.StyleStrategy.PreferAntialias | QtGui.QFont.StyleStrategy.PreferQuality
    )
    app.setFont(font)
    window = MainWindow()
    window.show()
    return app.exec()
