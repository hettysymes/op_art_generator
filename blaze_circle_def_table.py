import copy

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidgetItem, QTableWidget, QHeaderView, QMenu, QAction
)

from nodes.prop_types import PT_BlazeCircleDef
from nodes.prop_values import List, BlazeCircleDef


class BlazeCircleDefWidget(QWidget):
    def __init__(self, entries=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["X Offset", "Y Offset", "Radius"])
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

    def set_item(self, circle_def: BlazeCircleDef, row):
        values = [circle_def.x_offset, circle_def.y_offset, circle_def.radius]
        for i, value in enumerate(values):
            item = QTableWidgetItem(f"{value:.2f}")
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            item.setData(Qt.UserRole, value)
            self.table.setItem(row, i, item)

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.set_item(BlazeCircleDef(0, 0, 0.5), row)

    def on_item_changed(self, item: QTableWidgetItem):
        offset: float = item.data(Qt.UserRole)
        try:
            new_offset = float(item.text())
            if item.column() == 2:
                # Radius, needs to be 0 and 1
                if new_offset <= 0 or new_offset > 1:
                    raise ValueError("Radius needs to be in range (0,1]")
            # Update item
            item.setText(f"{new_offset:.2f}")
            item.setData(Qt.UserRole, new_offset)
        except ValueError:
            # TODO: Show error or revert if input is invalid
            item.setText(f"{offset:.2f}")

    def get_value(self):
        # Return sorted by offset
        circle_defs: list[BlazeCircleDef] = []
        for row in range(self.table.rowCount()):
            x_offset: float = self.table.item(row, 0).data(Qt.UserRole)
            y_offset: float = self.table.item(row, 1).data(Qt.UserRole)
            radius: float = self.table.item(row, 2).data(Qt.UserRole)
            circle_defs.append(BlazeCircleDef(x_offset, y_offset, radius))
        sorted_defs = sorted(circle_defs, key=lambda circle_def: circle_def.radius)
        return List(PT_BlazeCircleDef(), sorted_defs)
