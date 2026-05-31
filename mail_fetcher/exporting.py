from __future__ import annotations

from pathlib import Path


def ensure_export_suffix(path: Path, suffix: str) -> Path:
    if path.suffix:
        return path
    return path.with_suffix(suffix)


def join_export_parts(parts: list[object]) -> str:
    return "----".join("" if part is None else str(part) for part in parts)
