import copy
import math
import os
import pickle
import sys
import tempfile
from collections import defaultdict
from functools import partial
from typing import cast, Optional

from PyQt5.QtCore import QLineF, pyqtSignal, QObject, QRectF, QTimer, QMimeData, QRect
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QFont, QFontMetricsF, QTransform, QNativeGestureEvent, QKeySequence, \
    QFontMetrics, QRegion
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
                             QGraphicsLineItem, QMenu, QAction, QPushButton, QFileDialog, QGraphicsTextItem, QUndoStack,
                             QUndoCommand, QGraphicsProxyWidget, QDialog)
from PyQt5.QtWidgets import QGraphicsPathItem
from PyQt5.QtXml import QDomDocument, QDomElement

from app_state import NodeState, AppState, CustomNodeDef, NodeId
from delete_custom_node_dialog import DeleteCustomNodeDialog
from export_w_aspect_ratio import ExportWithAspectRatio
from id_datatypes import PortId, EdgeId, output_port, input_port, PropKey, node_changed_port, NodeIdGenerator
from node_graph import NodeGraph, RefId
from node_manager import NodeManager, NodeInfo
from node_props_dialog import NodePropertiesDialog
from nodes.all_nodes import get_node_classes
from nodes.node_defs import Node, PropDef, PortStatus, NodeCategory
from nodes.node_implementations.shapes import ShapeNode
from nodes.nodes import CombinationNode, CustomNode
from nodes.prop_types import PT_Element, PT_Warp, PT_Function, PT_Grid, PT_List, PT_Scalar, PropType, PT_Fill
from nodes.prop_values import PropValue
from nodes.shape_datatypes import Group, Element
from reg_custom_dialog import RegCustomDialog
from selectable_renderer import SelectableSvgElement
from vis_types import Visualisable


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

        # Change node colour based on category:
        if node_info.category == NodeCategory.SOURCE or node_info.category == NodeCategory.CANVAS:
            # Purple
            node_colour = QColor(195, 195, 225)
        elif node_info.category == NodeCategory.SHAPE_COMPOUNDER:
            # Blue
            node_colour = QColor(215, 225, 245)
        elif node_info.category == NodeCategory.PROPERTY_MODIFIER:
            # Peach
            node_colour = QColor(240, 220, 200)
        elif node_info.category == NodeCategory.SELECTOR:
            # Grey
            node_colour = QColor(220, 220, 230)
        else:
            # Green
            node_colour = QColor(200, 230, 220)
        self.setBrush(QBrush(node_colour))
        self.setPen(QPen(Qt.black, 2))

        # Add property button
        self._property_button = None
        if node_info.requires_property_box():
            self._property_button = QPushButton("P")
            self._property_button.setFixedSize(20, 20)
            self._property_button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #646464;
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

        # Add play button
        self._play_button = None
        if node_info.animatable:
            self._play_button = QPushButton("▶")
            self._play_button.setFixedSize(20, 20)
            self._play_button.setToolTip("Play animation")
            self._play_button.setStyleSheet("""
                        QPushButton {
                            background-color: #f0f0f0;
                            border: 1px solid #646464;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #cccccc;
                        }
                    """)
            self._play_button.clicked.connect(self.toggle_playback)

            # Proxy
            self._play_proxy = QGraphicsProxyWidget(self)
            self._play_proxy.setWidget(self._play_button)
            self._play_proxy.setZValue(101)

        # Add export button
        self._export_button = None
        if node_info.is_canvas:
            self._export_button = QPushButton("⬆")
            self._export_button.setFixedSize(20, 20)
            self._export_button.setToolTip("Export to SVG or PNG")
            self._export_button.setStyleSheet("""
                                    QPushButton {
                                        background-color: #f0f0f0;
                                        border: 1px solid #646464;
                                        font-weight: bold;
                                    }
                                    QPushButton:hover {
                                        background-color: #cccccc;
                                    }
                                """)
            self._export_button.clicked.connect(self.export_image)

            # Proxy
            self._export_proxy = QGraphicsProxyWidget(self)
            self._export_proxy.setWidget(self._export_button)
            self._export_proxy.setZValue(101)

        self._help_icon_rect = QRectF()
        self._help_hover_timer = QTimer()
        self._help_hover_timer.setSingleShot(True)
        self._help_hover_timer.timeout.connect(self._showHelpTooltip)
        self._help_tooltip = None
        self.setAcceptHoverEvents(True)

        # Set the help text for this node
        self._help_text = f"{node_info.base_name} Help:\n{node_info.description}"

        self.resize_handle = None
        if not node_info.is_canvas:
            # Add resize handle
            self.resize_handle = ResizeHandle(self, 'bottomright')

    def export_image(self):
        vis: Visualisable = self.visualise()
        if isinstance(vis, Element):
            svg_path: str = os.path.join(self.scene().temp_dir, f"{self.uid}_export.svg")
            width: int = self.node_manager.get_internal_property(self.uid, 'width')
            height: int = self.node_manager.get_internal_property(self.uid, 'height')
            dialog = ExportWithAspectRatio(svg_path, vis, width, height)
            dialog.exec_()
        # TODO: put warning here

    def update_play_btn_text(self):
        text = "❚❚" if self.node_manager.is_playing(self.uid) else "▶"
        self._play_button.setText(text)

    def toggle_playback(self):
        if self.node_manager.is_playing(self.uid):
            self.scene().undo_stack.push(PauseNodesCmd(self.scene(), {self.uid}))
        else:
            self.scene().undo_stack.push(PlayNodesCmd(self.scene(), {self.uid}))

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

    def change_properties(self, props_changed, ports_toggled: dict[PortId, bool]):
        self.scene().undo_stack.push(ChangePropertiesCmd(self, props_changed, ports_toggled))

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

        # Remove invalid keys (from extracted elements)
        invalid_keys: set[PropKey] = {port.key for port in self.node_state.ports_open if
                                      port.key not in self.node_info.prop_defs}
        for key in invalid_keys:
            self.scene().undo_stack.push(RemoveExtractedElementCmd(self, key))

        # Update output port shapes
        for port, port_item in self.port_items.items():
            if port.is_input:
                # Update input port shape
                incoming_edges: set[EdgeId] = self.node_graph.incoming_edges(port)
                if not incoming_edges:
                    # No incoming edges, defer to default
                    port_item.create_shape_for_port_type()
                elif len(incoming_edges) > 1:
                    # More than one edge
                    port_item.create_shape_for_port_type(PT_List())
                else:
                    # One edge, match port shape of source port
                    edge: EdgeId = next(iter(incoming_edges))
                    src_port_item: PortItem = self.scene().port_item(edge.src_port)
                    port_item.draw_port(src_port_item.curr_port_shape)
            else:
                # Update output port shape
                value: Optional[PropValue] = self.node_manager.get_compute_result(port.node, port.key)
                if value is None:
                    port_item.create_shape_for_port_type()
                else:
                    assert isinstance(value, PropValue)
                    port_item.create_shape_for_port_type(value.type)

        svg_filepath = os.path.join(self.scene().temp_dir, f"{self.node_state.node}.svg")
        # Base position for all SVG elements
        svg_pos_x = self.left_max_width + NodeItem.MARGIN_X + NodeItem.LABEL_SVG_DIST
        svg_pos_y = NodeItem.TITLE_HEIGHT + NodeItem.MARGIN_Y
        svg_width, svg_height = self.node_state.svg_size

        vis.save_to_svg(svg_filepath, svg_width, svg_height)
        if not self.node_info.selectable:
            self.svg_item = QGraphicsSvgItem(svg_filepath)
            # Apply position
            self.svg_item.setParentItem(self)
            self.svg_item.setPos(svg_pos_x, svg_pos_y)
            self.svg_item.setZValue(2)
        else:
            assert isinstance(vis, Group)
            assert not vis.transform_list.transforms

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
            self.add_port(port, update_layout=False)
        self.update_label_port_positions(update_vis=update_vis)

    def reset_ports_open(self, new_ports_open: list[PortId]):
        # Remove ports no longer in use
        ports_open = self.node_state.ports_open
        for port in ports_open:
            if port not in new_ports_open:
                # Update layout at the end for efficiency
                self.remove_port(port, update_layout=False)
        # Add new ports
        new_port_items = {}
        for port in new_ports_open:
            if port not in self.node_state.ports_open:
                # Update layout at the end for efficiency
                self.add_port(port, update_layout=False)
            new_port_items[port] = self.port_items[port]
        # Set new port item order
        self.port_items = new_port_items
        self.update_label_port_positions()

    def add_port(self, port: PortId, update_layout=True) -> None:
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
        title_text = self.node_info.base_name
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

        # Place optional buttons
        if self._property_button:
            self._property_proxy.setPos(QPointF(x_offset, self.rect().top() + 5))
            x_offset -= 25  # Move left for next button

        if self._randomise_button:
            self._randomise_proxy.setPos(QPointF(x_offset, self.rect().top() + 5))
            x_offset -= 25  # Move left for next button

        if self._play_button:
            self._play_proxy.setPos(QPointF(x_offset, self.rect().top() + 5))
            x_offset -= 25  # Move left for next button

        if self._export_button:
            self._export_proxy.setPos(QPointF(x_offset, self.rect().top() + 5))
            x_offset -= 25  # Move left for next button

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
        del self.scene().node_items[self.uid]  # Remove reference to item
        self.node_manager.remove_node(self.uid)  # Remove from node manager
        self.scene().removeItem(self)


