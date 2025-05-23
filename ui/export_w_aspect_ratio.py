import shutil

from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QComboBox, QPushButton, QVBoxLayout,
    QFileDialog, QMessageBox, QSpinBox
)
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QImage, QPainter

from ui.nodes.shape_datatypes import Element


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

        self.input_label = QLabel("Width (pixels):")
        self.input_field = QSpinBox()
        self.input_field.setRange(1, 10000)
        self.input_field.setValue(100)
        self.input_field.setValue(self.default_width)

        self.dimension_label = QLabel()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["SVG", "PNG"])

        self.browse_button = QPushButton("Choose Save Location")
        self.path_label = QLabel("No file chosen")

        self.save_button = QPushButton("Save")
        self.save_button.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self.input_label)
        layout.addWidget(self.input_field)
        layout.addWidget(self.dimension_label)
        layout.addWidget(QLabel("Format:"))
        layout.addWidget(self.format_combo)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.path_label)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

        # Connect signals
        self.input_field.textChanged.connect(self.update_dimensions)
        self.browse_button.clicked.connect(self.choose_file)
        self.save_button.clicked.connect(self.save_image)

        # Update height text
        self.update_dimensions()

    def update_dimensions(self):
        try:
            width = float(self.input_field.text())
            height = width / self.aspect_ratio
            self.dimension_label.setText(f"Height (pixels): {int(height)}")
        except ValueError:
            self.dimension_label.setText("Height (pixels): —")
        self.save_button.setEnabled(bool(self.input_field.text() and self.path_label.text() != "No file chosen"))

    def choose_file(self):
        ext = self.format_combo.currentText().lower()
        path, _ = QFileDialog.getSaveFileName(self, "Save As", f"untitled.{ext}", f"{ext.upper()} Files (*.{ext})")
        if path:
            self.path_label.setText(path)
            self.update_dimensions()

    def save_image(self):
        try:
            width = int(float(self.input_field.text()))
            height = int(width / self.aspect_ratio)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid width.")
            return

        path = self.path_label.text()
        if not path:
            QMessageBox.warning(self, "No Path", "Please choose a save location.")
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
