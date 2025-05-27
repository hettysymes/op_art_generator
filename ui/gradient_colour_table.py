import copy
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel,
    QSlider, QTableWidgetItem, QTableWidget, QHeaderView, QMenu, QAction
)

from ui.colour_prop_widget import ColorPropertyWidget
from ui.nodes.prop_types import PT_GradOffset
from ui.nodes.prop_values import List, Colour, GradOffset


class GradOffsetColourWidget(QWidget):
    def __init__(self, entries=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Offset", "Color"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        add_button = QPushButton("+")
        add_button.clicked.connect(self.add_row)
        layout.addWidget(add_button)

        self.table.itemChanged.connect(self.on_item_changed)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        self.set_entries(entries or [])

    def set_entries(self, entries):
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self.set_item(copy.deepcopy(entry), row)

    def show_context_menu(self, position):
        index = self.table.indexAt(position)
        if not index.isValid():
            return  # Do nothing if not clicking on a valid item

        menu = QMenu()
        delete_action = QAction("Delete Row", self)
        delete_action.triggered.connect(lambda: self.delete_row(index.row()))
        menu.addAction(delete_action)

        menu.exec_(self.table.viewport().mapToGlobal(position))

    def delete_row(self, row):
        self.table.removeRow(row)

    def set_item(self, grad_offset: GradOffset, row):
        offset_item = QTableWidgetItem(f"{grad_offset.offset:.2f}")
        offset_item.setFlags(offset_item.flags() | Qt.ItemIsEditable)
        offset_item.setData(Qt.UserRole, grad_offset)
        self.table.setItem(row, 0, offset_item)

        color_widget = ColorPropertyWidget(grad_offset.colour)
        color_widget.colorChanged.connect(partial(self.update_color, row))
        self.table.setCellWidget(row, 1, color_widget)

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.set_item(GradOffset(1, Colour()), row)

    def update_color(self, row, qcolour):
        grad_offset = self.table.item(row, 0).data(Qt.UserRole)
        grad_offset.colour = Colour(*qcolour.getRgb())

    def on_item_changed(self, item: QTableWidgetItem):
        if item.column() == 0:
            grad_offset: GradOffset = item.data(Qt.UserRole)
            try:
                new_offset = float(item.text())
                if new_offset <= 0 or new_offset > 1:
                    raise ValueError("Offset needs to be in range (0,1]")
                grad_offset.offset = new_offset
                # Update the item text to a formatted value
                item.setText(f"{new_offset:.2f}")
            except ValueError:
                # TODO: Show error or revert if input is invalid
                item.setText(f"{grad_offset.offset:.2f}")

    def get_value(self):
        # Return sorted by offset
        grad_offsets: list[GradOffset] = []
        for row in range(self.table.rowCount()):
            grad_offset: GradOffset = self.table.item(row, 0).data(Qt.UserRole)
            grad_offsets.append(grad_offset)
        sorted_offsets = sorted(grad_offsets, key=lambda grad_offset: grad_offset.offset)
        return List(PT_GradOffset(), sorted_offsets)
