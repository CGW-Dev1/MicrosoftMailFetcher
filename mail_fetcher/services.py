from __future__ import annotations

import imaplib
import re
import threading
from urllib.parse import urlencode

import msal
import requests

from .constants import (
    AUTHORITY_BASE,
    GRAPH_BASE,
    GRAPH_INTERACTIVE_SCOPES,
    GRAPH_REFRESH_SCOPE_OPTIONS,
    HTTP_TIMEOUT,
    IMAP_HOST,
    IMAP_REFRESH_SCOPE_OPTIONS,
)
from .models import AccountRecord, PhoneRecord
from .parsing import clean_verification_code, compact_text, extract_verification_code, fmt_dt, parse_imap_message
from .security import EncryptedTextFile, app_data_dir
from .storage import AccountStore, ConfigStore

_http_local = threading.local()


def http_session() -> requests.Session:
    session = getattr(_http_local, "session", None)
    if session is None:
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=16, pool_maxsize=16, max_retries=0)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        _http_local.session = session
    return session


class DirectOAuthClient:
    def __init__(self, config: ConfigStore, account_store: AccountStore) -> None:
        self.config = config
        self.account_store = account_store

    @property
    def token_url(self) -> str:
        tenant = self.config.tenant or "consumers"
        return f"{AUTHORITY_BASE}/{tenant}/oauth2/v2.0/token"

    def refresh_access_token(self, account: AccountRecord, scope_options: list[str | None]) -> str:
        if not account.client_id or not account.refresh_token:
            raise RuntimeError("缺少 client_id 或 refresh_token")
        errors: list[str] = []
        for scope in scope_options:
            data = {
                "client_id": account.client_id,
                "grant_type": "refresh_token",
                "refresh_token": account.refresh_token,
            }
            if scope:
                data["scope"] = scope
            try:
                response = http_session().post(self.token_url, data=data, timeout=HTTP_TIMEOUT)
                payload = response.json() if response.content else {}
            except Exception as exc:
                errors.append(str(exc))
                continue
            if response.status_code < 400 and payload.get("access_token"):
                if payload.get("refresh_token"):
                    self.account_store.update_refresh_token(account.email, payload["refresh_token"])
                return payload["access_token"]
            errors.append(payload.get("error_description") or payload.get("error") or response.text[:300])
        raise RuntimeError("刷新 Graph 访问令牌失败：" + " | ".join(errors[-2:]))


class GraphMailClient:
    def __init__(self, config: ConfigStore, account_store: AccountStore) -> None:
        self.config = config
        self.direct = DirectOAuthClient(config, account_store)
        self.cache_file: EncryptedTextFile | None = None
        self.cache: msal.SerializableTokenCache | None = None
        self.app: msal.PublicClientApplication | None = None

    def _ensure_msal_app(self) -> msal.PublicClientApplication | None:
        if self.cache is None:
            self.cache_file = EncryptedTextFile(app_data_dir() / "msal_cache.dat")
            self.cache = msal.SerializableTokenCache()
            cached = self.cache_file.read_text()
            if cached:
                self.cache.deserialize(cached)
        if self.app is None and self.config.client_id:
            self.app = msal.PublicClientApplication(
                client_id=self.config.client_id,
                authority=f"{AUTHORITY_BASE}/{self.config.tenant}",
                token_cache=self.cache,
            )
        return self.app

    def save_cache(self) -> None:
        if self.cache and self.cache_file and self.cache.has_state_changed:
            self.cache_file.write_text(self.cache.serialize())

    def authorize(self, email_address: str) -> dict:
        app = self._ensure_msal_app()
        if not app:
            raise RuntimeError("交互授权需要先填写全局 Client ID")
        result = app.acquire_token_interactive(scopes=GRAPH_INTERACTIVE_SCOPES, login_hint=email_address)
        self.save_cache()
        return result

    def access_token(self, account: AccountRecord) -> str:
        if account.client_id and account.refresh_token:
            return self.direct.refresh_access_token(account, GRAPH_REFRESH_SCOPE_OPTIONS)
        app = self._ensure_msal_app()
        if not app:
            raise RuntimeError("没有 refresh_token，也没有全局 Client ID 授权缓存")
        accounts = app.get_accounts(username=account.email)
        if not accounts:
            raise RuntimeError("未找到授权缓存")
        result = app.acquire_token_silent(scopes=GRAPH_INTERACTIVE_SCOPES, account=accounts[0])
        self.save_cache()
        if not result or "access_token" not in result:
            raise RuntimeError("授权缓存失效")
        return result["access_token"]

    def latest_messages(self, account: AccountRecord, top: int) -> list[dict]:
        token = self.access_token(account)
        query = urlencode(
            {
                "$top": max(1, min(top, 50)),
                "$orderby": "receivedDateTime desc",
                "$select": "receivedDateTime,from,sender,subject,bodyPreview,webLink,isRead",
            }
        )
        url = f"{GRAPH_BASE}/me/mailFolders/inbox/messages?{query}"
        response = http_session().get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Prefer": 'outlook.body-content-type="text"',
            },
            timeout=HTTP_TIMEOUT,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Graph 请求失败 HTTP {response.status_code}: {response.text[:500]}")
        return response.json().get("value", [])


