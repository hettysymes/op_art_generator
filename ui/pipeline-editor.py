import ast
import copy
import math
import os
import pickle
import shutil
import sys
import tempfile
import uuid

from PyQt5.QtCore import QLineF, pyqtSignal, QObject, QRectF, QModelIndex, QAbstractTableModel, QTimer, QPoint, QRect, \
    QEvent
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QFont, QFontMetricsF, QDoubleValidator, QDropEvent, QIcon, QTextDocument
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
                             QGraphicsLineItem, QMenu, QAction, QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QSpinBox, QDoubleSpinBox, QComboBox, QPushButton, QCheckBox,
                             QDialogButtonBox, QGroupBox, QTableWidget, QTableWidgetItem, QWidget,
                             QHBoxLayout, QFileDialog, QHeaderView, QStyledItemDelegate, QColorDialog,
                             QAbstractItemView, QStyleOptionViewItem, QGraphicsItemGroup, QGraphicsTextItem, QLabel,
                             QToolTip)
from PyQt5.QtWidgets import QGraphicsPathItem
from PyQt5.QtXml import QDomDocument

from ui.colour_prop_widget import ColorPropertyWidget
from ui.nodes.shape import ElemRef
from ui.port_defs import PT_Element, PT_Grid, PT_Function, PT_Warp, PT_ValueList
from ui.reorderable_table_widget import ReorderableTableWidget
from ui.scene import Scene, NodeState, PortState, EdgeState
from ui.nodes.all_nodes import node_classes
from ui.nodes.nodes import CombinationNode, UnitNode
from ui.selectable_renderer import SelectableSvgElement


class ConnectionSignals(QObject):
    """Signals for the connection process"""
    connectionStarted = pyqtSignal(object)  # Emits the source port
    connectionMade = pyqtSignal(object, object)  # Emits source and destination ports


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QPen, QColor
from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer


class ResizeHandle(QGraphicsRectItem):
    """Resize handle for NodeItem"""

    def __init__(self, parent, position, size=8):
        super().__init__(0, 0, size, size)
        self.setParentItem(parent)
        self.position = position  # 'bottomright', 'bottomleft', etc.
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setBrush(QBrush(QColor(50, 50, 50)))
        self.setPen(QPen(Qt.black, 1))
        self.setCursor(Qt.SizeFDiagCursor)  # Diagonal resize cursor
        self.setZValue(3)  # Above the node
        self.update_position()

    def update_position(self):
        """Update handle position based on parent node size"""
        parent_rect = self.parentItem().rect()
        if self.position == 'bottomright':
            self.setPos(parent_rect.width() - self.rect().width(),
                        parent_rect.height() - self.rect().height())
        elif self.position == 'bottomleft':
            self.setPos(0, parent_rect.height() - self.rect().height())
        elif self.position == 'topright':
            self.setPos(parent_rect.width() - self.rect().width(), 0)
        elif self.position == 'topleft':
            self.setPos(0, 0)

    def mouseMoveEvent(self, event):
        # Override to handle resize logic
        parent = self.parentItem()
        orig_pos = event.lastScenePos()
        new_pos = event.scenePos()
        dx = new_pos.x() - orig_pos.x()
        dy = new_pos.y() - orig_pos.y()

        # Get current dimensions
        rect = parent.rect()

        # Minimum size constraints
        min_width = 80
        min_height = 60

        if self.position == 'bottomright':
            new_width = max(min_width, rect.width() + dx)
            new_height = max(min_height, rect.height() + dy)
            parent.resize(new_width, new_height)

        # You can add other positions as needed
        # Skip default implementation to prevent the handle itself from moving
        event.accept()


