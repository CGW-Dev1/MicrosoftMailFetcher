from __future__ import annotations

import email
import re
from datetime import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

from .constants import (
    ACCOUNT_CATEGORY_BANNED,
    ACCOUNT_CATEGORY_FREE,
    ACCOUNT_CATEGORY_PLUS,
    ACCOUNT_CATEGORY_UNUSED,
    CODE_PATTERNS,
    EMAIL_RE,
)
from .models import ImportRecord, PhoneImportRecord

PHONE_RE = re.compile(r"^\+\d{6,18}$")

_HTML_BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "div",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
}
_HTML_IGNORED_TAGS = {"head", "script", "style", "template"}


class _HtmlTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self.ignored_tags: list[str] = []

    def handle_starttag(self, tag: str, _attrs) -> None:
        tag = tag.lower()
        if tag in _HTML_IGNORED_TAGS:
            self.ignored_tags.append(tag)
            return
        if not self.ignored_tags and tag in _HTML_BLOCK_TAGS:
            self.chunks.append("\n")

    def handle_startendtag(self, tag: str, _attrs) -> None:
        if not self.ignored_tags and tag.lower() in _HTML_BLOCK_TAGS:
            self.chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.ignored_tags:
            if tag == self.ignored_tags[-1]:
                self.ignored_tags.pop()
            return
        if tag in _HTML_BLOCK_TAGS:
            self.chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.ignored_tags:
            self.chunks.append(data)

    def text(self) -> str:
        return " ".join("".join(self.chunks).split())


def normalize_account_category(value: str | None) -> str:
    raw = (value or "").strip()
    text = raw.lower()
    if text in {"plus", "p", "已plus", "标记plus"}:
        return ACCOUNT_CATEGORY_PLUS
    if text in {"free", "f", "已free", "标记free"}:
        return ACCOUNT_CATEGORY_FREE
    if text in {"banned", "ban", "blocked", "封禁", "已封禁", "被封禁", "标记封禁"}:
        return ACCOUNT_CATEGORY_BANNED
    if text in {"unused", "未使用", "未标记", "none", ""}:
        return ACCOUNT_CATEGORY_UNUSED
    # Preserve unknown labels so AccountStore can resolve them against (or add
    # them to) the user's custom category menu during import.
    return raw[:24] or ACCOUNT_CATEGORY_UNUSED


def is_ignored_import_line(line: str) -> bool:
    text = line.strip()
    if not text:
        return True
    if text.startswith("#"):
        return True
    stripped = text.strip("=-_ *\t")
    return not stripped


def parse_import_text(text: str) -> tuple[list[ImportRecord], int]:
    records: list[ImportRecord] = []
    invalid = 0
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip().strip("\ufeff").rstrip(",;")
        if is_ignored_import_line(line):
            continue
        parts = [part.strip() for part in line.split("----")]
        if not parts or not EMAIL_RE.match(parts[0]):
            invalid += 1
            continue
        key = parts[0].lower()
        if key in seen:
            continue
        seen.add(key)
        category_index = 4
        phone = ""
        phone_api_url = ""
        tag = ""
        if len(parts) > 4 and PHONE_RE.match(parts[4]):
            category = ACCOUNT_CATEGORY_UNUSED
            phone = parts[4]
            phone_api_url = parts[5] if len(parts) > 5 and parts[5].startswith(("http://", "https://")) else ""
        else:
            category = normalize_account_category(parts[category_index] if len(parts) > category_index else "")
            cursor = 5
            if len(parts) > cursor and parts[cursor] and not PHONE_RE.match(parts[cursor]) and not parts[cursor].startswith(("http://", "https://")):
                tag = parts[cursor][:40]
                cursor += 1
            elif len(parts) > cursor and not parts[cursor]:
                cursor += 1
            if len(parts) > cursor and PHONE_RE.match(parts[cursor]):
                phone = parts[cursor]
                cursor += 1
            if len(parts) > cursor and parts[cursor].startswith(("http://", "https://")):
                phone_api_url = parts[cursor]
        records.append(
            ImportRecord(
                email=parts[0],
                password=parts[1] if len(parts) > 1 else "",
                client_id=parts[2] if len(parts) > 2 else "",
                refresh_token=parts[3] if len(parts) > 3 else "",
                category=category,
                tag=tag,
                phone=phone,
                phone_api_url=phone_api_url,
            )
        )
    return records, invalid


