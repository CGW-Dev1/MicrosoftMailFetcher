from __future__ import annotations

import json
import threading
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .categories import CategoryStore
from .constants import ACCOUNT_CATEGORY_PLUS, ACCOUNT_CATEGORY_UNUSED
from .models import AccountRecord, ImportRecord, PhoneImportRecord, PhoneRecord
from .security import EncryptedTextFile, app_data_dir


class AccountStore:
    def __init__(self, category_store: CategoryStore | None = None) -> None:
        self.category_store = category_store or CategoryStore()
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
        category = self.category_store.resolve_or_add(item.get("category", ""))
        if category == ACCOUNT_CATEGORY_UNUSED and bool(item.get("used", False)):
            category = self.category_store.resolve(ACCOUNT_CATEGORY_PLUS) or ACCOUNT_CATEGORY_UNUSED
        return {
            "email": item.get("email", ""),
            "password": item.get("password", ""),
            "client_id": item.get("client_id", ""),
            "refresh_token": item.get("refresh_token", ""),
            "phone": item.get("phone", ""),
            "tag": item.get("tag", ""),
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
                current = existing.get(record.email.lower())
                if current:
                    changed = False
                    category = self.category_store.resolve_or_add(record.category)
                    updates = {
                        "password": record.password,
                        "client_id": record.client_id,
                        "refresh_token": record.refresh_token,
                        "tag": " ".join((record.tag or "").split())[:40],
                    }
                    for field_name, value in updates.items():
                        if value and getattr(current, field_name) != value:
                            setattr(current, field_name, value)
                            changed = True
                    if category != ACCOUNT_CATEGORY_UNUSED and current.category != category:
                        current.category = category
                        current.used = True
                        changed = True
                    if changed:
                        updated += 1
                    else:
                        skipped += 1
                    continue
                category = self.category_store.resolve_or_add(record.category)
                account = AccountRecord(
                    email=record.email,
                    password=record.password,
                    client_id=record.client_id,
                    refresh_token=record.refresh_token,
                    phone="",
                    tag=" ".join((record.tag or "").split())[:40],
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

    def set_tag(self, email_address: str, tag: str) -> bool:
        clean = " ".join((tag or "").split())[:40]
        with self.lock:
            account = self.get(email_address)
            if not account:
                return False
            if account.tag == clean:
                return True
            account.tag = clean
            self.save()
            return True

    def set_used(self, emails: set[str], used: bool) -> int:
        return self.set_category(emails, ACCOUNT_CATEGORY_PLUS if used else ACCOUNT_CATEGORY_UNUSED)

    def set_category(self, emails: set[str], category: str) -> int:
        normalized = self.category_store.resolve(category) or ACCOUNT_CATEGORY_UNUSED
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

    def category_label(self, category: str) -> str:
        return self.category_store.label(category)

    def reassign_category(self, source: str, target: str = ACCOUNT_CATEGORY_UNUSED) -> int:
        normalized_target = self.category_store.resolve(target) or ACCOUNT_CATEGORY_UNUSED
        with self.lock:
            changed = 0
            for account in self.accounts:
                if account.category != source:
                    continue
                account.category = normalized_target
                account.used = normalized_target != ACCOUNT_CATEGORY_UNUSED
                changed += 1
            if changed:
                self.save()
            return changed

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


class PhoneStore:
    max_emails_per_phone = 3

    def __init__(self, account_store: AccountStore) -> None:
        self.account_store = account_store
        self.path = app_data_dir() / "phones.sec"
        self.secure_file = EncryptedTextFile(self.path)
        self.lock = threading.RLock()
        self.phones: list[PhoneRecord] = []
        self.load()

    def load(self) -> None:
        try:
            text = self.secure_file.read_text() if self.path.exists() else ""
            if not text:
                self.phones = []
                return
            data = json.loads(text)
            self.phones = [PhoneRecord(**self._normalize(item)) for item in data.get("phones", [])]
            self._sync_account_phone_fields(save_accounts=False)
        except Exception:
            self.phones = []
            return

    def _normalize(self, item: dict) -> dict:
        emails = item.get("emails") or []
        if isinstance(emails, str):
            emails = [part.strip() for part in emails.replace("，", ",").replace(";", ",").split(",")]
        clean_emails: list[str] = []
        seen: set[str] = set()
        for email in emails:
            key = str(email).strip().lower()
            if not key or key in seen:
                continue
            account = self.account_store.get(str(email).strip())
            if account:
                clean_emails.append(account.email)
                seen.add(key)
            if len(clean_emails) >= self.max_emails_per_phone:
                break
        return {
            "phone": item.get("phone", ""),
            "api_url": item.get("api_url", ""),
            "emails": clean_emails,
            "imported_at": item.get("imported_at") or datetime.now(timezone.utc).isoformat(),
            "last_fetch_at": item.get("last_fetch_at", ""),
            "last_status": item.get("last_status", "未取码"),
            "last_code": item.get("last_code", ""),
            "last_message": item.get("last_message", ""),
        }

    def save(self) -> None:
        with self.lock:
            data = {"phones": [asdict(phone) for phone in self.phones]}
            self.secure_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def upsert_records(self, records: list[PhoneImportRecord]) -> tuple[int, int, int]:
        with self.lock:
            existing = {phone.phone: phone for phone in self.phones}
            added = updated = skipped = 0
            now = datetime.now(timezone.utc).isoformat()
            for record in records:
                phone = existing.get(record.phone)
                if phone:
                    if phone.api_url != record.api_url:
                        phone.api_url = record.api_url
                        updated += 1
                    else:
                        skipped += 1
                    if record.emails:
                        self.bind_emails(record.phone, set(record.emails), save=False)
                    continue
                phone = PhoneRecord(
                    phone=record.phone,
                    api_url=record.api_url,
                    emails=[],
                    imported_at=now,
                    last_status="已导入",
                )
                self.phones.append(phone)
                existing[phone.phone] = phone
                added += 1
                if record.emails:
                    self.bind_emails(record.phone, set(record.emails), save=False)
            self._sort()
            self.save()
            self.account_store.save()
            return added, updated, skipped

    def _sort(self) -> None:
        self.phones.sort(key=lambda phone: phone.phone.lower())

    def get(self, phone_number: str) -> PhoneRecord | None:
        with self.lock:
            for phone in self.phones:
                if phone.phone == phone_number:
                    return phone
        return None

    def phones_for_emails(self, emails: set[str]) -> list[PhoneRecord]:
        email_keys = {email.lower() for email in emails}
        with self.lock:
            matched = [
                phone
                for phone in self.phones
                if any(email.lower() in email_keys for email in phone.emails)
            ]
        return sorted(matched, key=lambda phone: phone.phone.lower())

    def bind_emails(self, phone_number: str, emails: set[str], save: bool = True) -> tuple[int, list[str]]:
        with self.lock:
            phone = self.get(phone_number)
            if not phone:
                return 0, list(emails)
            bound = 0
            rejected: list[str] = []
            for email in sorted(emails, key=str.lower):
                account = self.account_store.get(email)
                if not account:
                    rejected.append(email)
                    continue
                if account.email in phone.emails:
                    continue
                if len(phone.emails) >= self.max_emails_per_phone:
                    rejected.append(account.email)
                    continue
                self._remove_email_from_other_phones(account.email, except_phone=phone.phone)
                phone.emails.append(account.email)
                account.phone = phone.phone
                bound += 1
            phone.emails = sorted(phone.emails, key=str.lower)[: self.max_emails_per_phone]
            if save and bound:
                self.save()
                self.account_store.save()
            return bound, rejected

    def unbind_emails(self, emails: set[str], save: bool = True) -> int:
        with self.lock:
            removed = 0
            email_keys = {email.lower() for email in emails}
            for phone in self.phones:
                before = len(phone.emails)
                phone.emails = [email for email in phone.emails if email.lower() not in email_keys]
                removed += before - len(phone.emails)
            for email in emails:
                account = self.account_store.get(email)
                if account:
                    account.phone = ""
            if save and removed:
                self.save()
                self.account_store.save()
            return removed

    def remove_emails(self, emails: set[str]) -> None:
        self.unbind_emails(emails)

    def remove(self, phone_number: str) -> bool:
        with self.lock:
            phone = self.get(phone_number)
            if not phone:
                return False
            for email in phone.emails:
                account = self.account_store.get(email)
                if account:
                    account.phone = ""
            self.phones = [item for item in self.phones if item.phone != phone_number]
            self.save()
            self.account_store.save()
            return True

    def clear_bindings(self) -> None:
        with self.lock:
            for phone in self.phones:
                phone.emails = []
            for account in self.account_store.accounts:
                account.phone = ""
            self.save()
            self.account_store.save()

    def mark_fetch_result(self, phone_number: str, status: str, code: str = "", message: str = "", save: bool = True) -> None:
        with self.lock:
            phone = self.get(phone_number)
            if not phone:
                return
            phone.last_status = status
            phone.last_code = code
            phone.last_message = message[:500]
            phone.last_fetch_at = datetime.now(timezone.utc).isoformat()
            if save:
                self.save()

    def _remove_email_from_other_phones(self, email: str, except_phone: str = "") -> None:
        key = email.lower()
        for phone in self.phones:
            if phone.phone == except_phone:
                continue
            phone.emails = [item for item in phone.emails if item.lower() != key]

    def _sync_account_phone_fields(self, save_accounts: bool = True) -> None:
        for account in self.account_store.accounts:
            account.phone = ""
        for phone in self.phones:
            for email in phone.emails:
                account = self.account_store.get(email)
                if account:
                    account.phone = phone.phone
        if save_accounts:
            self.account_store.save()


class StandalonePhoneCodeStore:
    def __init__(self) -> None:
        self.path = app_data_dir() / "standalone_phones.sec"
        self.secure_file = EncryptedTextFile(self.path)
        self.lock = threading.RLock()
        self.phones: list[PhoneRecord] = []
        self.load()

    def load(self) -> None:
        try:
            text = self.secure_file.read_text() if self.path.exists() else ""
            if not text:
                self.phones = []
                return
            data = json.loads(text)
            self.phones = [PhoneRecord(**self._normalize(item)) for item in data.get("phones", [])]
            self._sort()
        except Exception:
            self.phones = []

    def _normalize(self, item: dict) -> dict:
        return {
            "phone": item.get("phone", ""),
            "api_url": item.get("api_url", ""),
            "emails": [],
            "imported_at": item.get("imported_at") or datetime.now(timezone.utc).isoformat(),
            "last_fetch_at": item.get("last_fetch_at", ""),
            "last_status": item.get("last_status", "已导入"),
            "last_code": item.get("last_code", ""),
            "last_message": item.get("last_message", ""),
        }

    def save(self) -> None:
        with self.lock:
            data = {"phones": [asdict(phone) for phone in self.phones]}
            self.secure_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _sort(self) -> None:
        self.phones.sort(key=lambda phone: phone.phone.lower())

    def as_dict(self) -> dict[str, PhoneRecord]:
        with self.lock:
            return {phone.phone: phone for phone in self.phones}

    def upsert_records(self, records: list[PhoneImportRecord]) -> tuple[int, int, int]:
        with self.lock:
            existing = {phone.phone: phone for phone in self.phones}
            added = updated = skipped = 0
            now = datetime.now(timezone.utc).isoformat()
            for record in records:
                phone = existing.get(record.phone)
                if phone:
                    if phone.api_url != record.api_url:
                        phone.api_url = record.api_url
                        phone.last_status = "已更新"
                        updated += 1
                    else:
                        skipped += 1
                    continue
                phone = PhoneRecord(
                    phone=record.phone,
                    api_url=record.api_url,
                    emails=[],
                    imported_at=now,
                    last_status="已导入",
                )
                self.phones.append(phone)
                existing[phone.phone] = phone
                added += 1
            self._sort()
            self.save()
            return added, updated, skipped

    def mark_fetch_result(self, phone_number: str, status: str, code: str = "", message: str = "", save: bool = True) -> None:
        with self.lock:
            for phone in self.phones:
                if phone.phone != phone_number:
                    continue
                phone.last_status = status
                phone.last_code = code
                phone.last_message = message[:500]
                phone.last_fetch_at = datetime.now(timezone.utc).isoformat()
                if save:
                    self.save()
                return

    def clear(self) -> None:
        with self.lock:
            self.phones = []
            self.save()


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (app_data_dir() / "config.json")
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
            self.protocol = "IMAP" if data.get("protocol") == "IMAP" else "Graph"
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