class NodeItem(QGraphicsRectItem):
    """Represents a node/box in the pipeline"""

    TITLE_HEIGHT = 20
    MARGIN_X = 5
    MARGIN_Y = 10
    LABEL_FONT = QFont("Arial", 8)

    def __init__(self, node_state: NodeState):
        self.svg_items = None
        self.svg_item = None
        self.left_max_width = NodeItem.MARGIN_Y - NodeItem.MARGIN_X
        self.right_max_width = NodeItem.MARGIN_Y - NodeItem.MARGIN_X
        if node_state.node.resizable():
            width, height = self.node_size_from_svg_size(node_state.svg_width, node_state.svg_height)
        else:
            # Assumes it's a canvas node
            width, height = self.node_size_from_svg_size(node_state.node.prop_vals.get('width', 150),
                                                         node_state.node.prop_vals.get('height', 150))
        super().__init__(0, 0, width, height)
        self.backend = node_state
        self.uid = node_state.uid
        self.setPos(node_state.x, node_state.y)
        self.setZValue(1)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.setBrush(QBrush(QColor(220, 230, 250)))
        self.setPen(QPen(Qt.black, 2))
        self.node = self.backend.node

        self._help_icon_rect = QRectF()
        self._help_hover_timer = QTimer()
        self._help_hover_timer.setSingleShot(True)
        self._help_hover_timer.timeout.connect(self._showHelpTooltip)
        self._help_tooltip = None
        self.setAcceptHoverEvents(True)

        # Set the help text for this node
        self._help_text = f"{self.node.name()} Help:\n{self.node.description()}"

        self.resize_handle = None

        if self.node.resizable():
            # Add resize handle
            self.resize_handle = ResizeHandle(self, 'bottomright')

    def hoverMoveEvent(self, event):
        if self._help_icon_rect.contains(event.pos()):
            if not self._help_hover_timer.isActive():
                # Start the timer when hovering over the help icon
                self._help_hover_timer.start(500)  # 500ms delay before showing tooltip
        else:
            # Stop the timer if the mouse moves away from the help icon
            self._help_hover_timer.stop()
            if self._help_tooltip and self._help_tooltip.isVisible():
                self._help_tooltip.hide()

        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event):
        # Stop the timer when the mouse leaves the item
        self._help_hover_timer.stop()
        if self._help_tooltip and self._help_tooltip.isVisible():
            self._help_tooltip.hide()

        super().hoverLeaveEvent(event)

    def _showHelpTooltip(self):
        # Create a tooltip if it doesn't exist
        if not self._help_tooltip:
            # Split text into title and content parts
            parts = self._help_text.split('\n', 1)
            title = parts[0]
            body = parts[1] if len(parts) > 1 else ""

            # Format the body text with paragraph breaks
            formatted_body = body.replace('\n', '<br>')

            # Create the tooltip HTML
            tooltip_html = f"""
            <div style='
                background-color: #ffcccc; 
                color: #333333; 
                padding: 12px;  /* Extra padding around the entire tooltip */
                border-radius: 12px; 
                width: 200px; 
                position: relative;
                word-wrap: break-word;
                border: 1px solid #d0d0d0;  /* Slightly darker border */
            '>
                <div style='
                    font-weight: bold;
                    text-align: center;
                    padding-bottom: 6px;
                    background-color: #ffcccc;  /* Explicitly set background color */
                    border-bottom: 1px solid rgba(0,0,0,0.2);
                '>{title}</div>
            
                <div style='background-color: #ffcccc; padding-top: 6px;'>{formatted_body}</div>
            
                <div style='
                    position: absolute;
                    bottom: -10px;
                    left: 50%;
                    margin-left: -10px;
                    width: 0;
                    height: 0;
                    border-left: 10px solid transparent;
                    border-right: 10px solid transparent;
                    border-top: 10px solid #ffcccc;  /* Match the tooltip color */
                '></div>
            </div>

            """

            self._help_tooltip = QGraphicsTextItem(self)
            self._help_tooltip.setDefaultTextColor(QColor("#333333"))
            self._help_tooltip.setHtml(tooltip_html)
            self._help_tooltip.setZValue(100)  # Make sure it's on top
            self._help_tooltip.setTextWidth(224)  # Account for padding (200px + 24px padding)

        # Position the tooltip above the help icon
        tooltip_rect = self._help_tooltip.boundingRect()

        # Center above the icon with some spacing
        tooltip_pos = QPointF(
            self._help_icon_rect.center().x() - tooltip_rect.width() / 2,
            self._help_icon_rect.top() - tooltip_rect.height()
        )
        self._help_tooltip.setPos(tooltip_pos)
        self._help_tooltip.show()

    def resize(self, width, height):
        """Resize the node to the specified dimensions"""
        self.setRect(0, 0, width, height)
        if self.resize_handle:
            self.resize_handle.update_position()
        self.update_vis_image()

        # Update port positions to match the new dimensions
        self.update_port_edge_positions()

        # Update backend state
        self.backend.svg_width, self.backend.svg_height = self.svg_size_from_node_size(width, height)

    def node_size_from_svg_size(self, svg_w, svg_h):
        return svg_w + self.left_max_width + self.right_max_width + 2 * NodeItem.MARGIN_X, svg_h + 2 * NodeItem.MARGIN_Y + NodeItem.TITLE_HEIGHT

    def svg_size_from_node_size(self, rect_w, rect_h):
        return rect_w - self.left_max_width - self.right_max_width - 2 * NodeItem.MARGIN_X, rect_h - 2 * NodeItem.MARGIN_Y - NodeItem.TITLE_HEIGHT

    def get_svg_path(self):
        wh_ratio = self.backend.svg_width / self.backend.svg_height if self.backend.svg_height > 0 else 1
        svg_path, exception = self.update_node().get_svg_path(self.scene().temp_dir, self.backend.svg_height, wh_ratio)
        return svg_path

    def update_vis_image(self):
        """Add an SVG image to the node that scales with node size and has selectable elements"""
        svg_path, selectable_shapes = self.get_svg_path()

        # Remove existing SVG items if necessary
        if self.svg_items:
            for item in self.svg_items:
                scene = self.scene()
                if scene and item in scene.items():
                    scene.removeItem(item)
        self.svg_items = []

        if self.svg_item:
            scene = self.scene()
            if scene and self.svg_item in scene.items():
                scene.removeItem(self.svg_item)

        # Create SVG renderer
        svg_renderer = QSvgRenderer(svg_path)

        # Get SVG dimensions - will be used for viewport clipping
        svg_size = svg_renderer.defaultSize()

        # Base position for all SVG elements
        svg_pos_x = self.left_max_width + NodeItem.MARGIN_X
        svg_pos_y = NodeItem.TITLE_HEIGHT + NodeItem.MARGIN_Y

        # Check file extension
        if not self.node.selectable():
            # Handle matplotlib or non-selectable SVG - use standard QGraphicsSvgItem
            self.svg_item = QGraphicsSvgItem(svg_path)

            # Apply position
            self.svg_item.setParentItem(self)
            self.svg_item.setPos(svg_pos_x, svg_pos_y)
            self.svg_item.setZValue(2)

        else:
            # Create a viewport SVG item that will act as both a container and clipper
            viewport_svg = QGraphicsSvgItem(svg_path)
            viewport_svg.setParentItem(self)
            viewport_svg.setPos(svg_pos_x, svg_pos_y)
            viewport_svg.setZValue(1)  # Set below selectable items
            self.svg_items.append(viewport_svg)

            # Set clip path based on SVG's viewBox
            clip_path = QPainterPath()
            clip_path.addRect(QRectF(0, 0, svg_size.width(), svg_size.height()))
            viewport_svg.setFlag(QGraphicsItem.ItemClipsChildrenToShape, True)

            # Load the SVG file as XML
            dom_document = QDomDocument()
            with open(svg_path, 'r') as file:
                content = file.read()
                dom_document.setContent(content)

            # Process SVG elements to make them selectable
            def process_element(element, inp_selectable_shapes):
                # SVG elements we're interested in making selectable
                selectable_types = ['path', 'rect', 'circle', 'ellipse', 'polygon', 'polyline', 'line']

                # Process all child elements
                child = element.firstChild()
                while not child.isNull():
                    if child.isElement():
                        element_node = child.toElement()
                        tag_name = element_node.tagName()
                        element_id = element_node.attribute('id')

                        # Only process elements with IDs
                        if element_id:
                            if tag_name in selectable_types:
                                # Create a selectable item for this element
                                selectable_item = SelectableSvgElement(element_id, svg_renderer, inp_selectable_shapes,
                                                                       self)
                                selectable_item.setParentItem(viewport_svg)  # Make it a child of the viewport
                                selectable_item.setPos(0, 0)  # Position relative to viewport
                                selectable_item.setZValue(3)  # Ensure it's above the viewport
                                self.svg_items.append(selectable_item)

                            # For groups, process children
                            if tag_name == 'g' or tag_name == 'svg':
                                process_element(element_node, inp_selectable_shapes)

                    child = child.nextSibling()

            # Start processing from root element
            root = dom_document.documentElement()
            process_element(root, selectable_shapes)

    def add_new_node(self, node):
        return self.scene().add_new_node(self.pos() + QPointF(10, 10), node)

    def get_input_node_items(self):
        input_nodes = []
        for input_port_id in self.backend.input_port_ids:
            input_port: PortItem = self.scene().scene.get(input_port_id)
            if len(input_port.backend.edge_ids) > 0:
                for edge_id in input_port.backend.edge_ids:
                    edge: EdgeItem = self.scene().scene.get(edge_id)
                    input_nodes.append(edge.source_port.parentItem())
            else:
                input_nodes.append(None)
        return input_nodes

    def get_output_node_items(self):
        output_nodes = []
        for output_port_id in self.backend.output_port_ids:
            output_port: PortItem = self.scene().scene.get(output_port_id)
            for edge_id in output_port.backend.edge_ids:  # Each output port can have 1+ edges
                edge: EdgeItem = self.scene().scene.get(edge_id)
                output_nodes.append(edge.dest_port.parentItem())
        return output_nodes

    def update_visualisations(self):
        self.update_vis_image()
        for output_node in self.get_output_node_items():
            output_node.update_visualisations()

    def update_node(self):
        input_node_items = self.get_input_node_items()
        if len(input_node_items) == 0:
            self.node.input_nodes = []
        else:
            extracted_nodes = []
            for node_item in input_node_items:
                if node_item:
                    extracted_nodes.append(node_item.node)
                else:
                    extracted_nodes.append(UnitNode(None, None, None))
            self.node.input_nodes = extracted_nodes
        return self.node

    def create_ports(self):
        # Create input ports (left side)
        input_count = len(self.node.in_port_defs())
        for i, port_def in enumerate(self.node.in_port_defs()):
            y_offset = (i + 1) * self.rect().height() / (input_count + 1)
            state_id = uuid.uuid4()
            input_port = PortItem(PortState(state_id,
                                            -10, y_offset,
                                            self.uid,
                                            True,
                                            [], port_def), self)
            self.backend.input_port_ids.append(state_id)
            self.scene().scene.add(input_port)

        # Create output ports (right side)
        output_count = len(self.node.out_port_defs())
        for i, port_def in enumerate(self.node.out_port_defs()):
            y_offset = (i + 1) * self.rect().height() / (output_count + 1)
            state_id = uuid.uuid4()
            output_port = PortItem(PortState(state_id,
                                             self.rect().width() + 10, y_offset,
                                             self.uid,
                                             False,
                                             [], port_def), self)
            self.backend.output_port_ids.append(state_id)
            self.scene().scene.add(output_port)

        self.update_label_containers()

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)

        painter.setFont(QFont("Arial", 8))
        painter.setPen(QColor("grey"))
        id_rect = self.rect().adjusted(10, 10, 0, 0)  # Shift the top edge down
        painter.drawText(id_rect, Qt.AlignTop | Qt.AlignLeft, f"id: #{self.node.node_id.hex[:3]}")

        # Draw node title
        painter.setFont(QFont("Arial", 10))
        painter.setPen(QColor("black"))
        title_rect = self.rect().adjusted(0, 10, 0, 0)  # Shift the top edge down
        painter.drawText(title_rect, Qt.AlignTop | Qt.AlignHCenter, self.node.name())

        # Draw the help icon (question mark) in the top-right corner
        help_icon_size = 16
        margin = 5
        help_rect = QRectF(
            self.rect().right() - help_icon_size - margin,
            self.rect().top() + margin,
            help_icon_size,
            help_icon_size
        )

        # Draw the circle background
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(QColor(240, 240, 240))
        painter.drawEllipse(help_rect)

        # Draw the question mark
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.setPen(QColor(80, 80, 80))
        painter.drawText(help_rect, Qt.AlignCenter, "?")

        # Store the help icon rect for hit testing in hover events
        self._help_icon_rect = help_rect

        # Draw port labels if there are multiple
        painter.setFont(NodeItem.LABEL_FONT)
        font_metrics = QFontMetricsF(NodeItem.LABEL_FONT)
        text_height = font_metrics.height()

        # Draw input port labels (left side)
        for port_id in self.backend.input_port_ids:
            port = self.scene().scene.get(port_id)
            text = port.backend.port_def.name

            # Calculate port's position in this item's coordinate system
            port_y = port.y()  # Since port is a child of this item

            # Center text vertically with port
            text_rect = QRectF(
                NodeItem.MARGIN_X,  # Left padding
                port_y - (text_height / 2),  # Vertical center alignment
                self.left_max_width,  # Width minus padding
                text_height  # Font height
            )

            # Draw the text
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, text)

        # Draw output port labels (right side)
        rect = self.rect()
        for port_id in self.backend.output_port_ids:
            port = self.scene().scene.get(port_id)
            text = port.backend.port_def.name

            # Calculate port's position in this item's coordinate system
            port_y = port.y()  # Since port is a child of this item

            # Center text vertically with port
            text_rect = QRectF(
                rect.width() - self.right_max_width - NodeItem.MARGIN_X,  # Right-aligned
                port_y - (text_height / 2),  # Vertical center alignment
                self.right_max_width,  # Width minus padding
                text_height  # Font height
            )

            # Draw the text
            painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, text)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # Update connected edges when node moves
            for port_id in self.backend.input_port_ids + self.backend.output_port_ids:
                port: PortItem = self.scene().scene.get(port_id)
                for edge_id in port.backend.edge_ids:
                    edge: EdgeItem = self.scene().scene.get(edge_id)
                    edge.update_position()
        elif change == QGraphicsItem.ItemPositionHasChanged:
            self.backend.x = self.pos().x()
            self.backend.y = self.pos().y()

        return super().itemChange(change, value)

    def update_port_edge_positions(self):
        """Update the positions of all ports based on current node dimensions"""
        # Update input ports (left side)
        input_count = len(self.backend.input_port_ids)
        for i, input_port_id in enumerate(self.backend.input_port_ids):
            input_port: PortItem = self.scene().scene.get(input_port_id)
            y_offset = (i + 1) * self.rect().height() / (input_count + 1)
            input_port.backend.x = -10  # Keep x position constant
            input_port.backend.y = y_offset
            input_port.setPos(input_port.backend.x, input_port.backend.y)

            # Update any connections to this port
            input_port.update_edge_positions()

        # Update output ports (right side)
        output_count = len(self.backend.output_port_ids)
        for i, output_port_id in enumerate(self.backend.output_port_ids):
            output_port = self.scene().scene.get(output_port_id)
            y_offset = (i + 1) * self.rect().height() / (output_count + 1)
            output_port.backend.x = self.rect().width() + 10
            output_port.backend.y = y_offset
            output_port.setPos(output_port.backend.x, output_port.backend.y)

            # Update any connections to this port
            output_port.update_edge_positions()

    def update_label_containers(self):
        # Calculate the maximum width needed for each side
        font_metrics = QFontMetricsF(NodeItem.LABEL_FONT)
        self.left_max_width = NodeItem.MARGIN_Y - NodeItem.MARGIN_X
        self.right_max_width = NodeItem.MARGIN_Y - NodeItem.MARGIN_X

        # Calculate max width for input port labels
        for port_id in self.backend.input_port_ids:
            port = self.scene().scene.get(port_id)
            text = port.backend.port_def.name
            width = font_metrics.horizontalAdvance(text)
            self.left_max_width = max(self.left_max_width, width)

        # Calculate max width for output port labels
        for port_id in self.backend.output_port_ids:
            port = self.scene().scene.get(port_id)
            text = port.backend.port_def.name
            width = font_metrics.horizontalAdvance(text)
            self.right_max_width = max(self.right_max_width, width)

        width, height = self.node_size_from_svg_size(self.backend.svg_width, self.backend.svg_height)
        self.resize(width, height)


