from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QStyledItemDelegate, \
    QHeaderView

from id_datatypes import PortId
from node_manager import NodeManager, NodeInfo
from nodes.prop_types import PT_ValProbPairHolder
from nodes.prop_values import List, PortRefTableEntry, ValProbPairRef


class RandomProbabilityWidget(QWidget):
    def __init__(self, ref_querier, node_manager: NodeManager, entries=None, parent=None):
        super().__init__(parent)
        self.ref_querier = ref_querier
        self.node_manager = node_manager
        self.text_callback = self.default_text_callback
        self.item_delegate = self.CenteredItemDelegate()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Reference", "Weight"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setItemDelegateForColumn(0, self.item_delegate)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setWordWrap(True)
        self.table.itemChanged.connect(self.on_item_changed)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)

        self.set_entries(entries or [])

    def row_count(self):
        return self.table.rowCount()

    def set_row_count(self, row):
        self.table.setRowCount(row)

    def set_entries(self, entries):
        new_entries = []
        i = 0
        while i < len(entries):
            entry = entries[i]
            if isinstance(entry, PortRefTableEntry):
                group_len: int = entry.group_idx[1]
                new_entries.append(entries[i:i + group_len])
                i += group_len
            else:
                new_entries.append([entry])
                i += 1

        self.table.setRowCount(len(new_entries))
        for row, entry in enumerate(new_entries):
            self.set_item(entry, row)

    def set_item(self, entry_group, row=None):
        first_entry = entry_group[0]
        assert isinstance(first_entry, ValProbPairRef)
        ref_port: PortId = self.ref_querier(first_entry.ref)

        # Column 0: Reference
        ref_item = QTableWidgetItem()
        ref_item.setTextAlignment(Qt.AlignCenter)
        ref_item.setText(self.text_callback(ref_port, self.node_manager, entry_group))

        if isinstance(first_entry, PortRefTableEntry) and not first_entry.deletable:
            ref_item.setBackground(QColor(237, 130, 157))

        # Column 1: Editable Probability
        prob_item = QTableWidgetItem(f"{first_entry.probability:.2f}")
        prob_item.setTextAlignment(Qt.AlignCenter)
        prob_item.setData(Qt.UserRole, entry_group) # Set data
        prob_item.setFlags(prob_item.flags() | Qt.ItemIsEditable)

        if row is not None:
            self.table.setItem(row, 0, ref_item)
            self.table.setItem(row, 1, prob_item)

        return ref_item, prob_item

    def on_item_changed(self, item: QTableWidgetItem):
        if item.column() == 1:
            entry_group = item.data(Qt.UserRole)
            try:
                new_probability = float(item.text())
                if new_probability <= 0:
                    raise ValueError("Weight needs to be greater than 0")
                for entry in entry_group:
                    assert isinstance(entry, ValProbPairRef)
                    entry.probability = new_probability
                item.setText(f"{new_probability:.2f}")
            except ValueError:
                # TODO: Show error or revert if input is invalid
                item.setText(f"{entry_group[0].probability:.2f}")

    def get_value(self):
        entries = []
        for row in range(self.table.rowCount()):
            entry_group = self.table.item(row, 1).data(Qt.UserRole)
            entries.extend(entry_group)
        return List(PT_ValProbPairHolder(), entries)

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
