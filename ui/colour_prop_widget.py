from PyQt5.QtWidgets import QWidget, QHBoxLayout, QColorDialog, QSpinBox
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtCore import Qt, pyqtSignal


class ColorPreviewWidget(QWidget):
    """Widget that displays a color preview and handles clicks."""
    clicked = pyqtSignal()

    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(80, 20)
        # Make it clear this is clickable
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.black)
        painter.setBrush(self.color)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def setColor(self, color):
        self.color = color
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ColorPropertyWidget(QWidget):
    """Widget for selecting colors in property editor."""
    colorChanged = pyqtSignal(QColor)

    def __init__(self, initial_color, parent=None):
        super().__init__(parent)
        self.color = initial_color if isinstance(initial_color, QColor) else QColor(initial_color)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Color preview (now clickable)
        self.preview = ColorPreviewWidget(self.color)
        self.preview.clicked.connect(self.showColorDialog)

        layout.addWidget(self.preview)
        layout.setStretch(0, 1)

    def showColorDialog(self):
        color = QColorDialog.getColor(self.color, self, "Select Color",  options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            self.setColor(color)
            self.colorChanged.emit(self.color)

    def setColor(self, color):
        self.color = color if isinstance(color, QColor) else QColor(color)
        self.preview.setColor(self.color)

    def get_value(self):
        return self.color.getRgb()