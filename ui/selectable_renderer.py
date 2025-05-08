from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QGraphicsItem, QMenu, QAction
from ui_old.nodes.immutable_elem_node import get_node_from_element


class SelectableSvgElement(QGraphicsItem):
    """A custom graphics item that represents an SVG element and can be selected."""

    def __init__(self, element_id, backend_child_elem, renderer, parent_node_item):
        super().__init__()
        self.element_id = element_id
        self.backend_child_elem = backend_child_elem
        self.renderer = renderer
        self.parent_node_item = parent_node_item

        # Set flags for interaction - selectable but NOT movable
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        # Enable context menu events
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)

    def boundingRect(self):
        """Return the bounding rectangle of the element."""
        rect = self.renderer.boundsOnElement(self.element_id)
        width, height = self.parent_node_item.backend.svg_width, self.parent_node_item.backend.svg_height
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

        # Add "Extract into node" action
        extract_action = QAction("Extract into node", menu)
        extract_action.triggered.connect(self.extractIntoNode)
        menu.addAction(extract_action)

        # Get the global position for the menu
        scene_pos = event.scenePos()
        view = self.scene().views()[0]  # Assuming there's at least one view
        global_pos = view.mapToGlobal(view.mapFromScene(scene_pos))

        # Show the menu
        menu.exec_(global_pos)

    def extractIntoNode(self):
        """Handle the 'Extract into node' action."""
        # node = get_node_from_element(self.backend_child_elem)
        # self.parent_node_item.add_new_node(node)
        pass