class PortItem(QGraphicsPathItem):
    """Represents connection points on nodes with shapes based on port_type"""

    def __init__(self, port: PortId, parent: NodeItem):
        super().__init__(parent)
        self.port = port
        self.curr_port_shape: Optional[str] = None
        self.edge_items: dict[PortId, EdgeItem] = {}  # Key is the port that it is connected to by the edge

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

    def draw_port(self, shape: str):
        if shape == self.curr_port_shape:
            return
        self.curr_port_shape = shape
        path = QPainterPath()
        half_size = self.size / 2
        if shape == 'circle':
            path.addEllipse(-half_size, -half_size, self.size, self.size)
        elif shape == 'rounded_square':
            path.addRoundedRect(-half_size, -half_size, self.size, self.size, 3, 3)
        elif shape == 'diamond':
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
        elif shape == 'square':
            path.addRect(-half_size, -half_size, self.size, self.size)
        elif shape == 'hexagon':
            points = []
            for i in range(6):
                angle = i * (360 / 6) * (3.14159 / 180)
                points.append(QPointF(half_size * 0.9 * math.cos(angle),
                                      half_size * 0.9 * math.sin(angle)))

            path.moveTo(points[0])
            for i in range(1, 6):
                path.lineTo(points[i])
            path.closeSubpath()
        elif shape == 'triangle':
            points = [
                QPointF(0, -half_size),  # Top
                QPointF(half_size * 0.866, half_size / 2),  # Bottom right
                QPointF(-half_size * 0.866, half_size / 2)  # Bottom left
            ]
            path.moveTo(points[0])
            path.lineTo(points[1])
            path.lineTo(points[2])
            path.closeSubpath()
        else:
            # Draw a star
            points = []
            for i in range(10):
                angle = i * (360 / 10) * (3.14159 / 180)
                radius = half_size * 0.9 if i % 2 == 0 else half_size * 0.4
                points.append(QPointF(radius * math.cos(angle),
                                      radius * math.sin(angle)))

            path.moveTo(points[0])
            for i in range(1, 10):
                path.lineTo(points[i])
            path.closeSubpath()
        self.setPath(path)

    def create_shape_for_port_type(self, temp_port_type=None):
        port_type = self.port_type if temp_port_type is None else temp_port_type
        port_shape = 'star'
        if type(port_type) != PropType:
            if port_type.is_compatible_with(PT_Element()):
                # Circle for element type
                port_shape = 'circle'
            elif port_type.is_compatible_with(PT_Fill()):
                # Rounded square for fill type
                port_shape = 'rounded_square'
            elif port_type.is_compatible_with(PT_Function()) or port_type.is_compatible_with(PT_Warp()):
                # Diamond for function or warp type
                port_shape = 'diamond'
            elif port_type.is_compatible_with(PT_Grid()):
                # Square for grid type
                port_shape = 'square'
            elif port_type.is_compatible_with(PT_Scalar()):
                # Triangle for scalar type
                port_shape = 'triangle'
            elif port_type.is_compatible_with(PT_List(PT_Scalar())):
                # Hexagon for list type
                port_shape = 'hexagon'
        # Update port shape
        self.draw_port(port_shape)

    def get_center_scene_pos(self):
        # For a path item, we need to calculate the center differently
        return self.mapToScene(self.boundingRect().center())

    def hoverEnterEvent(self, event):
        self.setPen(QPen(Qt.red, 2))
        if not self.port.is_input:
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
        node: NodeId = self.node_state.node if self.node_state else self.scene.gen_node_id()
        base_node: Node = self.node_class(add_info=self.add_info)
        self.node_graph.add_node(node)
        self.node_manager.add_node(node, base_node)
        node_info: NodeInfo = self.node_manager.node_info(node)
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
        self.node_graph = self.scene.node_graph
        self.edge = edge

    def undo(self):
        self.scene.remove_edge(self.edge)

    def redo(self):
        self.node_graph.add_edge(self.edge)
        self.scene.add_edge(self.edge)


