from PyQt5.QtCore import Qt
from PyQt5.QtCore import QRectF
from PyQt5.QtGui import QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QMainWindow, QWidget


class SvgDisplayWidget(QWidget):
    def __init__(self, svg_path):
        super().__init__()
        self.renderer = QSvgRenderer(svg_path)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Fill the entire widget background with black
        painter.fillRect(self.rect(), Qt.black)

        # Calculate a centered, scaled rectangle
        svg_size = self.renderer.defaultSize()
        widget_size = self.size()
        scale = min(widget_size.width() / svg_size.width(),
                    widget_size.height() / svg_size.height())

        new_width = svg_size.width() * scale
        new_height = svg_size.height() * scale
        x = (widget_size.width() - new_width) / 2
        y = (widget_size.height() - new_height) / 2

        target_rect = QRectF(x, y, new_width, new_height)
        self.renderer.render(painter, target_rect)

class SvgFullScreenWindow(QMainWindow):
    def __init__(self, svg_path):
        super().__init__()

        self.svg_widget = SvgDisplayWidget(svg_path)
        self.setCentralWidget(self.svg_widget)

        self.showFullScreen()