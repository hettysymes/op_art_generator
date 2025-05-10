import copy

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidgetItem, QMenu, QStyledItemDelegate

from ui.id_generator import shorten_uid
from ui.reorderable_table_widget import ReorderableTableWidget


class PortRefTableWidget(QWidget):
    def __init__(self, port_ref_getter, table_heading, entries=None, text_callback=None, context_menu_callback=None, parent=None):
        super().__init__(parent)
        self.port_ref_getter = port_ref_getter  # A function to get a port_ref given a ref_id
        self.text_callback = text_callback or self.default_text_callback
        self.context_menu_callback = context_menu_callback

        self.table = ReorderableTableWidget(self.add_item)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels([table_heading])
        self.table.setItemDelegate(self.CenteredItemDelegate())
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setWordWrap(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)

        self.set_entries(entries or [])

    def set_entries(self, entries):
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self.add_item(entry, row)

    def add_item(self, table_entry, row=None):
        ref_id = table_entry[0]
        port_ref = self.port_ref_getter(ref_id)
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setData(Qt.UserRole, table_entry)

        # Use text_callback to determine display string
        item.setText(self.text_callback(port_ref, table_entry))

        if not table_entry[2]:  # non-deletable
            item.setBackground(QColor(237, 130, 157))

        if row is not None:
            self.table.setItem(row, 0, item)

        return item

    def show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        item = self.table.item(row, 0)
        ref_id, data, deletable = item.data(Qt.UserRole)

        menu = QMenu()
        duplicate_action = menu.addAction("Duplicate")
        if deletable:
            delete_action = menu.addAction("Delete")

        # Allow external extension of the menu
        if self.context_menu_callback:
            self.context_menu_callback(menu, item, row)

        action = menu.exec_(self.table.viewport().mapToGlobal(position))

        if deletable and action == delete_action:
            self.table.removeRow(row)

        if action == duplicate_action:
            self.table.insertRow(row + 1)
            new_item = QTableWidgetItem(item.text())
            new_item.setData(Qt.UserRole, (ref_id, copy.deepcopy(data), True))
            self.table.setItem(row + 1, 0, new_item)

    def get_value(self):
        data = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            data.append(item.data(Qt.UserRole))
        return data

    class CenteredItemDelegate(QStyledItemDelegate):
        def initStyleOption(self, option, index):
            super().initStyleOption(option, index)
            option.displayAlignment = Qt.AlignCenter

    @staticmethod
    def default_text_callback(port_ref, table_entry):
        return f"{port_ref.base_node_name} (id: #{shorten_uid(port_ref.node_id)})"
