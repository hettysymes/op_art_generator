from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox, QPushButton, QDialogButtonBox, QGroupBox,
                             QHBoxLayout, QLabel, QTableWidget,
                             QHeaderView, QTableWidgetItem)


class CubicFunctionDialog(QDialog):
    """Dialog for editing cubic function parameters"""

    def __init__(self, node_item, parent=None):
        super().__init__(parent)
        self.node_item = node_item
        self.setWindowTitle("Edit Cubic Function")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()

        # Get current parameters
        a = node_item.property_values.get('cubic_param_a', 3.2206)
        b = node_item.property_values.get('cubic_param_b', 0.0)
        c = node_item.property_values.get('cubic_param_c', 0.0)
        d = node_item.property_values.get('cubic_param_d', 0.0)

        # Create input fields
        self.a_input = QDoubleSpinBox()
        self.a_input.setRange(-1000, 1000)
        self.a_input.setDecimals(4)
        self.a_input.setValue(a)

        self.b_input = QDoubleSpinBox()
        self.b_input.setRange(-1000, 1000)
        self.b_input.setDecimals(4)
        self.b_input.setValue(b)

        self.c_input = QDoubleSpinBox()
        self.c_input.setRange(-1000, 1000)
        self.c_input.setDecimals(4)
        self.c_input.setValue(c)

        self.d_input = QDoubleSpinBox()
        self.d_input.setRange(-1000, 1000)
        self.d_input.setDecimals(4)
        self.d_input.setValue(d)

        form.addRow("a (x³):", self.a_input)
        form.addRow("b (x²):", self.b_input)
        form.addRow("c (x):", self.c_input)
        form.addRow("d (constant):", self.d_input)

        # Function preview label
        self.preview_label = QLabel("f(x) = 3.2206x³ + 0x² + 0x + 0")
        self.update_preview()

        # Connect signals to update preview
        self.a_input.valueChanged.connect(self.update_preview)
        self.b_input.valueChanged.connect(self.update_preview)
        self.c_input.valueChanged.connect(self.update_preview)
        self.d_input.valueChanged.connect(self.update_preview)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(self.preview_label)
        layout.addWidget(buttons)

    def update_preview(self):
        """Update the function preview text"""
        a = self.a_input.value()
        b = self.b_input.value()
        c = self.c_input.value()
        d = self.d_input.value()

        self.preview_label.setText(f"f(x) = {a}x³ + {b}x² + {c}x + {d}")

    def accept(self):
        """Apply the cubic function parameters to the node"""
        self.node_item.property_values['function_type'] = 'cubic'
        self.node_item.property_values['cubic_param_a'] = self.a_input.value()
        self.node_item.property_values['cubic_param_b'] = self.b_input.value()
        self.node_item.property_values['cubic_param_c'] = self.c_input.value()
        self.node_item.property_values['cubic_param_d'] = self.d_input.value()
        super().accept()