class ChangePropertiesCmd(QUndoCommand):
    def __init__(self, node_item: NodeItem, props_changed, ports_toggled: dict[PortId, bool],
                 description="Change properties"):
        super().__init__(description)
        self.node_item = node_item
        self.node_manager: NodeManager = node_item.node_manager
        self.props_changed = props_changed
        self.ports_toggled = ports_toggled
        self.opened_ports_exist = True

    def update_properties(self, props):
        for prop_key, value in props.items():
            self.node_manager.set_internal_property(self.node_item.uid, prop_key, value)
            if self.node_manager.node_info(self.node_item.uid).is_canvas and (
                    prop_key == 'width' or prop_key == 'height'):
                svg_width = self.node_manager.get_internal_property(self.node_item.uid, 'width')
                svg_height = self.node_manager.get_internal_property(self.node_item.uid, 'height')
                self.node_item.resize(*self.node_item.node_size_from_svg_size(svg_width, svg_height))
        # Update the node's appearance
        self.node_item.update_visualisations()

    def open_ports(self, reverse: bool):
        for port, is_open in self.ports_toggled.items():
            actually_open = not is_open if reverse else is_open
            if actually_open:
                self.node_item.add_port(port)
            else:
                self.node_item.remove_port(port)

    def undo(self):
        props = {}
        for prop_name, value in self.props_changed.items():
            props[prop_name] = value[0]  # Take the old value
        self.update_properties(props)
        assert self.opened_ports_exist
        self.open_ports(reverse=True)
        self.opened_ports_exist = False

    def redo(self):
        props = {}
        for prop_name, value in self.props_changed.items():
            props[prop_name] = value[1]  # Take the new value
        self.update_properties(props)
        if not self.opened_ports_exist:
            self.open_ports(reverse=False)
            self.opened_ports_exist = True


