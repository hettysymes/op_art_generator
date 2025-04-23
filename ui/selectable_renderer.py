# The SelectableSvgElement class definition
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QGraphicsItem


class SelectableSvgElement(QGraphicsItem):
        """A custom graphics item that represents an SVG element and can be selected."""

        def __init__(self, element_id, renderer):
            super().__init__()
            self.element_id = element_id
            self.renderer = renderer

            # Set flags for interaction - selectable but NOT movable
            self.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self.setAcceptHoverEvents(True)

        def boundingRect(self):
            """Return the bounding rectangle of the element."""
            # Use element's bounding box within the full SVG
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
            """Handle selection."""
            if event.button() == Qt.LeftButton:
                self.setSelected(not self.isSelected())
            super().mousePressEvent(event)