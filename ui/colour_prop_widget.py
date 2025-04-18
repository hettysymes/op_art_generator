from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QColorDialog
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtCore import Qt, pyqtSignal


class ColorPreviewWidget(QWidget):
    """Widget that displays a color preview."""

    def __init__(self, color=Qt.black, parent=None):
        super().__init__(parent)
        self.color = color
        self.setMinimumSize(24, 24)
        self.setMaximumHeight(24)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.black)
        painter.setBrush(self.color)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def setColor(self, color):
        self.color = color
        self.update()


class ColorPropertyWidget(QWidget):
    """Widget for selecting colors in property editor."""
    colorChanged = pyqtSignal(QColor)

    def __init__(self, initial_color, parent=None):
        super().__init__(parent)
        self.color = initial_color

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Color preview
        self.preview = ColorPreviewWidget(self.color)

        # Button to show color dialog
        self.pickButton = QPushButton("Select...")
        self.pickButton.clicked.connect(self.showColorDialog)

        layout.addWidget(self.preview)
        layout.addWidget(self.pickButton)
        layout.setStretch(0, 1)
        layout.setStretch(1, 0)

    def showColorDialog(self):
        color = QColorDialog.getColor(self.color, self, "Select Color")
        if color.isValid():
            self.setColor(color)
            self.colorChanged.emit(self.color)

    def setColor(self, color):
        self.color = color
        self.preview.setColor(color)

    def getColor(self):
        return self.color