class PortItem(QGraphicsPathItem):
    """Represents connection points on nodes with shapes based on port_type"""

    def __init__(self, port_state: PortState, parent: NodeItem):
        super().__init__(parent)
        self.backend = port_state
        self.uid = port_state.uid
        self.size = 12  # Base size for the port

        # Create shape based on port_type
        self.create_shape_for_port_type()

        # Position the port
        self.setPos(self.backend.x, self.backend.y)
        self.setZValue(1)

        # Make port interactive
        self.setAcceptHoverEvents(True)

        # Set appearance based on input/output status
        if self.backend.is_input:
            self.setBrush(QBrush(QColor(100, 100, 100)))
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setBrush(QBrush(QColor(50, 150, 50)))
            self.setCursor(Qt.CrossCursor)

        self.setPen(QPen(Qt.black, 1))

    def create_shape_for_port_type(self):
        path = QPainterPath()
        half_size = self.size / 2
        port_type = self.backend.port_def.port_type
        if issubclass(port_type, PT_Element):
            # Circle for number type
            path.addEllipse(-half_size, -half_size, self.size, self.size)
        elif issubclass(port_type, PT_Grid):
            # Rounded rectangle for string type
            path.addRoundedRect(-half_size, -half_size, self.size, self.size, 3, 3)
        elif issubclass(port_type, PT_Function):
            # Diamond for boolean type
            points = [
                QPointF(0, -half_size),  # Top
                QPointF(half_size, 0),  # Right
                QPointF(0, half_size),  # Bottom
                QPointF(-half_size, 0)  # Left
            ]
            path.moveTo(points[0])
            for i in range(1, 4):
                path.lineTo(points[i])
            path.closeSubpath()

        elif issubclass(port_type, PT_Warp):
            # Square for array type
            path.addRect(-half_size, -half_size, self.size, self.size)

        elif issubclass(port_type, PT_ValueList):
            # Hexagon for object type
            points = []
            for i in range(6):
                angle = i * (360 / 6) * (3.14159 / 180)
                points.append(QPointF(half_size * 0.9 * math.cos(angle),
                                      half_size * 0.9 * math.sin(angle)))

            path.moveTo(points[0])
            for i in range(1, 6):
                path.lineTo(points[i])
            path.closeSubpath()

        else:
            # Default to triangle for other types
            points = [
                QPointF(0, -half_size),  # Top
                QPointF(half_size * 0.866, half_size / 2),  # Bottom right
                QPointF(-half_size * 0.866, half_size / 2)  # Bottom left
            ]
            path.moveTo(points[0])
            path.lineTo(points[1])
            path.lineTo(points[2])
            path.closeSubpath()

        self.setPath(path)

    def get_center_scene_pos(self):
        # For a path item, we need to calculate the center differently
        return self.mapToScene(self.boundingRect().center())

    # The rest of your methods remain the same
    def add_edge(self, edge_id):
        self.backend.edge_ids.append(edge_id)

    def remove_edge(self, edge_id):
        if edge_id in self.backend.edge_ids:
            self.backend.edge_ids.remove(edge_id)

    def hoverEnterEvent(self, event):
        self.setPen(QPen(Qt.red, 2))
        if not self.backend.is_input:
            self.setCursor(Qt.CrossCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPen(QPen(Qt.black, 1))
        super().hoverLeaveEvent(event)

    def update_edge_positions(self):
        for edge_id in self.backend.edge_ids:
            edge = self.scene().scene.get(edge_id)
            edge.update_position()


class EdgeItem(QGraphicsLineItem):
    """Represents connections between nodes"""

    def __init__(self, edge_state: EdgeState):
        super().__init__()
        self.source_port = None
        self.dest_port = None
        self.backend = edge_state
        self.uid = edge_state.uid
        self.setZValue(0)

        # Thicker line with rounded caps for better appearance
        self.setPen(QPen(Qt.black, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.setFlag(QGraphicsItem.ItemIsSelectable)

    def set_ports(self):
        self.source_port = self.scene().scene.get(self.backend.src_port_id)
        self.dest_port = self.scene().scene.get(self.backend.dst_port_id)
        self.update_position()

    def update_position(self):
        if self.source_port and self.dest_port:
            source_pos = self.source_port.get_center_scene_pos()
            dest_pos = self.dest_port.get_center_scene_pos()
            self.setLine(QLineF(source_pos, dest_pos))


class HelpIconLabel(QPushButton):
    def __init__(self, description, max_width=300, parent=None):
        super().__init__(parent)

        # Set up the help icon with "?" text
        self.setText("?")
        self.setFixedSize(16, 16)

        # Style the button to look like a help icon
        self.setStyleSheet("""
            QPushButton {
                background-color: #b0b0b0;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #8a8a8a;
            }
        """)

        # Apply word-wrapped tooltip using HTML
        width_px = str(max_width) + "px"
        wrapped_text = f"<div style='max-width: {width_px}; white-space: normal;'>{description}</div>"
        self.setToolTip(wrapped_text)

        # Remove focus outline
        self.setFocusPolicy(Qt.NoFocus)

class NodePropertiesDialog(QDialog):
    """Dialog for editing node properties"""

    def __init__(self, node_item, parent=None):
        super().__init__(parent)
        self.node_item: NodeItem = node_item
        self.setWindowTitle(f"Properties: {node_item.node.name()}")
        self.setMinimumWidth(400)

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create form layout for properties
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.property_widgets = {}

        # Add custom properties based on node type
        if node_item.node.prop_type_list():
            props_group = QGroupBox("Node Properties")
            props_layout = QFormLayout()
            props_group.setLayout(props_layout)

            # Now modify your existing code to use this function
            for prop in node_item.node.prop_type_list():
                if prop.prop_type != "hidden":
                    widget = self.create_property_widget(prop, node_item.node.prop_vals.get(prop.key_name,
                                                                                            prop.default_value), node_item)

                    # Create the row with label and help icon
                    label_container, widget_container = self.create_property_row(prop, widget)
                    props_layout.addRow(label_container, widget_container)
                    self.property_widgets[prop.key_name] = widget

            main_layout.addWidget(props_group)

        # Create buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

    def create_property_row(self, prop, widget):
        """Create a row with property label and a help icon to the right of the widget"""

        # Create a container widget for the label
        label_container = QWidget()
        label_layout = QHBoxLayout(label_container)
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setSpacing(4)  # Small spacing between elements

        # Create the label
        add_text = ":" if prop.auto_format else ""
        label = QLabel(prop.display_name + add_text)
        label_layout.addWidget(label)
        label_layout.addStretch()

        # Create a container for the widget and help icon
        widget_container = QWidget()
        widget_layout = QHBoxLayout(widget_container)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSpacing(4)  # Small spacing between widget and icon

        # Add the widget first
        widget_layout.addWidget(widget)

        # Add the help icon after the widget (on the right)
        if prop.description:
            help_icon = HelpIconLabel(prop.description, max_width=300)  # Set maximum width for tooltip
            widget_layout.addWidget(help_icon)

        return label_container, widget_container

    def create_property_widget(self, prop, current_value, node_item):
        """Create an appropriate widget for the property type"""
        if prop.prop_type == "int":
            widget = QSpinBox()
            if prop.min_value is not None:
                widget.setMinimum(prop.min_value)
            if prop.max_value is not None:
                widget.setMaximum(prop.max_value)
            widget.setValue(current_value or 0)

        elif prop.prop_type == "float":
            widget = QDoubleSpinBox()
            widget.setMinimum(prop.min_value if prop.min_value is not None else -999999.0)
            if prop.max_value is not None:
                widget.setMaximum(prop.max_value)
            widget.setValue(current_value or 0.0)

        elif prop.prop_type == "bool":
            widget = QCheckBox()
            widget.setChecked(current_value or False)

        elif prop.prop_type == "prop_enum":
            widget = QComboBox()
            input_node_props = node_item.node.input_nodes[1].prop_type_list()
            # Populate the widget
            widget.addItem("[none]", userData=None)
            for inp_prop in input_node_props:
                widget.addItem(inp_prop.display_name, userData=inp_prop.key_name)
            # Set the current value if available
            if current_value is not None:
                # Find the index where the key_name matches current_value
                index = next((i for i in range(widget.count())
                              if widget.itemData(i) == current_value), 0)
                widget.setCurrentIndex(index)

        elif prop.prop_type == "selector_enum":
            widget = QComboBox()
            input_prop_compute = node_item.node.input_nodes[0].compute()
            # Populate the widget
            widget.addItem("[none]", userData=None)
            if input_prop_compute:
                for i in range(len(input_prop_compute)):
                    widget.addItem(str(i+1), userData=i)
            # Set the current value if available
            if current_value is not None:
                # Find the index where the key_name matches current_value
                index = next((i for i in range(widget.count())
                              if widget.itemData(i) == current_value), 0)
                widget.setCurrentIndex(index)

        elif prop.prop_type == "point_table":
            def add_point_item(point, row=None, table=None):
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                item.setData(Qt.UserRole, point)
                if isinstance(point, ElemRef):
                    points = point.get_base_points()
                    start_x, start_y = points[0]
                    stop_x, stop_y = points[-1]
                    arrow = '←' if point.reversed else '→'
                    item.setText(
                        f"{point.node_type} (id: #{point.node_id.hex[:3]})\n({start_x:.2f}, {start_y:.2f}) {arrow} ({stop_x:.2f}, {stop_y:.2f})")
                    item.setBackground(QColor(237, 130, 157))
                else:
                    x, y = point
                    item.setText(f"({x:.2f}, {y:.2f})")
                if (row is not None) and (table is not None):
                    table.setItem(row, 0, item)
                return item

            # Create our custom table widget
            table = ReorderableTableWidget(add_point_item)

            # Set up the basic table structure with single column
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["Coordinate Points (X, Y)"])

            # Custom delegate to ensure text alignment is centered
            class CenteredItemDelegate(QStyledItemDelegate):
                def initStyleOption(self, option, index):
                    super().initStyleOption(option, index)
                    option.displayAlignment = Qt.AlignCenter

            # Apply the delegate to the table
            centered_delegate = CenteredItemDelegate()
            table.setItemDelegate(centered_delegate)
            table.verticalHeader().setDefaultSectionSize(40)
            table.setWordWrap(True)

            # Populate with current data
            points_data = current_value or prop.default_value or []
            table.setRowCount(len(points_data))
            for row, point in enumerate(points_data):
                add_point_item(point, row, table)

            # Add button to add points
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(0, 0, 0, 0)

            add_button = QPushButton("+")

            def show_point_dialog(initial_x=0.0, initial_y=0.0):
                dialog = QDialog()
                dialog.setWindowTitle("Coordinate Point")
                dialog_layout = QVBoxLayout(dialog)

                form_layout = QFormLayout()

                x_input = QDoubleSpinBox()
                x_input.setRange(0, 1)  # Adjust the range as needed
                x_input.setDecimals(2)
                x_input.setValue(initial_x)

                y_input = QDoubleSpinBox()
                y_input.setRange(0, 1)
                y_input.setDecimals(2)
                y_input.setValue(initial_y)

                form_layout.addRow("X:", x_input)
                form_layout.addRow("Y:", y_input)
                dialog_layout.addLayout(form_layout)

                button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                button_box.accepted.connect(dialog.accept)
                button_box.rejected.connect(dialog.reject)
                dialog_layout.addWidget(button_box)

                if dialog.exec_():
                    try:
                        return x_input.value(), y_input.value()
                    except ValueError:
                        return None
                return None

            # Add point dialog function
            def add_point():
                result = show_point_dialog()
                if result:
                    row = table.rowCount()
                    table.setRowCount(row + 1)
                    add_point_item(result, row, table)

            add_button.clicked.connect(add_point)
            button_layout.addWidget(add_button)

            # Set up context menu for deletion and editing
            def show_context_menu(position):
                row = table.rowAt(position.y())

                if row >= 0:
                    item = table.item(row, 0)
                    item_data = item.data(Qt.UserRole)
                    menu = QMenu()
                    if not isinstance(item_data, ElemRef):
                        edit_action = menu.addAction("Edit")
                        delete_action = menu.addAction("Delete")

                        action = menu.exec_(table.viewport().mapToGlobal(position))

                        if action == delete_action:
                            table.removeRow(row)

                        elif action == edit_action:
                            x_val, y_val = item_data
                            result = show_point_dialog(x_val, y_val)

                            if result:
                                add_point_item(result, row, table)
                    else:
                        reverse_action = menu.addAction("Reverse points")
                        action = menu.exec_(table.viewport().mapToGlobal(position))
                        if action == reverse_action:
                            item_data.reverse()
                            add_point_item(item_data, row, table)

            table.setContextMenuPolicy(Qt.CustomContextMenu)
            table.customContextMenuRequested.connect(show_context_menu)

            # Create a container for the table and button
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.addWidget(table)
            layout.addWidget(button_widget)

            # Function to get the current value from the table
            def get_table_value():
                points = []
                for row in range(table.rowCount()):
                    item = table.item(row, 0)
                    if item:
                        # Retrieve the actual tuple data stored in UserRole
                        point_data = item.data(Qt.UserRole)
                        if point_data:
                            points.append(point_data)
                return points

            # Store both the getter function and the reference to the table with the container
            container.get_value = get_table_value
            container.table_widget = table  # Store a reference to the actual table

            widget = container
        elif prop.prop_type == "elem_table":

            def add_elem_item(elem_ref, row=None, table=None):
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                item.setData(Qt.UserRole, elem_ref)
                item.setText(f"{elem_ref.node_type} (id: #{elem_ref.node_id.hex[:3]})")
                if (row is not None) and (table is not None):
                    table.setItem(row, 0, item)
                return item

            # Create our custom table widget
            table = ReorderableTableWidget(add_elem_item)

            # Set up the basic table structure with single column
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["Drawing"])

            # Custom delegate to ensure text alignment is centered
            class CenteredItemDelegate(QStyledItemDelegate):
                def initStyleOption(self, option, index):
                    super().initStyleOption(option, index)
                    option.displayAlignment = Qt.AlignCenter

            # Apply the delegate to the table
            centered_delegate = CenteredItemDelegate()
            table.setItemDelegate(centered_delegate)
            table.verticalHeader().setDefaultSectionSize(40)
            table.setWordWrap(True)

            # Populate with current data
            elem_refs = current_value or prop.default_value or []
            table.setRowCount(len(elem_refs))
            for row, elem_ref in enumerate(elem_refs):
                add_elem_item(elem_ref, row, table)

            # Create a container for the table and button
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.addWidget(table)

            # Function to get the current value from the table
            def get_table_value():
                elem_refs = []
                for row in range(table.rowCount()):
                    item = table.item(row, 0)
                    if item:
                        # Retrieve the actual tuple data stored in UserRole
                        elem_ref = item.data(Qt.UserRole)
                        if elem_ref:
                            elem_refs.append(elem_ref)
                return elem_refs

            # Store both the getter function and the reference to the table with the container
            container.get_value = get_table_value
            container.table_widget = table  # Store a reference to the actual table

            widget = container
        elif prop.prop_type == "colour_table":
            def add_colour_item(colour, row=None, table=None):
                string_col = str((colour.red(), colour.green(), colour.blue(), colour.alpha()))
                item = QTableWidgetItem(string_col)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setData(Qt.UserRole, colour)
                if (row is not None) and (table is not None):
                    table.setItem(row, 0, item)
                return item

            # Create a table widget
            table = ReorderableTableWidget(add_colour_item)

            # Set up the basic table structure
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["Colour"])

            # Custom delegate to display color swatches
            class ColorDelegate(QStyledItemDelegate):
                def paint(self, painter, option, index):
                    if index.column() == 0:
                        color_str = index.data()
                        if color_str:
                            color = QColor(*ast.literal_eval(color_str))
                            # Fill the entire cell with the color
                            painter.fillRect(option.rect, color)

                            # Add a border around the color swatch
                            painter.setPen(QPen(Qt.black, 1))
                            painter.drawRect(option.rect.adjusted(0, 0, -1, -1))

                            # The key part: prevent default text drawing
                            return
                    # Only call the base implementation if we didn't handle it above
                    super().paint(painter, option, index)

                def displayText(self, value, locale):
                    # Return empty string to prevent text display
                    return ""

            # Apply the delegate to the table
            table.setItemDelegate(ColorDelegate())

            # Make rows a bit taller to better display the color swatches
            table.verticalHeader().setDefaultSectionSize(30)

            # Populate with current data
            colours = current_value or prop.default_value or []
            table.setRowCount(len(colours))
            for row, colour in enumerate(colours):
                add_colour_item(QColor(*colour), row, table)

            # Add buttons to add/remove rows
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(0, 0, 0, 0)

            add_button = QPushButton("+")

            # Add row function
            def add_row():
                # Open color dialog directly when adding a new row
                color_dialog = QColorDialog()
                color_dialog.setOption(QColorDialog.ShowAlphaChannel, True)
                if color_dialog.exec_():
                    sel_col = color_dialog.selectedColor()
                    row = table.rowCount()
                    table.setRowCount(row + 1)
                    add_colour_item(sel_col, row, table)

            # Double-click to edit/select color for existing rows
            def on_cell_clicked(row, column):
                if column == 0:
                    color_dialog = QColorDialog()
                    color_dialog.setOption(QColorDialog.ShowAlphaChannel, True)
                    current_item = table.item(row, column)
                    current_color = current_item.data(Qt.UserRole)
                    color_dialog.setCurrentColor(current_color)
                    if color_dialog.exec_():
                        sel_col = color_dialog.selectedColor()
                        add_colour_item(sel_col, row, table)

            # Connect to cellDoubleClicked signal
            table.cellDoubleClicked.connect(on_cell_clicked)
            add_button.clicked.connect(add_row)
            button_layout.addWidget(add_button)

            # Set up context menu for deletion
            def show_context_menu(position):
                row = table.rowAt(position.y())
                if row >= 0:
                    menu = QMenu()
                    delete_action = menu.addAction("Delete")
                    action = menu.exec_(table.viewport().mapToGlobal(position))
                    if action == delete_action:
                        table.removeRow(row)

            table.setContextMenuPolicy(Qt.CustomContextMenu)
            table.customContextMenuRequested.connect(show_context_menu)

            # Create a container for the table and buttons
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.addWidget(table)
            layout.addWidget(button_widget)

            # Function to get the current value from the table
            def get_table_value():
                colours = []
                for row in range(table.rowCount()):
                    try:
                        colour = table.item(row, 0).text()
                        colours.append(ast.literal_eval(colour))
                    except (ValueError, AttributeError):
                        # Handle empty or invalid cells
                        pass
                return colours

            # Store both the getter function and the reference to the table with the container
            container.get_value = get_table_value
            container.table_widget = table  # Store a reference to the actual table

            widget = container

        elif prop.prop_type == "colour":
            r,g,b,a = current_value
            widget = ColorPropertyWidget(QColor(r,g,b,a) or QColor(0,0,0,255))
        else:  # Default to string type
            widget = QLineEdit(str(current_value) if current_value is not None else "")

        return widget

    def accept(self):
        """Apply properties and close dialog"""

        # Update custom properties
        for prop_name, widget in self.property_widgets.items():
            if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                value = widget.value()
            elif isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, QComboBox):
                value =  widget.itemData(widget.currentIndex())
            elif isinstance(widget, QWidget) and hasattr(widget.layout(), 'itemAt') and widget.layout().count() > 0:
                value = widget.get_value()
            else:  # QLineEdit
                value = widget.text()

            self.node_item.node.prop_vals[prop_name] = value
            if (not self.node_item.node.resizable()) and (prop_name == 'width' or prop_name == 'height'):
                svg_width = self.node_item.node.prop_vals.get('width', self.node_item.rect().width())
                svg_height = self.node_item.node.prop_vals.get('height', self.node_item.rect().height())
                self.node_item.resize(*self.node_item.node_size_from_svg_size(svg_width, svg_height))

        # Update the node's appearance
        self.node_item.update()
        self.node_item.update_visualisations()

        super().accept()


