from PyQt5.QtCore import Qt, QRectF, QTimer
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QGraphicsItem, QMenu, QAction

from ui.id_datatypes import PropKey


class SelectableSvgElement(QGraphicsItem):
    """A custom graphics item that represents an SVG element and can be selected."""

    def __init__(self, element_id, parent_group, renderer, node_item):
        super().__init__()
        self.element_id = element_id
        self.parent_group = parent_group
        self.renderer = renderer
        self.node_item = node_item

        # Set flags for interaction - selectable but NOT movable
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        # Enable context menu events
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)

    def boundingRect(self):
        """Return the bounding rectangle of the element."""
        rect = self.renderer.boundsOnElement(self.element_id)
        width, height = self.node_item.node_state.svg_size
        return QRectF(rect.x() * width, rect.y() * height,
                      max(rect.width() * width, 1), max(rect.height() * height, 1))  # Minimum width/height of 1

    def paint(self, painter, option, widget=None):
        """Paint the element in its original position."""
        # Skip rendering the SVG element itself

        # Draw selection visual if selected
        if self.isSelected():
            painter.save()
            painter.setPen(QPen(QColor(0, 0, 255, 180), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())
            painter.restore()

    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        self.setCursor(Qt.PointingHandCursor)
        super().hoverEnterEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            self.setSelected(not self.isSelected())
            super().mousePressEvent(event)
        elif event.button() == Qt.RightButton:
            # Only show context menu if the item is selected
            if self.isSelected():
                self.showContextMenu(event)
            super().mousePressEvent(event)

    def showContextMenu(self, event):
        """Show a context menu for the selected element."""
        # Create the context menu
        menu = QMenu()

        # Add "Extract into port" action
        extract_action = QAction("Extract into port", menu)
        extract_action.triggered.connect(self.extractElement)
        menu.addAction(extract_action)

        # Get the global position for the menu
        scene_pos = event.scenePos()
        view = self.scene().views()[0]  # Assuming there's at least one view
        global_pos = view.mapToGlobal(view.mapFromScene(scene_pos))

        event.accept()
        # Show the menu
        menu.exec_(global_pos)

    def extractElement(self):
        """Handle the 'Extract into node' action."""
        prop_key: PropKey = self.node_item.node_manager.extract_element(self.node_item.uid, self.parent_group,
                                                                        self.element_id)
        self.scene().skip_next_context_menu = True
        # Defer deletion of this element (from updating svg image) until after element extraction
        QTimer.singleShot(0, lambda: self.scene().extract_element(self.node_item, prop_key))
