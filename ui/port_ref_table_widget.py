import copy

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidgetItem, QMenu, QStyledItemDelegate, QHBoxLayout, QPushButton

from ui.nodes.prop_defs import PortRefTableEntry
from ui.reorderable_table_widget import ReorderableTableWidget


class PortRefTableWidget(QWidget):
    def __init__(self, port_ref_getter=None, table_heading=None, entries=None, text_callback=None,
                 context_menu_callback=None, additional_actions=None, item_delegate=None, parent=None):
        super().__init__(parent)
        self.port_ref_getter = port_ref_getter  # A function to get a port_ref given a ref_id
        self.text_callback = text_callback or self.default_text_callback
        self.context_menu_callback = context_menu_callback
        self.additional_actions = additional_actions
        self.item_delegate = item_delegate or self.CenteredItemDelegate()

        self.table = ReorderableTableWidget(self.set_item)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels([table_heading])
        self.table.setItemDelegate(self.item_delegate)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setWordWrap(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)

        if additional_actions and 'add' in additional_actions:
            # Set up button
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(0, 0, 0, 0)
            add_button = QPushButton("+")
            add_button.clicked.connect(lambda: additional_actions['add'](self))
            button_layout.addWidget(add_button)
            # Add to layout
            layout.addWidget(button_widget)

        self.set_entries(entries or [])

    def row_count(self):
        return self.table.rowCount()

    def set_row_count(self, row):
        return self.table.setRowCount(row)

    def set_entries(self, entries):
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self.set_item(entry, row)

    def set_item(self, table_entry, row=None):
        port_ref = None
        if isinstance(table_entry, PortRefTableEntry):
            if isinstance(table_entry.ref, tuple):
                ref_id = table_entry.ref[0]
            else:
                ref_id = table_entry.ref
            port_ref = self.port_ref_getter(ref_id)
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setData(Qt.UserRole, table_entry)

        # Use text_callback to determine display string
        item.setText(self.text_callback(port_ref, table_entry))

        if isinstance(table_entry, PortRefTableEntry) and not table_entry.deletable:  # non-deletable
            item.setBackground(QColor(237, 130, 157))

        if row is not None:
            self.table.setItem(row, 0, item)

        return item

    def show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        item = self.table.item(row, 0)
        table_entry = item.data(Qt.UserRole)

        menu = QMenu()

        # Allow external extension of the menu
        if self.context_menu_callback:
            self.context_menu_callback(menu, table_entry)

        duplicate_action = menu.addAction("Duplicate")
        if not isinstance(table_entry, PortRefTableEntry) or table_entry.deletable:
            delete_action = menu.addAction("Delete")

        action = menu.exec_(self.table.viewport().mapToGlobal(position))

        if (not isinstance(table_entry, PortRefTableEntry) or table_entry.deletable) and action == delete_action:
            self.table.removeRow(row)

        if action == duplicate_action:
            self.table.insertRow(row + 1)
            new_item = QTableWidgetItem(item.text())
            new_table_entry = copy.deepcopy(table_entry)
            if isinstance(new_table_entry, PortRefTableEntry):
                new_table_entry.deletable = True
            new_item.setData(Qt.UserRole, new_table_entry)
            self.table.setItem(row + 1, 0, new_item)

        if hasattr(menu, 'actions_map'):
            for action_key, action_def in menu.actions_map.items():
                if action == action_def:
                    self.additional_actions[action_key](self, table_entry, row)

    def get_value(self):
        entries = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            entries.append(item.data(Qt.UserRole))
        return entries

    class CenteredItemDelegate(QStyledItemDelegate):
        def initStyleOption(self, option, index):
            super().initStyleOption(option, index)
            option.displayAlignment = Qt.AlignCenter

    @staticmethod
    def default_text_callback(port_ref, table_entry):
        if port_ref:
            return f"{port_ref.base_name} (id: {port_ref.node})"
        return ""
