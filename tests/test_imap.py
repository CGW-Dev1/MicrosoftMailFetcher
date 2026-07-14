from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mail_fetcher.models import AccountRecord
from mail_fetcher.services import ImapMailClient
from mail_fetcher.storage import ConfigStore


RAW_MESSAGE = (
    b"From: Service <notice@example.com>\r\n"
    b"To: person@example.com\r\n"
    b"Subject: Verification code 482915\r\n"
    b"Date: Tue, 14 Jul 2026 10:00:00 +0800\r\n"
    b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
    b"Your code is 482915."
)


class FakeImap:
    def __init__(self) -> None:
        self.uid_calls: list[tuple] = []

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def authenticate(self, mechanism, callback):
        self.auth = (mechanism, callback(b""))
        return "OK", [b"authenticated"]

    def select(self, mailbox, readonly=False):
        self.selected = (mailbox, readonly)
        return "OK", [b"1"]

    def uid(self, command, *args):
        self.uid_calls.append((command, *args))
        if command == "search":
            return "OK", [b"103"]
        return "OK", [(b"103 (BODY[] {1})", RAW_MESSAGE)]


class ImapTests(unittest.TestCase):
    def test_imap_uses_uid_and_peek_without_marking_mail_read(self) -> None:
        fake = FakeImap()
        client = ImapMailClient.__new__(ImapMailClient)
        account = AccountRecord(email="person@example.com")
        with mock.patch("mail_fetcher.services.imaplib.IMAP4_SSL", return_value=fake):
            rows = client._latest_messages_once(account, "access-token", 5)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["protocol"], "IMAP")
        self.assertIn(("fetch", b"103", "(BODY.PEEK[])"), fake.uid_calls)
        self.assertEqual(fake.selected, ("INBOX", True))

    def test_saved_imap_protocol_is_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            store = ConfigStore(path)
            store.protocol = "IMAP"
            store.save()
            self.assertEqual(ConfigStore(path).protocol, "IMAP")


if __name__ == "__main__":
    unittest.main()
