from __future__ import annotations

import email
from datetime import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime

from .constants import CODE_PATTERNS, EMAIL_RE
from .models import ImportRecord


def parse_import_text(text: str) -> tuple[list[ImportRecord], int]:
    records: list[ImportRecord] = []
    invalid = 0
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip().strip("\ufeff").rstrip(",;")
        if not line:
            continue
        parts = [part.strip() for part in line.split("----")]
        if not parts or not EMAIL_RE.match(parts[0]):
            invalid += 1
            continue
        key = parts[0].lower()
        if key in seen:
            continue
        seen.add(key)
        records.append(
            ImportRecord(
                email=parts[0],
                password=parts[1] if len(parts) > 1 else "",
                client_id=parts[2] if len(parts) > 2 else "",
                refresh_token=parts[3] if len(parts) > 3 else "",
            )
        )
    return records, invalid


def decode_mime_header(value: str | None) -> str:
    if not value:
        return ""
    parts: list[str] = []
    for part, enc in decode_header(value):
        if isinstance(part, bytes):
            parts.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            parts.append(part)
    return "".join(parts).strip()


def extract_preview(message: email.message.Message) -> str:
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_disposition() == "attachment":
                continue
            if part.get_content_type() == "text/plain":
                raw = part.get_payload(decode=True) or b""
                return raw.decode(part.get_content_charset() or "utf-8", errors="replace").strip()[:800]
    if message.get_content_type() == "text/plain":
        raw = message.get_payload(decode=True) or b""
        return raw.decode(message.get_content_charset() or "utf-8", errors="replace").strip()[:800]
    return ""


def parse_imap_message(raw: bytes, account: str) -> dict:
    message = email.message_from_bytes(raw)
    return {
        "account": account,
        "protocol": "IMAP",
        "time": fmt_dt(message.get("Date") or ""),
        "sender": decode_mime_header(message.get("From")),
        "subject": decode_mime_header(message.get("Subject")),
        "read": "",
        "preview": extract_preview(message),
        "webLink": "",
    }


def fmt_dt(value: str) -> str:
    if not value:
        return ""
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value).astimezone().strftime("%m/%d %H:%M")
    except ValueError:
        try:
            return parsedate_to_datetime(value).astimezone().strftime("%m/%d %H:%M")
        except Exception:
            return value


def extract_verification_code(*parts: str) -> str:
    text = " ".join(part or "" for part in parts)
    for pattern in CODE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return ""


def compact_text(value: str, limit: int) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def short_sender(sender: str) -> str:
    if "<" in sender:
        return sender.split("<", 1)[0].strip().strip('"') or sender
    if "@" in sender:
        return sender.split("@", 1)[0]
    return sender or "(未知发件人)"