class ExtractElementCmd(QUndoCommand):
    def __init__(self, node_item: NodeItem, prop_key: PropKey, description="Extract element"):
        super().__init__(description)
        self.node_item = node_item
        self.prop_key = prop_key

    def undo(self):
        self.node_item.remove_port(output_port(self.node_item.uid, self.prop_key))

    def redo(self):
        self.node_item.add_port(output_port(self.node_item.uid, self.prop_key))


class RemoveExtractedElementCmd(QUndoCommand):
    def __init__(self, node_item: NodeItem, prop_key: PropKey, description="Remove extracted element"):
        super().__init__(description)
        self.node_item = node_item
        self.prop_key = prop_key

    def undo(self):
        self.node_item.add_port(output_port(self.node_item.uid, self.prop_key))

    def redo(self):
        self.node_item.remove_port(output_port(self.node_item.uid, self.prop_key))


class PasteCmd(QUndoCommand):
    def __init__(self, scene, node_states: dict[NodeId, NodeState], base_nodes: dict[NodeId, Node], edges: set[EdgeId],
                 port_refs: dict[NodeId, dict[PortId, RefId]], description="Paste"):
        super().__init__(description)
        self.scene = scene
        self.node_states = node_states
        self.base_nodes = base_nodes
        self.edges = edges
        self.port_refs = port_refs

    def undo(self):
        self.scene.remove_from_graph_and_scene(self.node_states.keys(), self.edges)

    def redo(self):
        self.scene.add_to_graph_and_scene(self.node_states, self.base_nodes, self.edges, self.port_refs)


class DeleteCmd(QUndoCommand):
    def __init__(self, scene, node_states: dict[NodeId, NodeState], base_nodes: dict[NodeId, Node], edges: set[EdgeId],
                 port_refs: dict[NodeId, dict[PortId, RefId]], description="Delete"):
        super().__init__(description)
        self.scene = scene
        self.node_states = node_states
        self.base_nodes = base_nodes
        self.edges = edges
        self.port_refs = port_refs

    def undo(self):
        self.scene.add_to_graph_and_scene(self.node_states, self.base_nodes, self.edges, self.port_refs)

    def redo(self):
        self.scene.remove_from_graph_and_scene(self.node_states.keys(), self.edges)


class RandomiseNodesCmd(QUndoCommand):
    def __init__(self, scene, nodes: set[NodeId], description="Randomise node(s)"):
        super().__init__(description)
        self.scene = scene
        self.node_manager: NodeManager = scene.node_manager
        self.nodes = nodes  # Assumes these nodes are randomisable
        self.prev_seeds = {}

    def undo(self):
        for node, prev_seed in self.prev_seeds.items():
            self.node_manager.randomise(node, prev_seed)
            self.scene.node_items[node].update_visualisations()

    def redo(self):
        for node in self.nodes:
            self.prev_seeds[node] = self.node_manager.get_seed(node)
            self.node_manager.randomise(node)  # TODO: store new seed for redo
            self.scene.node_item(node).update_visualisations()


class PlayNodesCmd(QUndoCommand):
    def __init__(self, scene, nodes: set[NodeId], description="Play node(s)"):
        super().__init__(description)
        self.scene = scene
        self.node_manager: NodeManager = scene.node_manager
        self.nodes = nodes  # Assumes these nodes are animatable
        self.play_states: dict[NodeId, bool] = {}  # Boolean is True if the node was playing

    def undo(self):
        for node in self.nodes:
            if not self.play_states[node]:
                self.node_manager.toggle_play(node)
                cast(NodeItem, self.scene.node_item(node)).update_play_btn_text()

    def redo(self):
        for node in self.nodes:
            playing: bool = self.node_manager.is_playing(node)
            self.play_states[node] = playing
            if not playing:
                self.node_manager.toggle_play(node)
                cast(NodeItem, self.scene.node_item(node)).update_play_btn_text()


