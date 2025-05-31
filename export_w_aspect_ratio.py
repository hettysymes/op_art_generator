import shutil

from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (
    QDialog, QLabel, QComboBox, QPushButton, QVBoxLayout,
    QFileDialog, QMessageBox, QSpinBox
)

from nodes.shape_datatypes import Element


class ExportWithAspectRatio(QDialog):
    def __init__(self, filepath, element: Element, default_width, default_height, parent=None):
        super().__init__(parent)
        self.svg_path = filepath
        self.element = element
        self.default_width = default_width
        self.aspect_ratio = default_width / default_height
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Export Image with Aspect Ratio")
        self.setMinimumWidth(300)

        self.input_label = QLabel("Width (pixels):")
        self.input_field = QSpinBox()
        self.input_field.setRange(1, 10000)
        self.input_field.setValue(100)
        self.input_field.setValue(self.default_width)

        self.dimension_label = QLabel()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["SVG", "PNG"])

        self.browse_button = QPushButton("Save")

        layout = QVBoxLayout()
        layout.addWidget(self.input_label)
        layout.addWidget(self.input_field)
        layout.addWidget(self.dimension_label)
        layout.addWidget(QLabel("Format:"))
        layout.addWidget(self.format_combo)
        layout.addWidget(self.browse_button)
        self.setLayout(layout)

        # Connect signals
        self.input_field.textChanged.connect(self.update_dimensions)
        self.browse_button.clicked.connect(self.choose_file)

        # Update height text
        self.update_dimensions()

    def update_dimensions(self):
        try:
            width = float(self.input_field.text())
            height = width / self.aspect_ratio
            self.dimension_label.setText(f"Height (pixels): {int(height)}")
        except ValueError:
            self.dimension_label.setText("Height (pixels): —")

    def choose_file(self):
        ext = self.format_combo.currentText().lower()
        path, _ = QFileDialog.getSaveFileName(self, "Save As", f"untitled.{ext}", f"{ext.upper()} Files (*.{ext})")
        if path:
            self.save_image(path)

    def save_image(self, path):
        try:
            width = int(float(self.input_field.text()))
            height = int(width / self.aspect_ratio)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid width.")
            return

        self.element.save_to_svg(self.svg_path, width, height)
        if path.endswith(".svg"):
            # Just copy the existing SVG file as-is
            shutil.copyfile(self.svg_path, path)
        elif path.endswith(".png"):
            # Render SVG to PNG with requested dimensions
            svg_renderer = QSvgRenderer(self.svg_path)
            image = QImage(width, height, QImage.Format_ARGB32)
            image.fill(0x00000000)  # transparent background
            painter = QPainter(image)
            svg_renderer.render(painter)
            painter.end()
            image.save(path)
        self.accept()
