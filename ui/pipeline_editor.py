import copy
import math
import os
import pickle
import sys
import tempfile
from collections import defaultdict
from functools import partial
from typing import cast

from PyQt5.QtCore import QLineF, pyqtSignal, QObject, QRectF, QTimer, QMimeData
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QFont, QFontMetricsF, QTransform, QNativeGestureEvent, QKeySequence, \
    QFontMetrics
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
                             QGraphicsLineItem, QMenu, QAction, QPushButton, QFileDialog, QGraphicsTextItem, QUndoStack,
                             QUndoCommand, QGraphicsProxyWidget)
from PyQt5.QtWidgets import QGraphicsPathItem
from PyQt5.QtXml import QDomDocument, QDomElement

from ui.app_state import NodeState, AppState, CustomNodeDef, NodeId
from ui.id_datatypes import PortId, EdgeId, gen_node_id, output_port, input_port, PropKey
from ui.node_graph import NodeGraph, RefId
from ui.node_manager import NodeManager, NodeInfo
from ui.node_props_dialog import NodePropertiesDialog
from ui.nodes.all_nodes import node_setting, node_classes
from ui.nodes.drawers.element_drawer import ElementDrawer
from ui.nodes.node_defs import Node
from ui.nodes.nodes import CombinationNode, SelectableNode, CustomNode
from ui.nodes.prop_defs import PT_Element, PT_Warp, PT_Function, PT_Grid, PT_List, PT_Scalar, PortStatus, PropDef, Int
from ui.nodes.shape_datatypes import Group, Element
from ui.reg_custom_dialog import RegCustomDialog
from ui.selectable_renderer import SelectableSvgElement
from ui.vis_types import ErrorFig, Visualisable


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
    LABEL_SVG_DIST = 5
    LABEL_FONT = QFont("Arial", 8)

    def __init__(self, node_state: NodeState, node_info: NodeInfo):
        super().__init__(0, 0, 0, 0)
        self.node_state: NodeState = node_state
        self.port_items: dict[PortId, PortItem] = {}
        pos_x, pos_y = node_state.pos

        self.left_max_width = NodeItem.MARGIN_Y - NodeItem.MARGIN_X
        self.right_max_width = NodeItem.MARGIN_Y - NodeItem.MARGIN_X
        width, height = self.node_size_from_svg_size(*node_state.svg_size)
        super().__init__(0, 0, width, height)
        self.svg_items = None
        self.svg_item = None
        self.setPos(pos_x, pos_y)
        self.setZValue(1)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setBrush(QBrush(QColor(220, 230, 250)))
        self.setPen(QPen(Qt.black, 2))

        # Add property button
        self._property_button = None
        if node_info.filter_ports_by_status(PortStatus.OPTIONAL):
            self._property_button = QPushButton("P")
            self._property_button.setFixedSize(20, 20)
            self._property_button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #646464;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #cccccc;
                }
            """)
            self._property_button.clicked.connect(lambda: self.scene().edit_node_properties(self))  # Define this method
            self._property_proxy = QGraphicsProxyWidget(self)
            self._property_proxy.setWidget(self._property_button)
            self._property_proxy.setZValue(101)
            self._property_button.setToolTip("Edit node properties")

        # Add randomise button
        self._randomise_button = None
        if node_info.randomisable:
            self._randomise_button = QPushButton("↺")
            self._randomise_button.setFixedSize(20, 20)
            self._randomise_button.setToolTip("Randomise selection")
            self._randomise_button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #646464;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #cccccc;
                }
            """)
            self._randomise_button.clicked.connect(
                lambda: self.scene().undo_stack.push(RandomiseNodesCmd(self.scene(), {self.node_state.node})))

            # Proxy
            self._randomise_proxy = QGraphicsProxyWidget(self)
            self._randomise_proxy.setWidget(self._randomise_button)
            self._randomise_proxy.setZValue(101)

        self._help_icon_rect = QRectF()
        self._help_hover_timer = QTimer()
        self._help_hover_timer.setSingleShot(True)
        self._help_hover_timer.timeout.connect(self._showHelpTooltip)
        self._help_tooltip = None
        self.setAcceptHoverEvents(True)

        # Set the help text for this node
        self._help_text = f"{node.base_node_name} Help:\n{node.get_description()}"

        self.resize_handle = None
        if node_setting(node_info.name).resizable:
            # Add resize handle
            self.resize_handle = ResizeHandle(self, 'bottomright')

    @property
    def uid(self) -> NodeId:
        return self.node_state.node

    @property
    def node_graph(self) -> NodeGraph:
        return self.scene().node_graph

    @property
    def node_manager(self) -> NodeManager:
        return self.scene().node_manager

    @property
    def node_info(self) -> NodeInfo:
        return self.node_manager.node_info(self.uid)

    def add_property_port(self, prop_key):
        self.scene().undo_stack.push(AddPropertyPortCmd(self, prop_key))

    def remove_property_port(self, prop_key):
        self.scene().undo_stack.push(RemovePropertyPortCmd(self, prop_key))

    def change_properties(self, props_changed):
        self.scene().undo_stack.push(ChangePropertiesCmd(self, props_changed))

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

            self._help_tooltip = QGraphicsTextItem()
            self.scene().addItem(self._help_tooltip)
            self._help_tooltip.setDefaultTextColor(QColor("#333333"))
            self._help_tooltip.setHtml(tooltip_html)
            self._help_tooltip.setZValue(100)  # Make sure it's on top
            self._help_tooltip.setTextWidth(224)  # Account for padding (200px + 24px padding)

        # Position the tooltip above the help icon
        tooltip_rect = self._help_tooltip.boundingRect()

        # Center above the icon with some spacing
        tooltip_pos_local = QPointF(
            self._help_icon_rect.center().x() - tooltip_rect.width() / 2,
            self._help_icon_rect.top() - tooltip_rect.height()
        )
        self._help_tooltip.setPos(self.mapToScene(tooltip_pos_local))
        self._help_tooltip.show()

    def resize(self, width, height, update_vis=True):
        """Resize the node to the specified dimensions"""
        self.setRect(0, 0, width, height)
        if self.resize_handle:
            self.resize_handle.update_position()

        # Update node state
        self.node_state.svg_size = self.svg_size_from_node_size(width, height)

        # Update vis image
        if update_vis:
            self.update_vis_image()

        # Update port positions to match the new dimensions
        self.update_all_port_positions()

    def node_size_from_svg_size(self, svg_w, svg_h):
        return svg_w + self.left_max_width + self.right_max_width + 2 * NodeItem.MARGIN_X + 2 * NodeItem.LABEL_SVG_DIST, svg_h + 2 * NodeItem.MARGIN_Y + NodeItem.TITLE_HEIGHT

    def svg_size_from_node_size(self, rect_w, rect_h):
        return rect_w - self.left_max_width - self.right_max_width - 2 * NodeItem.MARGIN_X - 2 * NodeItem.LABEL_SVG_DIST, rect_h - 2 * NodeItem.MARGIN_Y - NodeItem.TITLE_HEIGHT

    def visualise(self) -> Visualisable:
        return self.node_manager.visualise(self.uid)

    def update_vis_image(self):
        """Add an SVG image to the node that scales with node size and has selectable elements"""
        # Remove existing SVG items if necessary
        if self.svg_items:
            for item in self.svg_items:
                scene = self.scene()
                if scene and item in scene.items():
                    scene.removeItem(item)
        self.svg_items = []

        if self.svg_item:
            if self.svg_item in self.scene().items():
                self.scene().removeItem(self.svg_item)

        # Get item to draw
        vis: Visualisable = self.visualise()
        # Remove inactive port ids TODO
        # inactive_port_ids = self.node_graph().pop_inactive_port_ids(self.node_state.node)
        # for port_id in inactive_port_ids:
        #     self.scene().undo_stack.push(RemoveExtractedElementCmd(self, port_id))

        svg_filepath = os.path.join(self.scene().temp_dir, f"{self.node_state.node}.svg")
        # Base position for all SVG elements
        svg_pos_x = self.left_max_width + NodeItem.MARGIN_X + NodeItem.LABEL_SVG_DIST
        svg_pos_y = NodeItem.TITLE_HEIGHT + NodeItem.MARGIN_Y
        svg_width, svg_height = self.node_state.svg_size

        if not self.node_info.selectable:
            vis.save_to_svg(svg_filepath, svg_width, svg_height)
            self.svg_item = QGraphicsSvgItem(svg_filepath)
            # Apply position
            self.svg_item.setParentItem(self)
            self.svg_item.setPos(svg_pos_x, svg_pos_y)
            self.svg_item.setZValue(2)
        else:
            assert isinstance(vis, Group)
            assert not vis.transform_list.transforms
            ElementDrawer(svg_filepath, svg_width, svg_height, (vis, None)).save()

            # Create SVG renderer
            svg_renderer = QSvgRenderer(svg_filepath)

            viewport_svg = QGraphicsSvgItem(svg_filepath)
            viewport_svg.setParentItem(self)
            viewport_svg.setPos(svg_pos_x, svg_pos_y)
            viewport_svg.setZValue(1)  # Set below selectable items
            self.svg_items.append(viewport_svg)

            # Set clip path to clip out outside of SVG
            clip_path = QPainterPath()
            clip_path.addRect(QRectF(0, 0, svg_width, svg_height))
            viewport_svg.setFlag(QGraphicsItem.ItemClipsChildrenToShape, True)

            # Load the SVG file as XML
            dom_document = QDomDocument()
            with open(svg_filepath, 'r') as file:
                content = file.read()
                dom_document.setContent(content)

            def find_element_by_id(node, target_id):
                if node.isElement():
                    element = node.toElement()
                    if element.attribute('id') == target_id:
                        return element

                # Check children recursively
                child = node.firstChild()
                while not child.isNull():
                    result = find_element_by_id(child, target_id)
                    if result and not result.isNull():
                        return result
                    child = child.nextSibling()

                return QDomElement()  # Return null element if not found

            root = dom_document.documentElement()
            vis_element = find_element_by_id(root, vis.uid)
            assert not vis_element.isNull()

            child = vis_element.firstChild()
            while not child.isNull():
                if child.isElement():
                    child_element = child.toElement()
                    child_elem_id = child_element.attribute('id')
                    assert child_elem_id
                    selectable_item = SelectableSvgElement(child_elem_id, vis, svg_renderer, self)
                    selectable_item.setParentItem(viewport_svg)
                    selectable_item.setPos(0, 0)
                    selectable_item.setZValue(3)
                    self.svg_items.append(selectable_item)
                child = child.nextSibling()

    def update_visualisations(self):
        self.update_vis_image()
        for output_node in self.node_graph.output_nodes(self.uid):
            output_node_item: NodeItem = self.scene().node_item(output_node)
            output_node_item.update_visualisations()

    def create_ports(self, update_vis=True):
        for port in self.node_state.ports_open:
            # Update layout at the end for efficiency
            self.add_port(port, self.node_info.prop_defs[port.key], update_layout=False)
        self.update_label_port_positions(update_vis=update_vis)

    def reset_ports_open(self, new_ports_open: list[PortId]):
        pass
        # # Remove ports no longer in use
        # port_ids = list(self.port_items.keys())
        # for port_id in port_ids:
        #     if port_id not in new_ports_open:
        #         # Update layout at the end for efficiency
        #         self.remove_port(port_id, update_layout=False)
        # # Add new ports
        # new_port_items = {}
        # for port_id in new_ports_open:
        #     if port_id not in self.node_state.ports_open:
        #         # Update layout at the end for efficiency
        #         self.add_port(port_id, self.node().get_port_defs()[port_id], update_layout=False)
        #     new_port_items[port_id] = self.port_items[port_id]
        # # Set new port item order
        # self.port_items = new_port_items
        # self.update_label_port_positions()

    def add_port(self, port: PortId, prop_def: PropDef, update_layout=True) -> None:
        # Add port to scene
        port_item = PortItem(port, parent=self)
        self.port_items[port] = port_item  # Add reference to port
        if port not in self.node_state.ports_open:
            self.node_state.ports_open.append(port)  # Add to open ports
        if update_layout:
            self.update_label_port_positions()

    def remove_port(self, port: PortId, update_layout=True):
        port_item = self.port_items[port]
        port_item.remove_edges()  # Remove connections to/from this port
        del self.port_items[port]  # Remove reference to port
        self.node_state.ports_open.remove(port)  # Remove from open ports
        port_item.scene().removeItem(port_item)  # Remove port from scene
        if update_layout:
            self.update_label_port_positions()

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        painter.setFont(QFont("Arial", 8))
        painter.setPen(QColor("grey"))
        id_rect = self.rect().adjusted(10, 10, 0, 0)  # Shift the top edge down
        painter.drawText(id_rect, Qt.AlignTop | Qt.AlignLeft, f"id: {self.node_state.node}")

        # Draw node title
        title_font = QFont("Arial", 10)
        painter.setFont(title_font)
        painter.setPen(QColor("black"))
        metrics = QFontMetrics(title_font)
        title_text = self.node().base_node_name
        text_width = metrics.horizontalAdvance(title_text)
        text_height = metrics.height()
        node_rect = self.rect()
        title_x = node_rect.center().x() - text_width / 2
        title_y = node_rect.top() + 10  # adjust vertical offset as needed
        title_rect = QRectF(title_x, title_y, text_width, text_height)
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignTop, title_text)

        # Draw the help icon (question mark) in the top-right corner
        help_icon_size = 9
        help_rect = QRectF(
            title_rect.right() + help_icon_size / 2,
            title_rect.center().y() - help_icon_size / 2,  # center vertically
            help_icon_size,
            help_icon_size
        )

        # Draw the circle background
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(help_rect)

        # Draw the question mark
        painter.setFont(QFont("Arial", help_icon_size, QFont.Bold))
        painter.setPen(QColor(80, 80, 80))
        painter.drawText(help_rect, Qt.AlignCenter, "?")

        # Store the help icon rect for hit testing in hover events
        self._help_icon_rect = help_rect
        x_offset = self.rect().right() - 25  # Right edge - 20px width - 5px padding

        # If property button exists, place it rightmost
        if self._property_button:
            self._property_proxy.setPos(QPointF(x_offset, self.rect().top() + 5))
            x_offset -= 25  # Move left for next button

        # If randomise button exists, place it to the left of property or take its place
        if self._randomise_button:
            self._randomise_proxy.setPos(QPointF(x_offset, self.rect().top() + 5))

        # Draw port labels if there are multiple
        painter.setFont(NodeItem.LABEL_FONT)
        font_metrics = QFontMetricsF(NodeItem.LABEL_FONT)
        text_height = font_metrics.height()

        # Draw port labels
        for port_item in self.port_items.values():
            port: PortId = port_item.port
            text = self.node_info.prop_defs[port.key].display_name
            port_y = port_item.y()
            if port.is_input:
                x_offset = NodeItem.MARGIN_X
                width_to_use = self.left_max_width
                alignment = Qt.AlignLeft | Qt.AlignVCenter
            else:
                x_offset = self.rect().width() - self.right_max_width - NodeItem.MARGIN_X
                width_to_use = self.right_max_width
                alignment = Qt.AlignRight | Qt.AlignVCenter
            text_rect = QRectF(
                x_offset,
                port_y - (text_height / 2),  # Vertical center alignment
                width_to_use,
                text_height  # Font height
            )
            # Draw the text
            painter.drawText(text_rect, alignment, text)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # Update connected edges when node moves
            for port in self.port_items.values():
                port.update_edge_positions()
        elif change == QGraphicsItem.ItemPositionHasChanged:
            self.node_state.pos = (self.pos().x(), self.pos().y())
        return super().itemChange(change, value)

    def update_port_positions(self, is_input: bool):
        port_dict = {port: port_item for port, port_item in self.port_items.items() if port.is_input == is_input}
        port_count = len(port_dict)
        for i, (port, port_item) in enumerate(port_dict.items()):
            x_offset = -10 if port.is_input else self.rect().width() + 10
            y_offset = (i + 1) * self.rect().height() / (port_count + 1)
            port_item.setPos(x_offset, y_offset)
            # Update any connections to this port
            port_item.update_edge_positions()

    def update_all_port_positions(self):
        """Update the positions of all ports based on current node dimensions"""
        self.update_port_positions(is_input=True)
        self.update_port_positions(is_input=False)

    def update_label_port_positions(self, update_vis=True):
        # Calculate the maximum width needed for each side
        font_metrics = QFontMetricsF(NodeItem.LABEL_FONT)
        self.left_max_width = 0
        self.right_max_width = 0

        for port in self.port_items:
            text = self.node_info.prop_defs[port.key].display_name
            width = font_metrics.horizontalAdvance(text)
            if port.is_input:
                self.left_max_width = max(self.left_max_width, width)
            else:
                self.right_max_width = max(self.right_max_width, width)

        if self.left_max_width == 0:
            self.left_max_width = NodeItem.LABEL_SVG_DIST
        if self.right_max_width == 0:
            self.right_max_width = NodeItem.LABEL_SVG_DIST

        width, height = self.node_size_from_svg_size(*self.node_state.svg_size)
        self.resize(width, height, update_vis=update_vis)

    def remove_from_scene(self, update_vis=True):
        # Remove all connected edges
        for port_item in self.port_items.values():
            port_item.remove_edges(update_vis=update_vis)
        # Remove tooltip
        if self._help_tooltip:
            self.scene().removeItem(self._help_tooltip)
            self._help_tooltip = None
        # Remove this node item
        self.node_graph.remove_node(self.uid)
        del self.scene().node_items[self.uid] # Remove reference to item
        self.node_manager.remove_node(self.uid) # Remove from node manager
        self.scene().removeItem(self)


