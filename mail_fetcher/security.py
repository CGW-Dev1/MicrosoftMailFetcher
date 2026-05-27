from __future__ import annotations

import base64
import ctypes
import ctypes.wintypes
from pathlib import Path

from .constants import APP_NAME


def app_data_dir() -> Path:
    path = Path.home() / "AppData" / "Roaming" / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


class WindowsDpapi:
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", ctypes.wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_byte)),
        ]

    @classmethod
    def _blob_from_bytes(cls, data: bytes) -> "WindowsDpapi.DATA_BLOB":
        buf = ctypes.create_string_buffer(data)
        blob = cls.DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)))
        blob._buffer = buf
        return blob

    @classmethod
    def protect(cls, data: bytes) -> bytes:
        if not data:
            return b""
        in_blob = cls._blob_from_bytes(data)
        out_blob = cls.DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(in_blob), None, None, None, None, 0x1, ctypes.byref(out_blob)
        )
        if not ok:
            raise ctypes.WinError()
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)

    @classmethod
    def unprotect(cls, data: bytes) -> bytes:
        if not data:
            return b""
        in_blob = cls._blob_from_bytes(data)
        out_blob = cls.DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(in_blob), None, None, None, None, 0x1, ctypes.byref(out_blob)
        )
        if not ok:
            raise ctypes.WinError()
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)


class EncryptedTextFile:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read_text(self) -> str:
        if not self.path.exists():
            return ""
        raw = self.path.read_bytes()
        if not raw:
            return ""
        return WindowsDpapi.unprotect(base64.b64decode(raw)).decode("utf-8")

    def write_text(self, text: str) -> None:
        encrypted = WindowsDpapi.protect(text.encode("utf-8"))
        self.path.write_bytes(base64.b64encode(encrypted))
