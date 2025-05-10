# point_dialog.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, QDialogButtonBox
)


class PointDialog(QDialog):
    def __init__(self, initial_x=0.0, initial_y=0.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Coordinate Point")

        self.x_input = QDoubleSpinBox()
        self.x_input.setDecimals(2)
        self.x_input.setValue(initial_x)

        self.y_input = QDoubleSpinBox()
        self.y_input.setDecimals(2)
        self.y_input.setValue(initial_y)

        form_layout = QFormLayout()
        form_layout.addRow("X:", self.x_input)
        form_layout.addRow("Y:", self.y_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_value(self):
        return self.x_input.value(), self.y_input.value()
