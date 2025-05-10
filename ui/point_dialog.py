from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox,
    QDialogButtonBox
)

def show_point_dialog(initial_x=0.0, initial_y=0.0):
    dialog = QDialog()
    dialog.setWindowTitle("Coordinate Point")
    dialog_layout = QVBoxLayout(dialog)

    form_layout = QFormLayout()

    x_input = QDoubleSpinBox()
    x_input.setDecimals(2)
    x_input.setValue(initial_x)

    y_input = QDoubleSpinBox()
    y_input.setDecimals(2)
    y_input.setValue(initial_y)

    form_layout.addRow("X:", x_input)
    form_layout.addRow("Y:", y_input)
    dialog_layout.addLayout(form_layout)

    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    dialog_layout.addWidget(button_box)

    if dialog.exec_():
        try:
            return x_input.value(), y_input.value()
        except ValueError:
            return None
    return None