class PauseNodesCmd(QUndoCommand):
    def __init__(self, scene, nodes: set[NodeId], description="Pause node(s)"):
        super().__init__(description)
        self.scene = scene
        self.node_manager: NodeManager = scene.node_manager
        self.nodes = nodes  # Assumes these nodes are animatable
        self.play_states: dict[NodeId, bool] = {}  # Boolean is True if the node was playing

    def undo(self):
        for node in self.nodes:
            if self.play_states[node]:
                self.node_manager.toggle_play(node)
                cast(NodeItem, self.scene.node_item(node)).update_play_btn_text()

    def redo(self):
        for node in self.nodes:
            playing: bool = self.node_manager.is_playing(node)
            self.play_states[node] = playing
            if playing:
                self.node_manager.toggle_play(node)
                cast(NodeItem, self.scene.node_item(node)).update_play_btn_text()


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
        self.source_port_item = None
        self.dest_port_item = None

        self.node_items = {}
        self.custom_node_defs: dict[str, CustomNodeDef] = {}
        self.node_manager: NodeManager = NodeManager()
        self.node_id_generator: NodeIdGenerator = NodeIdGenerator()

        self.temp_dir = temp_dir
        self.undo_stack = QUndoStack()
        self.filepath = None

        # Connect signals
        self.connection_signals.connectionStarted.connect(self.start_connection)
        self.connection_signals.connectionMade.connect(self.finish_connection)

        # Animation
        self.timer = QTimer()
        self.timer_interval_ms = 10
        self.timer.setInterval(self.timer_interval_ms)
        self.timer.timeout.connect(self.animate)
        # TODO: uncomment this when figure out efficiency
        self.timer.start()

    def gen_node_id(self) -> NodeId:
        return self.node_id_generator.gen_node_id()

    def animate(self):
        for node in self.node_manager.playing_nodes():
            # Perform animation logic here
            if self.node_manager.reanimate(node, self.timer_interval_ms):
                self.node_item(node).update_visualisations()

    @property
    def node_graph(self):
        return self.node_manager.node_graph

    def view(self):
        return self.views()[0]

    def add_new_node(self, pos, node, add_info=None):
        self.undo_stack.push(AddNewNodeCmd(self, pos, node, add_info=add_info))

    def edit_node_properties(self, node):
        """Open a dialog to edit the node's properties"""
        NodePropertiesDialog(node).exec_()

    def start_connection(self, source_port_item: PortItem):
        """Start creating a connection from the given source port"""
        if source_port_item and not source_port_item.port.is_input:
            self.source_port_item = source_port_item
            start_pos = source_port_item.get_center_scene_pos()

            # Create a temporary line for visual feedback
            self.temp_line = QGraphicsLineItem()
            self.temp_line.setLine(QLineF(start_pos, start_pos))
            self.temp_line.setPen(QPen(Qt.darkGray, 2, Qt.DashLine))
            self.addItem(self.temp_line)

    def update_temp_connection(self, end_pos):
        """Update the temporary connection line to the current mouse position"""
        if self.source_port_item and self.temp_line:
            start_pos = self.source_port_item.get_center_scene_pos()
            self.temp_line.setLine(QLineF(start_pos, end_pos))

    def is_edge_type_valid(self, src_port: PortId, dst_port: PortId) -> bool:
        # Check compute result from source port is compatible with type of dest port
        compute_res: Optional[PropValue] = self.node_manager.get_compute_result(src_port.node, src_port.key)
        if not compute_res:
            # None input is allowed
            return True
        dst_port_type: PropType = self.node_manager.node_info(dst_port.node).prop_defs[dst_port.key].prop_type
        return compute_res.type.is_compatible_with(dst_port_type)

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
                if not connection_exists and (
                        not target_has_connection or dest_port_item.port_type.input_multiple) and self.is_edge_type_valid(
                    source_port_item.port, dest_port_item.port):
                    # Add the connection
                    self.undo_stack.push(
                        AddNewEdgeCmd(self, edge))

        # Clean up temporary line
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None

        # Reset ports
        self.source_port_item = None
        self.dest_port_item = None

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
        if self.source_port_item and self.temp_line:
            self.update_temp_connection(event.scenePos())

            # Highlight input port if we're hovering over one
            item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.view()))
            if isinstance(item, PortItem) and item.port.is_input:
                if self.dest_port_item != item:
                    # Reset previous dest port highlighting
                    if self.dest_port_item:
                        self.dest_port_item.setPen(QPen(Qt.black, 1))

                    # Set new dest port
                    self.dest_port_item = item
                    self.dest_port_item.setPen(QPen(Qt.red, 2))
            elif self.dest_port_item:
                # Reset dest port highlighting if not hovering over an input port
                self.dest_port_item.setPen(QPen(Qt.black, 1))
                self.dest_port_item = None

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events for the scene"""
        if event.button() == Qt.LeftButton and self.source_port_item:
            item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.view()))
            if isinstance(item, PortItem) and item.port.is_input:
                # Create permanent connection
                self.connection_signals.connectionMade.emit(self.source_port_item, item)
                event.accept()
                return
            else:
                # Clean up if not released over an input port
                if self.temp_line:
                    self.removeItem(self.temp_line)
                    self.temp_line = None
                self.source_port_item = None

                # Reset dest port highlighting if needed
                if self.dest_port_item:
                    self.dest_port_item.setPen(QPen(Qt.black, 1))
                    self.dest_port_item = None

        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        """Handle context menu events for the scene"""
        if self.skip_next_context_menu:
            self.skip_next_context_menu = False
            event.accept()  # Suppress the default scene menu
            return

        clicked_item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.view()))

        # if isinstance(clicked_item, PortItem):
        #     # Print type for debugging
        #     port: PortId = clicked_item.port
        #     print(
        #         f"Node {port.node} ({'Input' if port.is_input else 'Output'}, {port.key}): {clicked_item.port_type}")

        if isinstance(clicked_item, NodeItem):
            node_info: NodeInfo = clicked_item.node_info
            # Context menu for nodes
            menu = QMenu()
            # separate_from_inputs_action = QAction("Separate from inputs", menu)
            # separate_from_inputs_action.triggered.connect(lambda: self.separate_from_inputs_action(clicked_item))
            # menu.addAction(separate_from_inputs_action)
            if node_info.combination:
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
            for category, node_classes in get_node_classes():
                if len(node_classes) > 1:
                    category_menu = menu.addMenu(f"{category.value[1]}s")
                else:
                    category_menu = menu
                for node_class in node_classes:
                    if issubclass(node_class, CombinationNode):
                        submenu = category_menu.addMenu(f"{node_class.name()}s")
                        for i in range(len(node_class.selections())):
                            change_action = QAction(node_class.selections()[i].name(), submenu)
                            handler = partial(self.add_new_node, event.scenePos(), node_class, add_info=i)
                            change_action.triggered.connect(handler)
                            submenu.addAction(change_action)
                    else:
                        action = QAction(node_class.name(), category_menu)
                        handler = partial(self.add_new_node, event.scenePos(), node_class)
                        action.triggered.connect(handler)
                        category_menu.addAction(action)
            # Add custom nodes
            if self.custom_node_defs:
                menu.addSeparator()
                sorted_custom_node_defs = sorted(self.custom_node_defs.items(), key=lambda item: item[0])
                for name, node_def in sorted_custom_node_defs:
                    action = QAction(name, menu)
                    handler = partial(self.add_new_node, event.scenePos(), CustomNode,
                                      add_info=(name, copy.deepcopy(node_def)))
                    action.triggered.connect(handler)
                    menu.addAction(action)

            menu.exec_(event.screenPos())

    def save_scene(self, filepath):
        view = self.view()
        center = view.mapToScene(view.viewport().rect().center())
        zoom = view.current_zoom
        with open(filepath, "wb") as f:
            pickle.dump(AppState(view_pos=(center.x(), center.y()),
                                 zoom=zoom,
                                 node_states=[node_item.node_state for node_item in self.node_items.values()],
                                 node_manager=self.node_manager,
                                 custom_node_defs=self.custom_node_defs,
                                 next_node_id=self.node_id_generator.next_id), f)

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

    def add_to_graph_and_scene(self, node_states: dict[NodeId, NodeState], base_nodes: dict[NodeId, Node],
                               edges: set[EdgeId], more_node_to_port_refs: dict[NodeId, dict[PortId, RefId]]):
        # Add to node implementations
        self.node_manager.update_nodes(base_nodes)
        # Update graph
        for node in node_states:
            self.node_graph.add_node(node)
        for edge in edges:
            self.node_graph.add_edge(edge)
        self.node_graph.extend_port_refs(more_node_to_port_refs)
        # Load items
        self.load_from_node_states(node_states.values(), edges)

    def remove_from_graph_and_scene(self, nodes: set[NodeId], edges: set[EdgeId]):
        # Get affected nodes
        affected_nodes: set[NodeId] = set()
        for node in nodes:
            affected_nodes.update(self.node_graph.output_nodes(node))
        for edge in edges:
            affected_nodes.add(edge.dst_node)
        affected_nodes.difference_update(nodes)

        # Remove nodes
        for node in nodes:
            node_item = self.node_item(node)
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
            app_state: AppState = pickle.load(f)

        self.view().centerOn(*app_state.view_pos)
        self.view().set_zoom(app_state.zoom)
        self.node_manager = app_state.node_manager
        self.custom_node_defs = app_state.custom_node_defs
        self.node_id_generator = NodeIdGenerator(app_state.next_node_id)
        self.load_from_node_states(app_state.node_states, self.node_graph.edges)
        self.undo_stack.clear()
        self.filepath = filepath

    def change_node_selection(self, clicked_item: NodeItem, index):
        self.node_manager.set_selection(clicked_item.uid, index)
        new_node_info: NodeInfo = self.node_manager.node_info(clicked_item.uid)
        new_ports_open: list[PortId] = new_node_info.filter_ports_by_status(PortStatus.COMPULSORY)
        for port in clicked_item.node_state.ports_open:
            if (port.key in new_node_info.prop_defs) and (port not in new_ports_open):
                if (port.is_input and new_node_info.prop_defs[port.key].input_port_status != PortStatus.FORBIDDEN) or (
                        not port.is_input and new_node_info.prop_defs[
                    port.key].output_port_status != PortStatus.FORBIDDEN):
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

        play_animate = QAction("Play Selected Animatable Nodes", self)
        play_animate.setShortcut("Ctrl+P")
        play_animate.triggered.connect(self.play_selected)
        scene_menu.addAction(play_animate)

        pause_animate = QAction("Pause Selected Animatable Nodes", self)
        pause_animate.setShortcut("Ctrl+Shift+P")
        pause_animate.triggered.connect(self.pause_selected)
        scene_menu.addAction(pause_animate)

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

        custom_node_menu = menu_bar.addMenu("Custom Nodes")

        create_custom = QAction("Register Custom Node", self)
        create_custom.setShortcut("Ctrl+G")
        create_custom.triggered.connect(self.register_custom_node)
        custom_node_menu.addAction(create_custom)

        # Add Delete action
        self.delete_custom_node_action = QAction("Unregister Custom Node", self)
        self.delete_custom_node_action.triggered.connect(self.delete_custom_node)
        self.update_delete_custom_action_enabled()
        custom_node_menu.addAction(self.delete_custom_node_action)

    def update_delete_custom_action_enabled(self):
        self.delete_custom_node_action.setEnabled(len(self.scene.custom_node_defs) > 0)

    def delete_custom_node(self):
        dialog = DeleteCustomNodeDialog(list(self.scene.custom_node_defs.keys()))
        if dialog.exec_() == QDialog.Accepted:
            selected_node = dialog.get_selected_node()
            del self.scene.custom_node_defs[selected_node]
            self.update_delete_custom_action_enabled()

    def new_scene(self):
        self.scene.filepath = None
        self.scene.clear_scene()
        self.view.reset_zoom()
        self.view.centerOn(0, 0)
        self.scene.custom_node_defs = {}
        self.update_delete_custom_action_enabled()
        self.scene.node_id_generator = NodeIdGenerator()
        self.scene.undo_stack.clear()

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
            self.update_delete_custom_action_enabled()

    def select_all(self):
        for item in self.scene.items():
            if isinstance(item, NodeItem) or isinstance(item, EdgeItem):
                item.setSelected(True)

    def register_custom_node(self):
        node_states, base_nodes, edges, port_refs = self.identify_selected_subgraph()
        node_states, base_nodes, edges, port_refs, old_to_new_id_map = self.deep_copy_subgraph(node_states, base_nodes,
                                                                                               edges,
                                                                                               port_refs)

        # Add nodes to sub node manager
        sub_node_manager: NodeManager = NodeManager()
        subgraph: NodeGraph = sub_node_manager.node_graph
        sub_node_manager.update_nodes(base_nodes)

        # Add nodes and edges to subgraph
        for node in node_states:
            subgraph.add_node(node)
        for edge in edges:
            subgraph.add_edge(edge)
        subgraph.extend_port_refs(port_refs)

        # Get set of all ports participating in edges
        connected_ports: set[PortId] = {
            port for edge in subgraph.edges for port in (edge.src_port, edge.dst_port)
        }

        # Get node information for display
        new_nodes_topo_order: list[NodeId] = subgraph.get_topo_order_subgraph()
        # Get map for mapping new node IDs to old IDs
        new_to_old_map = {v: k for k, v in old_to_new_id_map.items()}
        # Map old node ID to node base name and port display names
        old_node_info: dict[NodeId, tuple[str, dict[PortId, str]]] = {}
        for new_node in new_nodes_topo_order:
            old_node: NodeId = new_to_old_map[new_node]
            # Get node info and base name
            node_info: NodeInfo = sub_node_manager.node_info(new_node)
            base_name: str = node_info.base_name

            # Get unconnected (open) ports and their display names
            port_map: dict[PortId, str] = {}
            ports_open: list[PortId] = node_states[new_node].ports_open
            for port in ports_open:
                if port not in connected_ports:
                    port_map[node_changed_port(old_node, port)] = node_info.prop_defs[port.key].display_name
            if port_map:
                # Only add to new node info if it has unconnected ports
                old_node_info[old_node] = (base_name, port_map)

        # Get node information from user
        dialog = RegCustomDialog(old_node_info, self.scene.custom_node_defs.keys())
        if dialog.exec_():
            # Get input and output node ids
            name, description, input_sel_ports, output_sel_ports, vis_sel_node, custom_names_dict = dialog.get_inputs()
            # Update selected ports
            selected_ports: defaultdict[NodeId, list[PortId]] = defaultdict(list)
            for old_port in input_sel_ports + output_sel_ports:
                new_node: NodeId = old_to_new_id_map[old_port.node]
                selected_ports[new_node].append(node_changed_port(new_node, old_port))
            selected_ports: dict[NodeId, list[PortId]] = dict(selected_ports)
            # Update visualisation node
            vis_sel_node: NodeId = old_to_new_id_map[vis_sel_node]
            # Update custom names
            custom_names_dict = {(old_to_new_id_map[node], key): name for (node, key), name in
                                 custom_names_dict.items()}
            # Register the custom node
            if name not in self.scene.custom_node_defs:
                self.scene.custom_node_defs[name] = CustomNodeDef(sub_node_manager, selected_ports,
                                                                  custom_names_dict,
                                                                  vis_sel_node, description=description)
            else:
                print("Error: custom node definition with same name already exists.")
            self.update_delete_custom_action_enabled()

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
            base_nodes: dict[NodeId, Node] = self.scene.node_manager.get_node_copies(
                subset={node for node in node_states})
            port_refs: dict[NodeId, dict[PortId, RefId]] = {node: copy.deepcopy(port_ref_data) for node, port_ref_data
                                                            in
                                                            self.scene.node_graph.node_to_port_ref.items() if
                                                            node in node_states}
            self.scene.undo_stack.push(DeleteCmd(self.scene, node_states, base_nodes, edges, port_refs))

    def identify_selected_subgraph(self) -> tuple[
        dict[NodeId, NodeState], dict[NodeId, Node], set[EdgeId], dict[NodeId, dict[PortId, RefId]]]:
        node_states, edges = self.identify_selected_items()
        base_nodes: dict[NodeId, Node] = self.scene.node_manager.get_node_copies(subset={node for node in node_states})
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
        return node_states, base_nodes, edges, new_port_refs

    def copy_selected_subgraph(self):
        node_states, base_nodes, edges, port_refs = self.identify_selected_subgraph()
        if node_states:
            # Calculate bounding rect
            bounding_rect = None
            for node in node_states:
                node_item: NodeItem = self.scene.node_item(node)
                # Make part of bounding rect
                if bounding_rect:
                    bounding_rect = bounding_rect.united(node_item.sceneBoundingRect())
                else:
                    bounding_rect = node_item.sceneBoundingRect()
            # Save to clipboard
            mime_data = QMimeData()
            mime_data.setData("application/pipeline_editor_items",
                              pickle.dumps((node_states, base_nodes, edges, port_refs, bounding_rect.center())))
            clipboard = QApplication.clipboard()
            clipboard.setMimeData(mime_data)

    def deep_copy_subgraph(self, node_states: dict[NodeId, NodeState], base_nodes: dict[NodeId, Node],
                           edges: set[EdgeId],
                           port_refs: dict[NodeId, dict[PortId, RefId]]):
        old_to_new_id_map = {}
        # Update node states
        new_node_states: dict[NodeId, NodeState] = {}
        new_base_nodes: dict[NodeId, Node] = {}
        for node, node_state in node_states.items():
            new_node: NodeId = self.scene.gen_node_id()
            # Copy node state
            new_node_state: NodeState = copy.deepcopy(node_state)
            new_node_state.node = new_node  # Update id in node state
            new_node_state.ports_open = [PortId(node=new_node, key=port.key, is_input=port.is_input) for port in
                                         node_state.ports_open]
            new_node_states[new_node] = new_node_state  # Add to new node states
            # Copy node
            new_base_node = copy.deepcopy(base_nodes[node])
            new_base_nodes[new_node] = new_base_node
            # Add id to conversion map
            old_to_new_id_map[node_state.node] = new_node
        # Update ids in connections
        new_edges: set[EdgeId] = set()
        for edge in edges:
            new_edges.add(EdgeId(output_port(node=old_to_new_id_map[edge.src_node], key=edge.src_key),
                                 input_port(node=old_to_new_id_map[edge.dst_node], key=edge.dst_key)))
        # Update ids in port refs
        new_port_refs: dict[NodeId, dict[PortId, RefId]] = {}
        for dst_node in port_refs:
            new_entry: dict[PortId, RefId] = {}
            for port, ref in port_refs[dst_node].items():
                new_entry[PortId(node=old_to_new_id_map[port.node], key=port.key, is_input=port.is_input)] = ref
            new_port_refs[old_to_new_id_map[dst_node]] = new_entry
        # Return results
        return new_node_states, new_base_nodes, new_edges, new_port_refs, old_to_new_id_map

    def paste_subgraph(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()

        if mime.hasFormat("application/pipeline_editor_items"):
            raw_data = mime.data("application/pipeline_editor_items")
            # Deserialize with pickle
            node_states, base_nodes, edges, port_refs, bounding_rect_centre = pickle.loads(bytes(raw_data))
            node_states, base_nodes, edges, port_refs, _ = self.deep_copy_subgraph(node_states, base_nodes, edges,
                                                                                   port_refs)
            # Modify positions
            offset = self.view.mouse_pos - bounding_rect_centre
            for node_state in node_states.values():
                node_state.pos = (node_state.pos[0] + offset.x(), node_state.pos[1] + offset.y())
            # Perform paste
            self.scene.undo_stack.push(PasteCmd(self.scene, node_states, base_nodes, edges, port_refs))

    def randomise_selected(self):
        randomisable_nodes: set[NodeId] = set()
        for item in self.scene.selectedItems():
            if isinstance(item, NodeItem):
                node_info: NodeInfo = self.scene.node_manager.node_info(item.uid)
                if node_info.randomisable:
                    randomisable_nodes.add(item.uid)
        self.scene.undo_stack.push(RandomiseNodesCmd(self.scene, randomisable_nodes))

    def get_selected_animatable_nodes(self) -> set[NodeId]:
        animatable_nodes: set[NodeId] = set()
        for item in self.scene.selectedItems():
            if isinstance(item, NodeItem):
                node_info: NodeInfo = self.scene.node_manager.node_info(item.uid)
                if node_info.animatable:
                    animatable_nodes.add(item.uid)
        return animatable_nodes

    def play_selected(self):
        self.scene.undo_stack.push(PlayNodesCmd(self.scene, self.get_selected_animatable_nodes()))

    def pause_selected(self):
        self.scene.undo_stack.push(PauseNodesCmd(self.scene, self.get_selected_animatable_nodes()))


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as temp_dir:
        app = QApplication(sys.argv)
        editor = PipelineEditor(temp_dir=temp_dir)
        sys.exit(app.exec_())
