from __future__ import annotations

from PyQt6 import QtCore, QtWidgets


class FlowLayout(QtWidgets.QLayout):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        margin: int = 0,
        h_spacing: int = 10,
        v_spacing: int = 8,
    ) -> None:
        super().__init__(parent)
        self.item_list: list[QtWidgets.QLayoutItem] = []
        self.h_spacing = h_spacing
        self.v_spacing = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item: QtWidgets.QLayoutItem) -> None:
        self.item_list.append(item)

    def count(self) -> int:
        return len(self.item_list)

    def itemAt(self, index: int) -> QtWidgets.QLayoutItem | None:
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index: int) -> QtWidgets.QLayoutItem | None:
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def expandingDirections(self) -> QtCore.Qt.Orientation:
        return QtCore.Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self.do_layout(QtCore.QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QtCore.QRect) -> None:
        super().setGeometry(rect)
        self.do_layout(rect, test_only=False)

    def sizeHint(self) -> QtCore.QSize:
        return self.minimumSize()

    def minimumSize(self) -> QtCore.QSize:
        size = QtCore.QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        size += QtCore.QSize(left + right, top + bottom)
        return size

    def do_layout(self, rect: QtCore.QRect, test_only: bool) -> int:
        left, top, right, bottom = self.getContentsMargins()
        effective = rect.adjusted(left, top, -right, -bottom)
        x = effective.x()
        y = effective.y()
        line_height = 0
        for item in self.item_list:
            hint = item.sizeHint()
            next_x = x + hint.width() + self.h_spacing
            if next_x - self.h_spacing > effective.right() and line_height > 0:
                x = effective.x()
                y += line_height + self.v_spacing
                next_x = x + hint.width() + self.h_spacing
                line_height = 0
            if not test_only:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), hint))
            x = next_x
            line_height = max(line_height, hint.height())
        return y + line_height + bottom - rect.y()