def save_as_svg(clicked_item: NodeItem):
    file_path, _ = QFileDialog.getSaveFileName(
        None, "Save SVG",
        f"{clicked_item.node.name()}_{str(clicked_item.uid)[:6]}.svg",
        "SVG Files (*.svg)"
    )

    if file_path:
        shutil.copy(clicked_item.get_svg_path()[0], file_path)


class PipelineScene(QGraphicsScene):
    """Scene that contains all pipeline elements"""

    def __init__(self, temp_dir, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 2000, 2000)

        # Connection related variables
        self.connection_signals = ConnectionSignals()
        self.active_connection = None
        self.temp_line = None
        self.source_port = None
        self.dest_port = None

        self.scene = Scene()
        self.temp_dir = temp_dir

        # Connect signals
        self.connection_signals.connectionStarted.connect(self.start_connection)
        self.connection_signals.connectionMade.connect(self.finish_connection)

    def add_node_from_class(self, node_class, pos, index=None):
        """Add a new node of the given type at the specified position"""
        uid = uuid.uuid4()
        if index is None:
            node = node_class(uid, None, None)
        else:
            node = node_class(uid, None, None, index)
        return self.add_new_node(pos, node)

    def add_new_node(self, pos, node):
        new_node = NodeItem(NodeState(node.node_id, pos.x(), pos.y(), [], [], node, 150, 150))
        self.scene.add(new_node)
        self.addItem(new_node)
        new_node.create_ports()
        new_node.update_vis_image()
        return new_node

    def edit_node_properties(self, node):
        """Open a dialog to edit the node's properties"""
        dialog = NodePropertiesDialog(node)
        if dialog.exec_() == QDialog.Accepted:
            node.update()

    def start_connection(self, source_port: PortItem):
        """Start creating a connection from the given source port"""
        if source_port and not source_port.backend.is_input:
            self.source_port = source_port
            start_pos = source_port.get_center_scene_pos()

            # Create a temporary line for visual feedback
            self.temp_line = QGraphicsLineItem()
            self.temp_line.setLine(QLineF(start_pos, start_pos))
            self.temp_line.setPen(QPen(Qt.darkGray, 2, Qt.DashLine))
            self.addItem(self.temp_line)

    def update_temp_connection(self, end_pos):
        """Update the temporary connection line to the current mouse position"""
        if self.source_port and self.temp_line:
            start_pos = self.source_port.get_center_scene_pos()
            self.temp_line.setLine(QLineF(start_pos, end_pos))

    def finish_connection(self, source_port: PortItem, dest_port: PortItem):
        """Create a permanent connection between source and destination ports"""
        if source_port and dest_port and source_port != dest_port:
            # Don't connect if they're on the same node
            if source_port.parentItem() != dest_port.parentItem():
                # Check if connection already exists
                connection_exists = False
                for edge_id in source_port.backend.edge_ids:
                    edge: EdgeItem = self.scene.get(edge_id)
                    if hasattr(edge, 'dest_port') and edge.dest_port == dest_port:
                        connection_exists = True
                        break

                # Check if target port already has a connection
                target_has_connection = len(dest_port.backend.edge_ids) > 0
                if not connection_exists and issubclass(source_port.backend.port_def.port_type, dest_port.backend.port_def.port_type) and (dest_port.backend.port_def.input_multiple or not target_has_connection):
                    edge = EdgeItem(EdgeState(uuid.uuid4(), source_port.backend.uid, dest_port.backend.uid))
                    self.scene.add(edge)
                    self.addItem(edge)
                    edge.set_ports()
                    edge.source_port.add_edge(edge.uid)
                    edge.dest_port.add_edge(edge.uid)
                    edge.dest_port.parentItem().update_visualisations()

        # Clean up temporary line
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None

        # Reset ports
        self.source_port = None
        self.dest_port = None

    def mousePressEvent(self, event):
        """Handle mouse press events for the scene"""
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.views()[0]))

            if isinstance(item, PortItem) and not item.backend.is_input:
                # Start creating a connection if an output port is clicked
                self.connection_signals.connectionStarted.emit(item)
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events for the scene"""
        if self.source_port and self.temp_line:
            self.update_temp_connection(event.scenePos())

            # Highlight input port if we're hovering over one
            item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.views()[0]))
            if isinstance(item, PortItem) and item.backend.is_input:
                if self.dest_port != item:
                    # Reset previous dest port highlighting
                    if self.dest_port:
                        self.dest_port.setPen(QPen(Qt.black, 1))

                    # Set new dest port
                    self.dest_port = item
                    self.dest_port.setPen(QPen(Qt.red, 2))
            elif self.dest_port:
                # Reset dest port highlighting if not hovering over an input port
                self.dest_port.setPen(QPen(Qt.black, 1))
                self.dest_port = None

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events for the scene"""
        if event.button() == Qt.LeftButton and self.source_port:
            item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.views()[0]))
            if isinstance(item, PortItem) and item.backend.is_input:
                # Create permanent connection
                self.connection_signals.connectionMade.emit(self.source_port, item)
                event.accept()
                return
            else:
                # Clean up if not released over an input port
                if self.temp_line:
                    self.removeItem(self.temp_line)
                    self.temp_line = None
                self.source_port = None

                # Reset dest port highlighting if needed
                if self.dest_port:
                    self.dest_port.setPen(QPen(Qt.black, 1))
                    self.dest_port = None

        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        """Handle context menu events for the scene"""
        clicked_item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.views()[0]))

        if isinstance(clicked_item, EdgeItem):
            # Context menu for connections
            menu = QMenu()
            delete_action = QAction("Delete Connection", menu)
            delete_action.triggered.connect(lambda: self.delete_edge(clicked_item))
            menu.addAction(delete_action)
            menu.exec_(event.screenPos())
        elif isinstance(clicked_item, NodeItem) or isinstance(clicked_item, PortItem):
            # Context menu for nodes (or ports on nodes)
            if isinstance(clicked_item, PortItem):
                clicked_item = clicked_item.parentItem()

            menu = QMenu()
            properties_action = QAction("Properties...", menu)
            properties_action.triggered.connect(lambda: self.edit_node_properties(clicked_item))

            duplicate_action = QAction("Duplicate Node", menu)
            duplicate_action.triggered.connect(lambda: self.duplicate_node(clicked_item))

            delete_action = QAction("Delete Node", menu)
            delete_action.triggered.connect(lambda: self.delete_node(clicked_item))

            if isinstance(clicked_item, NodeItem) and isinstance(clicked_item.node, CombinationNode):
                submenu = QMenu(f"Change {clicked_item.node.display_name()} to...")
                for i in range(len(clicked_item.node.selections())):
                    if i == clicked_item.node.selection_index: continue
                    change_action = QAction(clicked_item.node.selections()[i].display_name(), submenu)
                    change_action.triggered.connect(lambda _, index=i: self.change_node_selection(clicked_item, index))
                    submenu.addAction(change_action)
                menu.addMenu(submenu)

            menu.addAction(properties_action)
            menu.addAction(duplicate_action)
            menu.addAction(delete_action)
            menu.exec_(event.screenPos())
        elif isinstance(clicked_item, QGraphicsSvgItem):
            clicked_item = clicked_item.parentItem()  # Refer to parent node

            menu = QMenu()
            save_svg_action = QAction("Save as SVG", menu)
            save_svg_action.triggered.connect(lambda: save_as_svg(clicked_item))

            menu.addAction(save_svg_action)
            menu.exec_(event.screenPos())
        elif event.scenePos().x() >= 0 and event.scenePos().y() >= 0:
            menu = QMenu()
            add_node_menu = QMenu("Add Node", menu)
            menu.addMenu(add_node_menu)

            # Add actions for each node type
            for node_class in node_classes:
                if issubclass(node_class, CombinationNode):
                    submenu = add_node_menu.addMenu(node_class.display_name())
                    for i in range(len(node_class.selections())):
                        change_action = QAction(node_class.selections()[i].display_name(), submenu)
                        from functools import partial
                        handler = partial(self.add_node_from_class, node_class, event.scenePos(), i)
                        change_action.triggered.connect(handler)
                        submenu.addAction(change_action)
                else:
                    action = QAction(node_class.display_name(), add_node_menu)
                    action.triggered.connect(lambda checked=False, nt=node_class, pos=event.scenePos():
                                             self.add_node_from_class(nt, pos))
                    add_node_menu.addAction(action)

            menu.exec_(event.screenPos())

    def save_scene(self, filepath):
        save_states = {}
        for k, v in self.scene.states.items():
            save_states[k] = v.backend
        with open(filepath, "wb") as f:
            pickle.dump(save_states, f)

    def load_scene(self, filepath):
        self.clear_scene()
        with open(filepath, "rb") as f:
            save_states = pickle.load(f)
        node_ids = []
        for _, v in save_states.items():
            if isinstance(v, NodeState):
                node = NodeItem(v)
                self.scene.add(node)
                self.addItem(node)
                for port_id in v.input_port_ids + v.output_port_ids:
                    self.scene.add(PortItem(save_states[port_id], node))
                node_ids.append(v.uid)
        for _, v in save_states.items():
            if isinstance(v, EdgeState):
                edge = EdgeItem(v)
                self.scene.add(edge)
                self.addItem(edge)
                edge.set_ports()
        for uid in node_ids:
            node = self.scene.get(uid)
            node.update_vis_image()
            node.update_label_containers()

    def clear_scene(self):
        self.scene = Scene()
        for item in self.items():
            if isinstance(item, NodeItem) or isinstance(item, EdgeItem) or isinstance(item, PortItem):
                self.removeItem(item)

    def delete_edge(self, edge):
        """Delete the given edge"""
        edge.source_port.remove_edge(edge.uid)
        edge.dest_port.remove_edge(edge.uid)
        dest_node = edge.dest_port.parentItem()
        self.scene.remove(edge.uid)
        self.removeItem(edge)
        dest_node.update_visualisations()

    def delete_node(self, node: NodeItem):
        """Delete the given node and all its connections"""
        # Remove all connected edges first
        for port_id in node.backend.input_port_ids + node.backend.output_port_ids:
            port: PortItem = self.scene.get(port_id)
            for edge_id in list(port.backend.edge_ids):  # Use a copy to avoid issues while removing
                edge: EdgeItem = self.scene.get(edge_id)
                self.delete_edge(edge)

        for port_id in node.backend.input_port_ids + node.backend.output_port_ids:
            self.scene.remove(port_id)
        self.scene.remove(node.uid)
        self.removeItem(node)

    def change_node_selection(self, clicked_item: NodeItem, i):
        clicked_item.node.set_selection(i)
        clicked_item.update_visualisations()

    def duplicate_node(self, node_item: NodeItem):
        new_node = copy.deepcopy(node_item.backend.node)
        new_node.node_id = uuid.uuid4()
        self.add_new_node(node_item.pos() + QPointF(10, 10), new_node)

