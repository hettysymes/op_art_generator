import copy
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidgetItem, QMenu, QStyledItemDelegate, QHBoxLayout, QPushButton

from ui.id_datatypes import PortId
from ui.node_manager import NodeManager, NodeInfo
from ui.nodes.prop_defs import PortRefTableEntry, PropType, List
from ui.reorderable_table_widget import ReorderableTableWidget


class PortRefTableWidget(QWidget):
    def __init__(self, list_item_type: PropType, ref_querier=None, node_manager: Optional[NodeManager] = None, table_heading=None, entries=None, text_callback=None,
                 context_menu_callback=None, additional_actions=None, item_delegate=None, parent=None):
        super().__init__(parent)
        self.list_item_type = list_item_type
        self.ref_querier = ref_querier  # A function to get a port given a ref
        self.node_manager = node_manager
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
        new_entries = []
        i = 0
        while i < len(entries):
            if isinstance(entries[i], PortRefTableEntry):
                group_len: int = entries[i].group_idx[1]
                new_entries.append([entries[i+j] for j in range(group_len)])
                i += group_len-1
            else:
                new_entries.append([entries[i]])
            i += 1

        self.table.setRowCount(len(new_entries))
        for row, entry in enumerate(new_entries):
            self.set_item(entry, row)

    def set_item(self, entry_group, row=None):
        first_entry = entry_group[0]
        ref_port: Optional[PortId] = None
        if isinstance(first_entry, PortRefTableEntry):
            ref_port = self.ref_querier(first_entry.ref)
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        item.setData(Qt.UserRole, entry_group)

        # Use text_callback to determine display string
        item.setText(self.text_callback(ref_port, self.node_manager, entry_group))

        if isinstance(first_entry, PortRefTableEntry) and not first_entry.deletable:  # non-deletable
            item.setBackground(QColor(237, 130, 157))

        if row is not None:
            self.table.setItem(row, 0, item)

        return item

    def show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return

        item = self.table.item(row, 0)
        entry_group = item.data(Qt.UserRole)
        first_entry = entry_group[0]

        menu = QMenu()

        # Allow external extension of the menu
        if self.context_menu_callback:
            self.context_menu_callback(menu, entry_group)

        duplicate_action = menu.addAction("Duplicate")
        if not isinstance(first_entry, PortRefTableEntry) or first_entry.deletable:
            delete_action = menu.addAction("Delete")

        action = menu.exec_(self.table.viewport().mapToGlobal(position))

        if (not isinstance(first_entry, PortRefTableEntry) or first_entry.deletable) and action == delete_action:
            self.table.removeRow(row)

        if action == duplicate_action:
            self.table.insertRow(row + 1)
            new_item = QTableWidgetItem(item.text())
            new_entry_group = copy.deepcopy(entry_group)
            if isinstance(new_entry_group[0], PortRefTableEntry):
                # Update whole entry group
                for entry in new_entry_group:
                    entry.deletable = True
            new_item.setData(Qt.UserRole, new_entry_group)
            self.table.setItem(row + 1, 0, new_item)

        if hasattr(menu, 'actions_map'):
            for action_key, action_def in menu.actions_map.items():
                if action == action_def:
                    self.additional_actions[action_key](self, entry_group, row)

    def get_value(self):
        entries = [entry for row in range(self.table.rowCount())
                   for entry in self.table.item(row, 0).data(Qt.UserRole)]
        return List(self.list_item_type, entries)

    class CenteredItemDelegate(QStyledItemDelegate):
        def initStyleOption(self, option, index):
            super().initStyleOption(option, index)
            option.displayAlignment = Qt.AlignCenter

    @staticmethod
    def default_text_callback(ref_port: Optional[PortId], node_manager: Optional[NodeManager], _):
        if ref_port and node_manager:
            node_info: NodeInfo = node_manager.node_info(ref_port.node)
            return f"{node_info.base_name} (id: {node_info.uid})"
        return ""
