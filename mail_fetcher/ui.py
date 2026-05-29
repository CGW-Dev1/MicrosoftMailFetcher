from __future__ import annotations

from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from .constants import (
    ACCOUNT_CATEGORY_BANNED,
    ACCOUNT_CATEGORY_FREE,
    ACCOUNT_CATEGORY_LABELS,
    ACCOUNT_CATEGORY_ORDER,
    ACCOUNT_CATEGORY_PLUS,
    ACCOUNT_CATEGORY_UNUSED,
    APP_VERSION,
    DISPLAY_NAME,
    EXPORT_TOP_OPTIONS,
)
from .dialogs import ImportDialog, MailDetailDialog, PhoneCodeWorker, PhoneDialog
from .models import AccountRecord, ImportRecord, PhoneImportRecord
from .parsing import clean_verification_code, compact_text
from .services import MailService
from .storage import AccountStore, ConfigStore, PhoneStore
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


def app_stylesheet(theme: str = "light") -> str:
    if theme == "dark":
        surface = "#192333"
        surface_soft = "#142033"
        border = "#2d405c"
        bg = "#0f1724"
        text = "#eef5ff"
        muted = "#9fb1c7"
        blue = "#4f8cff"
        blue_dark = "#3a73dd"
        teal = "#20c7b7"
        green = "#39d79a"
        green_soft = "#12382f"
        cyan_soft = "#123044"
        cyan_text = "#62c7ff"
        blue_soft = "#1b3158"
        red_soft = "#3d2427"
        red = "#ff7a7a"
        tab_bg = "#22324a"
        disabled_bg = "#263244"
        disabled_text = "#708198"
        input_selection = "#274d86"
        accent_hover = "#25416f"
        scrollbar = "#3a5273"
    else:
        surface = SURFACE
        surface_soft = SURFACE_SOFT
        border = BORDER
        bg = BG
        text = TEXT
        muted = MUTED
        blue = BLUE
        blue_dark = BLUE_DARK
        teal = TEAL
        green = GREEN
        green_soft = GREEN_SOFT
        cyan_soft = CYAN_SOFT
        cyan_text = CYAN_TEXT
        blue_soft = BLUE_SOFT
        red_soft = RED_SOFT
        red = RED
        tab_bg = "#edf3fb"
        disabled_bg = "#e8eef6"
        disabled_text = "#a2b2c5"
        input_selection = "#dbeafe"
        accent_hover = "#d2e0ff"
        scrollbar = "#cfe0f6"
    return f"""
    QWidget {{
        color: {text};
        font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI";
        font-size: 14px;
    }}
    QLabel {{
        background: transparent;
    }}
    QMainWindow, QWidget#CentralRoot {{
        background: {bg};
    }}
    QDialog {{
        background: {bg};
        color: {text};
    }}
    QDialog QWidget {{
        background: {bg};
        color: {text};
    }}
    QFrame#HeaderCard, QFrame#SidebarCard, QFrame#ControlsCard, QFrame#MailCard, QFrame#AccountCard, QFrame#StatCard {{
        background: {surface};
        border: 1px solid {border};
        border-radius: 16px;
    }}
    QFrame#CountSelect {{
        background: {surface};
        border: 1px solid {border};
        border-radius: 14px;
    }}
    QFrame#CountSelect:hover {{
        border: 1px solid {blue};
    }}
    QFrame#SidebarCard {{
        background: {surface_soft};
    }}
    QFrame#AccountCard {{
        min-height: 54px;
    }}
    QFrame#MailCard {{
        min-height: 116px;
    }}
    QLabel#HeroTitle {{
        font-size: 23px;
        font-weight: 600;
        color: {text};
    }}
    QLabel#HeroSubTitle {{
        font-size: 14px;
        font-weight: 500;
        color: {muted};
    }}
    QLabel#SectionTitle {{
        font-size: 18px;
        font-weight: 600;
        color: {text};
    }}
    QLabel#AccountEmail {{
        font-size: 13px;
        font-weight: 500;
        color: {text};
    }}
    QLabel#AccountMeta, QLabel#MailMeta, QLabel#DialogText {{
        color: {muted};
        font-size: 12px;
    }}
    QLabel#MailSender {{
        font-size: 13px;
        font-weight: 600;
        color: {text};
    }}
    QLabel#MailSubject {{
        font-size: 15px;
        font-weight: 600;
        color: {text};
    }}
    QLabel#MailPreview {{
        color: {muted};
        font-size: 12px;
        font-weight: 400;
    }}
    QLabel#ProgressText {{
        color: {muted};
        font-size: 12px;
        font-weight: 500;
    }}
    QLabel#DialogTitle {{
        font-size: 24px;
        font-weight: 600;
        color: {text};
    }}
    QLabel#StatusLabel {{
        background: {blue_soft};
        border: 1px solid {border};
        border-radius: 14px;
        color: {blue};
        font-weight: 600;
        padding: 9px 14px;
    }}
    QLabel#SidebarCount {{
        background: {blue_soft};
        color: {blue};
        border-radius: 12px;
        padding: 6px 12px;
        font-weight: 600;
    }}
    QLabel#BadgeLabel {{
        border-radius: 12px;
        padding: 2px 10px;
        font-weight: 600;
        min-width: 74px;
    }}
    QLabel#BadgeLabel[tone="green"] {{
        background: {green_soft};
        color: {green};
    }}
    QLabel#BadgeLabel[tone="cyan"] {{
        background: {cyan_soft};
        color: {cyan_text};
    }}
    QLabel#BadgeLabel[tone="blue"] {{
        background: {blue_soft};
        color: {blue};
    }}
    QLineEdit#SearchField, QPlainTextEdit#ImportEditor, QTextEdit#DetailViewer, QComboBox#CountCombo {{
        background: {surface};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 9px 12px;
        color: {text};
        selection-background-color: {input_selection};
        selection-color: white;
    }}
    QPlainTextEdit#ImportEditor QWidget,
    QTextEdit#DetailViewer QWidget {{
        background: {surface};
        color: {text};
    }}
    QLineEdit#SearchField:focus, QPlainTextEdit#ImportEditor:focus, QTextEdit#DetailViewer:focus, QComboBox#CountCombo:focus {{
        border: 1px solid {blue};
    }}
    QTableWidget {{
        background: {surface};
        color: {text};
        border: 1px solid {border};
        border-radius: 12px;
        gridline-color: {border};
        alternate-background-color: {surface_soft};
        selection-background-color: {input_selection};
        selection-color: {text};
    }}
    QHeaderView::section {{
        background: {tab_bg};
        color: {text};
        border: none;
        border-right: 1px solid {border};
        padding: 8px 10px;
        font-weight: 600;
    }}
    QComboBox#CountCombo {{
        padding-right: 32px;
        min-height: 24px;
        font-weight: 600;
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
        border-radius: 12px;
        padding: 8px 14px;
        font-weight: 600;
        border: 1px solid transparent;
    }}
    QPushButton[role="primary"] {{
        background: {blue};
        color: white;
    }}
    QPushButton[role="primary"]:hover {{
        background: {blue_dark};
    }}
    QPushButton[role="secondary"] {{
        background: {surface};
        color: {text};
        border: 1px solid {border};
    }}
    QPushButton[role="secondary"]:hover {{
        border: 1px solid {blue};
        color: {blue};
    }}
    QPushButton[role="accent"] {{
        background: {blue_soft};
        color: {blue};
    }}
    QPushButton[role="accent"]:hover {{
        background: {accent_hover};
    }}
    QPushButton[role="danger"] {{
        background: {red_soft};
        color: {red};
    }}
    QPushButton[role="ghost"] {{
        background: {surface};
        color: {blue};
        border: 1px solid {border};
        padding: 8px 10px;
    }}
    QPushButton[compact="true"] {{
        padding: 3px 8px;
        border-radius: 11px;
        font-size: 13px;
        min-height: 0;
    }}
    QPushButton[role="dropdown-value"] {{
        background: transparent;
        color: {text};
        border: none;
        border-radius: 0;
        padding: 0;
        font-weight: 600;
        text-align: left;
    }}
    QToolButton[role="dropdown-arrow"] {{
        background: transparent;
        border: none;
        color: {muted};
        font-size: 14px;
        padding: 0;
    }}
    QPushButton[role="tab"] {{
        background: {tab_bg};
        color: {text};
        border: 1px solid transparent;
    }}
    QPushButton[role="tab"]:checked, QPushButton[role="protocol"]:checked {{
        background: {blue};
        color: white;
    }}
    QPushButton[role="protocol"] {{
        background: {tab_bg};
        color: {text};
    }}
    QPushButton:disabled {{
        background: {disabled_bg};
        color: {disabled_text};
        border-color: transparent;
    }}
    QProgressBar {{
        background: {tab_bg};
        border-radius: 7px;
        border: none;
        min-height: 10px;
    }}
    QProgressBar::chunk {{
        background: {teal};
        border-radius: 7px;
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollArea#AccountScroll QWidget#AccountViewport,
    QWidget#AccountContainer {{
        background: {surface_soft};
    }}
    QScrollArea#ResultScroll QWidget#ResultViewport,
    QWidget#ResultContainer {{
        background: {bg};
    }}
    QScrollArea#AccountScroll,
    QScrollArea#ResultScroll {{
        background: transparent;
    }}
    QScrollBar:vertical {{
        width: 11px;
        background: transparent;
        margin: 4px 0 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {scrollbar};
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

        icon_path = Path(__file__).resolve().parent.parent / "assets" / "mail.ico"
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))

        self.account_store = AccountStore()
        self.phone_store = PhoneStore(self.account_store)
        self.config_store = ConfigStore()
        self.setStyleSheet(app_stylesheet(self.config_store.theme))
        self.mail_service = MailService(self.config_store, self.account_store)

        self.fetch_worker: FetchWorker | None = None
        self.phone_code_workers: dict[str, PhoneCodeWorker] = {}
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
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(12)

        header = self.make_header(icon_path)
        outer.addWidget(header)

        body = QtWidgets.QHBoxLayout()
        body.setSpacing(14)
        outer.addLayout(body, 1)

        self.sidebar = self.make_sidebar()
        body.addWidget(self.sidebar, 0)

        self.main_panel = self.make_main_panel()
        body.addWidget(self.main_panel, 1)

    def make_header(self, icon_path: Path) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("HeaderCard")
        layout = QtWidgets.QHBoxLayout(frame)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        icon_box = QtWidgets.QLabel()
        icon_box.setFixedSize(48, 48)
        icon_box.setStyleSheet("background: transparent; border: none;")
        icon_box.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        if icon_path.exists():
            icon = QtGui.QIcon(str(icon_path))
            pixmap = icon.pixmap(QtCore.QSize(48, 48))
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

        self.dark_mode_box = CheckBox("深色模式")
        self.dark_mode_box.setFixedSize(104, 38)
        self.dark_mode_box.setChecked(self.config_store.theme == "dark")
        self.dark_mode_box.toggled.connect(self.apply_theme)
        layout.addWidget(self.dark_mode_box, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)

        self.status_label = QtWidgets.QLabel("就绪")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(40)
        self.status_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        layout.addWidget(self.status_label, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        return frame

    def make_sidebar(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("SidebarCard")
        frame.setFixedWidth(520)

        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

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
        self.account_search.setFixedHeight(38)
        layout.addWidget(self.account_search)

        group_line = QtWidgets.QHBoxLayout()
        group_line.setSpacing(8)
        self.unused_button = pill_button("未使用", role="tab", checkable=True)
        self.plus_button = pill_button("Plus", role="tab", checkable=True)
        self.free_button = pill_button("Free", role="tab", checkable=True)
        self.banned_button = pill_button("已封禁", role="tab", checkable=True)
        self.unused_button.setChecked(True)
        self.unused_button.clicked.connect(lambda: self.set_account_group(ACCOUNT_CATEGORY_UNUSED))
        self.plus_button.clicked.connect(lambda: self.set_account_group(ACCOUNT_CATEGORY_PLUS))
        self.free_button.clicked.connect(lambda: self.set_account_group(ACCOUNT_CATEGORY_FREE))
        self.banned_button.clicked.connect(lambda: self.set_account_group(ACCOUNT_CATEGORY_BANNED))
        for button in (self.unused_button, self.plus_button, self.free_button, self.banned_button):
            button.setFixedHeight(38)
            button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
            group_line.addWidget(button)
        layout.addLayout(group_line)

        import_export_line = QtWidgets.QHBoxLayout()
        import_export_line.setSpacing(8)
        import_button = pill_button("批量导入邮箱", role="primary")
        import_button.clicked.connect(self.open_import_dialog)
        import_button.setFixedHeight(38)
        export_button = pill_button("导出邮箱", role="secondary")
        export_button.clicked.connect(self.export_accounts)
        export_button.setFixedHeight(38)
        import_export_line.addWidget(import_button, 1)
        import_export_line.addWidget(export_button, 1)
        layout.addLayout(import_export_line)

        phone_button = pill_button("手机号管理", role="accent")
        phone_button.clicked.connect(self.open_phone_dialog)
        phone_button.setFixedHeight(38)
        layout.addWidget(phone_button)

        select_line = QtWidgets.QHBoxLayout()
        select_line.setSpacing(8)
        self.select_all_box = CheckBox("全选")
        self.select_all_box.setFixedHeight(38)
        self.select_all_box.setChecked(True)
        self.select_all_box.toggled.connect(self.toggle_all_accounts)
        select_line.addWidget(self.select_all_box)
        select_line.addStretch(1)
        delete_button = pill_button("删除选中", role="danger")
        delete_button.clicked.connect(self.remove_selected)
        delete_button.setFixedHeight(38)
        select_line.addWidget(delete_button)
        layout.addLayout(select_line)

        usage_line = QtWidgets.QHBoxLayout()
        usage_line.setSpacing(8)
        mark_plus_button = pill_button("Plus", role="accent")
        mark_plus_button.setToolTip("标记选中邮箱为 Plus")
        mark_plus_button.clicked.connect(lambda: self.set_selected_category(ACCOUNT_CATEGORY_PLUS))
        mark_free_button = pill_button("Free", role="accent")
        mark_free_button.setToolTip("标记选中邮箱为 Free")
        mark_free_button.clicked.connect(lambda: self.set_selected_category(ACCOUNT_CATEGORY_FREE))
        mark_banned_button = pill_button("封禁", role="danger")
        mark_banned_button.setToolTip("标记选中邮箱为已封禁")
        mark_banned_button.clicked.connect(lambda: self.set_selected_category(ACCOUNT_CATEGORY_BANNED))
        unmark_button = pill_button("未使用", role="secondary")
        unmark_button.setToolTip("将选中邮箱移回未使用")
        unmark_button.clicked.connect(lambda: self.set_selected_category(ACCOUNT_CATEGORY_UNUSED))
        for button in (mark_plus_button, mark_free_button, mark_banned_button, unmark_button):
            button.setFixedHeight(38)
            button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
            usage_line.addWidget(button)
        layout.addLayout(usage_line)

        self.account_scroll = QtWidgets.QScrollArea()
        self.account_scroll.setObjectName("AccountScroll")
        self.account_scroll.viewport().setObjectName("AccountViewport")
        self.account_scroll.setWidgetResizable(True)
        self.account_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.account_container = QtWidgets.QWidget()
        self.account_container.setObjectName("AccountContainer")
        self.account_layout = QtWidgets.QVBoxLayout(self.account_container)
        self.account_layout.setContentsMargins(0, 0, 12, 0)
        self.account_layout.setSpacing(6)
        self.account_layout.addStretch(1)
        self.account_scroll.setWidget(self.account_container)
        layout.addWidget(self.account_scroll, 1)

        footer = QtWidgets.QHBoxLayout()
        clear_button = pill_button("清空全部", role="secondary")
        clear_button.setFixedHeight(38)
        clear_button.clicked.connect(self.clear_accounts)
        footer.addWidget(clear_button)
        footer.addStretch(1)
        layout.addLayout(footer)
        return frame

    def make_main_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        controls = QtWidgets.QFrame()
        controls.setObjectName("ControlsCard")
        controls_layout = QtWidgets.QVBoxLayout(controls)
        controls_layout.setContentsMargins(14, 8, 14, 8)
        controls_layout.setSpacing(6)

        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(12)
        self.keyword_search = SearchField("邮件搜索")
        self.keyword_search.setFixedHeight(40)
        self.keyword_search.textChanged.connect(lambda: self.render_results())
        top_row.addWidget(self.keyword_search, 3)
        self.sender_search = SearchField("发件人搜索")
        self.sender_search.setFixedHeight(40)
        self.sender_search.textChanged.connect(lambda: self.render_results())
        top_row.addWidget(self.sender_search, 2)
        self.count_card = self.make_count_card()
        top_row.addWidget(self.count_card, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        controls_layout.addLayout(top_row)

        toolbar_row = QtWidgets.QHBoxLayout()
        toolbar_row.setSpacing(10)
        self.imap_button = pill_button("IMAP令牌", role="protocol", checkable=True)
        self.graph_button = pill_button("Graph令牌", role="protocol", checkable=True)
        self.imap_button.clicked.connect(lambda: self.set_protocol("IMAP"))
        self.graph_button.clicked.connect(lambda: self.set_protocol("Graph"))
        toolbar_buttons: list[QtWidgets.QPushButton] = [self.imap_button, self.graph_button]

        self.auto_fetch_box = CheckBox("导入后自动取件")
        self.auto_fetch_box.setFixedSize(152, 38)
        self.auto_fetch_box.setChecked(self.config_store.auto_fetch_after_import)
        self.auto_fetch_box.toggled.connect(self.save_config)

        self.concise_mode_box = CheckBox("简洁模式")
        self.concise_mode_box.setFixedSize(104, 38)
        self.concise_mode_box.setChecked(self.config_store.concise_mode)
        self.concise_mode_box.toggled.connect(self.save_config)

        export_csv_button = pill_button("导出CSV", role="secondary")
        export_csv_button.clicked.connect(self.export_csv)
        self.stop_button = pill_button("停止", role="secondary")
        self.stop_button.clicked.connect(self.request_stop)
        self.fetch_selected_button = pill_button("选中取件", role="primary")
        self.fetch_selected_button.clicked.connect(self.fetch_selected)
        self.fetch_all_button = pill_button("全部取件", role="primary")
        self.fetch_all_button.clicked.connect(self.fetch_all)
        self.fetch_all_button.setStyleSheet("")
        toolbar_buttons.extend([export_csv_button, self.stop_button, self.fetch_selected_button, self.fetch_all_button])

        for button in toolbar_buttons:
            self.prepare_toolbar_button(button)
            toolbar_row.addWidget(button)

        toolbar_row.addSpacing(4)
        toolbar_row.addWidget(self.auto_fetch_box)
        toolbar_row.addWidget(self.concise_mode_box)
        toolbar_row.addStretch(1)
        controls_layout.addLayout(toolbar_row)

        layout.addWidget(controls)

        self.progress_text = QtWidgets.QLabel("等待操作")
        self.progress_text.setObjectName("ProgressText")
        self.progress_text.setMaximumHeight(18)
        layout.addWidget(self.progress_text)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumHeight(10)
        layout.addWidget(self.progress_bar)

        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("取件结果")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        self.graph_badge = BadgeLabel("Graph: 0", tone="green")
        self.imap_badge = BadgeLabel("IMAP: 0", tone="cyan")
        self.sms_badge = BadgeLabel("SMS: 0", tone="blue")
        self.total_badge = BadgeLabel("共 0 封", tone="blue")
        header.addWidget(self.graph_badge)
        header.addWidget(self.imap_badge)
        header.addWidget(self.sms_badge)
        header.addWidget(self.total_badge)
        layout.addLayout(header)

        self.result_scroll = QtWidgets.QScrollArea()
        self.result_scroll.setObjectName("ResultScroll")
        self.result_scroll.viewport().setObjectName("ResultViewport")
        self.result_scroll.setWidgetResizable(True)
        self.result_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.result_container = QtWidgets.QWidget()
        self.result_container.setObjectName("ResultContainer")
        self.result_layout = QtWidgets.QVBoxLayout(self.result_container)
        self.result_layout.setContentsMargins(0, 0, 0, 0)
        self.result_layout.setSpacing(5)
        self.result_layout.addStretch(1)
        self.result_scroll.setWidget(self.result_container)
        layout.addWidget(self.result_scroll, 1)
        return panel

    @staticmethod
    def prepare_toolbar_button(button: QtWidgets.QPushButton) -> None:
        button.setFixedSize(104, 38)
        button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)

    def make_count_card(self) -> QtWidgets.QFrame:
        selector = CountSelector("每个邮箱最大取件数", EXPORT_TOP_OPTIONS, str(self.config_store.top))
        selector.currentTextChanged.connect(self.save_config)
        return selector

    def update_status(self, text: str) -> None:
        self.status_label.setText(text)
        width = self.status_label.fontMetrics().horizontalAdvance(text) + 42
        self.status_label.setFixedWidth(max(120, min(width, 520)))

    def save_config(self) -> None:
        try:
            top = int(self.count_card.currentText())
        except ValueError:
            top = 10
        self.config_store.protocol = self.protocol
        self.config_store.top = max(1, min(top, 50))
        self.config_store.auto_fetch_after_import = self.auto_fetch_box.isChecked()
        self.config_store.concise_mode = self.concise_mode_box.isChecked()
        if hasattr(self, "dark_mode_box"):
            self.config_store.theme = "dark" if self.dark_mode_box.isChecked() else "light"
        self.config_store.save()

    def apply_theme(self) -> None:
        self.config_store.theme = "dark" if self.dark_mode_box.isChecked() else "light"
        self.setStyleSheet(app_stylesheet(self.config_store.theme))
        self.save_config()

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
            button.setText(f"{name}令牌")
            button.setToolTip(f"当前使用{name}令牌" if active else f"切换到{name}令牌")

    def current_group(self) -> str:
        if self.plus_button.isChecked():
            return ACCOUNT_CATEGORY_PLUS
        if self.free_button.isChecked():
            return ACCOUNT_CATEGORY_FREE
        if self.banned_button.isChecked():
            return ACCOUNT_CATEGORY_BANNED
        return ACCOUNT_CATEGORY_UNUSED

    def set_account_group(self, group: str) -> None:
        if group not in ACCOUNT_CATEGORY_LABELS:
            group = ACCOUNT_CATEGORY_UNUSED
        self.unused_button.setChecked(group == ACCOUNT_CATEGORY_UNUSED)
        self.plus_button.setChecked(group == ACCOUNT_CATEGORY_PLUS)
        self.free_button.setChecked(group == ACCOUNT_CATEGORY_FREE)
        self.banned_button.setChecked(group == ACCOUNT_CATEGORY_BANNED)
        self.refresh_accounts(reset_scroll=True)

    def filtered_accounts(self) -> list[AccountRecord]:
        needle = self.account_search.text().strip().lower()
        current = self.current_group()
        pool = sorted(
            [account for account in self.account_store.accounts if account.category == current],
            key=lambda account: account.email.lower(),
        )
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
        card.mail_code_requested.connect(self.fetch_account_mail_code)
        card.phone_code_requested.connect(self.fetch_account_phone_code)
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

    def fetch_account_mail_code(self, email_address: str) -> None:
        if self.fetch_running:
            self.update_status("正在取件，请稍后")
            return
        account = self.account_store.get(email_address)
        if not account:
            self.update_status("邮箱不存在")
            return
        self.update_status(f"正在获取邮箱验证码：{email_address}")
        self.fetch_accounts([email_address])

    def open_import_dialog(self) -> None:
        dialog = ImportDialog(self)
        dialog.setStyleSheet(self.styleSheet())
        dialog.import_requested.connect(self.handle_import)
        dialog.exec()

    def open_phone_dialog(self) -> None:
        dialog = PhoneDialog(self.phone_store, self.selected_emails(), self)
        dialog.setStyleSheet(self.styleSheet())
        dialog.changed.connect(lambda: self.refresh_accounts())
        dialog.sms_result_ready.connect(self.add_sms_result)
        dialog.exec()

    def add_sms_result(self, row: object) -> None:
        data = dict(row)
        data["code"] = clean_verification_code(data.get("code", ""))
        if data.get("protocol") == "SMS" and data.get("code"):
            data["subject"] = data["code"]
        self.mail_rows = [data]
        self.render_results(reset_scroll=True)
        code = data.get("code") or "未识别"
        self.update_status(f"手机号验证码：{code}")

    def fetch_account_phone_code(self, email_address: str) -> None:
        account = self.account_store.get(email_address)
        if not account or not account.phone:
            self.update_status("该邮箱未绑定手机号")
            return
        phone = self.phone_store.get(account.phone)
        if not phone:
            self.update_status("绑定的手机号不存在，请在手机号管理中重新绑定")
            return
        if phone.phone in self.phone_code_workers and self.phone_code_workers[phone.phone].isRunning():
            self.update_status(f"正在获取 {phone.phone} 的验证码")
            return
        self.mail_rows.clear()
        self.render_results(reset_scroll=True)
        self.update_status(f"正在获取手机号验证码：{phone.phone}")
        self.progress_text.setText(f"正在获取 {compact_text(email_address, 36)} 绑定手机号的验证码...")
        worker = PhoneCodeWorker(phone)
        self.phone_code_workers[phone.phone] = worker
        worker.result_ready.connect(lambda row, email=email_address, number=phone.phone: self.on_account_phone_code_result(email, number, row))
        worker.error_ready.connect(lambda error, number=phone.phone: self.on_account_phone_code_error(number, error))
        worker.finished.connect(lambda number=phone.phone: self.phone_code_workers.pop(number, None))
        worker.start()

    def on_account_phone_code_result(self, email_address: str, phone_number: str, row: object) -> None:
        data = dict(row)
        data["account"] = email_address
        data["phone"] = phone_number
        code = clean_verification_code(data.get("code", ""))
        data["code"] = code
        if code:
            data["subject"] = code
        self.phone_store.mark_fetch_result(
            phone_number,
            "成功" if code else "未识别验证码",
            code=code,
            message=data.get("preview", ""),
        )
        self.add_sms_result(data)
        self.progress_text.setText(f"{compact_text(email_address, 36)} 手机验证码：{code or '未识别'}")
        self.refresh_accounts()

    def on_account_phone_code_error(self, phone_number: str, error: str) -> None:
        self.phone_store.mark_fetch_result(phone_number, "获取失败", message=error)
        self.update_status(f"手机号验证码获取失败：{error[:120]}")
        self.progress_text.setText("手机号验证码获取失败")
        self.refresh_accounts()

    def handle_import(self, records: list[ImportRecord], invalid: int) -> None:
        added, updated, skipped = self.account_store.upsert_records(records)
        phone_records: list[PhoneImportRecord] = []
        phone_only_bindings: list[tuple[str, str]] = []
        for record in records:
            self.account_states.setdefault(record.email, True)
            if record.phone and record.phone_api_url:
                phone_records.append(PhoneImportRecord(record.phone, record.phone_api_url, [record.email]))
            elif record.phone:
                phone_only_bindings.append((record.phone, record.email))
        phone_added = phone_updated = phone_bound = 0
        if phone_records:
            phone_added, phone_updated, _phone_skipped = self.phone_store.upsert_records(phone_records)
        for phone_number, email in phone_only_bindings:
            if self.phone_store.get(phone_number):
                bound, _rejected = self.phone_store.bind_emails(phone_number, {email})
                phone_bound += bound
        imported_groups = [record.category for record in records if record.category in ACCOUNT_CATEGORY_LABELS]
        target_group = next((group for group in imported_groups if group != ACCOUNT_CATEGORY_UNUSED), ACCOUNT_CATEGORY_UNUSED)
        self.set_account_group(target_group)
        self.refresh_accounts(reset_scroll=True)
        phone_total = phone_added + phone_updated + phone_bound
        phone_text = f"，手机号 {phone_total}" if phone_total else ""
        self.update_status(f"导入完成：新增 {added}，重复 {skipped}{phone_text}")
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
        order = {category: index for index, category in enumerate(ACCOUNT_CATEGORY_ORDER)}
        accounts = sorted(
            self.account_store.accounts,
            key=lambda account: (order.get(account.category, 99), account.email.lower()),
        )
        lines: list[str] = []
        current_category = ""
        for account in accounts:
            label = ACCOUNT_CATEGORY_LABELS.get(account.category, ACCOUNT_CATEGORY_LABELS[ACCOUNT_CATEGORY_UNUSED])
            if account.category != current_category:
                if lines:
                    lines.append("")
                lines.append(f"# ===== {label} =====")
                current_category = account.category
            lines.append(
                "----".join(self.export_account_parts(account, label))
            )
        Path(path).write_text("\n".join(lines), encoding="utf-8")
        self.update_status(f"已导出 {len(accounts)} 个邮箱")

    def export_account_parts(self, account: AccountRecord, label: str) -> list[str]:
        parts = [
            account.email,
            account.password,
            account.client_id,
            account.refresh_token,
            label,
        ]
        if account.phone:
            phone = self.phone_store.get(account.phone)
            parts.extend([account.phone, phone.api_url if phone else ""])
        return parts

    def remove_selected(self) -> None:
        selected = set(self.selected_emails())
        if not selected:
            return
        if QtWidgets.QMessageBox.question(self, "删除选中", f"确定删除选中的 {len(selected)} 个邮箱吗？") != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        self.phone_store.remove_emails(selected)
        removed = self.account_store.remove(selected)
        for email in selected:
            self.account_states.pop(email, None)
        self.refresh_accounts()
        self.update_status(f"已删除 {removed} 个邮箱")

    def mark_selected_used(self) -> None:
        self.set_selected_category(ACCOUNT_CATEGORY_PLUS)

    def mark_selected_unused(self) -> None:
        self.set_selected_category(ACCOUNT_CATEGORY_UNUSED)

    def set_selected_usage(self, used: bool) -> None:
        self.set_selected_category(ACCOUNT_CATEGORY_PLUS if used else ACCOUNT_CATEGORY_UNUSED)

    def set_selected_category(self, category: str) -> None:
        selected = set(self.selected_emails())
        if not selected:
            return
        changed = self.account_store.set_category(selected, category)
        for email in selected:
            self.account_states[email] = False
        self.refresh_accounts(reset_scroll=True)
        target = ACCOUNT_CATEGORY_LABELS.get(category, "未使用")
        self.update_status(f"已将 {changed} 个邮箱移动到 {target}")

    def clear_accounts(self) -> None:
        if not self.account_store.accounts:
            return
        if QtWidgets.QMessageBox.question(self, "清空全部", "确定清空全部邮箱吗？") != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        self.phone_store.clear_bindings()
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
            self.phone_store,
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
        self.progress_text.setText(f"[{done}/{total}] {compact_text(account, 44)}，已取 {messages} 条")

    def on_result_chunk(self, rows: object) -> None:
        self.mail_rows.extend(list(rows))
        self.update_result_badges()

    def on_fetch_finished(self, success: int, total_accounts: int, total_messages: int, stopped: bool) -> None:
        self.fetch_running = False
        self.update_fetch_buttons()
        if stopped:
            self.update_status(f"已停止 | 已完成 {success}/{total_accounts} | {total_messages} 条")
            self.progress_text.setText("已停止")
        else:
            self.update_status(f"完成 {success}/{total_accounts} | {total_messages} 条")
            self.progress_text.setText(f"完成：{success}/{total_accounts} 个任务，{total_messages} 条")
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
        sms_count = sum(1 for row in rows if row.get("protocol") == "SMS")
        self.total_badge.setText(f"共 {len(rows)} 条")
        self.graph_badge.setText(f"Graph: {graph_count}")
        self.imap_badge.setText(f"IMAP: {imap_count}")
        self.sms_badge.setText(f"SMS: {sms_count}")

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
        card.copy_code_requested.connect(self.copy_code)
        return card

    def copy_code(self, code: str) -> None:
        if not code:
            return
        QtWidgets.QApplication.clipboard().setText(code)
        self.update_status(f"已复制验证码：{code}")

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
                fieldnames=["account", "phone", "protocol", "time", "sender", "subject", "code", "read", "preview", "webLink", "concise"],
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
    icon_path = Path(__file__).resolve().parent.parent / "assets" / "mail.ico"
    if icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))
    font = QtGui.QFont("Microsoft YaHei UI", 10)
    font.setHintingPreference(QtGui.QFont.HintingPreference.PreferNoHinting)
    font.setStyleStrategy(
        QtGui.QFont.StyleStrategy.PreferAntialias
        | QtGui.QFont.StyleStrategy.PreferQuality
        | QtGui.QFont.StyleStrategy.ForceOutline
    )
    app.setFont(font)
    window = MainWindow()
    window.show()
    return app.exec()