class PipelineView(QGraphicsView):
    """View to interact with the pipeline scene"""

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))

        # Enable zooming
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)

        # Add grid lines
        self.draw_grid()

    def draw_grid(self):
        """Draw a grid background for the scene"""
        grid_size = 20
        scene_rect = self.scene().sceneRect()

        # Draw vertical lines
        for x in range(0, int(scene_rect.width()), grid_size):
            line = QGraphicsLineItem(x, 0, x, scene_rect.height())
            line.setPen(QPen(QColor(200, 200, 200), 1))
            line.setZValue(-1000)  # Place behind all other items
            self.scene().addItem(line)

        # Draw horizontal lines
        for y in range(0, int(scene_rect.height()), grid_size):
            line = QGraphicsLineItem(0, y, scene_rect.width(), y)
            line.setPen(QPen(QColor(200, 200, 200), 1))
            line.setZValue(-1000)  # Place behind all other items
            self.scene().addItem(line)

    def mousePressEvent(self, event):
        """Handle mouse press events for the view"""
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            # Create a fake mouse press event to initiate the drag
            fake_event = event
            fake_event.button = lambda: Qt.LeftButton
            super().mousePressEvent(fake_event)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events for the view"""
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.RubberBandDrag)

        super().mouseReleaseEvent(event)


class PipelineEditor(QMainWindow):
    """Main application window"""

    def __init__(self, temp_dir):
        super().__init__()
        self.setWindowTitle("Pipeline Editor")
        self.setGeometry(100, 100, 1000, 800)

        # Create the scene and view
        self.scene = PipelineScene(temp_dir)
        self.view = PipelineView(self.scene)
        self.setCentralWidget(self.view)

        # Create menu bar
        self.setup_menu()

        # Create a status bar with instructions
        self.statusBar().showMessage(
            "Right-click for node menu | Drag from output port (green) to input port (gray) to create connections")

        self.show()

    def setup_menu(self):
        # Create the menu bar
        menu_bar = self.menuBar()

        # Create File menu
        file_menu = menu_bar.addMenu("File")

        # Add Save action
        save_action = QAction("Save to file", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_scene)
        file_menu.addAction(save_action)

        # Add Load action
        load_action = QAction("Load from file", self)
        load_action.setShortcut("Ctrl+L")
        load_action.triggered.connect(self.load_scene)
        file_menu.addAction(load_action)

        scene_menu = menu_bar.addMenu("Scene")

        # Add Clear action
        clear_action = QAction("Clear Scene", self)
        clear_action.setShortcut("Ctrl+C")
        clear_action.triggered.connect(self.clear_scene)
        scene_menu.addAction(clear_action)

    def save_scene(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Pipeline Scene",
            "",
            "Pipeline Scene Files (*.pipeline);;All Files (*)"
        )

        if file_path:
            self.scene.save_scene(file_path)
            self.statusBar().showMessage(f"Scene saved to {file_path}", 3000)

    def load_scene(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Pipeline Scene",
            "",
            "Pipeline Scene Files (*.pipeline);;All Files (*)"
        )

        if file_path:
            self.scene.load_scene(file_path)
            # Update the view to reflect the loaded scene
            self.view.update()
            self.statusBar().showMessage(f"Scene loaded from {file_path}", 3000)

    def clear_scene(self):
        self.scene.clear_scene()

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as temp_dir:
        app = QApplication(sys.argv)
        editor = PipelineEditor(temp_dir=temp_dir)
        sys.exit(app.exec_())
