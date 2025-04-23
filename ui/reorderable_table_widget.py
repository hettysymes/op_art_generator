from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDropEvent, QColor
from PyQt5.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView, QTableWidgetItem

from ui.nodes.point_ref import PointRef


class ReorderableTableWidget(QTableWidget):
    def __init__(self, add_item_fun, parent=None):
        super().__init__(parent)

        self.add_item_fun = add_item_fun
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)  # <--- Not InternalMove
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)

    def mimeData(self, items):
        mime_data = super().mimeData(items)
        mime_data.setText("drag-row")
        return mime_data

    def dropEvent(self, event: QDropEvent):
        if event.source() == self:
            drop_row = self.drop_on(event)

            selected_rows = sorted(set(index.row() for index in self.selectedIndexes()))
            items_to_move = []

            # Grab data from selected rows
            for row in selected_rows:
                item = self.item(row, 0)
                new_item = self.add_item_fun(item.data(Qt.UserRole))
                items_to_move.append(new_item)

            # Remove selected rows (in reverse order to avoid shifting)
            for row in reversed(selected_rows):
                self.removeRow(row)
                if row < drop_row:
                    drop_row -= 1

            # Insert rows at new position
            for i, item in enumerate(items_to_move):
                self.insertRow(drop_row + i)
                self.setItem(drop_row + i, 0, item)
                self.selectRow(drop_row + i)

            for row in range(self.rowCount()):
                self.setRowHeight(row, 40)

            event.accept()
        else:
            super().dropEvent(event)

    def drop_on(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return self.rowCount()
        return index.row() + 1 if self.is_below(event.pos(), index) else index.row()

    def is_below(self, pos, index):
        rect = self.visualRect(index)
        margin = 2
        if pos.y() - rect.top() < margin:
            return False
        elif rect.bottom() - pos.y() < margin:
            return True
        return rect.contains(pos) and pos.y() >= rect.center().y()

    def dragEnterEvent(self, event):
        if event.source() == self:
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.source() == self:
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            super().dragMoveEvent(event)