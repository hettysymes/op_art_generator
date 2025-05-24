from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel,
    QSlider, QTableWidgetItem, QTableWidget
)

from ui.colour_prop_widget import ColorPropertyWidget
from ui.nodes.prop_defs import PT_GradOffset, List, Colour, GradOffset
from ui.reorderable_table_widget import ReorderableTableWidget


class AddItemDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Item")
        self.resize(300, 150)
        layout = QVBoxLayout(self)

        self.offset_slider = QSlider(Qt.Horizontal)
        self.offset_slider.setRange(0, 100)
        self.offset_slider.setValue(50)
        layout.addWidget(QLabel("Offset"))
        layout.addWidget(self.offset_slider)

        self.color_widget = ColorPropertyWidget(Colour(0, 0, 0, 255))
        layout.addWidget(QLabel("Color"))
        layout.addWidget(self.color_widget)

        button_box = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_box.addWidget(self.ok_button)
        button_box.addWidget(self.cancel_button)
        layout.addLayout(button_box)

    def accept(self):
        self.done(1)

    def reject(self):
        self.done(0)

    def done(self, result):
        self.result = result
        self.close()

    def exec_(self):
        self.show()
        app = QApplication.instance()
        while self.isVisible():
            app.processEvents()
        return self.result

    def get_value(self) -> GradOffset:
        offset = self.offset_slider.value() / 100.0
        color = self.color_widget.get_value()
        return GradOffset(offset, color)

class GradOffsetColourWidget(QWidget):
    def __init__(self, entries=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Offset", "Color"])
        layout.addWidget(self.table)

        add_button = QPushButton("Add Row")
        add_button.clicked.connect(self.add_row)
        layout.addWidget(add_button)

        self.set_entries(entries or [])

    def set_entries(self, entries):
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self.set_item(entry, row)

    def set_item(self, grad_offset: GradOffset, row):
        offset_item = QTableWidgetItem(f"{grad_offset.offset:.2f}")
        offset_item.setData(Qt.UserRole, grad_offset)
        self.table.setItem(row, 0, offset_item)

        color_widget = ColorPropertyWidget(grad_offset.colour)
        color_widget.colorChanged.connect(partial(self.update_color, row))
        self.table.setCellWidget(row, 1, color_widget)

    def add_row(self):
        dialog = AddItemDialog(self)
        if dialog.exec_() == 1:
            grad_offset: GradOffset = dialog.get_value()
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.set_item(grad_offset, row)

    def update_color(self, row, qcolour):
        grad_offset = self.table.item(row, 0).data(Qt.UserRole)
        grad_offset.colour = Colour(*qcolour.getRgb())

    def get_value(self):
        values = []
        for row in range(self.table.rowCount()):
            grad_offset: GradOffset = self.table.item(row, 0).data(Qt.UserRole)
            values.append(grad_offset)
        return values