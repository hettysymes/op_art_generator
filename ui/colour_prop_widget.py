from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QColorDialog

from ui.nodes.prop_defs import Colour


class ColorPreviewWidget(QWidget):
    """Widget that displays a color preview and handles clicks."""
    clicked = pyqtSignal()

    def __init__(self, color: Colour, parent=None):
        super().__init__(parent)
        assert isinstance(color, Colour)
        self.color = color
        self.setFixedSize(80, 20)
        # Make it clear this is clickable
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.black)
        painter.setBrush(QColor(*self.color))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def setColor(self, color: Colour):
        self.color = color
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ColorPropertyWidget(QWidget):
    """Widget for selecting colors in property editor."""
    colorChanged = pyqtSignal(QColor)

    def __init__(self, initial_color: Colour, parent=None):
        super().__init__(parent)
        self.colour = initial_color

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Color preview (now clickable)
        self.preview = ColorPreviewWidget(self.colour)
        self.preview.clicked.connect(self.showColorDialog)

        layout.addWidget(self.preview)
        layout.setStretch(0, 1)

    def showColorDialog(self):
        qcolour = QColorDialog.getColor(QColor(*self.colour), self, "Select Color", options=QColorDialog.ShowAlphaChannel)
        if qcolour.isValid():
            colour: Colour = Colour(*qcolour.getRgb())
            self.set_colour(colour)
            self.colorChanged.emit(qcolour)

    def set_colour(self, colour: Colour):
        self.colour = colour
        self.preview.setColor(self.colour)

    def get_value(self) -> Colour:
        return self.colour
