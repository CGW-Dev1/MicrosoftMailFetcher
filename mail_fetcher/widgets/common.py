from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets


def pill_button(
    text: str,
    role: str = "secondary",
    checkable: bool = False,
    icon: QtGui.QIcon | None = None,
) -> QtWidgets.QPushButton:
    button = QtWidgets.QPushButton(text)
    button.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
    button.setCheckable(checkable)
    button.setProperty("role", role)
    if icon is not None:
        button.setIcon(icon)
        button.setIconSize(QtCore.QSize(16, 16))
    return button


class SearchField(QtWidgets.QLineEdit):
    def __init__(self, placeholder: str) -> None:
        super().__init__()
        self.setObjectName("SearchField")
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)


class ElidedLabel(QtWidgets.QLabel):
    def __init__(self, text: str = "", color: str = "#16304d") -> None:
        super().__init__()
        self._full_text = text
        self._color = color
        self.setText(text)

    def setText(self, text: str) -> None:  # type: ignore[override]
        self._full_text = text
        self.setToolTip(text)
        self._update_text()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._update_text()

    def _update_text(self) -> None:
        metrics = self.fontMetrics()
        shown = metrics.elidedText(self._full_text, QtCore.Qt.TextElideMode.ElideRight, max(10, self.width() - 2))
        super().setText(shown)


class CheckBox(QtWidgets.QCheckBox):
    def __init__(self, text: str = "") -> None:
        super().__init__(text)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(32)

    def sizeHint(self) -> QtCore.QSize:
        metrics = self.fontMetrics()
        text_width = metrics.horizontalAdvance(self.text()) if self.text() else 0
        width = 34 + (text_width + 12 if self.text() else 0)
        height = max(32, metrics.height() + 10)
        return QtCore.QSize(width, height)

    def hitButton(self, pos: QtCore.QPoint) -> bool:
        return self.rect().contains(pos)

    def paintEvent(self, _event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing, True)

        rect = self.rect()
        box = QtCore.QRectF(3, (rect.height() - 24) / 2, 24, 24)
        fill = QtGui.QColor("#dbe8ff" if self.isChecked() else "#e7f0ff")
        border = QtGui.QColor("#2f6fed" if self.underMouse() else ("#7fa2f8" if self.isChecked() else "#9bbcff"))

        painter.setPen(QtGui.QPen(border, 2))
        painter.setBrush(fill)
        painter.drawRoundedRect(box, 6, 6)

        if self.isChecked():
            pen = QtGui.QPen(QtGui.QColor("#e25353"), 2.6, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap, QtCore.Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(QtCore.QPointF(box.left() + 5.8, box.top() + 12.6), QtCore.QPointF(box.left() + 10.0, box.top() + 16.8))
            painter.drawLine(QtCore.QPointF(box.left() + 9.8, box.top() + 16.4), QtCore.QPointF(box.left() + 18.0, box.top() + 6.8))

        if self.text():
            painter.setPen(self.palette().color(QtGui.QPalette.ColorRole.WindowText))
            text_rect = QtCore.QRectF(box.right() + 10, 0, rect.width() - box.right() - 10, rect.height())
            painter.drawText(text_rect, QtCore.Qt.AlignmentFlag.AlignVCenter | QtCore.Qt.AlignmentFlag.AlignLeft, self.text())


class CountSelector(QtWidgets.QFrame):
    currentTextChanged = QtCore.pyqtSignal(str)

    def __init__(self, label: str, options: list[str], current: str) -> None:
        super().__init__()
        self.setObjectName("CountSelect")
        self.options = options
        self.current_value = current
        self.setToolTip(label)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setFixedSize(132, 40)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(4)

        self.value_button = QtWidgets.QPushButton(self.display_text(current))
        self.value_button.setProperty("role", "dropdown-value")
        self.value_button.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.value_button.clicked.connect(self.open_menu)
        self.value_button.setToolTip(label)
        layout.addWidget(self.value_button, 1)

        self.arrow_button = QtWidgets.QToolButton()
        self.arrow_button.setText("▾")
        self.arrow_button.setProperty("role", "dropdown-arrow")
        self.arrow_button.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.arrow_button.clicked.connect(self.open_menu)
        self.arrow_button.setToolTip(label)
        self.arrow_button.setFixedWidth(24)
        layout.addWidget(self.arrow_button)

    def currentText(self) -> str:
        return self.current_value

    def setCurrentText(self, value: str) -> None:
        self.current_value = value
        self.value_button.setText(self.display_text(value))

    def open_menu(self) -> None:
        menu = QtWidgets.QMenu(self)
        for option in self.options:
            action = menu.addAction(self.display_text(option))
            action.triggered.connect(lambda checked=False, value=option: self._choose(value))
        menu.exec(self.mapToGlobal(QtCore.QPoint(0, self.height())))

    def _choose(self, value: str) -> None:
        if value == self.current_value:
            return
        self.setCurrentText(value)
        self.currentTextChanged.emit(value)

    @staticmethod
    def display_text(value: str) -> str:
        return f"{value} 封"

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.open_menu()
            event.accept()
            return
        super().mousePressEvent(event)


class BadgeLabel(QtWidgets.QLabel):
    def __init__(self, text: str, tone: str = "blue") -> None:
        super().__init__(text)
        self.setObjectName("BadgeLabel")
        self.setProperty("tone", tone)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(28)