class ImapMailClient:
    def __init__(self, config: ConfigStore, account_store: AccountStore) -> None:
        self.direct = DirectOAuthClient(config, account_store)

    def latest_messages(self, account: AccountRecord, top: int) -> list[dict]:
        token = self.direct.refresh_access_token(account, IMAP_REFRESH_SCOPE_OPTIONS)
        auth = f"user={account.email}\x01auth=Bearer {token}\x01\x01"
        with imaplib.IMAP4_SSL(IMAP_HOST, 993, timeout=30) as client:
            client.authenticate("XOAUTH2", lambda _challenge: auth.encode("utf-8"))
            client.select("INBOX", readonly=True)
            status, data = client.search(None, "ALL")
            if status != "OK" or not data or not data[0]:
                return []
            ids = data[0].split()[-max(1, min(top, 50)) :]
            rows: list[dict] = []
            for msg_id in reversed(ids):
                status, fetched = client.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue
                raw = next((part[1] for part in fetched if isinstance(part, tuple)), b"")
                if raw:
                    rows.append(parse_imap_message(raw, account.email))
            return rows


class SmsService:
    def fetch_phone_row(self, phone: PhoneRecord, concise_mode: bool = True) -> dict:
        response = http_session().get(phone.api_url, timeout=HTTP_TIMEOUT)
        text = response.text or ""
        if response.status_code >= 400:
            raise RuntimeError(f"短信 API 请求失败 HTTP {response.status_code}: {text[:300]}")
        payload = self._json_payload(response)
        searchable = self._searchable_text(payload, text, phone.phone)
        api_code = self._api_code(payload)
        if self._has_sms8_code_field(payload):
            code = api_code
        else:
            code = api_code or clean_verification_code(extract_verification_code(searchable))
        api_message = self._api_message(payload)
        subject = code or "未识别"
        preview_source = api_message or searchable
        preview = "" if concise_mode and code else compact_text(preview_source, 900)
        return {
            "account": ", ".join(phone.emails) or phone.phone,
            "protocol": "SMS",
            "time": fmt_dt(response.headers.get("Date", "")),
            "sender": phone.phone,
            "subject": subject,
            "read": "",
            "preview": preview,
            "webLink": "",
            "code": code,
            "concise": concise_mode,
            "phone": phone.phone,
        }

    def _json_payload(self, response: requests.Response) -> object | None:
        try:
            return response.json()
        except Exception:
            return None

    def _api_code(self, payload: object | None) -> str:
        if not isinstance(payload, dict):
            return ""
        data = payload.get("data")
        if isinstance(data, dict):
            code = clean_verification_code(str(data.get("code") or "").strip())
            if code:
                return code
        return clean_verification_code(str(payload.get("code_value") or payload.get("verify_code") or "").strip())

    def _has_sms8_code_field(self, payload: object | None) -> bool:
        if not isinstance(payload, dict):
            return False
        data = payload.get("data")
        return isinstance(data, dict) and "code" in data

    def _api_message(self, payload: object | None) -> str:
        if not isinstance(payload, dict):
            return ""
        data = payload.get("data")
        parts: list[str] = []
        if payload.get("msg"):
            parts.append(str(payload.get("msg")))
        if isinstance(data, dict):
            for key in ("code_time", "expired_date", "message", "msg", "content"):
                if data.get(key):
                    parts.append(str(data.get(key)))
        return " ".join(parts)

    def _searchable_text(self, payload: object | None, fallback: str, phone_number: str = "") -> str:
        if payload is None:
            return self._prefer_phone_text([fallback], phone_number)
        strings: list[str] = []
        chunks: list[str] = []

        def walk(value: object) -> None:
            if isinstance(value, dict):
                chunk_parts: list[str] = []
                for key, item in value.items():
                    chunk_parts.append(str(key))
                    if not isinstance(item, (dict, list)) and item is not None:
                        chunk_parts.append(str(item))
                    walk(item)
                if chunk_parts:
                    chunks.append(" ".join(chunk_parts))
            elif isinstance(value, list):
                for item in value:
                    walk(item)
            elif value is not None:
                strings.append(str(value))

        walk(payload)
        candidates = chunks or strings or [fallback]
        return self._prefer_phone_text(candidates, phone_number)

    def _prefer_phone_text(self, chunks: list[str], phone_number: str) -> str:
        target = re.sub(r"\D+", "", phone_number)
        suffixes = [target[-length:] for length in (11, 10, 8, 6) if len(target) >= length]
        if target:
            matched = [
                chunk
                for chunk in chunks
                if any(suffix and suffix in re.sub(r"\D+", "", chunk) for suffix in suffixes)
            ]
            if matched:
                return " ".join(matched)
        return " ".join(chunks)


