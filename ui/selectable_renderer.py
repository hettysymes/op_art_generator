from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QPen, QTransform
from PyQt5.QtWidgets import QGraphicsItem, QMenu, QAction
from PyQt5.QtSvg import QSvgRenderer

from ui.nodes.shape import get_node_from_shape
from ui.nodes.shape_datatypes import Group
from ui.nodes.transforms import Scale


class SelectableSvgElement(QGraphicsItem):
    """A custom graphics item that represents an SVG element and can be selected."""

    def __init__(self, element, parent_group: Group, renderer, parent):
        super().__init__()
        self.element = element
        self.renderer = renderer
        self.parent = parent
        self.is_hovered = False
        self.transform = QTransform()
        self.parent_group = parent_group

        # Store scale for debug
        self.scale = parent_group.transform_list.transforms[0] if parent_group.transform_list.transforms else None

        if self.scale:
            print(f"Scale for element {element.uid}: sx={self.scale.sx}, sy={self.scale.sy}")
            self.transform.scale(self.scale.sx, self.scale.sy)

        # Set flags for interaction - selectable but NOT movable
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        # Enable context menu events
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)

    def boundingRect(self):
        """Return the transformed bounding rectangle of the element."""
        # Get original bounds from renderer
        bounds = self.renderer.boundsOnElement(self.element.uid)
        print(f"Original bounds for {self.element.uid}: {bounds}")

        # Apply transform to bounds
        transformed_bounds = self.transform.mapRect(bounds)
        print(f"Transformed bounds for {self.element.uid}: {transformed_bounds}")

        # Add a small margin to ensure selection outline is visible
        return transformed_bounds.adjusted(-2, -2, 2, 2)

    def paint(self, painter, option, widget=None):
        """Paint the element in its original position."""
        # Save the painter state
        painter.save()

        # Apply the same transform to the painter that we applied to the bounding rect
        # This is critical - the painter needs to be transformed the same way
        painter.setTransform(self.transform, True)

        # Get the original bounds (untransformed)
        original_bounds = self.renderer.boundsOnElement(self.element.uid)

        try:
            # Render the SVG element (the transform is already applied to the painter)
            self.renderer.render(painter, self.element.uid)

            # Draw selection visual if selected (in original space before transform)
            if self.isSelected():
                # Reset transform for drawing selection indicator
                painter.resetTransform()
                painter.setPen(QPen(QColor(0, 0, 255, 180), 2, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(self.boundingRect().adjusted(2, 2, -2, -2))  # Use transformed bounds

            # Draw hover visual
            elif self.is_hovered:
                # Reset transform for drawing hover indicator
                painter.resetTransform()
                painter.setPen(QPen(QColor(0, 150, 0, 120), 2, Qt.DashLine))  # Reduced from 50 to 2
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(self.boundingRect().adjusted(2, 2, -2, -2))  # Use transformed bounds

        except Exception as e:
            print(f"Error rendering element {self.element.uid}: {e}")
            # Debug information
            painter.resetTransform()
            painter.setPen(QPen(Qt.red, 2))
            painter.drawRect(self.boundingRect())
            painter.drawText(self.boundingRect(), Qt.AlignCenter, f"Error: {str(e)}")

        # Restore painter state
        painter.restore()

    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        self.is_hovered = True
        self.setCursor(Qt.PointingHandCursor)
        print(f"Hover enter for {self.element.uid}")
        self.update()  # Trigger repaint to show hover highlight
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Remove highlight when not hovering."""
        self.is_hovered = False
        self.setCursor(Qt.ArrowCursor)
        print(f"Hover leave for {self.element.uid}")
        self.update()  # Trigger repaint to remove hover highlight
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            prev_selected = self.isSelected()
            self.setSelected(not prev_selected)
            print(f"Selection change for {self.element.uid}: {prev_selected} -> {self.isSelected()}")
            self.update()  # Ensure visual update
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
        print(f"Extracting element {self.element.uid} into node")
        # node = get_node_from_shape(self.element)
        # if node:
        #     self.parent.add_new_node(node)
        # else:
        #     print(f"Could not create node from element {self.element.uid}")