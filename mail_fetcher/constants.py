from __future__ import annotations

import re

APP_NAME = "OutlookHotmailMailFetcher"
DISPLAY_NAME = "邮件验证码助手"
APP_VERSION = "V1.6"

AUTHORITY_BASE = "https://login.microsoftonline.com"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"
GRAPH_INTERACTIVE_SCOPES = ["Mail.Read", "offline_access"]
GRAPH_REFRESH_SCOPE_OPTIONS: list[str | None] = [
    "https://graph.microsoft.com/Mail.Read offline_access",
    "Mail.Read offline_access",
    "https://graph.microsoft.com/.default",
    None,
]
IMAP_REFRESH_SCOPE_OPTIONS: list[str | None] = [
    "https://outlook.office.com/IMAP.AccessAsUser.All offline_access",
    "IMAP.AccessAsUser.All offline_access",
]
IMAP_HOST = "outlook.office365.com"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CODE_PATTERNS = [
    re.compile(r"(?i)(?:验证码|校验码|动态码|安全代码|verification code|security code|code|otp|pin)[^A-Z0-9]{0,24}([A-Z0-9]{4,10})"),
    re.compile(r"(?<!\d)(\d{4,8})(?!\d)"),
]

EXPORT_TOP_OPTIONS = ["1", "5", "10", "20", "30"]
HTTP_TIMEOUT = (8, 22)

ACCOUNT_CATEGORY_UNUSED = "unused"
ACCOUNT_CATEGORY_PLUS = "plus"
ACCOUNT_CATEGORY_FREE = "free"
ACCOUNT_CATEGORY_BANNED = "banned"
ACCOUNT_CATEGORY_ORDER = [
    ACCOUNT_CATEGORY_UNUSED,
    ACCOUNT_CATEGORY_PLUS,
    ACCOUNT_CATEGORY_FREE,
    ACCOUNT_CATEGORY_BANNED,
]
ACCOUNT_CATEGORY_LABELS = {
    ACCOUNT_CATEGORY_UNUSED: "未使用",
    ACCOUNT_CATEGORY_PLUS: "Plus",
    ACCOUNT_CATEGORY_FREE: "Free",
    ACCOUNT_CATEGORY_BANNED: "已封禁",
}