def parse_phone_import_text(text: str) -> tuple[list[PhoneImportRecord], int]:
    records: list[PhoneImportRecord] = []
    invalid = 0
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip().strip("\ufeff").rstrip(",;")
        if is_ignored_import_line(line):
            continue
        parts = [part.strip() for part in line.split("----")]
        if len(parts) < 2 or not PHONE_RE.match(parts[0]) or not parts[1].startswith(("http://", "https://")):
            invalid += 1
            continue
        key = parts[0]
        if key in seen:
            continue
        seen.add(key)
        emails: list[str] = []
        if len(parts) > 2:
            for email_text in re.split(r"[,;，\s]+", parts[2]):
                email_text = email_text.strip()
                if EMAIL_RE.match(email_text) and email_text.lower() not in {item.lower() for item in emails}:
                    emails.append(email_text)
                if len(emails) >= 3:
                    break
        records.append(PhoneImportRecord(phone=parts[0], api_url=parts[1], emails=emails))
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


def _decode_text_part(part: email.message.Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        undecoded = part.get_payload()
        return undecoded if isinstance(undecoded, str) else ""
    if isinstance(payload, str):
        return payload

    charset = part.get_content_charset()
    if charset:
        try:
            return payload.decode(charset, errors="replace")
        except LookupError:
            pass
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        return payload.decode("windows-1252", errors="replace")


def _html_to_text(value: str) -> str:
    parser = _HtmlTextExtractor()
    try:
        parser.feed(value)
        parser.close()
    except Exception:
        # Keep malformed marketing emails readable instead of dropping the body.
        return " ".join(re.sub(r"<[^>]+>", " ", value).split())
    return parser.text()


def extract_preview(message: email.message.Message) -> str:
    plain_parts: list[email.message.Message] = []
    html_parts: list[email.message.Message] = []
    parts = message.walk() if message.is_multipart() else [message]
    for part in parts:
        if part.is_multipart():
            continue
        if part.get_content_disposition() == "attachment" or part.get_filename():
            continue
        content_type = part.get_content_type().lower()
        if content_type == "text/plain":
            plain_parts.append(part)
        elif content_type == "text/html":
            html_parts.append(part)

    for part in plain_parts:
        text = " ".join(_decode_text_part(part).split())
        if text:
            return text[:800]
    for part in html_parts:
        text = _html_to_text(_decode_text_part(part))
        if text:
            return text[:800]
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
    if "no verification code" in text.lower():
        return ""
    for pattern in CODE_PATTERNS:
        match = pattern.search(text)
        if match:
            candidate = match.group(1).strip()
            if is_probable_verification_code(candidate):
                return candidate
    return ""


def is_probable_verification_code(value: str) -> bool:
    text = (value or "").strip()
    if not re.fullmatch(r"[A-Z0-9]{4,10}", text, flags=re.IGNORECASE):
        return False
    if text.lower() in {"code", "data", "none", "null", "true", "false"}:
        return False
    return any(char.isdigit() for char in text)


def clean_verification_code(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if is_probable_verification_code(text):
        return text
    return extract_verification_code(text)


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


def phone_without_country_code(phone_number: str) -> str:
    # phonenumbers ships a sizeable metadata table.  Phone normalization is a
    # secondary workflow, so defer that import until the feature is used.
    import phonenumbers

    text = (phone_number or "").strip()
    if not text:
        return ""
    try:
        parsed = phonenumbers.parse(text, None)
        national = str(parsed.national_number)
        if getattr(parsed, "italian_leading_zero", False):
            zeros = getattr(parsed, "number_of_leading_zeros", None) or 1
            national = ("0" * zeros) + national
        if national:
            return national
    except Exception:
        pass
    digits = re.sub(r"\D+", "", text)
    if text.startswith("+") and len(digits) > 3:
        for code in sorted(phonenumbers.COUNTRY_CODE_TO_REGION_CODE, key=lambda item: len(str(item)), reverse=True):
            prefix = str(code)
            if digits.startswith(prefix):
                return digits[len(prefix):] or digits
    return digits
