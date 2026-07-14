from __future__ import annotations

from dataclasses import dataclass

from .constants import ACCOUNT_CATEGORY_LABELS, ACCOUNT_CATEGORY_UNUSED


@dataclass
class AccountRecord:
    email: str
    password: str = ""
    client_id: str = ""
    refresh_token: str = ""
    phone: str = ""
    tag: str = ""
    imported_at: str = ""
    last_fetch_at: str = ""
    last_status: str = "未取件"
    used: bool = False
    category: str = ACCOUNT_CATEGORY_UNUSED

    @property
    def source(self) -> str:
        return "OAuth令牌" if self.client_id and self.refresh_token else "交互授权"

    @property
    def category_label(self) -> str:
        return ACCOUNT_CATEGORY_LABELS.get(self.category, self.category or ACCOUNT_CATEGORY_LABELS[ACCOUNT_CATEGORY_UNUSED])


@dataclass
class ImportRecord:
    email: str
    password: str = ""
    client_id: str = ""
    refresh_token: str = ""
    category: str = ACCOUNT_CATEGORY_UNUSED
    tag: str = ""
    phone: str = ""
    phone_api_url: str = ""


@dataclass
class PhoneRecord:
    phone: str
    api_url: str
    emails: list[str]
    imported_at: str = ""
    last_fetch_at: str = ""
    last_status: str = "未取码"
    last_code: str = ""
    last_message: str = ""


@dataclass
class PhoneImportRecord:
    phone: str
    api_url: str
    emails: list[str]