class PiecewiseLinearDialog(QDialog):
    """Dialog for editing piecewise linear function points"""

    def __init__(self, node_item, parent=None):
        super().__init__(parent)
        self.node_item = node_item
        self.setWindowTitle("Edit Piecewise Linear Function")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Get current points or use defaults
        self.points = node_item.property_values.get('piecewise_points',
                                                    [(0, 0), (0.5, 0.5), (1, 1)])

        # Create table for points
        self.table = QTableWidget(len(self.points), 2)
        self.table.setHorizontalHeaderLabels(["X", "Y"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Fill the table with point data
        for i, (x, y) in enumerate(self.points):
            self.table.setItem(i, 0, QTableWidgetItem(str(x)))
            self.table.setItem(i, 1, QTableWidgetItem(str(y)))

        # Buttons for modifying points
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Point")
        remove_button = QPushButton("Remove Selected")

        add_button.clicked.connect(self.add_point)
        remove_button.clicked.connect(self.remove_point)

        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)

        # Dialog buttons
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)

        layout.addWidget(QLabel("Define points for piecewise linear function:"))
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        layout.addWidget(dialog_buttons)

    def add_point(self):
        """Add a new point to the table"""
        current_row = self.table.rowCount()
        self.table.insertRow(current_row)

        # Default to next x value and midpoint y
        default_x = 0.0
        if current_row > 0:
            last_x = float(self.table.item(current_row - 1, 0).text())
            default_x = last_x + 0.1

        self.table.setItem(current_row, 0, QTableWidgetItem(str(default_x)))
        self.table.setItem(current_row, 1, QTableWidgetItem("0.0"))

    def remove_point(self):
        """Remove the selected point"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)

    def accept(self):
        """Apply the piecewise points to the node"""
        points = []
        for i in range(self.table.rowCount()):
            try:
                x = float(self.table.item(i, 0).text())
                y = float(self.table.item(i, 1).text())
                points.append((x, y))
            except (ValueError, TypeError):
                continue

        # Sort points by x value
        points.sort(key=lambda p: p[0])

        self.node_item.property_values['function_type'] = 'piecewise'
        self.node_item.property_values['piecewise_points'] = points
        super().accept()


class FunctionEditorDialog(QDialog):
    """Dialog for editing grid warping function"""

    def __init__(self, node_item, parent=None):
        super().__init__(parent)
        self.node_item = node_item
        self.setWindowTitle("Grid Warping Function Editor")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Function type selection
        type_group = QGroupBox("Function Type")
        type_layout = QHBoxLayout()
        type_group.setLayout(type_layout)

        self.cubic_button = QPushButton("Cubic Function")
        self.piecewise_button = QPushButton("Piecewise Linear")

        self.cubic_button.clicked.connect(self.edit_cubic)
        self.piecewise_button.clicked.connect(self.edit_piecewise)

        type_layout.addWidget(self.cubic_button)
        type_layout.addWidget(self.piecewise_button)

        # Current function display
        function_group = QGroupBox("Current Function")
        function_layout = QVBoxLayout()
        function_group.setLayout(function_layout)

        function_type = node_item.property_values.get('function_type', 'cubic')

        if function_type == 'cubic':
            a = node_item.property_values.get('cubic_param_a', 3.2206)
            b = node_item.property_values.get('cubic_param_b', 0.0)
            c = node_item.property_values.get('cubic_param_c', 0.0)
            d = node_item.property_values.get('cubic_param_d', 0.0)
            function_text = f"Cubic Function: f(x) = {a}x³ + {b}x² + {c}x + {d}"
        else:
            points = node_item.property_values.get('piecewise_points', [(0, 0), (1, 1)])
            function_text = "Piecewise Linear Function:\n"
            for i, (x, y) in enumerate(points):
                function_text += f"  Point {i + 1}: ({x}, {y})\n"

        self.function_label = QLabel(function_text)
        function_layout.addWidget(self.function_label)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)

        layout.addWidget(type_group)
        layout.addWidget(function_group)
        layout.addWidget(buttons)

    def edit_cubic(self):
        """Open the cubic function editor"""
        dialog = CubicFunctionDialog(self.node_item, self)
        if dialog.exec_() == QDialog.Accepted:
            # Update the function display
            a = self.node_item.property_values.get('cubic_param_a', 0)
            b = self.node_item.property_values.get('cubic_param_b', 0)
            c = self.node_item.property_values.get('cubic_param_c', 0)
            d = self.node_item.property_values.get('cubic_param_d', 0)
            function_text = f"Cubic Function: f(x) = {a}x³ + {b}x² + {c}x + {d}"
            self.function_label.setText(function_text)

    def edit_piecewise(self):
        """Open the piecewise linear function editor"""
        dialog = PiecewiseLinearDialog(self.node_item, self)
        if dialog.exec_() == QDialog.Accepted:
            # Update the function display
            points = self.node_item.property_values.get('piecewise_points', [])
            function_text = "Piecewise Linear Function:\n"
            for i, (x, y) in enumerate(points):
                function_text += f"  Point {i + 1}: ({x}, {y})\n"
            self.function_label.setText(function_text)
