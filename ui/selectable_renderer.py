from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QGraphicsItem, QMenu, QAction

from ui.nodes.shape import get_node_from_shape


class SelectableSvgElement(QGraphicsItem):
    """A custom graphics item that represents an SVG element and can be selected."""

    def __init__(self, element_id, renderer, selectable_shapes, parent):
        super().__init__()
        self.element_id = element_id
        self.renderer = renderer
        self.selectable_shapes = selectable_shapes
        self.parent = parent

        # Set flags for interaction - selectable but NOT movable
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        # Enable context menu events
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)

    def boundingRect(self):
        """Return the bounding rectangle of the element."""
        return self.renderer.boundsOnElement(self.element_id)

    def paint(self, painter, option, widget=None):
        """Paint the element in its original position."""
        # Render only this element using the renderer
        self.renderer.render(painter, self.element_id, self.boundingRect())

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
        for s in self.selectable_shapes:
            if str(s.shape_id) == self.element_id:
                node = get_node_from_shape(s)
                if node:
                    self.parent.add_new_node(node)
