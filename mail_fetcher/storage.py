from __future__ import annotations

import json
import threading
from dataclasses import asdict
from datetime import datetime, timezone

from .constants import (
    ACCOUNT_CATEGORY_LABELS,
    ACCOUNT_CATEGORY_PLUS,
    ACCOUNT_CATEGORY_UNUSED,
)
from .models import AccountRecord, ImportRecord
from .parsing import normalize_account_category
from .security import EncryptedTextFile, app_data_dir


class AccountStore:
    def __init__(self) -> None:
        self.legacy_path = app_data_dir() / "accounts.json"
        self.path = app_data_dir() / "accounts.sec"
        self.secure_file = EncryptedTextFile(self.path)
        self.lock = threading.RLock()
        self.accounts: list[AccountRecord] = []
        self.load()

    def load(self) -> None:
        try:
            text = ""
            if self.path.exists():
                text = self.secure_file.read_text()
            elif self.legacy_path.exists():
                text = self.legacy_path.read_text(encoding="utf-8")
            if not text:
                self.accounts = []
                return
            data = json.loads(text)
            self.accounts = [AccountRecord(**self._normalize(item)) for item in data.get("accounts", [])]
        except Exception:
            self.accounts = []
            return
        try:
            self.save()
        except Exception:
            pass

    def _normalize(self, item: dict) -> dict:
        category = normalize_account_category(item.get("category", ""))
        if category == ACCOUNT_CATEGORY_UNUSED and bool(item.get("used", False)):
            category = ACCOUNT_CATEGORY_PLUS
        return {
            "email": item.get("email", ""),
            "password": item.get("password", ""),
            "client_id": item.get("client_id", ""),
            "refresh_token": item.get("refresh_token", ""),
            "imported_at": item.get("imported_at") or datetime.now(timezone.utc).isoformat(),
            "last_fetch_at": item.get("last_fetch_at", ""),
            "last_status": item.get("last_status", "未取件"),
            "used": bool(item.get("used", False)),
            "category": category,
        }

    def save(self) -> None:
        with self.lock:
            data = {"accounts": [asdict(account) for account in self.accounts]}
            self.secure_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def upsert_records(self, records: list[ImportRecord]) -> tuple[int, int, int]:
        with self.lock:
            existing = {account.email.lower(): account for account in self.accounts}
            added = updated = skipped = 0
            now = datetime.now(timezone.utc).isoformat()
            for record in records:
                if existing.get(record.email.lower()):
                    skipped += 1
                    continue
                category = normalize_account_category(record.category)
                account = AccountRecord(
                    email=record.email,
                    password=record.password,
                    client_id=record.client_id,
                    refresh_token=record.refresh_token,
                    imported_at=now,
                    last_status="已导入" if record.refresh_token else "未取件",
                    used=category != ACCOUNT_CATEGORY_UNUSED,
                    category=category,
                )
                self.accounts.append(account)
                existing[account.email.lower()] = account
                added += 1
            self.save()
            return added, updated, skipped

    def get(self, email_address: str) -> AccountRecord | None:
        with self.lock:
            for account in self.accounts:
                if account.email.lower() == email_address.lower():
                    return account
        return None

    def mark(self, email_address: str, status: str, fetched: bool = False, save: bool = True) -> None:
        with self.lock:
            account = self.get(email_address)
            if not account:
                return
            account.last_status = status
            if fetched:
                account.last_fetch_at = datetime.now(timezone.utc).isoformat()
            if save:
                self.save()

    def update_refresh_token(self, email_address: str, refresh_token: str) -> None:
        with self.lock:
            account = self.get(email_address)
            if account and refresh_token and account.refresh_token != refresh_token:
                account.refresh_token = refresh_token
                self.save()

    def set_used(self, emails: set[str], used: bool) -> int:
        return self.set_category(emails, ACCOUNT_CATEGORY_PLUS if used else ACCOUNT_CATEGORY_UNUSED)

    def set_category(self, emails: set[str], category: str) -> int:
        normalized = normalize_account_category(category)
        with self.lock:
            changed = 0
            for account in self.accounts:
                if account.email in emails and account.category != normalized:
                    account.category = normalized
                    account.used = normalized != ACCOUNT_CATEGORY_UNUSED
                    changed += 1
            if changed:
                self.save()
            return changed

    @staticmethod
    def category_label(category: str) -> str:
        normalized = normalize_account_category(category)
        return ACCOUNT_CATEGORY_LABELS.get(normalized, ACCOUNT_CATEGORY_LABELS[ACCOUNT_CATEGORY_UNUSED])

    def remove(self, emails: set[str]) -> int:
        with self.lock:
            before = len(self.accounts)
            self.accounts = [account for account in self.accounts if account.email not in emails]
            self.save()
            return before - len(self.accounts)

    def clear(self) -> int:
        with self.lock:
            total = len(self.accounts)
            self.accounts = []
            self.save()
            return total


class ConfigStore:
    def __init__(self) -> None:
        self.path = app_data_dir() / "config.json"
        self.client_id = ""
        self.tenant = "consumers"
        self.top = 10
        self.protocol = "Graph"
        self.auto_fetch_after_import = True
        self.concise_mode = False
        self.theme = "light"
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.client_id = data.get("client_id", "")
            self.tenant = data.get("tenant", "consumers")
            self.top = max(1, min(int(data.get("top", 10)), 50))
            self.protocol = "Graph"
            self.auto_fetch_after_import = bool(data.get("auto_fetch_after_import", True))
            self.concise_mode = bool(data.get("concise_mode", False))
            self.theme = "dark" if data.get("theme") == "dark" else "light"
        except Exception:
            self.protocol = "Graph"

    def save(self) -> None:
        data = {
            "client_id": self.client_id,
            "tenant": self.tenant,
            "top": self.top,
            "protocol": self.protocol,
            "auto_fetch_after_import": self.auto_fetch_after_import,
            "concise_mode": self.concise_mode,
            "theme": self.theme,
        }
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
