from __future__ import annotations

from pathlib import Path
import sys

from PyQt6 import QtCore, QtGui, QtWidgets

from .constants import (
    ACCOUNT_CATEGORY_UNUSED,
    APP_VERSION,
    DISPLAY_NAME,
    EXPORT_TOP_OPTIONS,
)
from .exporting import ensure_export_suffix, join_export_parts
from .models import AccountRecord, ImportRecord, PhoneImportRecord
from .parsing import clean_verification_code, compact_text
from .services import MailService
from .storage import AccountStore, ConfigStore, PhoneStore
from .widgets import AccountCard, BadgeLabel, CategorySelector, CheckBox, CountSelector, MailCard, SearchField, pill_button

SURFACE = "#ffffff"
SURFACE_SOFT = "#f7f8fa"
BORDER = "#e1e5ea"
BG = "#f1f3f6"
TEXT = "#17202e"
MUTED = "#697386"
BLUE = "#2563eb"
BLUE_DARK = "#1d4ed8"
TEAL = "#2563eb"
GREEN = "#16745a"
GREEN_SOFT = "#e8f5f0"
CYAN_SOFT = "#edf3ff"
CYAN_TEXT = "#315fba"
BLUE_SOFT = "#eaf0ff"
RED_SOFT = "#fff0f0"
RED = "#c63f4a"


def app_icon() -> QtGui.QIcon:
    candidates = [Path(__file__).resolve().parent.parent / "assets" / "mail.ico"]
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable))
    for path in candidates:
        if path.exists():
            return QtGui.QIcon(str(path))
    return QtGui.QIcon()