class PortItem(QGraphicsPathItem):
    """Represents connection points on nodes with shapes based on port_type"""

    def __init__(self, port: PortId, parent: NodeItem):
        super().__init__(parent)
        self.port = port
        self.edge_items: dict[PortId, EdgeItem] = {} # Key is the port that it is connected to by the edge

        self.size = 12  # Base size for the port
        # Create shape based on port_type
        self.create_shape_for_port_type()
        self.setZValue(1)

        # Make port interactive
        self.setAcceptHoverEvents(True)

        # Set appearance based on input/output status
        if port.is_input:
            self.setBrush(QBrush(QColor(100, 100, 100)))
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setBrush(QBrush(QColor(50, 150, 50)))
            self.setCursor(Qt.CrossCursor)

        self.setPen(QPen(Qt.black, 1))

    @property
    def port_type(self):
        prop_def: PropDef = cast(NodeItem, self.parentItem()).node_info.prop_defs[self.port.key]
        return prop_def.prop_type

    def create_shape_for_port_type(self):
        path = QPainterPath()
        half_size = self.size / 2
        port_type = self.port_type
        if port_type.is_compatible_with(PT_Element()):
            # Circle for number type
            path.addEllipse(-half_size, -half_size, self.size, self.size)
        elif port_type.is_compatible_with(PT_Grid()):
            # Rounded rectangle for string type
            path.addRoundedRect(-half_size, -half_size, self.size, self.size, 3, 3)
        elif port_type.is_compatible_with(PT_Function()):
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

        elif port_type.is_compatible_with(PT_Warp()):
            # Square for array type
            path.addRect(-half_size, -half_size, self.size, self.size)

        elif port_type.is_compatible_with(PT_List(PT_Scalar())):
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

    def hoverEnterEvent(self, event):
        self.setPen(QPen(Qt.red, 2))
        if not self.is_input:
            self.setCursor(Qt.CrossCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPen(QPen(Qt.black, 1))
        super().hoverLeaveEvent(event)

    def update_edge_positions(self):
        for edge_item in self.edge_items.values():
            edge_item.update_position()

    def remove_edges(self, update_vis=True):
        connected_ports: list[PortId] = list(self.edge_items.keys())
        for connected_port in connected_ports:
            self.edge_items[connected_port].remove_from_scene(update_vis=update_vis)


class EdgeItem(QGraphicsLineItem):
    """Represents connections between nodes"""

    def __init__(self, src_port_item: PortItem, dst_port_item: PortItem):
        super().__init__()
        self.src_port_item = src_port_item
        self.dst_port_item = dst_port_item

        self.setZValue(0)
        # Thicker line with rounded caps for better appearance
        self.setPen(QPen(Qt.black, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.setFlag(QGraphicsItem.ItemIsSelectable)

    @property
    def edge(self) -> EdgeId:
        return EdgeId(self.src_port_item.port, self.dst_port_item.port)

    def update_position(self):
        source_pos = self.src_port_item.get_center_scene_pos()
        dest_pos = self.dst_port_item.get_center_scene_pos()
        self.setLine(QLineF(source_pos, dest_pos))

    def remove_from_scene(self, update_vis=True):
        del self.src_port_item.edge_items[self.dst_port_item.port]
        del self.dst_port_item.edge_items[self.src_port_item.port]
        # Remove from node graph
        cast(PipelineScene, self.scene()).node_graph.remove_edge(self.edge)
        # Update dest node visualisations
        if update_vis:
            cast(NodeItem, self.dst_port_item.parentItem()).update_visualisations()
        # Remove from scene
        self.scene().removeItem(self)


class AddNewNodeCmd(QUndoCommand):
    def __init__(self, scene, pos, node_class, add_info=None, description="Add new node"):
        super().__init__(description)
        self.scene = scene
        self.node_graph: NodeGraph = scene.node_graph
        self.node_manager: NodeManager = scene.node_manager
        self.pos = pos
        self.node_class = node_class
        self.add_info = add_info
        self.node_state = None

    def undo(self):
        node_item = self.scene.node_items[self.node_state.node]
        node_item.remove_from_scene()

    def redo(self):
        node_id: NodeId = self.node_state.node if self.node_state else gen_node_id()
        node: Node = self.node_class(node_id, self.node_graph, add_info=self.add_info)
        self.node_graph.add_node(node_id)
        self.node_manager.add_node(node)
        node_info: NodeInfo = self.node_manager.node_info(node_id)
        if not self.node_state:
            self.node_state = NodeState(node=node_info.uid,
                                        ports_open=node_info.filter_ports_by_status(PortStatus.COMPULSORY),
                                        pos=(self.pos.x(), self.pos.y()),
                                        svg_size=(150, 150))  # TODO: save as constant somewhere
        self.scene.add_node(self.node_state)


class AddNewEdgeCmd(QUndoCommand):
    def __init__(self, scene, edge: EdgeId, description="Add new edge"):
        super().__init__(description)
        self.scene = scene
        self.node_graph = self.scene.graph_querier
        self.edge = edge

    def undo(self):
        self.scene.remove_edge(self.edge)

    def redo(self):
        self.node_graph.add_edge(self.edge)
        self.scene.add_edge(self.edge)


class ChangePropertiesCmd(QUndoCommand):
    def __init__(self, node_item: NodeItem, props_changed, description="Change properties"):
        super().__init__(description)
        self.node_item = node_item
        self.node_manager: NodeManager = node_item.node_manager
        self.props_changed = props_changed

    def update_properties(self, props):
        for prop_key, value in props.items():
            self.node_manager.set_property(self.node_item.uid, prop_key, value)
            if (not node_setting(self.node_item.node_info.name).resizable) and (
                    prop_key == 'width' or prop_key == 'height'):
                svg_width: Int = self.node_manager.get_property(self.node_item.uid, 'width')
                svg_height: Int = self.node_manager.get_property(self.node_item.uid, 'height')
                self.node_item.resize(*self.node_item.node_size_from_svg_size(svg_width.value, svg_height.value))
        # Update the node's appearance
        self.node_item.update_visualisations()

    def undo(self):
        props = {}
        for prop_name, value in self.props_changed.items():
            props[prop_name] = value[0]  # Take the old value
        self.update_properties(props)

    def redo(self):
        props = {}
        for prop_name, value in self.props_changed.items():
            props[prop_name] = value[1]  # Take the new value
        self.update_properties(props)


class AddPropertyPortCmd(QUndoCommand):
    def __init__(self, node_item: NodeItem, prop_key, description="Add property port"):
        super().__init__(description)
        self.node_item = node_item
        self.prop_key = prop_key

    def undo(self):
        self.node_item.remove_port(input_port(self.node_item.uid, self.prop_key))

    def redo(self):
        prop_def: PropDef = self.node_item.node_info.prop_defs[self.prop_key]
        self.node_item.add_port(input_port(self.node_item.uid, self.prop_key), prop_def)


class RemovePropertyPortCmd(QUndoCommand):
    def __init__(self, node_item: NodeItem, prop_key: PropKey, description="Remove property port"):
        super().__init__(description)
        self.node_item = node_item
        self.prop_key = prop_key

    def undo(self):
        prop_def: PropDef = self.node_item.node_info.prop_defs[self.prop_key]
        self.node_item.add_port(input_port(self.node_item.uid, self.prop_key), prop_def)

    def redo(self):
        self.node_item.remove_port(input_port(self.node_item.uid, self.prop_key))


class ExtractElementCmd(QUndoCommand):
    def __init__(self, node_item: NodeItem, prop_key: PropKey, description="Extract element"):
        super().__init__(description)
        self.node_item = node_item
        self.prop_key = prop_key

    def undo(self):
        pass

    def redo(self):
        prop_def: PropDef = self.node_item.node_info.prop_defs[self.prop_key]
        self.node_item.add_port(input_port(self.node_item.uid, self.prop_key), prop_def)


class RemoveExtractedElementCmd(QUndoCommand):
    def __init__(self, node_item: NodeItem, prop_key: PropKey, description="Remove extracted element"):
        super().__init__(description)
        self.node_item = node_item
        self.prop_key = prop_key

    def undo(self):
        pass

    def redo(self):
        self.node_item.remove_port(input_port(self.node_item.uid, self.prop_key))


class PasteCmd(QUndoCommand):
    def __init__(self, scene, node_states: dict[NodeId, NodeState], subset_node_manager: NodeManager, edges: set[EdgeId], port_refs: dict[NodeId, dict[PortId, RefId]], description="Paste"):
        super().__init__(description)
        self.scene = scene
        self.node_states = node_states
        self.subset_node_manager = subset_node_manager
        self.edges = edges
        self.port_refs = port_refs

    def undo(self):
        self.scene.remove_from_graph_and_scene(self.node_states, self.edges)

    def redo(self):
        self.scene.add_to_graph_and_scene(self.node_states, self.subset_node_manager, self.edges, self.port_refs)


class DeleteCmd(QUndoCommand):
    def __init__(self, scene, node_states: dict[NodeId, NodeState], subset_node_manager: NodeManager, edges: set[EdgeId], port_refs: dict[NodeId, dict[PortId, RefId]], description="Delete"):
        super().__init__(description)
        self.scene = scene
        self.node_states = node_states
        self.subset_node_manager = subset_node_manager
        self.edges = edges
        self.port_refs = port_refs

    def undo(self):
        self.scene.add_to_graph_and_scene(self.node_states, self.subset_node_manager, self.edges, self.port_refs)

    def redo(self):
        self.scene.remove_from_graph_and_scene(self.node_states, self.edges)


class RegisterCustomNodeCmd(QUndoCommand):
    def __init__(self, scene, name, custom_node_def, description="Register Custom Node"):
        super().__init__(description)
        self.scene = scene
        self.node_graph: NodeGraph = scene.graph_querier
        self.name = name
        self.custom_node_def = custom_node_def

    def undo(self):
        pass

    def redo(self):
        # Register custom node definition
        if self.name not in self.scene.custom_node_defs:
            self.scene.custom_node_defs[self.name] = self.custom_node_def
        else:
            print("Error: custom node definition with same name already exists.")


class RandomiseNodesCmd(QUndoCommand):
    def __init__(self, scene, node_ids, description="Randomise node(s)"):
        super().__init__(description)
        self.scene = scene
        self.node_graph: NodeGraph = scene.graph_querier
        self.node_ids = node_ids  # Assumes these nodes are randomisable
        self.prev_seeds = {}

    def undo(self):
        for node_id, prev_seed in self.prev_seeds.items():
            self.node_graph.node(node_id).randomise(prev_seed)
            self.scene.node_items[node_id].update_visualisations()

    def redo(self):
        for node_id in self.node_ids:
            node = self.node_graph.node(node_id)
            self.prev_seeds[node_id] = node.get_seed()
            node.randomise()  # TODO: store new seed for redo
            self.scene.node_items[node_id].update_visualisations()


class PipelineScene(QGraphicsScene):
    """Scene that contains all pipeline elements"""

    def __init__(self, temp_dir: str, parent=None):
        super().__init__(parent)
        self.setSceneRect(-100000, -100000, 200000, 200000)
        self.skip_next_context_menu = False

        # Connection related variables
        self.connection_signals = ConnectionSignals()
        self.active_connection = None
        self.temp_line = None
        self.source_port = None
        self.dest_port = None

        self.node_items = {}
        self.custom_node_defs: dict[str, CustomNodeDef] = {}
        self.node_graph: NodeGraph = NodeGraph()
        self.node_manager: NodeManager = NodeManager()

        self.temp_dir = temp_dir
        print(temp_dir)
        self.undo_stack = QUndoStack()
        self.filepath = None

        # Connect signals
        self.connection_signals.connectionStarted.connect(self.start_connection)
        self.connection_signals.connectionMade.connect(self.finish_connection)

    def view(self):
        return self.views()[0]

    def add_new_node(self, pos, node, add_info=None):
        self.undo_stack.push(AddNewNodeCmd(self, pos, node, add_info=add_info))

    def edit_node_properties(self, node):
        """Open a dialog to edit the node's properties"""
        NodePropertiesDialog(node).exec_()

    def start_connection(self, source_port: PortItem):
        """Start creating a connection from the given source port"""
        if source_port and not source_port.is_input:
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

    def finish_connection(self, source_port_item: PortItem, dest_port_item: PortItem):
        """Create a permanent connection between source and destination ports"""
        if source_port_item and dest_port_item and source_port_item != dest_port_item:
            # Don't connect if they're on the same node
            if source_port_item.parentItem() != dest_port_item.parentItem():
                edge: EdgeId = EdgeId(source_port_item.port, dest_port_item.port)
                # Check if connection already exists
                connection_exists = self.node_graph.does_edge_exist(edge)

                # Check if target port already has a connection
                target_has_connection = len(dest_port_item.edge_items) > 0
                if not connection_exists and source_port_item.port_type.is_compatible_with(dest_port_item.port_type) and \
                        (not target_has_connection or (
                                isinstance(dest_port_item.port_type, PT_List) and dest_port_item.port_type.input_multiple)):
                    # Add the connection
                    self.undo_stack.push(
                        AddNewEdgeCmd(self, edge))

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
            item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.view()))

            if isinstance(item, PortItem) and not item.port.is_input:
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
            item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.view()))
            if isinstance(item, PortItem) and item.port.is_input:
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
            item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.view()))
            if isinstance(item, PortItem) and item.port.is_input:
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
        if self.skip_next_context_menu:
            self.skip_next_context_menu = False
            event.accept()  # Suppress the default scene menu
            return

        clicked_item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.view()))

        if isinstance(clicked_item, PortItem):
            # Print type for debugging
            port: PortId = clicked_item.port
            print(
                f"Node {port.node} ({"Input" if port.is_input else "Output"}, {port.key}): {clicked_item.port_type}")

        elif isinstance(clicked_item, NodeItem):
            node_info: NodeInfo = clicked_item.node_info
            # Context menu for nodes
            menu = QMenu()
            # separate_from_inputs_action = QAction("Separate from inputs", menu)
            # separate_from_inputs_action.triggered.connect(lambda: self.separate_from_inputs_action(clicked_item))
            # menu.addAction(separate_from_inputs_action)

            if node_info.selectable:
                selections, curr_idx = self.node_manager.selections_w_idx(clicked_item.uid)
                submenu = QMenu(f"Change {node_info.name} to...")
                for i in range(len(selections)):
                    if i == curr_idx: continue
                    change_action = QAction(selections[i].name(), submenu)
                    change_action.triggered.connect(lambda _, index=i: self.change_node_selection(clicked_item, index))
                    submenu.addAction(change_action)
                menu.addMenu(submenu)

            menu.exec_(event.screenPos())
        else:
            menu = QMenu()

            # Add actions for each node type
            for node_class in node_classes():
                if issubclass(node_class, CombinationNode):
                    submenu = menu.addMenu(node_class.name())
                    for i in range(len(node_class.selections())):
                        change_action = QAction(node_class.selections()[i].name(), submenu)
                        handler = partial(self.add_new_node, event.scenePos(), node_class, add_info=i)
                        change_action.triggered.connect(handler)
                        submenu.addAction(change_action)
                else:
                    action = QAction(node_class.name(), menu)
                    handler = partial(self.add_new_node, event.scenePos(), node_class)
                    action.triggered.connect(handler)
                    menu.addAction(action)
            # Add custom nodes
            if self.custom_node_defs:
                submenu = menu.addMenu("Custom Node")
                for name, node_def in self.custom_node_defs.items():
                    action = QAction(name, menu)
                    handler = partial(self.add_new_node, event.scenePos(), CustomNode,
                                      add_info=(name, copy.deepcopy(node_def)))
                    action.triggered.connect(handler)
                    submenu.addAction(action)

            menu.exec_(event.screenPos())

    def save_scene(self, filepath):
        view = self.view()
        center = view.mapToScene(view.viewport().rect().center())
        zoom = view.current_zoom
        with open(filepath, "wb") as f:
            pickle.dump(AppState(view_pos=(center.x(), center.y()),
                                 zoom=zoom,
                                 node_states=[node_item.node_state for node_item in self.node_items.values()],
                                 node_graph=self.node_graph,
                                 node_manager=self.node_manager,
                                 custom_node_defs=self.custom_node_defs), f)

    # Item getter functions
    def node_item(self, node: NodeId) -> NodeItem:
        return self.node_items[node]

    def port_item(self, port: PortId) -> PortItem:
        node_item: NodeItem = self.node_item(port.node)
        return node_item.port_items[port]

    def edge_item(self, edge: EdgeId) -> EdgeItem:
        # Obtain edge via source port
        src_port_item: PortItem = self.port_item(edge.src_port)
        return src_port_item.edge_items[edge.dst_port]

    # Other functions
    def add_edge(self, edge: EdgeId, update_vis=True):
        src_port_item = self.port_item(edge.src_port)
        dst_port_item = self.port_item(edge.dst_port)
        new_edge_item = EdgeItem(src_port_item, dst_port_item)
        self.addItem(new_edge_item)
        new_edge_item.update_position()
        # Update port edge_items
        src_port_item.edge_items[edge.dst_port] = new_edge_item
        dst_port_item.edge_items[edge.src_port] = new_edge_item
        if update_vis:
            self.node_item(edge.dst_node).update_visualisations()

    def remove_edge(self, edge: EdgeId, update_vis=True):
        self.edge_item(edge).remove_from_scene(update_vis=update_vis)

    def add_node(self, node_state: NodeState, update_vis=True):
        node_item = NodeItem(node_state, self.node_manager.node_info(node_state.node))
        self.node_items[node_state.node] = node_item
        self.addItem(node_item)
        node_item.create_ports(update_vis=update_vis)

    def load_from_node_states(self, node_states: set[NodeState], edges: set[EdgeId]):
        # Add node items
        for node_state in node_states:
            self.add_node(node_state, update_vis=False)
        # Add edge items
        for edge in edges:
            self.add_edge(edge, update_vis=False)
        # Update visualisations in order
        for node in self.node_graph.get_topo_order_subgraph({node_state.node for node_state in node_states}):
            self.node_item(node).update_vis_image()

    def add_to_graph_and_scene(self, node_states: dict[NodeId, NodeState], subset_node_manager: NodeManager, edges: set[EdgeId], more_node_to_port_refs: dict[NodeId, dict[PortId, RefId]]):
        # Add to node implementations
        self.node_manager.update_nodes(subset_node_manager)
        # Update graph
        for node in node_states:
            self.node_graph.add_node(node)
        for edge in edges:
            self.node_graph.add_edge(edge)
        self.node_graph.extend_port_refs(more_node_to_port_refs)
        # Load items
        self.load_from_node_states(set(node_states.values()), edges)

    def remove_from_graph_and_scene(self, node_states: set[NodeState], edges: set[EdgeId]):
        removed_nodes: set[NodeId] = {node_state.node for node_state in node_states}
        # Get affected nodes
        affected_nodes: set[NodeId] = set()
        for node in removed_nodes:
            affected_nodes.update(self.node_graph.output_nodes(node))
        for edge in edges:
            affected_nodes.add(edge.dst_node)
        affected_nodes.difference_update(removed_nodes)

        # Remove nodes
        for node_state in node_states:
            node_item = self.node_item(node_state.node)
            node_item.remove_from_scene(update_vis=False)
        # Remove edges
        for edge in edges:
            if edge.src_node in self.node_items and edge.dst_node in self.node_items:
                # Connection still exists, remove now
                self.remove_edge(edge, update_vis=False)
        # Update affected nodes in topological order
        for affected_node in self.node_graph.get_topo_order_subgraph(affected_nodes):
            affected_node_item = self.node_item(affected_node)
            affected_node_item.update_visualisations()

    def clear_scene(self):
        nodes = list(self.node_items.keys())
        for node in nodes:
            self.node_item(node).remove_from_scene(update_vis=False)

    def load_scene(self, filepath):
        self.clear_scene()

        with open(filepath, "rb") as f:
            app_state = pickle.load(f)

        self.view().centerOn(*app_state.view_pos)
        self.view().set_zoom(app_state.zoom)
        self.node_graph = app_state.node_graph
        self.node_manager = app_state.node_manager
        self.custom_node_defs = app_state.custom_node_defs
        self.load_from_node_states(app_state.node_states, self.node_graph.edges)
        self.undo_stack.clear()
        self.filepath = filepath

    def change_node_selection(self, clicked_item: NodeItem, index):
        self.node_manager.set_selection(clicked_item.uid, index)
        new_node_info: NodeInfo = self.node_manager.node_info(clicked_item.uid)
        new_ports_open: list[PortId] = new_node_info.filter_ports_by_status(PortStatus.COMPULSORY)
        for port in clicked_item.node_state.ports_open:
            if (port.key in new_node_info.prop_defs) and (port not in new_ports_open):
                if (port.is_input and new_node_info.prop_defs[port.key].input_port_status != PortStatus.FORBIDDEN) or (not port.is_input and new_node_info.prop_defs[port.key].output_port_status != PortStatus.FORBIDDEN):
                    new_ports_open.append(port)
        clicked_item.reset_ports_open(new_ports_open)
        clicked_item.update_visualisations()

    def extract_element(self, node_item: NodeItem, prop_key: PropKey):
        self.undo_stack.push(ExtractElementCmd(node_item, prop_key))


