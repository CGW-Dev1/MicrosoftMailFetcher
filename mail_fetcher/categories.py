from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from .constants import (
    ACCOUNT_CATEGORY_BANNED,
    ACCOUNT_CATEGORY_FREE,
    ACCOUNT_CATEGORY_PLUS,
    ACCOUNT_CATEGORY_UNUSED,
    DEFAULT_ACCOUNT_CATEGORIES,
)
from .security import app_data_dir


@dataclass(frozen=True)
class AccountCategory:
    key: str
    label: str
    protected: bool = False


class CategoryStore:
    """Persistent, ordered account categories.

    `unused` is the only protected category because it is the safe destination
    for imports and for accounts whose category is deleted.  All other default
    and custom categories may be renamed or removed.
    """

    _legacy_aliases = {
        "unused": ACCOUNT_CATEGORY_UNUSED,
        "未使用": ACCOUNT_CATEGORY_UNUSED,
        "未标记": ACCOUNT_CATEGORY_UNUSED,
        "none": ACCOUNT_CATEGORY_UNUSED,
        "plus": ACCOUNT_CATEGORY_PLUS,
        "p": ACCOUNT_CATEGORY_PLUS,
        "已plus": ACCOUNT_CATEGORY_PLUS,
        "标记plus": ACCOUNT_CATEGORY_PLUS,
        "free": ACCOUNT_CATEGORY_FREE,
        "f": ACCOUNT_CATEGORY_FREE,
        "已free": ACCOUNT_CATEGORY_FREE,
        "标记free": ACCOUNT_CATEGORY_FREE,
        "banned": ACCOUNT_CATEGORY_BANNED,
        "ban": ACCOUNT_CATEGORY_BANNED,
        "blocked": ACCOUNT_CATEGORY_BANNED,
        "封禁": ACCOUNT_CATEGORY_BANNED,
        "已封禁": ACCOUNT_CATEGORY_BANNED,
        "被封禁": ACCOUNT_CATEGORY_BANNED,
        "标记封禁": ACCOUNT_CATEGORY_BANNED,
    }

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (app_data_dir() / "categories.json")
        self.lock = threading.RLock()
        self.categories: list[AccountCategory] = []
        self.load()

    def load(self) -> None:
        with self.lock:
            if not self.path.exists():
                self.categories = self._default_categories()
                self.save()
                return
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                loaded: list[AccountCategory] = []
                seen_keys: set[str] = set()
                seen_labels: set[str] = set()
                for item in data.get("categories", []):
                    key = str(item.get("key") or "").strip().lower()
                    label = self.clean_label(str(item.get("label") or ""))
                    if not key or not label or key in seen_keys or label.casefold() in seen_labels:
                        continue
                    loaded.append(AccountCategory(key, label, key == ACCOUNT_CATEGORY_UNUSED))
                    seen_keys.add(key)
                    seen_labels.add(label.casefold())
                if ACCOUNT_CATEGORY_UNUSED not in seen_keys:
                    loaded.insert(0, AccountCategory(ACCOUNT_CATEGORY_UNUSED, "未使用", True))
                else:
                    loaded.sort(key=lambda item: 0 if item.key == ACCOUNT_CATEGORY_UNUSED else 1)
                self.categories = loaded
            except Exception:
                self.categories = self._default_categories()
            self.save()

    def save(self) -> None:
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"categories": [asdict(category) for category in self.categories]}
            self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _default_categories() -> list[AccountCategory]:
        return [
            AccountCategory(key, label, key == ACCOUNT_CATEGORY_UNUSED)
            for key, label in DEFAULT_ACCOUNT_CATEGORIES
        ]

    @staticmethod
    def clean_label(label: str) -> str:
        text = " ".join((label or "").split()).strip()
        if "----" in text or text.startswith("#"):
            return ""
        return text[:24]

    def keys(self) -> list[str]:
        return [category.key for category in self.categories]

    def contains(self, key: str) -> bool:
        return any(category.key == key for category in self.categories)

    def get(self, key: str) -> AccountCategory | None:
        return next((category for category in self.categories if category.key == key), None)

    def label(self, key: str) -> str:
        category = self.get(key)
        return category.label if category else self.label(ACCOUNT_CATEGORY_UNUSED)

    def resolve(self, value: str | None) -> str | None:
        raw = (value or "").strip()
        if not raw:
            return ACCOUNT_CATEGORY_UNUSED
        lowered = raw.lower()
        if self.contains(lowered):
            return lowered
        by_label = next(
            (category.key for category in self.categories if category.label.casefold() == raw.casefold()),
            None,
        )
        if by_label:
            return by_label
        alias = self._legacy_aliases.get(lowered)
        return alias if alias and self.contains(alias) else None

    def resolve_or_add(self, value: str | None) -> str:
        resolved = self.resolve(value)
        if resolved:
            return resolved
        label = self.clean_label(value or "")
        if not label:
            return ACCOUNT_CATEGORY_UNUSED
        return self.add(label).key

    def add(self, label: str) -> AccountCategory:
        clean = self.clean_label(label)
        if not clean:
            raise ValueError("分类名称不能为空，也不能包含分隔符")
        existing = self.resolve(clean)
        if existing:
            raise ValueError("分类名称已存在")
        with self.lock:
            category = AccountCategory(f"custom_{uuid.uuid4().hex[:12]}", clean)
            self.categories.append(category)
            self.save()
            return category

    def rename(self, key: str, label: str) -> None:
        category = self.get(key)
        if not category:
            raise ValueError("分类不存在")
        if category.protected:
            raise ValueError("“未使用”分类不能重命名")
        clean = self.clean_label(label)
        if not clean:
            raise ValueError("分类名称不能为空，也不能包含分隔符")
        duplicate = next(
            (item for item in self.categories if item.key != key and item.label.casefold() == clean.casefold()),
            None,
        )
        if duplicate:
            raise ValueError("分类名称已存在")
        with self.lock:
            self.categories = [
                AccountCategory(item.key, clean, item.protected) if item.key == key else item
                for item in self.categories
            ]
            self.save()

    def delete(self, key: str) -> None:
        category = self.get(key)
        if not category:
            return
        if category.protected:
            raise ValueError("“未使用”分类不能删除")
        with self.lock:
            self.categories = [item for item in self.categories if item.key != key]
            self.save()