def app_stylesheet(theme: str = "light") -> str:
    if theme == "dark":
        surface = "#191c23"
        surface_soft = "#15181e"
        border = "#2d323c"
        bg = "#101218"
        text = "#f1f3f6"
        muted = "#9aa3b2"
        blue = "#5b8def"
        blue_dark = "#4778dc"
        teal = blue
        green = "#71bca1"
        green_soft = "#183329"
        cyan_soft = "#202c43"
        cyan_text = "#8eb0f4"
        blue_soft = "#202d49"
        purple = blue
        purple_soft = blue_soft
        amber = muted
        amber_soft = surface_soft
        red_soft = "#3b2328"
        red = "#f07d86"
        tab_bg = "#22262e"
        disabled_bg = "#242831"
        disabled_text = "#687181"
        input_selection = "#294674"
        accent_hover = "#2a3e63"
        scrollbar = "#3c424e"
        focus_border = "#5b8def"
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
        purple = BLUE
        purple_soft = BLUE_SOFT
        amber = MUTED
        amber_soft = SURFACE_SOFT
        red_soft = RED_SOFT
        red = RED
        tab_bg = "#eef0f3"
        disabled_bg = "#eceff2"
        disabled_text = "#a4acb8"
        input_selection = "#dbe7ff"
        accent_hover = "#dce7ff"
        scrollbar = "#c9cfd8"
        focus_border = BLUE
    return f"""
    QWidget {{
        color: {text};
        font-family: "Segoe UI Variable", "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI";
        font-size: 13px;
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
    QFrame#HeaderCard, QFrame#AccountToolsCard, QFrame#SidebarCard, QFrame#WorkspaceCard, QFrame#ControlsCard, QFrame#ProgressCard, QFrame#PhoneProgressCard, QFrame#MailCard, QFrame#AccountCard, QFrame#StatCard {{
        background: {surface};
        border: 1px solid {border};
        border-radius: 12px;
    }}
    QFrame#HeaderCard {{
        background: {surface};
        border-bottom: 1px solid {border};
    }}
    QFrame#AccountToolsCard {{
        background: {surface};
    }}
    QFrame#WorkspaceCard, QFrame#ControlsCard, QFrame#ProgressCard {{
        background: {surface};
    }}
    QFrame#AccountCard:hover, QFrame#MailCard:hover {{
        border: 1px solid {focus_border};
        background: {surface};
    }}
    QFrame#AccountCard[selected="true"] {{
        border: 1px solid {border};
        background: {blue_soft};
    }}
    QFrame#AccountCard[selected="true"]:hover {{
        border: 1px solid {focus_border};
    }}
    QFrame#ResultDivider {{
        background: {border};
        border: none;
        min-height: 1px;
        max-height: 1px;
    }}
    QFrame#CountSelect {{
        background: {surface};
        border: 1px solid {border};
        border-radius: 9px;
    }}
    QFrame#CountSelect:hover {{
        border: 1px solid {focus_border};
    }}
    QFrame#ResultSection,
    QFrame#ResultHeaderBand {{
        background: {surface};
        border: 1px solid {border};
        border-radius: 12px;
    }}
    QFrame#ResultHeaderBand {{
        border: none;
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
    }}
    QFrame#SidebarCard {{
        background: {surface};
    }}
    QFrame#AccountCard {{
        min-height: 72px;
        background: {surface_soft};
        border-radius: 9px;
    }}
    QFrame#MailCard {{
        min-height: 112px;
    }}
    QLabel#HeroTitle {{
        font-size: 20px;
        font-weight: 600;
        color: {text};
    }}
    QLabel#HeroSubTitle {{
        font-size: 12px;
        font-weight: 400;
        color: {muted};
    }}
    QLabel#SectionTitle {{
        font-size: 16px;
        font-weight: 600;
        color: {text};
    }}
    QLabel#AccountEmail {{
        font-size: 13px;
        font-weight: 600;
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
    QLabel#ToolbarLabel {{
        color: {muted};
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel#EmptyStateMark {{
        background: {blue_soft};
        color: {blue};
        border: 1px solid {border};
        border-radius: 18px;
        font-size: 25px;
        font-weight: 600;
    }}
    QLabel#EmptyStateTitle {{
        color: {text};
        font-size: 18px;
        font-weight: 600;
        margin-top: 6px;
    }}
    QLabel#EmptyStateText {{
        color: {muted};
        font-size: 13px;
        margin-bottom: 10px;
    }}
    QLabel#ProgressTitle {{
        color: {text};
        font-size: 13px;
        font-weight: 600;
    }}
    QLabel#ProgressPercent {{
        background: {blue_soft};
        color: {blue};
        border-radius: 10px;
        padding: 3px 10px;
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel#PhoneProgressTitle {{
        background: transparent;
        border: none;
        color: {text};
        font-size: 13px;
        font-weight: 600;
    }}
    QLabel#PhoneProgressText {{
        background: transparent;
        border: none;
        color: {muted};
        font-size: 12px;
        font-weight: 500;
    }}
    QLabel#PhoneProgressPercent {{
        background: transparent;
        border: 1px solid {border};
        border-radius: 10px;
        color: {blue};
        padding: 2px 10px;
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel#DialogTitle {{
        font-size: 24px;
        font-weight: 600;
        color: {text};
    }}
    QLabel#StatusLabel {{
        background: {surface_soft};
        border: 1px solid {border};
        border-radius: 8px;
        color: {text};
        font-weight: 600;
        padding: 6px 12px;
    }}
    QLabel#SidebarCount {{
        background: {surface_soft};
        color: {muted};
        border-radius: 7px;
        padding: 4px 9px;
        font-weight: 600;
    }}
    QLabel#BadgeLabel {{
        border-radius: 6px;
        padding: 2px 8px;
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
    QLineEdit#SearchField, QPlainTextEdit#ImportEditor, QTextEdit#DetailViewer {{
        background: {surface};
        border: 1px solid {border};
        border-radius: 8px;
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
    QLineEdit#SearchField:focus, QPlainTextEdit#ImportEditor:focus, QTextEdit#DetailViewer:focus {{
        border: 1px solid {focus_border};
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
    QLabel#BoundEmailText {{
        background: transparent;
        color: {text};
        font-size: 13px;
    }}
    QWidget#BoundEmailCell {{
        background: transparent;
    }}
    QWidget#BoundEmailCell[selected="true"] {{
        background: {input_selection};
    }}
    QToolButton[role="email-menu"] {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        color: {blue};
        font-size: 15px;
        font-weight: 700;
        padding: 0;
    }}
    QToolButton[role="email-menu"]:hover {{
        background: {blue_soft};
        border: 1px solid {border};
    }}
    QPushButton {{
        background: {surface};
        color: {text};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 8px 14px;
        font-weight: 600;
        outline: none;
    }}
    QPushButton[role="primary"] {{
        background: {blue};
        color: white;
        border: 1px solid {blue};
    }}
    QPushButton[role="primary"]:hover {{
        background: {blue_dark};
        border: 1px solid {blue_dark};
    }}
    QPushButton[role="primary"]:pressed {{
        background: {blue_dark};
        padding-top: 9px;
        padding-bottom: 7px;
    }}
    QPushButton[role="secondary"] {{
        background: {surface_soft};
        color: {text};
        border: 1px solid {border};
    }}
    QPushButton[role="secondary"]:hover {{
        background: {blue_soft};
        border: 1px solid {border};
        color: {blue};
    }}
    QPushButton[role="accent"] {{
        background: {blue_soft};
        color: {blue};
        border: 1px solid {border};
    }}
    QPushButton[role="accent"]:hover {{
        background: {accent_hover};
        border: 1px solid {border};
    }}
    QPushButton[role="tool"] {{
        background: {surface_soft};
        color: {text};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 7px 10px;
    }}
    QPushButton[role="tool"]:hover {{
        background: {blue_soft};
        color: {blue};
        border: 1px solid {focus_border};
    }}
    QPushButton[role="tool"]:pressed {{
        background: {cyan_text};
    }}
    QPushButton[role="danger"] {{
        background: {red_soft};
        color: {red};
        border: 1px solid {border};
    }}
    QPushButton[role="danger"]:hover {{
        background: {red};
        color: white;
        border: 1px solid {border};
    }}
    QPushButton[role="move"] {{
        background: {amber_soft};
        color: {amber};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 7px 10px;
    }}
    QPushButton[role="move"]:hover {{
        background: {amber};
        border: 1px solid {border};
        color: white;
    }}
    QPushButton[role="move"]:pressed {{
        background: {amber};
    }}
    QPushButton[role="move-danger"] {{
        background: {red_soft};
        color: {red};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 7px 10px;
    }}
    QPushButton[role="move-danger"]:hover {{
        background: {red};
        color: white;
        border: 1px solid {border};
    }}
    QPushButton[role="move-danger"]:pressed {{
        background: {red};
    }}
    QPushButton[role="mini-action"] {{
        background: {purple_soft};
        color: {purple};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 3px 8px;
    }}
    QPushButton[role="mini-action"]:hover {{
        background: {purple};
        border: 1px solid {border};
        color: white;
    }}
    QPushButton[role="ghost"] {{
        background: transparent;
        color: {muted};
        border: 1px solid transparent;
        padding: 8px 10px;
    }}
    QPushButton[role="ghost"]:hover {{
        background: {surface_soft};
        color: {text};
        border: 1px solid {border};
    }}
    QPushButton[role="tagged"] {{
        background: {green_soft};
        color: {green};
        border: 1px solid {border};
        padding: 8px 10px;
    }}
    QPushButton[role="tagged"]:hover {{
        background: {green_soft};
        border: 1px solid {border};
        color: {green};
    }}
    QPushButton[role="account-action"] {{
        background: {surface};
        color: {blue};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 0;
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton[role="account-action"]:hover {{
        background: {blue_soft};
        color: {blue_dark};
        border: 1px solid {focus_border};
    }}
    QPushButton[role="account-tagged"] {{
        background: {green_soft};
        color: {green};
        border: 1px solid {green};
        border-radius: 6px;
        padding: 0;
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton[role="account-tagged"]:hover {{
        background: {green_soft};
        color: {green};
        border: 1px solid {green};
    }}
    QFrame#CategorySelect {{
        background: {blue_soft};
        border: 1px solid {border};
        border-radius: 8px;
    }}
    QFrame#CategorySelect:hover,
    QFrame#CategorySelect:focus {{
        background: {accent_hover};
        border: 1px solid {focus_border};
    }}
    QLabel#CategoryCaption {{
        color: {muted};
        font-size: 12px;
        font-weight: 500;
    }}
    QLabel#CategoryValue {{
        color: {blue};
        font-size: 13px;
        font-weight: 600;
    }}
    QLabel#CategoryCount {{
        background: {surface};
        color: {blue};
        border: 1px solid {border};
        border-radius: 7px;
        padding: 2px 7px;
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel#CategoryArrow {{
        color: {muted};
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton[role="move-picker"]::menu-indicator {{
        image: none;
        width: 0;
    }}
    QPushButton[role="move-picker"] {{
        background: {surface_soft};
        color: {text};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 6px 12px;
        text-align: center;
    }}
    QPushButton[role="move-picker"]:hover {{
        background: {blue_soft};
        color: {blue};
        border: 1px solid {focus_border};
    }}
    QPushButton[compact="true"] {{
        padding: 3px 8px;
        border-radius: 7px;
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
        background: {surface_soft};
        color: {muted};
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 8px 10px;
    }}
    QPushButton[role="tab"]:checked {{
        background: {blue};
        color: white;
        border: 1px solid {blue};
    }}
    QPushButton[role="tab"]:hover {{
        background: {blue_soft};
        border: 1px solid {border};
    }}
    QPushButton[role="protocol"] {{
        background: {surface_soft};
        color: {muted};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 8px 12px;
    }}
    QPushButton[role="protocol"]:checked {{
        background: {blue_soft};
        color: {blue};
        border: 1px solid {focus_border};
    }}
    QPushButton[role="protocol"]:hover {{
        background: {blue_soft};
        color: {blue};
        border: 1px solid {focus_border};
    }}
    QPushButton:disabled {{
        background: {disabled_bg};
        color: {disabled_text};
        border: 1px solid {border};
    }}
    QProgressBar {{
        background: {tab_bg};
        border-radius: 6px;
        border: none;
        min-height: 8px;
    }}
    QProgressBar::chunk {{
        background: {teal};
        border-radius: 6px;
    }}
    QMenu {{
        background: {surface};
        color: {text};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 6px;
    }}
    QMenu::item {{
        border-radius: 6px;
        padding: 7px 28px 7px 10px;
    }}
    QMenu::item:selected {{
        background: {blue_soft};
        color: {blue};
    }}
    QMenu::item:disabled {{
        color: {disabled_text};
    }}
    QMenu#CategoryMenu::item {{
        min-height: 24px;
        padding: 7px 30px 7px 12px;
    }}
    QMenu::separator {{
        background: {border};
        height: 1px;
        margin: 5px 8px;
    }}
    QListWidget#CategoryManagerList {{
        background: {surface_soft};
        border: 1px solid {border};
        border-radius: 10px;
        outline: none;
        padding: 6px;
    }}
    QListWidget#CategoryManagerList::item {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        min-height: 38px;
        padding: 4px 10px;
    }}
    QListWidget#CategoryManagerList::item:hover {{
        background: {surface};
        border: 1px solid {border};
    }}
    QListWidget#CategoryManagerList::item:selected {{
        background: {blue_soft};
        border: 1px solid {focus_border};
        color: {blue};
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollArea#AccountScroll QWidget#AccountViewport,
    QWidget#AccountContainer {{
        background: {surface};
    }}
    QScrollArea#AccountScroll,
    QScrollArea#ResultScroll {{
        background: transparent;
    }}
    QScrollArea#ResultScroll QWidget#ResultViewport,
    QWidget#ResultContainer {{
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
    QSplitter::handle:horizontal {{
        background: transparent;
        border-left: 1px solid {border};
        border-right: 1px solid transparent;
    }}
    QSplitter::handle:horizontal:hover {{
        border-left: 2px solid {focus_border};
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
        self.resize(1440, 880)
        self.setMinimumSize(1120, 720)

        icon_path = Path(__file__).resolve().parent.parent / "assets" / "mail.ico"
        self.setWindowIcon(app_icon())

        self.account_store = AccountStore()
        self.category_store = self.account_store.category_store
        self.phone_store = PhoneStore(self.account_store)
        self.config_store = ConfigStore()
        self.setStyleSheet(app_stylesheet(self.config_store.theme))
        self.mail_service = MailService(self.config_store, self.account_store)

        self.fetch_worker: FetchWorker | None = None
        self.phone_code_workers: dict[str, object] = {}
        self.standalone_phone_dialog: QtWidgets.QDialog | None = None
        self.fetch_running = False
        self.account_states: dict[str, bool] = {account.email: True for account in self.account_store.accounts}
        self.mail_rows: list[dict] = []
        self.logs: list[str] = []
        self.current_category_key = ACCOUNT_CATEGORY_UNUSED

        self.build_ui(icon_path)
        self.render_results(reset_scroll=True)
        self.set_protocol(self.config_store.protocol, save=False)
        self.update_status("正在载入账号")
        # Let the shell paint before constructing every account card.  With a
        # large account pool this changes startup from a blank wait to an
        # immediately responsive window.
        QtCore.QTimer.singleShot(30, self.finish_initialization)

    def finish_initialization(self) -> None:
        self.refresh_accounts()
        self.update_status("就绪")

    def build_ui(self, icon_path: Path) -> None:
        root = QtWidgets.QWidget()
        root.setObjectName("CentralRoot")
        self.setCentralWidget(root)

        outer = QtWidgets.QVBoxLayout(root)
        outer.setContentsMargins(16, 14, 16, 16)
        outer.setSpacing(10)

        header = self.make_header(icon_path)
        outer.addWidget(header)

        body = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        body.setHandleWidth(10)
        body.setChildrenCollapsible(False)
        outer.addWidget(body, 1)

        self.sidebar = self.make_left_panel()
        body.addWidget(self.sidebar)

        self.main_panel = self.make_main_panel()
        body.addWidget(self.main_panel)
        body.setStretchFactor(0, 28)
        body.setStretchFactor(1, 72)
        body.setSizes([390, 1030])

    def make_header(self, icon_path: Path) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("HeaderCard")
        layout = QtWidgets.QHBoxLayout(frame)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        icon_box = QtWidgets.QLabel()
        icon_box.setFixedSize(40, 40)
        icon_box.setStyleSheet("background: transparent; border: none;")
        icon_box.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        if icon_path.exists():
            icon = QtGui.QIcon(str(icon_path))
            pixmap = icon.pixmap(QtCore.QSize(40, 40))
            icon_box.setPixmap(pixmap)
        else:
            icon_box.setText("✉")
            icon_box.setStyleSheet(
                f"background:{BLUE}; border-radius:18px; color:white; font-size:24px; font-weight:700;"
            )
        layout.addWidget(icon_box)

        titles = QtWidgets.QVBoxLayout()
        titles.setSpacing(2)
        title = QtWidgets.QLabel(f"{DISPLAY_NAME} {APP_VERSION}")
        title.setObjectName("HeroTitle")
        titles.addWidget(title)
        subtitle = QtWidgets.QLabel("邮箱验证码工作台 · IMAP / Graph")
        subtitle.setObjectName("HeroSubTitle")
        titles.addWidget(subtitle)
        layout.addLayout(titles, 1)

        self.auto_fetch_box = CheckBox("导入后自动取件")
        self.auto_fetch_box.setFixedSize(140, 34)
        self.auto_fetch_box.setChecked(self.config_store.auto_fetch_after_import)
        self.auto_fetch_box.toggled.connect(self.save_config)
        layout.addWidget(self.auto_fetch_box, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)

        self.concise_mode_box = CheckBox("简洁模式")
        self.concise_mode_box.setFixedSize(96, 34)
        self.concise_mode_box.setChecked(self.config_store.concise_mode)
        self.concise_mode_box.toggled.connect(self.save_config)
        layout.addWidget(self.concise_mode_box, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)

        self.dark_mode_box = CheckBox("深色模式")
        self.dark_mode_box.setFixedSize(96, 34)
        self.dark_mode_box.setChecked(self.config_store.theme == "dark")
        self.dark_mode_box.toggled.connect(self.apply_theme)
        layout.addWidget(self.dark_mode_box, 0, QtCore.Qt.AlignmentFlag.AlignVCenter)

        self.status_label = QtWidgets.QLabel("就绪")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(34)
        self.status_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        layout.addWidget(self.status_label, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        return frame

    def make_left_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        panel.setMinimumWidth(340)
        panel.setMaximumWidth(560)
        panel.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)

        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.make_account_tools_card())
        layout.addWidget(self.make_sidebar(), 1)
        return panel

    def make_account_tools_card(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("AccountToolsCard")
        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(7)

        title = QtWidgets.QLabel("快速操作")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        tools_grid = QtWidgets.QGridLayout()
        tools_grid.setHorizontalSpacing(8)
        tools_grid.setVerticalSpacing(8)
        tools = (
            ("导入邮箱", "primary", self.open_import_dialog),
            ("导出邮箱", "secondary", self.export_accounts),
            ("手机号管理", "secondary", self.open_phone_dialog),
            ("手机号取码", "secondary", self.open_standalone_phone_code_dialog),
        )
        for index, (text, role, handler) in enumerate(tools):
            button = pill_button(text, role=role)
            button.setFixedHeight(34)
            button.setMinimumWidth(max(96, button.fontMetrics().horizontalAdvance(text) + 24))
            button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
            button.clicked.connect(handler)
            tools_grid.addWidget(button, index // 2, index % 2)
        tools_grid.setColumnStretch(0, 1)
        tools_grid.setColumnStretch(1, 1)
        layout.addLayout(tools_grid)
        return frame

    def make_sidebar(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("SidebarCard")
        frame.setMinimumWidth(340)
        frame.setMaximumWidth(560)
        frame.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)

        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(8)

        top = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("账号库")
        title.setObjectName("SectionTitle")
        top.addWidget(title)
        top.addStretch(1)
        self.account_count_label = QtWidgets.QLabel("0/0")
        self.account_count_label.setObjectName("SidebarCount")
        top.addWidget(self.account_count_label)
        manage_button = pill_button("管理分类", role="secondary")
        manage_button.setFixedHeight(32)
        manage_button.clicked.connect(self.open_category_manager)
        top.addWidget(manage_button)
        layout.addLayout(top)

        category_line = QtWidgets.QHBoxLayout()
        category_line.setSpacing(6)
        self.category_selector = CategorySelector()
        self.category_selector.currentKeyChanged.connect(self.on_category_changed)
        category_line.addWidget(self.category_selector, 1)
        layout.addLayout(category_line)

        self.account_search = SearchField("搜索当前分类中的邮箱")
        self.account_search.textChanged.connect(lambda: self.refresh_accounts(reset_scroll=True))
        self.account_search.setFixedHeight(38)
        layout.addWidget(self.account_search)

        list_action_line = QtWidgets.QHBoxLayout()
        list_action_line.setSpacing(6)
        self.select_all_box = CheckBox("全选")
        self.select_all_box.setFixedSize(68, 34)
        self.select_all_box.setChecked(True)
        self.select_all_box.toggled.connect(self.toggle_all_accounts)
        list_action_line.addWidget(self.select_all_box)

        self.move_button = pill_button("移动到分类  ▾", role="move-picker")
        self.move_button.setFixedHeight(34)
        self.move_button.setMinimumWidth(104)
        self.move_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        list_action_line.addWidget(self.move_button, 2)

        clear_button = pill_button("清空", role="ghost")
        clear_button.setFixedHeight(34)
        clear_button.setMinimumWidth(52)
        clear_button.setMaximumWidth(110)
        clear_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        clear_button.clicked.connect(self.clear_accounts)
        list_action_line.addWidget(clear_button, 1)

        delete_button = pill_button("删除", role="danger")
        delete_button.clicked.connect(self.remove_selected)
        delete_button.setFixedHeight(34)
        delete_button.setMinimumWidth(52)
        delete_button.setMaximumWidth(110)
        delete_button.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        list_action_line.addWidget(delete_button, 1)
        layout.addLayout(list_action_line)
        self.refresh_category_controls(ACCOUNT_CATEGORY_UNUSED)

        self.account_scroll = QtWidgets.QScrollArea()
        self.account_scroll.setObjectName("AccountScroll")
        self.account_scroll.viewport().setObjectName("AccountViewport")
        self.account_scroll.setWidgetResizable(True)
        self.account_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.account_container = QtWidgets.QWidget()
        self.account_container.setObjectName("AccountContainer")
        self.account_layout = QtWidgets.QVBoxLayout(self.account_container)
        self.account_layout.setContentsMargins(0, 4, 10, 0)
        self.account_layout.setSpacing(8)
        self.account_layout.addStretch(1)
        self.account_scroll.setWidget(self.account_container)
        layout.addWidget(self.account_scroll, 1)
        return frame

    def make_main_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        workspace = QtWidgets.QFrame()
        workspace.setObjectName("WorkspaceCard")
        workspace_layout = QtWidgets.QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(16, 14, 16, 14)
        workspace_layout.setSpacing(11)

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
        workspace_layout.addLayout(top_row)

        toolbar_row = QtWidgets.QHBoxLayout()
        toolbar_row.setSpacing(10)
        channel_label = QtWidgets.QLabel("取件通道")
        channel_label.setObjectName("ToolbarLabel")
        toolbar_row.addWidget(channel_label)
        self.imap_button = pill_button("IMAP", role="protocol", checkable=True)
        self.graph_button = pill_button("Graph", role="protocol", checkable=True)
        self.imap_button.clicked.connect(lambda: self.set_protocol("IMAP"))
        self.graph_button.clicked.connect(lambda: self.set_protocol("Graph"))
        toolbar_buttons: list[QtWidgets.QPushButton] = [self.imap_button, self.graph_button]

        export_csv_button = pill_button("导出 CSV", role="ghost")
        export_csv_button.clicked.connect(self.export_csv)
        self.stop_button = pill_button("停止", role="danger")
        self.stop_button.clicked.connect(self.request_stop)
        self.fetch_selected_button = pill_button("选中取件", role="primary")
        self.fetch_selected_button.clicked.connect(self.fetch_selected)
        self.fetch_all_button = pill_button("全部取件", role="secondary")
        self.fetch_all_button.clicked.connect(self.fetch_all)
        self.fetch_all_button.setStyleSheet("")
        toolbar_buttons.extend([export_csv_button, self.stop_button, self.fetch_selected_button, self.fetch_all_button])

        for button in toolbar_buttons:
            self.prepare_toolbar_button(button)
        toolbar_row.addWidget(self.imap_button)
        toolbar_row.addWidget(self.graph_button)
        toolbar_row.addSpacing(4)
        toolbar_row.addWidget(export_csv_button)
        toolbar_row.addWidget(self.stop_button)
        toolbar_row.addStretch(1)
        toolbar_row.addWidget(self.fetch_selected_button)
        toolbar_row.addWidget(self.fetch_all_button)
        workspace_layout.addLayout(toolbar_row)

        progress_header = QtWidgets.QHBoxLayout()
        progress_header.setSpacing(8)
        progress_title = QtWidgets.QLabel("取件进度")
        progress_title.setObjectName("SectionTitle")
        progress_header.addWidget(progress_title)

        self.progress_text = QtWidgets.QLabel("等待操作")
        self.progress_text.setObjectName("ProgressText")
        self.progress_text.setMaximumHeight(18)
        progress_header.addWidget(self.progress_text, 1)

        self.progress_percent = QtWidgets.QLabel("0%")
        self.progress_percent.setObjectName("ProgressPercent")
        self.progress_percent.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.progress_percent.setFixedHeight(24)
        self.progress_percent.setMinimumWidth(54)
        progress_header.addWidget(self.progress_percent)
        workspace_layout.addLayout(progress_header)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        workspace_layout.addWidget(self.progress_bar)
        layout.addWidget(workspace)

        result_section = QtWidgets.QFrame()
        result_section.setObjectName("ResultSection")
        result_section_layout = QtWidgets.QVBoxLayout(result_section)
        result_section_layout.setContentsMargins(0, 0, 0, 0)
        result_section_layout.setSpacing(0)

        header_band = QtWidgets.QFrame()
        header_band.setObjectName("ResultHeaderBand")
        header = QtWidgets.QHBoxLayout(header_band)
        header.setContentsMargins(16, 10, 16, 10)
        header.setSpacing(8)
        title = QtWidgets.QLabel("验证码与邮件")
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
        result_section_layout.addWidget(header_band)

        result_divider = QtWidgets.QFrame()
        result_divider.setObjectName("ResultDivider")
        result_section_layout.addWidget(result_divider)

        self.result_scroll = QtWidgets.QScrollArea()
        self.result_scroll.setObjectName("ResultScroll")
        self.result_scroll.viewport().setObjectName("ResultViewport")
        self.result_scroll.setWidgetResizable(True)
        self.result_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.result_container = QtWidgets.QWidget()
        self.result_container.setObjectName("ResultContainer")
        self.result_layout = QtWidgets.QVBoxLayout(self.result_container)
        self.result_layout.setContentsMargins(16, 12, 12, 16)
        self.result_layout.setSpacing(8)
        self.result_layout.addStretch(1)
        self.result_scroll.setWidget(self.result_container)
        result_section_layout.addWidget(self.result_scroll, 1)
        layout.addWidget(result_section, 1)
        return panel

    @staticmethod
    def prepare_toolbar_button(button: QtWidgets.QPushButton) -> None:
        text_width = button.fontMetrics().horizontalAdvance(button.text())
        button.setFixedHeight(38)
        button.setMinimumWidth(max(92, text_width + 30))
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
        if self.standalone_phone_dialog is not None:
            self.standalone_phone_dialog.setStyleSheet(self.styleSheet())
        self.save_config()

    @property
    def protocol(self) -> str:
        return "IMAP" if self.imap_button.isChecked() else "Graph"

    def set_protocol(self, protocol: str, save: bool = True) -> None:
        protocol = "IMAP" if protocol == "IMAP" else "Graph"
        self.graph_button.setChecked(protocol == "Graph")
        self.imap_button.setChecked(protocol == "IMAP")
        self.update_protocol_buttons()
        if save:
            self.save_config()

    def update_protocol_buttons(self) -> None:
        if not self.graph_button.isChecked() and not self.imap_button.isChecked():
            self.graph_button.setChecked(True)
        for name, button in (("IMAP", self.imap_button), ("Graph", self.graph_button)):
            active = button.isChecked()
            button.setText(f"{name}令牌")
            button.setToolTip(f"当前使用{name}令牌" if active else f"切换到{name}令牌")

    def current_group(self) -> str:
        key = self.category_selector.currentKey() if hasattr(self, "category_selector") else self.current_category_key
        return str(key) if key and self.category_store.contains(str(key)) else ACCOUNT_CATEGORY_UNUSED

    def set_account_group(self, group: str) -> None:
        group = self.category_store.resolve(group) or ACCOUNT_CATEGORY_UNUSED
        if not self.category_store.contains(group):
            group = ACCOUNT_CATEGORY_UNUSED
        self.current_category_key = group
        self.category_selector.setCurrentKey(group)
        self.refresh_accounts(reset_scroll=True)

    def on_category_changed(self, category: str) -> None:
        self.current_category_key = category
        if hasattr(self, "account_scroll"):
            self.refresh_accounts(reset_scroll=True)

    def refresh_category_controls(self, selected: str | None = None) -> None:
        if not hasattr(self, "category_selector"):
            return
        selected_key = self.category_store.resolve(selected or self.current_group()) or ACCOUNT_CATEGORY_UNUSED
        counts = {
            category.key: sum(1 for account in self.account_store.accounts if account.category == category.key)
            for category in self.category_store.categories
        }
        category_items = [
            (category.key, category.label, counts.get(category.key, 0))
            for category in self.category_store.categories
        ]
        self.category_selector.setItems(category_items, selected_key)
        self.current_category_key = self.category_selector.currentKey() or ACCOUNT_CATEGORY_UNUSED

        if hasattr(self, "move_button"):
            old_menu = self.move_button.menu()
            menu = QtWidgets.QMenu(self.move_button)
            menu.setObjectName("CategoryMenu")
            menu.setMinimumWidth(max(200, self.move_button.width()))
            for category in self.category_store.categories:
                action = menu.addAction(category.label)
                action.triggered.connect(
                    lambda checked=False, value=category.key: self.set_selected_category(value)
                )
            self.move_button.setMenu(menu)
            if old_menu is not None and old_menu is not menu:
                old_menu.deleteLater()

    def open_category_manager(self) -> None:
        from .category_dialog import CategoryManagerDialog

        dialog = CategoryManagerDialog(self.category_store, self.account_store, self)
        dialog.setStyleSheet(self.styleSheet())
        dialog.categories_changed.connect(self.on_categories_changed)
        dialog.exec()

    def on_categories_changed(self) -> None:
        current = self.current_group()
        if not self.category_store.contains(current):
            current = ACCOUNT_CATEGORY_UNUSED
        self.refresh_category_controls(current)
        self.refresh_accounts(reset_scroll=True)

    def filtered_accounts(self) -> list[AccountRecord]:
        needle = self.account_search.text().strip().lower()
        pool = self.current_group_accounts()
        if not needle:
            return pool
        starts = [account for account in pool if account.email.lower().startswith(needle)]
        contains = [account for account in pool if needle in account.email.lower() and account not in starts]
        return starts + contains

    def current_group_accounts(self) -> list[AccountRecord]:
        current = self.current_group()
        return sorted(
            [account for account in self.account_store.accounts if account.category == current],
            key=lambda account: account.email.lower(),
        )

    def current_group_emails(self) -> list[str]:
        return [account.email for account in self.current_group_accounts()]

    def visible_account_emails(self) -> set[str]:
        return {account.email for account in self.filtered_accounts()}

    def selected_emails(self) -> list[str]:
        visible = self.visible_account_emails()
        return [email for email, checked in self.account_states.items() if checked and email in visible and self.account_store.get(email)]

    def on_account_checked(self, email: str, checked: bool) -> None:
        self.account_states[email] = checked
        self.sync_select_all_box()

    def refresh_accounts(self, reset_scroll: bool = False) -> None:
        current = self.current_group()
        self.refresh_category_controls(current)
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
        card = AccountCard(account, checked, self.category_store.label(account.category))
        card.selection_changed.connect(self.on_account_checked)
        card.copy_requested.connect(self.copy_email)
        card.mail_code_requested.connect(self.fetch_account_mail_code)
        card.phone_code_requested.connect(self.fetch_account_phone_code)
        card.tag_requested.connect(self.edit_account_tag)
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

    def edit_account_tag(self, email_address: str) -> None:
        account = self.account_store.get(email_address)
        if not account:
            self.update_status("邮箱不存在")
            return
        tag, ok = QtWidgets.QInputDialog.getText(
            self,
            "编辑标签",
            f"为 {email_address} 设置标签：",
            QtWidgets.QLineEdit.EchoMode.Normal,
            account.tag,
        )
        if not ok:
            return
        clean = " ".join(tag.split())[:40]
        if self.account_store.set_tag(email_address, clean):
            self.refresh_accounts()
            self.update_status(f"已更新标签：{clean or '已清除'}")

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
        from .dialogs import ImportDialog

        dialog = ImportDialog(self)
        dialog.setStyleSheet(self.styleSheet())
        dialog.import_requested.connect(self.handle_import)
        dialog.exec()

    def open_phone_dialog(self) -> None:
        from .dialogs import PhoneDialog

        dialog = PhoneDialog(self.phone_store, self.selected_emails(), self.current_group_emails(), self)
        dialog.setStyleSheet(self.styleSheet())
        dialog.changed.connect(lambda: self.refresh_accounts())
        dialog.sms_result_ready.connect(self.add_sms_result)
        dialog.exec()

    def open_standalone_phone_code_dialog(self) -> None:
        from .dialogs import StandalonePhoneCodeDialog

        if self.standalone_phone_dialog is None:
            self.standalone_phone_dialog = StandalonePhoneCodeDialog(self)
            self.standalone_phone_dialog.destroyed.connect(lambda: setattr(self, "standalone_phone_dialog", None))
        self.standalone_phone_dialog.setStyleSheet(self.styleSheet())
        self.standalone_phone_dialog.show()
        self.standalone_phone_dialog.raise_()
        self.standalone_phone_dialog.activateWindow()

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
        from .dialogs import PhoneCodeWorker

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
        imported_groups = [
            resolved
            for record in records
            if (resolved := self.category_store.resolve(record.category))
        ]
        target_group = next((group for group in imported_groups if group != ACCOUNT_CATEGORY_UNUSED), ACCOUNT_CATEGORY_UNUSED)
        self.refresh_category_controls(target_group)
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
        export_path = ensure_export_suffix(Path(path), ".txt")
        order = {category: index for index, category in enumerate(self.category_store.keys())}
        accounts = sorted(
            self.account_store.accounts,
            key=lambda account: (order.get(account.category, 99), account.email.lower()),
        )
        lines: list[str] = []
        current_category = ""
        for account in accounts:
            label = self.category_store.label(account.category)
            if account.category != current_category:
                if lines:
                    lines.append("")
                lines.append(f"# ===== {label} =====")
                current_category = account.category
            lines.append(
                join_export_parts(self.export_account_parts(account, label))
            )
        try:
            export_path.write_text("\n".join(lines), encoding="utf-8")
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "导出失败", f"无法写入文件：{exc}")
            self.update_status("导出失败")
            return
        self.update_status(f"已导出 {len(accounts)} 个邮箱")

    def export_account_parts(self, account: AccountRecord, label: str) -> list[str]:
        parts = [
            account.email,
            account.password,
            account.client_id,
            account.refresh_token,
            label,
            account.tag,
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

    def set_selected_category(self, category: str) -> None:
        selected = set(self.selected_emails())
        if not selected:
            self.update_status("请先勾选要移动的邮箱")
            return
        category = self.category_store.resolve(category) or ACCOUNT_CATEGORY_UNUSED
        changed = self.account_store.set_category(selected, category)
        for email in selected:
            self.account_states[email] = False
        self.refresh_accounts(reset_scroll=True)
        target = self.category_store.label(category)
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
        from .workers import FetchWorker

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
        self.progress_percent.setText("0%")
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
            self.progress_percent.setText("停止中")
            self.update_status("正在停止取件")

    def on_progress(self, done: int, total: int, account: str, messages: int) -> None:
        self.progress_bar.setRange(0, max(total, 1))
        self.progress_bar.setValue(done)
        percent = int((done / max(total, 1)) * 100)
        self.progress_percent.setText(f"{percent}%")
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
            self.progress_percent.setText("已停止")
        elif success == 0 and total_accounts:
            self.update_status("取件失败，请查看左侧账号状态中的错误详情")
            self.progress_bar.setRange(0, max(total_accounts, 1))
            self.progress_bar.setValue(total_accounts)
            self.progress_percent.setText("失败")
            self.progress_text.setText(f"{total_accounts} 个任务均未成功，请检查令牌权限或网络")
        else:
            self.update_status(f"完成 {success}/{total_accounts} | {total_messages} 条")
            self.progress_bar.setRange(0, max(total_accounts, 1))
            self.progress_bar.setValue(total_accounts)
            self.progress_percent.setText("100%")
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
        if rows:
            widgets = [self.build_mail_card(row) for row in rows]
            self.rebuild_list(self.result_layout, widgets)
        else:
            self.rebuild_list(self.result_layout, [self.build_results_empty_state()], fill=True)
        self.update_result_badges()
        if reset_scroll:
            self.result_scroll.verticalScrollBar().setValue(0)

    def build_mail_card(self, row: dict) -> QtWidgets.QWidget:
        card = MailCard(row)
        card.open_requested.connect(self.open_mail_detail)
        card.copy_code_requested.connect(self.copy_code)
        return card

    def build_results_empty_state(self) -> QtWidgets.QWidget:
        state = QtWidgets.QFrame()
        state.setObjectName("EmptyState")
        state.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        layout = QtWidgets.QVBoxLayout(state)
        layout.setContentsMargins(32, 44, 32, 52)
        layout.setSpacing(8)
        layout.addStretch(1)

        mark = QtWidgets.QLabel("✉")
        mark.setObjectName("EmptyStateMark")
        mark.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(56, 56)
        layout.addWidget(mark, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)

        title = QtWidgets.QLabel("还没有取件结果")
        title.setObjectName("EmptyStateTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        hint = QtWidgets.QLabel("在左侧勾选邮箱，然后开始取件。验证码会集中显示在这里。")
        hint.setObjectName("EmptyStateText")
        hint.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        action = pill_button("选中账号取件", role="primary")
        action.setFixedHeight(38)
        action.setMinimumWidth(132)
        action.clicked.connect(self.fetch_selected)
        layout.addWidget(action, 0, QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(2)
        return state

    def copy_code(self, code: str) -> None:
        if not code:
            return
        QtWidgets.QApplication.clipboard().setText(code)
        self.update_status(f"已复制验证码：{code}")

    def open_mail_detail(self, row: dict) -> None:
        from .dialogs import MailDetailDialog

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

        export_path = ensure_export_suffix(Path(path), ".csv")
        try:
            with open(export_path, "w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["account", "phone", "protocol", "time", "sender", "subject", "code", "read", "preview", "webLink", "concise"],
                    extrasaction="ignore",
                )
                writer.writeheader()
                writer.writerows(rows)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "导出失败", f"无法写入文件：{exc}")
            self.update_status("导出失败")
            return
        self.update_status(f"已导出 {len(rows)} 条结果")

    @staticmethod
    def rebuild_list(
        layout: QtWidgets.QVBoxLayout,
        widgets: list[QtWidgets.QWidget],
        fill: bool = False,
    ) -> None:
        parent = layout.parentWidget()
        if parent is not None:
            parent.setUpdatesEnabled(False)
        try:
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
                layout.addWidget(widget, 1 if fill else 0)
            if not fill:
                layout.addStretch(1)
        finally:
            if parent is not None:
                parent.setUpdatesEnabled(True)


def run_app() -> int:
    enable_qt_dpi()
    app = QtWidgets.QApplication([])
    app.setApplicationDisplayName(DISPLAY_NAME)
    app.setStyle("Fusion")
    app.setWindowIcon(app_icon())
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
