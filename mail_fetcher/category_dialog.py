from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from .categories import CategoryStore
from .constants import ACCOUNT_CATEGORY_UNUSED
from .storage import AccountStore
from .widgets import SearchField, pill_button


class CategoryManagerDialog(QtWidgets.QDialog):
    categories_changed = QtCore.pyqtSignal()

    def __init__(
        self,
        category_store: CategoryStore,
        account_store: AccountStore,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.category_store = category_store
        self.account_store = account_store
        self.setWindowTitle("管理账号分类")
        self.setModal(True)
        self.resize(500, 480)
        self.setMinimumSize(440, 400)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        title = QtWidgets.QLabel("账号分类")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)
        hint = QtWidgets.QLabel("新增分类后会同步出现在左侧菜单、批量移动和导入导出中。")
        hint.setObjectName("DialogText")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        add_row = QtWidgets.QHBoxLayout()
        add_row.setSpacing(8)
        self.name_input = SearchField("输入新分类名称")
        self.name_input.setMaxLength(24)
        self.name_input.returnPressed.connect(self.add_category)
        add_row.addWidget(self.name_input, 1)
        add_button = pill_button("新增分类", role="primary")
        add_button.setFixedHeight(38)
        add_button.clicked.connect(self.add_category)
        add_row.addWidget(add_button)
        layout.addLayout(add_row)

        self.category_list = QtWidgets.QListWidget()
        self.category_list.setObjectName("CategoryManagerList")
        self.category_list.setAlternatingRowColors(False)
        self.category_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.category_list.itemDoubleClicked.connect(lambda _item: self.rename_category())
        layout.addWidget(self.category_list, 1)

        footer = QtWidgets.QHBoxLayout()
        footer.setSpacing(8)
        self.summary_label = QtWidgets.QLabel()
        self.summary_label.setObjectName("DialogText")
        footer.addWidget(self.summary_label, 1)
        rename_button = pill_button("重命名", role="secondary")
        rename_button.clicked.connect(self.rename_category)
        footer.addWidget(rename_button)
        delete_button = pill_button("删除分类", role="danger")
        delete_button.clicked.connect(self.delete_category)
        footer.addWidget(delete_button)
        close_button = pill_button("完成", role="primary")
        close_button.clicked.connect(self.accept)
        footer.addWidget(close_button)
        layout.addLayout(footer)

        self.refresh_list()

    def selected_key(self) -> str | None:
        item = self.category_list.currentItem()
        return str(item.data(QtCore.Qt.ItemDataRole.UserRole)) if item else None

    def account_count(self, key: str) -> int:
        return sum(1 for account in self.account_store.accounts if account.category == key)

    def refresh_list(self, select_key: str | None = None) -> None:
        current = select_key or self.selected_key()
        self.category_list.clear()
        total_accounts = len(self.account_store.accounts)
        for category in self.category_store.categories:
            count = self.account_count(category.key)
            suffix = " · 系统默认" if category.protected else ""
            item = QtWidgets.QListWidgetItem(f"{category.label}    {count} 个账号{suffix}")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, category.key)
            item.setToolTip("双击可重命名" if not category.protected else "未使用是账号的默认归类，不能删除")
            self.category_list.addItem(item)
            if category.key == current:
                self.category_list.setCurrentItem(item)
        if self.category_list.currentRow() < 0 and self.category_list.count():
            self.category_list.setCurrentRow(0)
        self.summary_label.setText(f"{len(self.category_store.categories)} 个分类 · {total_accounts} 个账号")

    def add_category(self) -> None:
        try:
            category = self.category_store.add(self.name_input.text())
        except ValueError as exc:
            self.show_error(str(exc))
            return
        self.name_input.clear()
        self.refresh_list(category.key)
        self.categories_changed.emit()

    def rename_category(self) -> None:
        key = self.selected_key()
        category = self.category_store.get(key or "")
        if not category:
            return
        if category.protected:
            self.show_error("“未使用”分类用于接收未归类账号，不能重命名")
            return
        value, accepted = QtWidgets.QInputDialog.getText(
            self,
            "重命名分类",
            "分类名称：",
            QtWidgets.QLineEdit.EchoMode.Normal,
            category.label,
        )
        if not accepted:
            return
        try:
            self.category_store.rename(category.key, value)
        except ValueError as exc:
            self.show_error(str(exc))
            return
        self.refresh_list(category.key)
        self.categories_changed.emit()

    def delete_category(self) -> None:
        key = self.selected_key()
        category = self.category_store.get(key or "")
        if not category:
            return
        if category.protected:
            self.show_error("“未使用”分类不能删除")
            return
        count = self.account_count(category.key)
        detail = f"其中 {count} 个账号会移回“未使用”。" if count else "该分类当前没有账号。"
        answer = QtWidgets.QMessageBox.question(
            self,
            "删除分类",
            f"确定删除“{category.label}”吗？\n{detail}",
        )
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        self.account_store.reassign_category(category.key, ACCOUNT_CATEGORY_UNUSED)
        self.category_store.delete(category.key)
        self.refresh_list(ACCOUNT_CATEGORY_UNUSED)
        self.categories_changed.emit()

    def show_error(self, message: str) -> None:
        QtWidgets.QMessageBox.information(self, "无法完成操作", message)