class PipelineView(QGraphicsView):
    """View to interact with the pipeline scene"""

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.mouse_pos = scene.sceneRect().center()
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))

        # Zoom settings
        self.default_zoom = 0.8
        self.zoom_factor = 1.15
        self.zoom_min = 0.1
        self.zoom_max = 10.0
        self.current_zoom = self.default_zoom
        self.setTransform(QTransform().scale(self.current_zoom, self.current_zoom))

        self.centerOn(0, 0)

        # Add grid lines
        self.draw_grid()

    def event(self, event):
        """Handle macOS native pinch-to-zoom gesture"""
        if isinstance(event, QNativeGestureEvent) and event.gestureType() == Qt.ZoomNativeGesture:
            return self.zoomNativeEvent(event)
        return super().event(event)

    def zoomNativeEvent(self, event: QNativeGestureEvent):
        """Zoom in/out based on pinch gesture on macOS"""
        # event.value() > 0 means pinch out (zoom in), < 0 means pinch in (zoom out)
        sensitivity = 0.7
        factor = 1 + event.value() * sensitivity  # Typically a small float, e.g. ±0.1
        resulting_zoom = self.current_zoom * factor

        if resulting_zoom < self.zoom_min or resulting_zoom > self.zoom_max:
            return True  # consume event, but no zoom

        self.scale(factor, factor)
        self.current_zoom *= factor
        self.update()
        return True  # event handled

    def wheelEvent(self, event):
        """Handle zoom or pan based on wheel/trackpad event"""
        delta = event.angleDelta()
        delta_x = delta.x()
        delta_y = delta.y()
        threshold = 15  # Dead zone for accidental touches

        # Ctrl/Command+Scroll = Zoom
        if event.modifiers() & Qt.ControlModifier:
            if abs(delta_y) < threshold:
                return  # Too small, ignore
            zoom_in = delta_y > 0
            factor = self.zoom_factor if zoom_in else 1 / self.zoom_factor
            resulting_zoom = self.current_zoom * factor

            if self.zoom_min <= resulting_zoom <= self.zoom_max:
                self.scale(factor, factor)
                self.current_zoom *= factor
                self.update()
            return

        # Otherwise, treat as panning (touchpad 2-finger scroll)
        # Use scroll deltas to translate the view
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta_x)
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta_y)

    def zoom(self, factor):
        resulting_zoom = self.current_zoom * factor
        if resulting_zoom < self.zoom_min or resulting_zoom > self.zoom_max:
            return
        self.scale(factor, factor)
        self.current_zoom *= factor
        self.update()

    def set_zoom(self, zoom):
        self.setTransform(QTransform().scale(zoom, zoom))
        self.current_zoom = zoom
        self.update()

    def reset_zoom(self):
        self.set_zoom(self.default_zoom)

    def draw_grid(self):
        """Draw a grid background for the scene"""
        grid_size = 20
        scene_rect = self.scene().sceneRect()

        left = int(scene_rect.left())
        right = int(scene_rect.right())
        top = int(scene_rect.top())
        bottom = int(scene_rect.bottom())

        # Align to the grid
        left -= left % grid_size
        top -= top % grid_size

        # Draw vertical lines
        for x in range(left, right + 1, grid_size):
            line = QGraphicsLineItem(x, top, x, bottom)
            line.setPen(QPen(QColor(200, 200, 200), 1))
            line.setZValue(-1000)
            self.scene().addItem(line)

        # Draw horizontal lines
        for y in range(top, bottom + 1, grid_size):
            line = QGraphicsLineItem(left, y, right, y)
            line.setPen(QPen(QColor(200, 200, 200), 1))
            line.setZValue(-1000)
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

    def mouseMoveEvent(self, event):
        # Get mouse position relative to the scene
        self.mouse_pos = self.mapToScene(event.pos())
        super().mouseMoveEvent(event)


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

        # Add New scene action
        new_scene_action = QAction("New Scene", self)
        new_scene_action.setShortcut(QKeySequence.New)
        new_scene_action.triggered.connect(self.new_scene)
        file_menu.addAction(new_scene_action)

        # Add Save action
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_scene)
        file_menu.addAction(save_action)

        # Add Save As action
        save_action = QAction("Save As", self)
        save_action.setShortcut(QKeySequence.SaveAs)
        save_action.triggered.connect(self.save_as_scene)
        file_menu.addAction(save_action)

        # Add Load action
        load_action = QAction("Load from file", self)
        load_action.setShortcut("Ctrl+L")
        load_action.triggered.connect(self.load_scene)
        file_menu.addAction(load_action)

        scene_menu = menu_bar.addMenu("Scene")

        # Add Delete action
        delete = QAction("Delete", self)
        delete.setShortcut(Qt.Key_Backspace)
        delete.triggered.connect(self.delete_selected_items)
        scene_menu.addAction(delete)

        copy = QAction("Copy", self)
        copy.setShortcut(QKeySequence.Copy)
        copy.triggered.connect(self.copy_selected_subgraph)
        copy.setMenuRole(QAction.NoRole)
        scene_menu.addAction(copy)

        paste = QAction("Paste", self)
        paste.setShortcut(QKeySequence.Paste)
        paste.triggered.connect(self.paste_subgraph)
        paste.setMenuRole(QAction.NoRole)
        scene_menu.addAction(paste)

        # Add Select all action
        select_all = QAction("Select All", self)
        select_all.setShortcut(QKeySequence.SelectAll)
        select_all.triggered.connect(self.select_all)
        select_all.setMenuRole(QAction.NoRole)
        scene_menu.addAction(select_all)

        randomise = QAction("Randomise Selected Nodes", self)
        randomise.setShortcut("Ctrl+R")
        randomise.triggered.connect(self.randomise_selected)
        scene_menu.addAction(randomise)

        create_custom = QAction("Group Nodes to Custom Node", self)
        create_custom.setShortcut("Ctrl+G")
        create_custom.triggered.connect(self.register_custom_node)
        scene_menu.addAction(create_custom)

        # Add Undo action
        undo = self.scene.undo_stack.createUndoAction(self, "Undo")
        undo.setShortcut(QKeySequence.Undo)
        scene_menu.addAction(undo)

        # Add Redo action
        redo = self.scene.undo_stack.createRedoAction(self, "Redo")
        redo.setShortcut(QKeySequence.Redo)
        scene_menu.addAction(redo)

        # Add Zoom in action
        zoom_in = QAction("Zoom In", self)
        zoom_in.setShortcut(QKeySequence.ZoomIn)
        zoom_in.triggered.connect(lambda: self.view.zoom(self.view.zoom_factor))
        scene_menu.addAction(zoom_in)

        # Add Zoom out action
        zoom_out = QAction("Zoom Out", self)
        zoom_out.setShortcut(QKeySequence.ZoomOut)
        zoom_out.triggered.connect(lambda: self.view.zoom(1 / self.view.zoom_factor))
        scene_menu.addAction(zoom_out)

        # Add Reset zoom action
        reset_zoom = QAction("Reset Zoom", self)
        reset_zoom.setShortcut("Ctrl+0")
        reset_zoom.triggered.connect(self.view.reset_zoom)
        scene_menu.addAction(reset_zoom)

        # Add Centre view action
        centre = QAction("Centre View", self)
        centre.setShortcut("Ctrl+1")
        centre.triggered.connect(lambda: self.view.centerOn(0, 0))
        scene_menu.addAction(centre)

    def new_scene(self):
        self.scene.filepath = None
        self.scene.clear_scene()
        self.view.reset_zoom()
        self.view.centerOn(0, 0)
        self.scene.custom_node_defs = {}

    def save_as_scene(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Pipeline Scene",
            "",
            "Pipeline Scene Files (*.pipeline);;All Files (*)"
        )

        if filepath:
            self.scene.filepath = filepath
            self.save_scene()

    def save_scene(self):
        if self.scene.filepath:
            self.scene.save_scene(self.scene.filepath)
            self.statusBar().showMessage(f"Scene saved to {self.scene.filepath}", 3000)
        else:
            self.save_as_scene()

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

    def select_all(self):
        for item in self.scene.items():
            if isinstance(item, NodeItem) or isinstance(item, EdgeItem):
                item.setSelected(True)

    def register_custom_node(self):
        node_states, nodes, connections, port_refs = self.identify_selected_subgraph()
        subgraph = NodeGraph()
        node_states, nodes, connections, port_refs, old_to_new_id_map = self.deep_copy_subgraph(node_states, nodes,
                                                                                                connections, port_refs,
                                                                                                node_graph=subgraph)
        # Set up subgraph querier
        subgraph.node_map = nodes
        subgraph.ref_ports = port_refs
        for connection in connections:
            subgraph.add_edge(*connection)

        # Get node information for display
        new_ids_topo_order = subgraph.get_topo_order_subgraph()
        new_id_to_info = {}
        for new_id in new_ids_topo_order:
            node = subgraph.node(new_id)
            unconnected_ports = subgraph.unconnected_ports(new_id)
            base_name = node.base_node_name
            # Get port id (io, port_key) mapped to port display name
            port_map = {}
            ports_open = node_states[new_id].ports_open
            port_defs = node.get_port_defs()
            for port_id in ports_open:
                if port_id in unconnected_ports:
                    port_map[port_id] = port_defs[port_id].display_name
            if port_map:
                # Add base name and port map to new_id_to_info
                new_id_to_info[new_id] = (base_name, port_map)
        new_to_old_id_map = {v: k for k, v in old_to_new_id_map.items()}
        old_id_to_info = {new_to_old_id_map[k]: v for k, v in new_id_to_info.items()}
        # Get node information from user
        dialog = RegCustomDialog(old_id_to_info, self.scene.custom_node_defs.keys())
        if dialog.exec_():
            # Get input and output node ids
            name, description, input_sel_ports, output_sel_ports, vis_sel_node = dialog.get_inputs()
            selected_ports = defaultdict(list)
            for node_id, port_id in input_sel_ports + output_sel_ports:
                selected_ports[old_to_new_id_map[node_id]].append(port_id)
            selected_ports = dict(selected_ports)
            vis_sel_node = old_to_new_id_map[vis_sel_node]
            self.scene.undo_stack.push(RegisterCustomNodeCmd(self.scene, name,
                                                             CustomNodeDef(subgraph, selected_ports,
                                                                           vis_sel_node, description=description)))

    def identify_selected_items(self):
        node_states: dict[NodeId, NodeState] = {}
        edges: set[EdgeId] = set()
        for item in self.scene.selectedItems():
            if isinstance(item, NodeItem):
                node_states[item.node_state.node] = copy.deepcopy(item.node_state)
            elif isinstance(item, EdgeItem):
                edges.add(item.edge)
        return node_states, edges

    def delete_selected_items(self):
        node_states, edges = self.identify_selected_items()
        if node_states or edges:
            subset_node_manager: NodeManager = self.scene.node_manager.subset_node_manager({node for node in node_states})
            port_refs: dict[NodeId, dict[PortId, RefId]] = {node: copy.deepcopy(port_ref_data) for node, port_ref_data in
                         self.scene.node_graph.node_to_port_ref.items() if node in node_states}
            self.scene.undo_stack.push(DeleteCmd(self.scene, node_states, subset_node_manager, edges, port_refs))

    def identify_selected_subgraph(self):
        node_states, edges = self.identify_selected_items()
        subset_node_manager: NodeManager = self.scene.node_manager.subset_node_manager({node for node in node_states})
        # Remove edges which are not connected at both ends to selected nodes
        edges_to_remove = {
            edge for edge in edges
            if edge.src_node not in node_states or edge.dst_node not in node_states
        }
        edges.difference_update(edges_to_remove)
        # Get relevant port refs
        new_port_refs: dict[NodeId, dict[PortId, RefId]] = {}
        dst_nodes = {edge.dst_node for edge in edges}
        for dst_node in dst_nodes:
            if dst_node in self.scene.node_graph.node_to_port_ref:
                port_refs = self.scene.node_graph.node_to_port_ref[dst_node]
                # Port refs exist, add
                new_port_refs[dst_node] = copy.deepcopy(port_refs)
                for port in port_refs:
                    # Remove port refs referring to non-relevant nodes
                    if port.node not in node_states:
                        del new_port_refs[dst_node][port]
        # Return node states and connections between them
        return node_states, subset_node_manager, edges, new_port_refs

    def deep_copy_subgraph(self, node_states, nodes, connections, port_refs, node_graph=None):
        node_graph = node_graph or self.scene.node_graph
        old_to_new_id_map: dict[NodeId, NodeId] = {}
        # Copy nodes
        new_node_states: dict[NodeId, NodeState] = {}
        for node_state in node_states:
            new_uid: NodeId = gen_node_id()
            # Copy node state
            new_node_state: NodeState = copy.deepcopy(node_state)
            new_node_state.node = new_uid # Update id in node state
            new_node_states[new_uid] = new_node_state # Add to new node states
            # Copy node
            node = nodes[node_state.node]
            new_node = copy.deepcopy(node)
            new_node.port = new_uid
            new_node.graph_querier = node_graph  # Set graph querier
            new_nodes[new_uid] = new_node
            # Add id to conversion map
            old_to_new_id_map[node_state.node] = new_uid
        # Update ids in connections
        new_connections = []
        for (src_node_id, src_port_key), (dst_node_id, dst_port_key) in connections:
            new_connections.append(((old_to_new_id_map[src_node_id], src_port_key),
                                    (old_to_new_id_map[dst_node_id], dst_port_key)))
        # Update ids in port refs
        new_port_refs = {}
        for dst_conn_id in port_refs:
            dst_node_id, dst_port_key = dst_conn_id
            new_entry = copy.deepcopy(port_refs[dst_conn_id])
            for ref_id, (src_node_id, src_port_key) in new_entry['ref_map'].items():
                new_entry['ref_map'][ref_id] = (old_to_new_id_map[src_node_id], src_port_key)
            new_port_refs[(old_to_new_id_map[dst_node_id], dst_port_key)] = new_entry
        # Return results
        return new_node_states, new_nodes, new_connections, new_port_refs, old_to_new_id_map

    def copy_selected_subgraph(self):
        node_states, nodes, connections, port_refs = self.identify_selected_subgraph()
        if node_states:
            # Calculate bounding rect
            bounding_rect = None
            for node_state in node_states:
                node_item = self.scene.node_items[node_state.node]
                # Make part of bounding rect
                if bounding_rect:
                    bounding_rect = bounding_rect.united(node_item.sceneBoundingRect())
                else:
                    bounding_rect = node_item.sceneBoundingRect()
            # Save to clipboard
            mime_data = QMimeData()
            mime_data.setData("application/pipeline_editor_items",
                              pickle.dumps((node_states, nodes, connections, port_refs, bounding_rect.center())))
            clipboard = QApplication.clipboard()
            clipboard.setMimeData(mime_data)

    def paste_subgraph(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()

        if mime.hasFormat("application/pipeline_editor_items"):
            raw_data = mime.data("application/pipeline_editor_items")
            # Deserialize with pickle
            node_states, nodes, connections, port_refs, bounding_rect_centre = pickle.loads(bytes(raw_data))
            node_states, nodes, connections, port_refs, _ = self.deep_copy_subgraph(node_states, nodes, connections,
                                                                                    port_refs)
            node_states = node_states.values()
            # Modify positions
            offset = self.view.mouse_pos - bounding_rect_centre
            for node_state in node_states:
                node_state.pos = (node_state.pos[0] + offset.x(), node_state.pos[1] + offset.y())
            # Perform paste
            self.scene.undo_stack.push(PasteCmd(self.scene, node_states, nodes.values(), connections, port_refs))

    def randomise_selected(self):
        randomisable_ids = set()
        for item in self.scene.selectedItems():
            if isinstance(item, NodeItem):
                node = self.scene.node_graph.node(item.node_state.node)
                if node.randomisable:
                    randomisable_ids.add(node.port)
        self.scene.undo_stack.push(RandomiseNodesCmd(self.scene, randomisable_ids))


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as temp_dir:
        app = QApplication(sys.argv)
        editor = PipelineEditor(temp_dir=temp_dir)
        sys.exit(app.exec_())
