from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mail_fetcher.categories import CategoryStore
from mail_fetcher.constants import ACCOUNT_CATEGORY_UNUSED
from mail_fetcher.parsing import parse_import_text


class CategoryStoreTests(unittest.TestCase):
    def test_add_rename_delete_and_reload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "categories.json"
            store = CategoryStore(path)
            category = store.add("待复核")
            self.assertEqual(store.resolve("待复核"), category.key)

            store.rename(category.key, "已复核")
            reloaded = CategoryStore(path)
            self.assertEqual(reloaded.label(category.key), "已复核")

            reloaded.delete(category.key)
            self.assertFalse(reloaded.contains(category.key))
            self.assertTrue(reloaded.contains(ACCOUNT_CATEGORY_UNUSED))

    def test_import_preserves_custom_category_label(self) -> None:
        rows, invalid = parse_import_text("person@example.com----pw----client----token----客户 A")
        self.assertEqual(invalid, 0)
        self.assertEqual(rows[0].category, "客户 A")


if __name__ == "__main__":
    unittest.main()
