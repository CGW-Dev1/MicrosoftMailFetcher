from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AccountRecord:
    email: str
    password: str = ""
    client_id: str = ""
    refresh_token: str = ""
    imported_at: str = ""
    last_fetch_at: str = ""
    last_status: str = "未取件"
    used: bool = False

    @property
    def source(self) -> str:
        return "OAuth令牌" if self.client_id and self.refresh_token else "交互授权"


@dataclass
class ImportRecord:
    email: str
    password: str = ""
    client_id: str = ""
    refresh_token: str = ""