class MailService:
    def __init__(self, config: ConfigStore, account_store: AccountStore) -> None:
        self.config = config
        self.account_store = account_store
        self.graph: GraphMailClient | None = None
        self.imap = ImapMailClient(config, account_store)
        self.sms = SmsService()

    def ensure_graph(self) -> GraphMailClient:
        if self.graph is None:
            self.graph = GraphMailClient(self.config, self.account_store)
        return self.graph

    def authorize(self, email_address: str) -> dict:
        return self.ensure_graph().authorize(email_address)

    def fetch_account_rows(self, account: AccountRecord, protocol: str, top: int, concise_mode: bool = False) -> list[dict]:
        if protocol == "IMAP":
            rows = self.imap.latest_messages(account, top)
            return [self.concise_row(row) for row in rows] if concise_mode else rows
        messages = self.ensure_graph().latest_messages(account, top)
        rows = [self.graph_row(account.email, message) for message in messages]
        return [self.concise_row(row) for row in rows] if concise_mode else rows

    def fetch_phone_row(self, phone: PhoneRecord, concise_mode: bool = True) -> dict:
        return self.sms.fetch_phone_row(phone, concise_mode)

    @staticmethod
    def concise_row(row: dict) -> dict:
        code = clean_verification_code(extract_verification_code(row.get("subject", ""), row.get("preview", "")))
        return {
            "account": row.get("account", ""),
            "protocol": row.get("protocol", ""),
            "time": row.get("time", ""),
            "sender": row.get("sender", ""),
            "subject": code if code else "未识别到验证码",
            "read": row.get("read", ""),
            "preview": "",
            "webLink": row.get("webLink", ""),
            "code": code,
            "concise": True,
        }

    @staticmethod
    def graph_row(account: str, message: dict) -> dict:
        sender_obj = message.get("from") or message.get("sender") or {}
        email_obj = sender_obj.get("emailAddress") or {}
        return {
            "account": account,
            "protocol": "GRAPH",
            "time": fmt_dt(message.get("receivedDateTime", "")),
            "sender": email_obj.get("address") or email_obj.get("name") or "",
            "subject": message.get("subject") or "",
            "read": "是" if message.get("isRead") else "否",
            "preview": message.get("bodyPreview") or "",
            "webLink": message.get("webLink") or "",
        }
