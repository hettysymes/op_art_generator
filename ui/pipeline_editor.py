import ast
import copy
import json
import math
import os
import pickle
import random
import sys
import tempfile
import traceback
from functools import partial

from PyQt5.QtCore import QLineF, pyqtSignal, QObject, QRectF, QTimer, QEvent, QMimeData
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QFont, QFontMetricsF, QTransform, QNativeGestureEvent, QFocusEvent, QKeySequence, \
    QFontMetrics
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
                             QGraphicsLineItem, QMenu, QAction, QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QSpinBox, QDoubleSpinBox, QComboBox, QPushButton, QCheckBox,
                             QDialogButtonBox, QGroupBox, QTableWidgetItem, QWidget,
                             QHBoxLayout, QFileDialog, QStyledItemDelegate, QColorDialog,
                             QGraphicsTextItem, QLabel, QUndoStack, QUndoCommand, QGraphicsProxyWidget)
from PyQt5.QtWidgets import QGraphicsPathItem
from PyQt5.QtXml import QDomDocument, QDomElement
from sympy.physics.quantum.cartesian import PositionState3D

from ui.app_state import NodeState
from ui.node_graph import NodeGraph
from ui.node_props_dialog import NodePropertiesDialog
from ui.nodes.all_nodes import node_setting
from ui.nodes.drawers.group_drawer import GroupDrawer
from ui.nodes.port_defs import PortIO, PT_Element, PT_Warp, PT_ValueList, PT_Function, PT_Grid
from ui.nodes.shape_datatypes import Group
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
    LABEL_FONT = QFont("Arial", 8)

    def __init__(self, node_state: NodeState):
        self.node_state = node_state
        self.left_max_width = NodeItem.MARGIN_Y - NodeItem.MARGIN_X
        self.right_max_width = NodeItem.MARGIN_Y - NodeItem.MARGIN_X
        if node_setting(self.node().name()).resizable:
            svg_width, svg_height = node_state.svg_size
            width, height = self.node_size_from_svg_size(svg_width, svg_height)
        else:
            # Assumes it's a canvas node TODO: also put constant somewhere
            width, height = self.node_size_from_svg_size(self.node().prop_vals.get('width', 150),
                                                         self.node().prop_vals.get('height', 150))
        super().__init__(0, 0, width, height)
        self.svg_items = None
        self.svg_item = None
        self.port_items = {} # Key is port id, value is port item
        pos_x, pos_y = node_state.pos
        self.setPos(pos_x, pos_y)
        self.setZValue(1)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setBrush(QBrush(QColor(220, 230, 250)))
        self.setPen(QPen(Qt.black, 2))

        if self.node().prop_entries().is_empty():
            self._property_button = None
        else:
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

    def node_graph(self):
        return self.scene().node_graph

    def node(self):
        return self.node_graph().node(self.node_state.node_id)
#
#     def hoverMoveEvent(self, event):
#         if self._help_icon_rect.contains(event.pos()):
#             if not self._help_hover_timer.isActive():
#                 # Start the timer when hovering over the help icon
#                 self._help_hover_timer.start(500)  # 500ms delay before showing tooltip
#         else:
#             # Stop the timer if the mouse moves away from the help icon
#             self._help_hover_timer.stop()
#             if self._help_tooltip and self._help_tooltip.isVisible():
#                 self._help_tooltip.hide()
#
#         super().hoverMoveEvent(event)
#
#     def hoverLeaveEvent(self, event):
#         # Stop the timer when the mouse leaves the item
#         self._help_hover_timer.stop()
#         if self._help_tooltip and self._help_tooltip.isVisible():
#             self._help_tooltip.hide()
#
#         super().hoverLeaveEvent(event)
#
#     def _showHelpTooltip(self):
#         # Create a tooltip if it doesn't exist
#         if not self._help_tooltip:
#             # Split text into title and content parts
#             parts = self._help_text.split('\n', 1)
#             title = parts[0]
#             body = parts[1] if len(parts) > 1 else ""
#
#             # Format the body text with paragraph breaks
#             formatted_body = body.replace('\n', '<br>')
#
#             # Create the tooltip HTML
#             tooltip_html = f"""
#             <div style='
#                 background-color: #ffcccc;
#                 color: #333333;
#                 padding: 12px;  /* Extra padding around the entire tooltip */
#                 border-radius: 12px;
#                 width: 200px;
#                 position: relative;
#                 word-wrap: break-word;
#                 border: 1px solid #d0d0d0;  /* Slightly darker border */
#             '>
#                 <div style='
#                     font-weight: bold;
#                     text-align: center;
#                     padding-bottom: 6px;
#                     background-color: #ffcccc;  /* Explicitly set background color */
#                     border-bottom: 1px solid rgba(0,0,0,0.2);
#                 '>{title}</div>
#
#                 <div style='background-color: #ffcccc; padding-top: 6px;'>{formatted_body}</div>
#
#                 <div style='
#                     position: absolute;
#                     bottom: -10px;
#                     left: 50%;
#                     margin-left: -10px;
#                     width: 0;
#                     height: 0;
#                     border-left: 10px solid transparent;
#                     border-right: 10px solid transparent;
#                     border-top: 10px solid #ffcccc;  /* Match the tooltip color */
#                 '></div>
#             </div>
#
#             """
#
#             self._help_tooltip = QGraphicsTextItem()
#             self.scene().addItem(self._help_tooltip)
#             self._help_tooltip.setDefaultTextColor(QColor("#333333"))
#             self._help_tooltip.setHtml(tooltip_html)
#             self._help_tooltip.setZValue(100)  # Make sure it's on top
#             self._help_tooltip.setTextWidth(224)  # Account for padding (200px + 24px padding)
#
#         # Position the tooltip above the help icon
#         tooltip_rect = self._help_tooltip.boundingRect()
#
#         # Center above the icon with some spacing
#         tooltip_pos_local = QPointF(
#             self._help_icon_rect.center().x() - tooltip_rect.width() / 2,
#             self._help_icon_rect.top() - tooltip_rect.height()
#         )
#         self._help_tooltip.setPos(self.mapToScene(tooltip_pos_local))
#         self._help_tooltip.show()
#
    def resize(self, width, height):
        """Resize the node to the specified dimensions"""
        self.setRect(0, 0, width, height)
        if self.resize_handle:
            self.resize_handle.update_position()

        # Update node state
        self.node_state.svg_size = self.svg_size_from_node_size(width, height)

        # Update vis image
        self.update_vis_image()

        # Update port positions to match the new dimensions
        self.update_all_port_positions()

    def node_size_from_svg_size(self, svg_w, svg_h):
        return svg_w + self.left_max_width + self.right_max_width + 2 * NodeItem.MARGIN_X, svg_h + 2 * NodeItem.MARGIN_Y + NodeItem.TITLE_HEIGHT

    def svg_size_from_node_size(self, rect_w, rect_h):
        return rect_w - self.left_max_width - self.right_max_width - 2 * NodeItem.MARGIN_X, rect_h - 2 * NodeItem.MARGIN_Y - NodeItem.TITLE_HEIGHT

#     def visualise(self):
#         return self.update_node().safe_visualise()
#
#     def get_svg_path(self):
#         wh_ratio = self.backend.svg_width / self.backend.svg_height if self.backend.svg_height > 0 else 1
#         # svg_path, exception = self.update_node().get_svg_path(self.scene().temp_dir, self.backend.svg_height, wh_ratio)
#         compute = self.update_node().safe_visualise(self.scene().temp_dir, self.backend.svg_height, wh_ratio)
#         # return svg_path
#         return
#
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
        vis = self.visualise()
        svg_filepath = os.path.join(self.scene().temp_dir, f"{self.uid}.svg")
        # Base position for all SVG elements
        svg_pos_x = self.left_max_width + NodeItem.MARGIN_X
        svg_pos_y = NodeItem.TITLE_HEIGHT + NodeItem.MARGIN_Y
        svg_width, svg_height = self.node_state.svg_size

        if isinstance(vis, ErrorFig) or not self.node.selectable():
            if isinstance(vis, Group):
                GroupDrawer(svg_filepath, svg_width, svg_height, (vis, None)).save()
            else:
                assert isinstance(vis, Visualisable)
                vis.save_to_svg(svg_filepath, svg_width, svg_height)

            self.svg_item = QGraphicsSvgItem(svg_filepath)
            # Apply position
            self.svg_item.setParentItem(self)
            self.svg_item.setPos(svg_pos_x, svg_pos_y)
            self.svg_item.setZValue(2)
        else:
            assert isinstance(vis, Group)
            assert not vis.transform_list.transforms
            GroupDrawer(svg_filepath, svg_width, svg_height, (vis, None)).save()

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
                    backend_child_elem = vis.get_element_from_id(child_elem_id)
                    assert backend_child_elem is not None
                    selectable_item = SelectableSvgElement(child_elem_id, backend_child_elem, svg_renderer, self)
                    selectable_item.setParentItem(viewport_svg)
                    selectable_item.setPos(0, 0)
                    selectable_item.setZValue(3)
                    self.svg_items.append(selectable_item)
                child = child.nextSibling()

    def create_ports(self):
        for (port_io, port_key), port_def in self.node().port_defs():
            is_input = port_io == PortIO.INPUT
            port = PortItem(port_key=port_key,
                            port_type=port_def.port_type,
                            is_input=is_input,
                            parent=self)
            self.port_items[(port_io, port_key)] = port
        self.update_all_port_positions()
        self.update_label_containers()
#
#     def add_port(self, port_def, is_input=True):
#         """
#         Add a new port to the node.
#
#         Args:
#             is_input (bool): True for input port, False for output port
#             port_def (dict): Port definition (if None, a default will be used)
#
#         Returns:
#             PortItem: The newly created port item
#         """
#
#         # Generate a unique ID for the new port
#         state_id = gen_uid()
#
#         if is_input:
#             # Calculate position for the new input port
#             input_count = len(self.backend.input_port_ids) + 1
#             y_offset = input_count * self.rect().height() / (input_count + 1)
#
#             # Create the new input port
#             res_port = PortItem(PortState(state_id,
#                                           -10, y_offset,
#                                           self.uid,
#                                           True,
#                                           [], port_def), self)
#
#             # Add to the backend tracking
#             self.backend.input_port_ids.append(state_id)
#
#             # Add to scene
#             self.scene().scene.add(res_port)
#
#             # Reposition existing input ports to distribute evenly
#             self._reposition_ports(True)
#
#         else:
#             # Calculate position for the new output port
#             output_count = len(self.backend.output_port_ids) + 1
#             y_offset = output_count * self.rect().height() / (output_count + 1)
#
#             # Create the new output port
#             res_port = PortItem(PortState(state_id,
#                                           self.rect().width() + 10, y_offset,
#                                           self.uid,
#                                           False,
#                                           [], port_def), self)
#
#             # Add to the backend tracking
#             self.backend.output_port_ids.append(state_id)
#
#             # Add to scene
#             self.scene().scene.add(res_port)
#
#             # Reposition existing output ports to distribute evenly
#             self._reposition_ports(False)
#
#         self.update_node()
#
#     def remove_port_by_name(self, key_name, is_input=None):
#         """
#         Remove a port from the node by its key name.
#
#         Args:
#             key_name (str): The name of the port to remove
#             is_input (bool, optional): Whether to only look for input or output ports.
#                                       If None, will search both types.
#
#         Returns:
#             bool: True if the port was successfully removed, False otherwise
#         """
#         # Find the port to remove by name
#         port_to_remove = None
#
#         for item in self.scene().items():
#             if isinstance(item, PortItem) and item.parentItem().uid == self.uid:
#                 # Check if port definition has the specified name
#                 if item.backend.port_def.key_name == key_name:
#                     port_to_remove = item
#                     break
#
#         # If no port found to remove
#         if port_to_remove is None:
#             return False
#
#         # First, remove any connections to/from this port
#         edges_to_remove = []
#         for edge_id in port_to_remove.backend.edge_ids:
#             edge: EdgeItem = self.scene().scene.get(edge_id)
#             edges_to_remove.append(edge)
#         for edge in edges_to_remove:
#             self.scene().delete_edge(edge)
#
#         # Remove port from backend tracking
#         if port_to_remove.backend.is_input:
#             if port_to_remove.uid in self.backend.input_port_ids:
#                 self.backend.input_port_ids.remove(port_to_remove.uid)
#         else:
#             if port_to_remove.uid in self.backend.output_port_ids:
#                 self.backend.output_port_ids.remove(port_to_remove.uid)
#
#         # Remove port from scene
#         self.scene().scene.remove(port_to_remove.uid)
#         self.scene().removeItem(port_to_remove)
#
#         # Reposition remaining ports to maintain even spacing
#         self._reposition_ports(port_to_remove.backend.is_input)
#
#         # Update label containers
#         self.update_label_containers()
#         self.update_node()
#
#         return True
#
#     def _reposition_ports(self, is_input=True):
#         """
#         Reposition all ports of a given type to be evenly distributed.
#
#         Args:
#             is_input (bool): True for input ports, False for output ports
#         """
#         # Get all relevant port items
#         port_items = []
#         for item in self.scene().items():
#             if isinstance(item, PortItem) and item.uid == self.uid:
#                 if item.backend.is_input == is_input:
#                     port_items.append(item)
#
#         # Calculate new positions
#         port_count = len(port_items)
#         for i, port in enumerate(port_items):
#             y_offset = (i + 1) * self.rect().height() / (port_count + 1)
#             if is_input:
#                 port.state.x = -10
#             else:
#                 port.state.x = self.rect().width() + 10
#             port.state.y = y_offset
#             port.setPos(port.state.x, port.state.y)
#
#         # Update connections if needed
#         for port in port_items:
#             for edge_id in port.backend.edge_ids:
#                 edge: EdgeItem = self.scene.get(edge_id)
#                 edge.update_position()
#
#         # Update the label containers to reflect new ports
#         self.update_label_containers()
#
#     def paint(self, painter, option, widget):
#         super().paint(painter, option, widget)
#
#         painter.setFont(QFont("Arial", 8))
#         painter.setPen(QColor("grey"))
#         id_rect = self.rect().adjusted(10, 10, 0, 0)  # Shift the top edge down
#         painter.drawText(id_rect, Qt.AlignTop | Qt.AlignLeft, f"id: #{shorten_uid(self.node.node_id)}")
#
#         # Draw node title
#         title_font = QFont("Arial", 10)
#         painter.setFont(title_font)
#         painter.setPen(QColor("black"))
#         metrics = QFontMetrics(title_font)
#         title_text = self.node.name()
#         text_width = metrics.horizontalAdvance(title_text)
#         text_height = metrics.height()
#         node_rect = self.rect()
#         title_x = node_rect.center().x() - text_width / 2
#         title_y = node_rect.top() + 10  # adjust vertical offset as needed
#         title_rect = QRectF(title_x, title_y, text_width, text_height)
#         painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignTop, title_text)
#
#         # Draw the help icon (question mark) in the top-right corner
#         help_icon_size = 9
#         help_rect = QRectF(
#             title_rect.right() + help_icon_size / 2,
#             title_rect.center().y() - help_icon_size / 2,  # center vertically
#             help_icon_size,
#             help_icon_size
#         )
#
#         # Draw the circle background
#         painter.setPen(QPen(QColor(100, 100, 100), 1))
#         painter.setBrush(Qt.NoBrush)
#         painter.drawEllipse(help_rect)
#
#         # Draw the question mark
#         painter.setFont(QFont("Arial", help_icon_size, QFont.Bold))
#         painter.setPen(QColor(80, 80, 80))
#         painter.drawText(help_rect, Qt.AlignCenter, "?")
#
#         # Store the help icon rect for hit testing in hover events
#         self._help_icon_rect = help_rect
#         if self._property_button:
#             property_button_pos = QPointF(
#                 self.rect().right() - 25,  # Button width (20) + 5px spacing
#                 self.rect().top() + 5
#             )
#             self._property_proxy.setPos(property_button_pos)
#
#         # Draw port labels if there are multiple
#         painter.setFont(NodeItem.LABEL_FONT)
#         font_metrics = QFontMetricsF(NodeItem.LABEL_FONT)
#         text_height = font_metrics.height()
#
#         # Draw input port labels (left side)
#         for port_id in self.backend.input_port_ids:
#             port = self.scene().scene.get(port_id)
#             text = port.backend.port_def.name
#
#             # Calculate port's position in this item's coordinate system
#             port_y = port.y()  # Since port is a child of this item
#
#             # Center text vertically with port
#             text_rect = QRectF(
#                 NodeItem.MARGIN_X,  # Left padding
#                 port_y - (text_height / 2),  # Vertical center alignment
#                 self.left_max_width,  # Width minus padding
#                 text_height  # Font height
#             )
#
#             # Draw the text
#             painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, text)
#
#         # Draw output port labels (right side)
#         rect = self.rect()
#         for port_id in self.backend.output_port_ids:
#             port = self.scene().scene.get(port_id)
#             text = port.backend.port_def.name
#
#             # Calculate port's position in this item's coordinate system
#             port_y = port.y()  # Since port is a child of this item
#
#             # Center text vertically with port
#             text_rect = QRectF(
#                 rect.width() - self.right_max_width - NodeItem.MARGIN_X,  # Right-aligned
#                 port_y - (text_height / 2),  # Vertical center alignment
#                 self.right_max_width,  # Width minus padding
#                 text_height  # Font height
#             )
#
#             # Draw the text
#             painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, text)
#
#     def itemChange(self, change, value):
#         if change == QGraphicsItem.ItemPositionChange:
#             # Update connected edges when node moves
#             for port_id in self.backend.input_port_ids + self.backend.output_port_ids:
#                 port: PortItem = self.scene().scene.get(port_id)
#                 for edge_id in port.backend.edge_ids:
#                     edge: EdgeItem = self.scene().scene.get(edge_id)
#                     edge.update_position()
#         elif change == QGraphicsItem.ItemPositionHasChanged:
#             self.backend.x = self.pos().x()
#             self.backend.y = self.pos().y()
#
#         return super().itemChange(change, value)

    def update_port_positions(self, port_io):
        port_dict = {port_key: port for (io, port_key), port in self.port_items.items() if io == port_io}
        port_count = len(port_dict)
        for i, (port_key, port) in enumerate(port_dict.items()):
            x_offset = -10 if port.is_input else self.rect().width() + 10
            y_offset = (i + 1) * self.rect().height() / (port_count + 1)
            port.setPos(x_offset, y_offset)
            # Update any connections to this port
            port.update_edge_positions()

    def update_all_port_positions(self):
        """Update the positions of all ports based on current node dimensions"""
        self.update_port_positions(PortIO.INPUT)
        self.update_port_positions(PortIO.OUTPUT)

    def update_label_containers(self):
        # Calculate the maximum width needed for each side
        font_metrics = QFontMetricsF(NodeItem.LABEL_FONT)
        self.left_max_width = NodeItem.MARGIN_Y - NodeItem.MARGIN_X
        self.right_max_width = NodeItem.MARGIN_Y - NodeItem.MARGIN_X

        for port_id in self.port_items:
            text = self.node().port_defs()[port_id].display_name
            width = font_metrics.horizontalAdvance(text)
            if port_id[0] == PortIO.INPUT:
                self.left_max_width = max(self.left_max_width, width)
            else:
                self.right_max_width = max(self.right_max_width, width)

        width, height = self.node_size_from_svg_size(*self.node_state.svg_size)
        self.resize(width, height)
#
#     def create_separated_inputs_copy(self):
#         self.scene().undo_stack.push(SeparateFromInputsCmd(self.scene(), (self.pos().x(), self.pos().y()), self.node))
#
class PortItem(QGraphicsPathItem):
    """Represents connection points on nodes with shapes based on port_type"""

    def __init__(self, port_key, port_type, is_input, parent: NodeItem):
        super().__init__(parent)
        self.port_key = port_key
        self.port_type = port_type
        self.is_input = is_input
        self.edge_items = {} # Key is port (node id, port key) connected to by edge, value is edge item

        self.size = 12  # Base size for the port
        # Create shape based on port_type
        self.create_shape_for_port_type()
        self.setZValue(1)

        # Make port interactive
        self.setAcceptHoverEvents(True)

        # Set appearance based on input/output status
        if self.is_input:
            self.setBrush(QBrush(QColor(100, 100, 100)))
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setBrush(QBrush(QColor(50, 150, 50)))
            self.setCursor(Qt.CrossCursor)

        self.setPen(QPen(Qt.black, 1))

    def create_shape_for_port_type(self):
        path = QPainterPath()
        half_size = self.size / 2
        if issubclass(self.port_type, PT_Element):
            # Circle for number type
            path.addEllipse(-half_size, -half_size, self.size, self.size)
        elif issubclass(self.port_type, PT_Grid):
            # Rounded rectangle for string type
            path.addRoundedRect(-half_size, -half_size, self.size, self.size, 3, 3)
        elif issubclass(self.port_type, PT_Function):
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

        elif issubclass(self.port_type, PT_Warp):
            # Square for array type
            path.addRect(-half_size, -half_size, self.size, self.size)

        elif issubclass(self.port_type, PT_ValueList):
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
        for edge in self.edge_items.values():
            edge.update_position()


class EdgeItem(QGraphicsLineItem):
    """Represents connections between nodes"""

    def __init__(self, src_port, dst_port):
        super().__init__()
        self.src_port = src_port
        self.dst_port = dst_port

        self.setZValue(0)
        # Thicker line with rounded caps for better appearance
        self.setPen(QPen(Qt.black, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.setFlag(QGraphicsItem.ItemIsSelectable)

    def update_position(self):
        source_pos = self.src_port.get_center_scene_pos()
        dest_pos = self.dst_port.get_center_scene_pos()
        self.setLine(QLineF(source_pos, dest_pos))


class AddNewNodeCmd(QUndoCommand):
    def __init__(self, scene, pos, node_class, description="Add new node"):
        super().__init__(description)
        self.scene = scene
        self.node_graph: NodeGraph = scene.node_graph
        self.pos = pos
        self.node_class = node_class

    def undo(self):
        pass
        # assert self.save_states
        # for state in self.save_states.values():
        #     if isinstance(state, NodeState):
        #         node_item = self.scene.get(state.uid)
        #         self.pipeline_scene.delete_node(node_item)
        #         return

    def redo(self):
        node_id = self.node_graph.add_new_node(self.node_class)
        ports_open = self.node_graph.node(node_id).compulsory_ports()
        node_state = NodeState(node_id=node_id,
                               ports_open=ports_open,
                               pos=(self.pos.x(), self.pos.y()),
                               svg_size=(150, 150)) # TODO: save as constant somewhere
        node_item = NodeItem(node_state)
        self.scene.node_items[node_id] = node_item
        self.scene.addItem(node_item)
        # if self.save_states:
        #     self.pipeline_scene.load_from_save_states(self.save_states)
        # else:
        #     node_item = NodeItem(NodeState(self.node.node_id, self.pos.x(), self.pos.y(), [], [], self.node, 150, 150))
        #     self.scene.add(node_item)
        #     self.pipeline_scene.addItem(node_item)
        #     node_item.create_ports()
        #     node_item.update_vis_image()
        #     # Save to save_states for further redos
        #     self.save_states = {node_item.uid: node_item.backend}
        #     for port_id in node_item.backend.input_port_ids + node_item.backend.output_port_ids:
        #         port = self.scene.get(port_id)
        #         self.save_states[port.uid] = port.backend
#
# class SeparateFromInputsCmd(QUndoCommand):
#     def __init__(self, pipeline_scene, pos, node: Node, description="Separate Node From Inputs"):
#         super().__init__(description)
#         self.pipeline_scene = pipeline_scene
#         self.scene: Scene = pipeline_scene.scene
#         self.pos = pos
#         self.node = node
#         self.node_item = None
#         self.output_port_ids = []
#
#     def undo(self):
#         assert self.node_item
#         self.pipeline_scene.delete_node(self.node_item)
#
#     def redo(self):
#         new_id = gen_uid()
#         new_node = copy.deepcopy(self.node)
#         new_node.node_id = new_id
#         node_item = NodeItem(
#             NodeState(new_id, self.pos[0] + 10, self.pos[1] + 10, [], [], new_node, 150, 150, ignore_inputs=True))
#         # Create output ports (right side)
#         output_count = len(new_node.out_port_defs())
#         output_ids_len = len(self.output_port_ids)
#         for i, port_def in enumerate(new_node.out_port_defs()):
#             y_offset = (i + 1) * node_item.rect().height() / (output_count + 1)
#             state_id = gen_uid() if i >= output_ids_len else self.output_port_ids[i]
#             output_port = PortItem(PortState(state_id,
#                                              node_item.rect().width() + 10, y_offset,
#                                              node_item.uid,
#                                              False,
#                                              [], port_def), node_item)
#             node_item.backend.output_port_ids.append(state_id)
#             self.scene.add(output_port)
#         # Add node to scene
#         self.scene.add(node_item)
#         self.pipeline_scene.addItem(node_item)
#         node_item.update_label_containers()
#         node_item.update_vis_image()
#         self.node_item = node_item
#         self.output_port_ids = node_item.backend.output_port_ids
#
class AddNewEdgeCmd(QUndoCommand):
    def __init__(self, scene, src_node_id, src_port_key, dst_node_id, dst_port_key, description="Add new edge"):
        super().__init__(description)
        self.scene = scene
        self.node_graph = self.scene.node_graph
        self.src_node_id = src_node_id
        self.src_port_key = src_port_key
        self.dst_node_id = dst_node_id
        self.dst_port_key = dst_port_key

    def undo(self):
        pass
        # assert self.edge
        # self.pipeline_scene.delete_edge(self.edge)

    def redo(self):
        self.node_graph.add_connection(self.src_node_id, self.src_port_key, self.dst_node_id, self.dst_port_key)
        src_node_item = self.scene.node_items[self.src_node_id]
        dst_node_item = self.scene.node_items[self.dst_node_id]
        src_port_item = src_node_item.port_items[(PortIO.INPUT, self.src_port_key)]
        dst_port_item = dst_node_item.port_items[(PortIO.OUTPUT, self.dst_port_key)]
        edge = EdgeItem(src_port_item, dst_port_item)
        self.scene.addItem(edge)
        # Update port edge_items
        src_port_item.edge_items[(self.dst_node_id, self.dst_port_key)] = edge
        dst_port_item.edge_items[(self.src_node_id, self.src_port_key)] = edge
#
# class ChangePropertiesCmd(QUndoCommand):
#     def __init__(self, pipeline_scene, node_item: NodeItem, props_changed, description="Change properties"):
#         super().__init__(description)
#         self.pipeline_scene = pipeline_scene
#         self.scene: Scene = pipeline_scene.scene
#         self.node_item = node_item
#         self.props_changed = props_changed
#
#     def update_properties(self, props):
#         for prop_name, prop in props.items():
#             self.node_item.node.prop_vals[prop_name] = prop
#             if (not self.node_item.node.resizable()) and (prop_name == 'width' or prop_name == 'height'):
#                 svg_width = self.node_item.node.prop_vals.get('width', self.node_item.rect().width())
#                 svg_height = self.node_item.node.prop_vals.get('height', self.node_item.rect().height())
#                 self.node_item.resize(*self.node_item.node_size_from_svg_size(svg_width, svg_height))
#
#         # Update the node's appearance
#         self.node_item.update()
#         self.node_item.update_visualisations()
#
#     def undo(self):
#         props = {}
#         for prop_name, value in self.props_changed.items():
#             props[prop_name] = value[0]
#         self.update_properties(props)
#
#     def redo(self):
#         props = {}
#         for prop_name, value in self.props_changed.items():
#             props[prop_name] = value[1]
#         self.update_properties(props)
#
class AddPropertyPortCmd(QUndoCommand):
    def __init__(self, node_item: NodeItem, prop_key, description="Add property port"):
        super().__init__(description)
        self.node_item = node_item
        self.prop_key = prop_key

    def undo(self):
        pass
        # self.node_item.remove_port_by_name(self.prop_key_name)
        # self.node_item.backend.prop_ports.remove(self.prop_key_name)

    def redo(self):
        for port_def in self.node_item.node().prop_port_defs():
            if port_def.key_name == self.prop_key_name:
                self.node_item.add_port(port_def)
                self.node_item.backend.prop_ports.append(self.prop_key_name)
                break
#
# class RemovePropertyPortCmd(QUndoCommand):
#     def __init__(self, pipeline_scene, node_item: NodeItem, prop_key_name, description="Remove property port"):
#         super().__init__(description)
#         self.pipeline_scene = pipeline_scene
#         self.scene: Scene = pipeline_scene.scene
#         self.node_item = node_item
#         self.prop_key_name = prop_key_name
#
#     def undo(self):
#         for port_def in self.node_item.node.prop_port_defs():
#             if port_def.key_name == self.prop_key_name:
#                 self.node_item.add_port(port_def)
#                 self.node_item.backend.prop_ports.append(self.prop_key_name)
#                 break
#
#     def redo(self):
#         self.node_item.remove_port_by_name(self.prop_key_name)
#         self.node_item.backend.prop_ports.remove(self.prop_key_name)
#
# class PasteCmd(QUndoCommand):
#     def __init__(self, pipeline_scene, save_states, description="Paste"):
#         super().__init__(description)
#         self.pipeline_scene = pipeline_scene
#         self.scene: Scene = pipeline_scene.scene
#         self.save_states = save_states
#
#     def undo(self):
#         items_to_remove = {}
#         for uid, state in self.save_states.items():
#             if not isinstance(state, PortState):
#                 items_to_remove[uid] = self.scene.get(uid)
#         for uid, item in items_to_remove.items():
#             self.scene.remove(uid)
#             self.pipeline_scene.removeItem(item)
#
#     def redo(self):
#         self.pipeline_scene.load_from_save_states(self.save_states)
#
# class DeleteCmd(QUndoCommand):
#     def __init__(self, pipeline_scene, nodes_to_delete, edges_to_delete, description="Delete edge"):
#         super().__init__(description)
#         self.pipeline_scene = pipeline_scene
#         self.nodes_to_delete = nodes_to_delete
#         self.edges_to_delete = edges_to_delete
#         self.save_states = None
#
#     def undo(self):
#         assert self.save_states
#         self.pipeline_scene.load_from_save_states(self.save_states)
#
#     def redo(self):
#         self.save_states = {}
#         for node in self.nodes_to_delete:
#             self.save_states[node.uid] = node.backend
#             for port_id in node.backend.input_port_ids + node.backend.output_port_ids:
#                 port = self.pipeline_scene.scene.get(port_id)
#                 self.save_states[port_id] = port.backend
#                 for edge_id in port.backend.edge_ids:
#                     edge = self.pipeline_scene.scene.get(edge_id)
#                     self.save_states[edge_id] = edge.backend
#             self.pipeline_scene.delete_node(node)
#         for edge in self.edges_to_delete:
#             if edge.uid not in self.save_states:
#                 self.save_states[edge.uid] = edge.backend
#                 self.pipeline_scene.delete_edge(edge)
#
# class AddCustomNodeCmd(QUndoCommand):
#     def __init__(self, pipeline_scene, save_states, inp_node_id, out_node_id, description="Make Custom Node"):
#         super().__init__(description)
#         self.pipeline_scene = pipeline_scene
#         self.scene: Scene = pipeline_scene.scene
#         self.save_states = save_states
#         self.inp_node_id = inp_node_id
#         self.out_node_id = out_node_id
#         self.custom_node_states = None
#         print("Creating custom node: ", inp_node_id, out_node_id)
#
#     def undo(self):
#         assert self.custom_node_states
#         for uid, item in self.custom_node_states.items() + self.save_states.items():
#             self.scene.remove(uid)
#             self.pipeline_scene.removeItem(item)
#
#     def redo(self):
#         if not self.custom_node_states:
#             for state in self.save_states.values():
#                 if isinstance(state, NodeState) or isinstance(state, EdgeState):
#                     state.invisible = True
#                 if isinstance(state, NodeState) or isinstance(state, PortState):
#                     state.x = None
#                     state.y = None
#         self.pipeline_scene.load_from_save_states(self.save_states)
#         if self.custom_node_states:
#             self.pipeline_scene.load_from_save_states(self.custom_node_states)
#         else:
#             unit_node_info = UnitNodeInfo(
#                 name="Custom node",
#                 description="Custom node.",
#                 in_port_defs=self.save_states[self.inp_node_id].node.in_port_defs(),
#                 out_port_defs=self.save_states[self.out_node_id].node.out_port_defs(),
#                 prop_port_defs=self.save_states[self.inp_node_id].node.prop_port_defs()
#             )
#             involved_ids = []
#             for uid, state in self.save_states.items():
#                 if isinstance(state, NodeState) or isinstance(state, EdgeState):
#                     involved_ids.append(uid)
#             custom_node = CustomNode(node_id=gen_uid(), unit_node_info=unit_node_info, final_node=self.save_states[self.out_node_id].node, involved_ids=involved_ids, first_id=self.inp_node_id, end_id=self.out_node_id)
#             # TODO: change where the node item is created
#             node_item = NodeItem(NodeState(custom_node.node_id, 0, 0, [], [], custom_node, 150, 150, nodes_to_update=[self.inp_node_id]))
#             self.scene.add(node_item)
#             self.pipeline_scene.addItem(node_item)
#             node_item.create_ports()
#             node_item.update_vis_image()
#             # Add property ports
#             port_defs = {}
#             for port_def in self.save_states[self.inp_node_id].node.prop_port_defs():
#                 port_defs[port_def.key_name] = port_def
#             for prop_port in self.save_states[self.inp_node_id].prop_ports:
#                 node_item.add_port(port_defs[prop_port])
#             # Save states for further redos
#             self.custom_node_states = {node_item.uid: node_item.backend}
#             for port_id in node_item.backend.input_port_ids + node_item.backend.output_port_ids:
#                 port = self.scene.get(port_id)
#                 self.custom_node_states[port.uid] = port.backend
#             # Replace input port and output port ids
#             for port_id in self.save_states[self.inp_node_id].input_port_ids + self.save_states[self.out_node_id].output_port_ids:
#                 del self.save_states[port_id]
#             self.save_states[self.inp_node_id].input_port_ids = []
#             self.save_states[self.out_node_id].output_port_ids = []
#             self.save_states[self.inp_node_id].ignore_inputs = True
#             self.save_states[self.out_node_id].nodes_to_update = [node_item.uid]
#
class PipelineScene(QGraphicsScene):
    """Scene that contains all pipeline elements"""

    def __init__(self, temp_dir, node_graph=None, parent=None):
        super().__init__(parent)
        self.setSceneRect(-100000, -100000, 200000, 200000)

        # Connection related variables
        self.connection_signals = ConnectionSignals()
        self.active_connection = None
        self.temp_line = None
        self.source_port = None
        self.dest_port = None

        self.node_items = {}
        self.node_graph = node_graph if node_graph else NodeGraph()

        self.temp_dir = temp_dir
        print(temp_dir)
        self.undo_stack = QUndoStack()
        self.filepath = None

        # Connect signals
        self.connection_signals.connectionStarted.connect(self.start_connection)
        self.connection_signals.connectionMade.connect(self.finish_connection)

    def view(self):
        return self.views()[0]
#
#     def add_node_from_class(self, node_class, pos, index=None):
#         """Add a new node of the given type at the specified position"""
#         uid = gen_uid()
#         if index is None:
#             node = node_class(node_id=uid)
#         else:
#             node = node_class(node_id=uid, selection_index=index)
#         return self.add_new_node(pos, node)
#
    def add_new_node(self, pos, node):
        self.undo_stack.push(AddNewNodeCmd(self, pos, node))

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

    def finish_connection(self, source_port: PortItem, dest_port: PortItem):
        """Create a permanent connection between source and destination ports"""
        if source_port and dest_port and source_port != dest_port:
            # Don't connect if they're on the same node
            if source_port.parentItem() != dest_port.parentItem():
                src_node_id = source_port.parentItem().node_state.node_id
                dst_node_id = dest_port.parentItem().node_state.node_id
                # Check if connection already exists
                connection_exists = False
                for dst_node_port_key in source_port.edge_items:
                    if dst_node_port_key == (dst_node_id, dest_port.port_key):
                        connection_exists = True
                        break

                # Check if target port already has a connection
                target_has_connection = len(dest_port.edge_items) > 0
                if not connection_exists and issubclass(source_port.port_type, dest_port.port_type) and (not target_has_connection):
                    self.undo_stack.push(AddNewEdgeCmd(self, src_node_id, source_port.port_key, dst_node_id, dest_port.port_key))
                # target_has_connection = len(dest_port.backend.edge_ids) > 0
                # if not connection_exists and issubclass(source_port.backend.port_def.port_type,
                #                                         dest_port.backend.port_def.port_type) and (
                #         dest_port.backend.port_def.input_multiple or not target_has_connection):
                #     self.undo_stack.push(AddNewEdgeCmd(self, source_port.backend.uid, dest_port.backend.uid))

        # Clean up temporary line
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None

        # Reset ports
        self.source_port = None
        self.dest_port = None
#
#     def mousePressEvent(self, event):
#         """Handle mouse press events for the scene"""
#         if event.button() == Qt.LeftButton:
#             item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.view()))
#
#             if isinstance(item, PortItem) and not item.backend.is_input:
#                 # Start creating a connection if an output port is clicked
#                 self.connection_signals.connectionStarted.emit(item)
#                 event.accept()
#                 return
#
#         super().mousePressEvent(event)
#
#     def mouseMoveEvent(self, event):
#         """Handle mouse move events for the scene"""
#         if self.source_port and self.temp_line:
#             self.update_temp_connection(event.scenePos())
#
#             # Highlight input port if we're hovering over one
#             item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.view()))
#             if isinstance(item, PortItem) and item.backend.is_input:
#                 if self.dest_port != item:
#                     # Reset previous dest port highlighting
#                     if self.dest_port:
#                         self.dest_port.setPen(QPen(Qt.black, 1))
#
#                     # Set new dest port
#                     self.dest_port = item
#                     self.dest_port.setPen(QPen(Qt.red, 2))
#             elif self.dest_port:
#                 # Reset dest port highlighting if not hovering over an input port
#                 self.dest_port.setPen(QPen(Qt.black, 1))
#                 self.dest_port = None
#
#             event.accept()
#             return
#
#         super().mouseMoveEvent(event)
#
#     def mouseReleaseEvent(self, event):
#         """Handle mouse release events for the scene"""
#         if event.button() == Qt.LeftButton and self.source_port:
#             item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.view()))
#             if isinstance(item, PortItem) and item.backend.is_input:
#                 # Create permanent connection
#                 self.connection_signals.connectionMade.emit(self.source_port, item)
#                 event.accept()
#                 return
#             else:
#                 # Clean up if not released over an input port
#                 if self.temp_line:
#                     self.removeItem(self.temp_line)
#                     self.temp_line = None
#                 self.source_port = None
#
#                 # Reset dest port highlighting if needed
#                 if self.dest_port:
#                     self.dest_port.setPen(QPen(Qt.black, 1))
#                     self.dest_port = None
#
#         super().mouseReleaseEvent(event)
#
#     def contextMenuEvent(self, event):
#         """Handle context menu events for the scene"""
#         clicked_item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.view()))
#
#         if isinstance(clicked_item, EdgeItem):
#             # Context menu for connections
#             menu = QMenu()
#             delete_action = QAction("Delete Connection", menu)
#             delete_action.triggered.connect(lambda: self.delete_edge(clicked_item))
#             menu.addAction(delete_action)
#             menu.exec_(event.screenPos())
#         elif isinstance(clicked_item, NodeItem) or isinstance(clicked_item, PortItem):
#             # Context menu for nodes (or ports on nodes)
#             if isinstance(clicked_item, PortItem):
#                 clicked_item = clicked_item.parentItem()
#
#             menu = QMenu()
#             separate_from_inputs_action = QAction("Separate from inputs", menu)
#             separate_from_inputs_action.triggered.connect(lambda: self.separate_from_inputs_action(clicked_item))
#             menu.addAction(separate_from_inputs_action)
#
#             if isinstance(clicked_item.node, CombinationNode):
#                 submenu = QMenu(f"Change {clicked_item.node.display_name()} to...")
#                 for i in range(len(clicked_item.node.selections())):
#                     if i == clicked_item.node.selection_index: continue
#                     change_action = QAction(clicked_item.node.selections()[i].name(), submenu)
#                     change_action.triggered.connect(lambda _, index=i: self.change_node_selection(clicked_item, index))
#                     submenu.addAction(change_action)
#                 menu.addMenu(submenu)
#
#             if isinstance(clicked_item.node, RandomColourSelectorNode):
#                 randomise_action = QAction("Randomise", menu)
#                 randomise_action.triggered.connect(lambda: self.randomise(clicked_item))
#                 menu.addAction(randomise_action)
#
#             menu.exec_(event.screenPos())
#         else:
#             menu = QMenu()
#
#             # Add actions for each node type
#             for node_class in node_classes:
#                 if issubclass(node_class, CombinationNode):
#                     submenu = menu.addMenu(node_class.display_name())
#                     for i in range(len(node_class.selections())):
#                         change_action = QAction(node_class.selections()[i].name(), submenu)
#                         handler = partial(self.add_node_from_class, node_class, event.scenePos(), i)
#                         change_action.triggered.connect(handler)
#                         submenu.addAction(change_action)
#                 else:
#                     action = QAction(node_class.display_name(), menu)
#                     handler = partial( self.add_node_from_class, node_class, event.scenePos(), None)
#                     action.triggered.connect(handler)
#                     menu.addAction(action)
#
#             menu.exec_(event.screenPos())
#
#     def save_scene(self, filepath):
#         save_states = {}
#         for k, v in self.scene.states.items():
#             save_states[k] = v.backend
#         view = self.view()
#         center = view.mapToScene(view.viewport().rect().center())
#         zoom = view.current_zoom
#         with open(filepath, "wb") as f:
#             pickle.dump(AppState((center.x(), center.y()), zoom, save_states), f)
#
#     def load_from_save_states(self, save_states):
#         # Process the loaded states as before
#         node_ids = []
#         newly_joined_node_ids = []
#         for v in save_states.values():
#             if isinstance(v, NodeState):
#                 node = NodeItem(v)
#                 self.scene.add(node)
#                 if not hasattr(node.backend, 'invisible'):
#                     node.backend.invisible = False  # For backward compatibility
#                 if node.backend.invisible: node.setVisible(False)
#                 self.addItem(node)
#                 for port_id in v.input_port_ids + v.output_port_ids:
#                     self.scene.add(PortItem(save_states[port_id], node))
#                 node_ids.append(v.uid)
#
#         for v in save_states.values():
#             if isinstance(v, EdgeState):
#                 edge = EdgeItem(v)
#                 self.scene.add(edge)
#                 if not hasattr(edge.backend, 'invisible'):
#                     edge.backend.invisible = False  # For backward compatibility
#                 if edge.backend.invisible: edge.setVisible(False)
#                 self.addItem(edge)
#                 edge.set_ports()
#                 added_src = edge.source_port.add_edge(edge.uid)
#                 added_dst = edge.dest_port.add_edge(edge.uid)
#                 if added_src or added_dst:
#                     newly_joined_node_ids.append(edge.dest_port.parentItem().uid)
#
#         for uid in node_ids:
#             node = self.scene.get(uid)
#             if not node.backend.invisible:
#                 node.update_vis_image()
#                 node.update_label_containers()
#
#         for uid in newly_joined_node_ids:
#             node = self.scene.get(uid)
#             if not node.backend.invisible:
#                 node.update_visualisations()
#
#     def clear_scene(self):
#         self.scene = Scene()
#         for item in self.items():
#             if isinstance(item, NodeItem) or isinstance(item, EdgeItem) or isinstance(item, PortItem):
#                 self.removeItem(item)
#
#     def load_scene(self, filepath):
#         self.clear_scene()
#
#         # Use the custom unpickler to load the scene
#         try:
#             # Import the helper function - adjust the import path as needed
#             app_state = load_scene_with_elements(filepath)
#         except ImportError:
#             # Fall back to regular unpickler if the helper isn't available
#             with open(filepath, "rb") as f:
#                 app_state = pickle.load(f)
#         self.view().centerOn(*app_state.pos)
#         self.view().set_zoom(app_state.zoom)
#         self.load_from_save_states(app_state.save_states)
#         self.undo_stack.clear()
#         self.filepath = filepath
#
#     def delete_edge(self, edge):
#         """Delete the given edge"""
#         edge.source_port.remove_edge(edge.uid)
#         edge.dest_port.remove_edge(edge.uid)
#         dest_node = edge.dest_port.parentItem()
#         self.scene.remove(edge.uid)
#         self.removeItem(edge)
#         node_to_update = self.scene.get(edge.dest_port.backend.parent_node_id)
#         node_to_update.update_visualisations()
#
#     def add_edge(self, src_port_id, dst_port_id):
#         edge = EdgeItem(EdgeState(gen_uid(), src_port_id, dst_port_id))
#         self.scene.add(edge)
#         self.addItem(edge)
#         edge.set_ports()
#         edge.source_port.add_edge(edge.uid)
#         edge.dest_port.add_edge(edge.uid)
#         node_to_update = self.scene.get(edge.dest_port.backend.parent_node_id)
#         node_to_update.update_visualisations()
#         return edge
#
#     def delete_node(self, node: NodeItem):
#         """Delete the given node and all its connections"""
#         # Remove all connected edges first
#         for port_id in node.backend.input_port_ids + node.backend.output_port_ids:
#             port: PortItem = self.scene.get(port_id)
#             for edge_id in list(port.backend.edge_ids):  # Use a copy to avoid issues while removing
#                 edge: EdgeItem = self.scene.get(edge_id)
#                 self.delete_edge(edge)
#
#         for port_id in node.backend.input_port_ids + node.backend.output_port_ids:
#             self.scene.remove(port_id)
#
#         # Remove tooltip
#         if node._help_tooltip:
#             self.removeItem(node._help_tooltip)
#             self._help_tooltip = None
#
#         self.scene.remove(node.uid)
#         self.removeItem(node)
#
#     def change_node_selection(self, clicked_item: NodeItem, i):
#         clicked_item.node.set_selection(i)
#         clicked_item.update_visualisations()
#
#     def randomise(self, clicked_item: RandomColourSelectorNode):
#         clicked_item.node.prop_vals['_actual_seed'] = random.random()
#         clicked_item.update_visualisations()
#
#     def separate_from_inputs_action(self, clicked_item: NodeItem):
#         clicked_item.create_separated_inputs_copy()
#
#
# class PipelineView(QGraphicsView):
#     """View to interact with the pipeline scene"""
#
#     def __init__(self, scene, parent=None):
#         super().__init__(scene, parent)
#         self.mouse_pos = scene.sceneRect().center()
#         self.setRenderHint(QPainter.Antialiasing)
#         self.setRenderHint(QPainter.TextAntialiasing)
#         self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
#         self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
#         self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
#         self.setDragMode(QGraphicsView.RubberBandDrag)
#         self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
#
#         # Zoom settings
#         self.default_zoom = 0.8
#         self.zoom_factor = 1.15
#         self.zoom_min = 0.1
#         self.zoom_max = 10.0
#         self.current_zoom = self.default_zoom
#         self.setTransform(QTransform().scale(self.current_zoom, self.current_zoom))
#
#         self.centerOn(0, 0)
#
#         # Add grid lines
#         self.draw_grid()
#
#     def event(self, event):
#         """Handle macOS native pinch-to-zoom gesture"""
#         if isinstance(event, QNativeGestureEvent) and event.gestureType() == Qt.ZoomNativeGesture:
#             return self.zoomNativeEvent(event)
#         return super().event(event)
#
#     def zoomNativeEvent(self, event: QNativeGestureEvent):
#         """Zoom in/out based on pinch gesture on macOS"""
#         # event.value() > 0 means pinch out (zoom in), < 0 means pinch in (zoom out)
#         sensitivity = 0.7
#         factor = 1 + event.value()*sensitivity  # Typically a small float, e.g. ±0.1
#         resulting_zoom = self.current_zoom * factor
#
#         if resulting_zoom < self.zoom_min or resulting_zoom > self.zoom_max:
#             return True  # consume event, but no zoom
#
#         self.scale(factor, factor)
#         self.current_zoom *= factor
#         self.update()
#         return True  # event handled
#
#     def wheelEvent(self, event):
#         """Handle zoom or pan based on wheel/trackpad event"""
#         delta = event.angleDelta()
#         delta_x = delta.x()
#         delta_y = delta.y()
#         threshold = 15  # Dead zone for accidental touches
#
#         # Ctrl/Command+Scroll = Zoom
#         if event.modifiers() & Qt.ControlModifier:
#             if abs(delta_y) < threshold:
#                 return  # Too small, ignore
#             zoom_in = delta_y > 0
#             factor = self.zoom_factor if zoom_in else 1 / self.zoom_factor
#             resulting_zoom = self.current_zoom * factor
#
#             if self.zoom_min <= resulting_zoom <= self.zoom_max:
#                 self.scale(factor, factor)
#                 self.current_zoom *= factor
#                 self.update()
#             return
#
#         # Otherwise, treat as panning (touchpad 2-finger scroll)
#         # Use scroll deltas to translate the view
#         self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta_x)
#         self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta_y)
#
#     def zoom(self, factor):
#         resulting_zoom = self.current_zoom * factor
#         if resulting_zoom < self.zoom_min or resulting_zoom > self.zoom_max:
#             return
#         self.scale(factor, factor)
#         self.current_zoom *= factor
#         self.update()
#
#     def set_zoom(self, zoom):
#         self.setTransform(QTransform().scale(zoom, zoom))
#         self.current_zoom = zoom
#         self.update()
#
#     def reset_zoom(self):
#         self.set_zoom(self.default_zoom)
#
#     def draw_grid(self):
#         """Draw a grid background for the scene"""
#         grid_size = 20
#         scene_rect = self.scene().sceneRect()
#
#         left = int(scene_rect.left())
#         right = int(scene_rect.right())
#         top = int(scene_rect.top())
#         bottom = int(scene_rect.bottom())
#
#         # Align to the grid
#         left -= left % grid_size
#         top -= top % grid_size
#
#         # Draw vertical lines
#         for x in range(left, right + 1, grid_size):
#             line = QGraphicsLineItem(x, top, x, bottom)
#             line.setPen(QPen(QColor(200, 200, 200), 1))
#             line.setZValue(-1000)
#             self.scene().addItem(line)
#
#         # Draw horizontal lines
#         for y in range(top, bottom + 1, grid_size):
#             line = QGraphicsLineItem(left, y, right, y)
#             line.setPen(QPen(QColor(200, 200, 200), 1))
#             line.setZValue(-1000)
#             self.scene().addItem(line)
#
#     def mousePressEvent(self, event):
#         """Handle mouse press events for the view"""
#         if event.button() == Qt.MiddleButton:
#             self.setDragMode(QGraphicsView.ScrollHandDrag)
#             # Create a fake mouse press event to initiate the drag
#             fake_event = event
#             fake_event.button = lambda: Qt.LeftButton
#             super().mousePressEvent(fake_event)
#         else:
#             super().mousePressEvent(event)
#
#     def mouseReleaseEvent(self, event):
#         """Handle mouse release events for the view"""
#         if event.button() == Qt.MiddleButton:
#             self.setDragMode(QGraphicsView.RubberBandDrag)
#
#         super().mouseReleaseEvent(event)
#
#     def mouseMoveEvent(self, event):
#         # Get mouse position relative to the scene
#         self.mouse_pos = self.mapToScene(event.pos())
#         super().mouseMoveEvent(event)
#
#
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
#
#     def setup_menu(self):
#         # Create the menu bar
#         menu_bar = self.menuBar()
#
#         # Create File menu
#         file_menu = menu_bar.addMenu("File")
#
#         # Add New scene action
#         new_scene_action = QAction("New Scene", self)
#         new_scene_action.setShortcut(QKeySequence.New)
#         new_scene_action.triggered.connect(self.new_scene)
#         file_menu.addAction(new_scene_action)
#
#         # Add Save action
#         save_action = QAction("Save", self)
#         save_action.setShortcut(QKeySequence.Save)
#         save_action.triggered.connect(self.save_scene)
#         file_menu.addAction(save_action)
#
#         # Add Save As action
#         save_action = QAction("Save As", self)
#         save_action.setShortcut(QKeySequence.SaveAs)
#         save_action.triggered.connect(self.save_as_scene)
#         file_menu.addAction(save_action)
#
#         # Add Load action
#         load_action = QAction("Load from file", self)
#         load_action.setShortcut("Ctrl+L")
#         load_action.triggered.connect(self.load_scene)
#         file_menu.addAction(load_action)
#
#         scene_menu = menu_bar.addMenu("Scene")
#
#         # Add Delete action
#         delete = QAction("Delete", self)
#         delete.setShortcut(Qt.Key_Backspace)
#         delete.triggered.connect(self.delete_selected_items)
#         scene_menu.addAction(delete)
#
#         copy = QAction("Copy", self)
#         copy.setShortcut(QKeySequence.Copy)
#         copy.triggered.connect(self.copy_selected_items)
#         copy.setMenuRole(QAction.NoRole)
#         scene_menu.addAction(copy)
#
#         paste = QAction("Paste", self)
#         paste.setShortcut(QKeySequence.Paste)
#         paste.triggered.connect(self.paste_items)
#         paste.setMenuRole(QAction.NoRole)
#         scene_menu.addAction(paste)
#
#         # Add Select all action
#         select_all = QAction("Select All", self)
#         select_all.setShortcut(QKeySequence.SelectAll)
#         select_all.triggered.connect(self.select_all)
#         select_all.setMenuRole(QAction.NoRole)
#         scene_menu.addAction(select_all)
#
#         create_custom = QAction("Group Nodes to Custom", self)
#         create_custom.setShortcut("Ctrl+G")
#         create_custom.triggered.connect(self.create_custom_node)
#         scene_menu.addAction(create_custom)
#
#         # Add Undo action
#         undo = self.scene.undo_stack.createUndoAction(self, "Undo")
#         undo.setShortcut(QKeySequence.Undo)
#         scene_menu.addAction(undo)
#
#         # Add Redo action
#         redo = self.scene.undo_stack.createRedoAction(self, "Redo")
#         redo.setShortcut(QKeySequence.Redo)
#         scene_menu.addAction(redo)
#
#         # Add Zoom in action
#         zoom_in = QAction("Zoom In", self)
#         zoom_in.setShortcut(QKeySequence.ZoomIn)
#         zoom_in.triggered.connect(lambda: self.view.zoom(self.view.zoom_factor))
#         scene_menu.addAction(zoom_in)
#
#         # Add Zoom out action
#         zoom_out = QAction("Zoom Out", self)
#         zoom_out.setShortcut(QKeySequence.ZoomOut)
#         zoom_out.triggered.connect(lambda: self.view.zoom(1/self.view.zoom_factor))
#         scene_menu.addAction(zoom_out)
#
#         # Add Reset zoom action
#         reset_zoom = QAction("Reset Zoom", self)
#         reset_zoom.setShortcut("Ctrl+0")
#         reset_zoom.triggered.connect(self.view.reset_zoom)
#         scene_menu.addAction(reset_zoom)
#
#         # Add Centre view action
#         centre = QAction("Centre View", self)
#         centre.setShortcut("Ctrl+1")
#         centre.triggered.connect(lambda: self.view.centerOn(0, 0))
#         scene_menu.addAction(centre)
#
#     def new_scene(self):
#         self.scene.filepath = None
#         self.scene.clear_scene()
#         self.view.reset_zoom()
#         self.view.centerOn(0, 0)
#
#     def save_as_scene(self):
#         filepath, _ = QFileDialog.getSaveFileName(
#             self,
#             "Save Pipeline Scene",
#             "",
#             "Pipeline Scene Files (*.pipeline);;All Files (*)"
#         )
#
#         if filepath:
#             self.scene.save_scene(filepath)
#
#     def save_scene(self, filepath=None):
#         if filepath:
#             save_filepath = filepath
#         elif self.scene.filepath:
#             save_filepath = self.scene.filepath
#         else:
#             return self.save_as_scene()
#         self.scene.save_scene(save_filepath)
#         self.statusBar().showMessage(f"Scene saved to {save_filepath}", 3000)
#
#     def load_scene(self):
#         file_path, _ = QFileDialog.getOpenFileName(
#             self,
#             "Load Pipeline Scene",
#             "",
#             "Pipeline Scene Files (*.pipeline);;All Files (*)"
#         )
#
#         if file_path:
#             self.scene.load_scene(file_path)
#             # Update the view to reflect the loaded scene
#             self.view.update()
#             self.statusBar().showMessage(f"Scene loaded from {file_path}", 3000)
#
#     def select_all(self):
#         for item in self.scene.items():
#             if isinstance(item, NodeItem) or isinstance(item, EdgeItem) or isinstance(item, PortItem):
#                 item.setSelected(True)
#
#     def delete_selected_items(self):
#         nodes_to_delete = []
#         edges_to_delete = []
#         for item in self.scene.selectedItems():
#             if isinstance(item, NodeItem):
#                 nodes_to_delete.append(item)
#             elif isinstance(item, EdgeItem):
#                 edges_to_delete.append(item)
#         if nodes_to_delete or edges_to_delete:
#             self.scene.undo_stack.push(DeleteCmd(self.scene, nodes_to_delete, edges_to_delete))
#
#     class TwoInputDialog(QDialog):
#         def __init__(self):
#             super().__init__()
#             self.setWindowTitle("Create custom node")
#
#             self.layout = QVBoxLayout()
#
#             self.label1 = QLabel("Input node ID:")
#             self.input1 = QLineEdit()
#             self.hash_label = QLabel("#")
#
#             # Create a horizontal layout for the # and input field
#             self.input_layout1 = QHBoxLayout()
#             self.input_layout1.addWidget(self.hash_label)
#             self.input_layout1.addWidget(self.input1)
#
#             # Add to the main layout
#             self.layout.addWidget(self.label1)
#             self.layout.addLayout(self.input_layout1)
#
#             self.label2 = QLabel("Output node ID:")
#             self.input2 = QLineEdit()
#             self.hash_label = QLabel("#")
#
#             # Create a horizontal layout for the # and input field
#             self.input_layout2 = QHBoxLayout()
#             self.input_layout2.addWidget(self.hash_label)
#             self.input_layout2.addWidget(self.input2)
#
#             # Add to the main layout
#             self.layout.addWidget(self.label2)
#             self.layout.addLayout(self.input_layout2)
#
#             self.ok_button = QPushButton("OK")
#             self.ok_button.clicked.connect(self.accept)
#             self.layout.addWidget(self.ok_button)
#
#             self.setLayout(self.layout)
#
#         def get_inputs(self):
#             return self.input1.text(), self.input2.text()
#
#     def create_custom_node(self):
#         # Simple dialog for testing
#         dialog = PipelineEditor.TwoInputDialog()
#         if dialog.exec_():
#             node_states, port_states, edge_states = self.identify_selected_items()
#             save_states, old_to_new_id_map = self.deep_copy_items(node_states, port_states, edge_states)
#             inp_node_id = None
#             out_node_id = None
#             string1, string2 = dialog.get_inputs()
#             print("First:", string1)
#             print("Second:", string2)
#             for old_key, new_key in old_to_new_id_map.items():
#                 short_id = shorten_uid(old_key)
#                 if short_id == string1:
#                     inp_node_id = new_key
#                 elif short_id == string2:
#                     out_node_id = new_key
#             if inp_node_id and out_node_id:
#                 self.scene.undo_stack.push(AddCustomNodeCmd(self.scene, save_states, inp_node_id, out_node_id))
#
#     def identify_selected_items(self):
#         nodes = []
#         edges = []
#         for item in self.scene.selectedItems():
#             if isinstance(item, NodeItem):
#                 nodes.append(item)
#                 if isinstance(item.node, CustomNode):
#                     for uid in item.node.involved_ids:
#                         custom_node_item = self.scene.scene.get(uid)
#                         if isinstance(custom_node_item, NodeItem):
#                             nodes.append(custom_node_item)
#                         elif isinstance(custom_node_item, EdgeItem):
#                             edges.append(custom_node_item)
#             elif isinstance(item, EdgeItem):
#                 edges.append(item)
#         if not (nodes or edges):
#             return
#
#         # Populate states
#         node_states = {}
#         port_states = {}
#         for node in nodes:
#             node_states[node.uid] = node.backend
#             for port_id in node.backend.input_port_ids + node.backend.output_port_ids:
#                 port = self.scene.scene.get(port_id)
#                 port_states[port_id] = port.backend
#         edge_states = {}
#         for edge in edges:
#             if (edge.backend.src_port_id in port_states) and (edge.backend.dst_port_id in port_states):
#                 edge_states[edge.uid] = edge.backend
#         return node_states, port_states, edge_states
#
#     def deep_copy_items(self, node_states, port_states, edge_states):
#         # Update ids
#         save_states = {}
#         old_to_new_id_map = {}
#         for old_id, node_state in node_states.items():
#             new_node_state = copy.deepcopy(node_state)
#             # Set node uid
#             new_uid = gen_uid()
#             new_node_state.uid = new_uid
#             new_node_state.node.node_id = new_uid
#             old_to_new_id_map[old_id] = new_uid
#             save_states[new_uid] = new_node_state
#         for old_id, port_state in port_states.items():
#             new_port_state = copy.deepcopy(port_state)
#             # Set port uid
#             new_uid = gen_uid()
#             new_port_state.uid = new_uid
#             old_to_new_id_map[old_id] = new_uid
#             save_states[new_uid] = new_port_state
#         for old_id, edge_state in edge_states.items():
#             new_edge_state = copy.deepcopy(edge_state)
#             # Set edge uid
#             new_uid = gen_uid()
#             new_edge_state.uid = new_uid
#             old_to_new_id_map[old_id] = new_uid
#             save_states[new_uid] = new_edge_state
#         # Rewire connections
#         for state in save_states.values():
#             if isinstance(state, NodeState):
#                 # Update port ids
#                 state.input_port_ids = [old_to_new_id_map[i] for i in state.input_port_ids]
#                 state.output_port_ids = [old_to_new_id_map[i] for i in state.output_port_ids]
#                 if not hasattr(state, 'nodes_to_update'):
#                     state.nodes_to_update = []  # For backward compatibility
#                 state.nodes_to_update = [old_to_new_id_map[i] for i in state.nodes_to_update]
#                 if isinstance(state.node, CustomNode):
#                     state.node.involved_ids = [old_to_new_id_map[i] for i in state.node.involved_ids]
#                     state.node.first_id = old_to_new_id_map[state.node.first_id]
#                     state.node.end_id = old_to_new_id_map[state.node.end_id]
#                     state.node.final_node = None
#                 if isinstance(state.node, DrawingGroupNode):
#                     for elem_ref in state.node.prop_vals['elem_order']:
#                         new_id = old_to_new_id_map[elem_ref.node_id]
#                         elem_ref.node = save_states[new_id].node
#                         elem_ref.node_type = elem_ref.node.node_info().name
#                         elem_ref.node_id = new_id
#             elif isinstance(state, PortState):
#                 # Update parent node id
#                 state.parent_node_id = old_to_new_id_map[state.parent_node_id]
#                 # Update edge ids
#                 edge_ids = []
#                 for old_edge_id in state.edge_ids:
#                     if old_edge_id in old_to_new_id_map:
#                         edge_ids.append(old_to_new_id_map[old_edge_id])
#                 state.edge_ids = edge_ids
#             elif isinstance(state, EdgeState):
#                 # Update src and dst port ids
#                 state.src_port_id = old_to_new_id_map[state.src_port_id]
#                 state.dst_port_id = old_to_new_id_map[state.dst_port_id]
#         return save_states, old_to_new_id_map
#
#     def copy_selected_items(self):
#         node_states, port_states, edge_states = self.identify_selected_items()
#         if node_states:
#             # Calculate bounding rect
#             bounding_rect = None
#             for item in self.scene.selectedItems():
#                 if isinstance(item, NodeItem) or isinstance(item, EdgeItem):
#                     if (item.uid in node_states or item.uid in edge_states) and not item.backend.invisible:
#                         # Make part of bounding rect
#                         if bounding_rect:
#                             bounding_rect = bounding_rect.united(item.sceneBoundingRect())
#                         else:
#                             bounding_rect = item.sceneBoundingRect()
#             assert bounding_rect
#
#             # Save to clipboard
#             mime_data = QMimeData()
#             mime_data.setData("application/pipeline_editor_items", pickle.dumps((node_states, port_states, edge_states, bounding_rect.center())))
#             clipboard = QApplication.clipboard()
#             clipboard.setMimeData(mime_data)
#
#     def paste_items(self):
#         clipboard = QApplication.clipboard()
#         mime = clipboard.mimeData()
#
#         if mime.hasFormat("application/pipeline_editor_items"):
#             raw_data = mime.data("application/pipeline_editor_items")
#             # Deserialize with pickle
#             node_states, port_states, edge_states, bounding_rect_centre = pickle.loads(bytes(raw_data))
#             save_states = self.deep_copy_items(node_states, port_states, edge_states)[0]
#             print(len(save_states))
#             # Modify positions
#             offset = self.view.mouse_pos - bounding_rect_centre
#             for state in save_states.values():
#                 if isinstance(state, NodeState) or isinstance(state, PortState):
#                     if (state.x is not None) and (state.y is not None):
#                         if isinstance(state, NodeState):
#                             print(f"Changing node position: {shorten_uid(state.uid)} from ({state.x}, {state.y}) to ({state.x + offset.x()}, {state.y + offset.y()})")
#                             state.x += offset.x()
#                             state.y += offset.y()
#                         # if isinstance(state, PortState):
#                         #     print(f"Changing port position: {shorten_uid(state.uid)} from ({state.x}, {state.y}) to ({state.x + offset.x()}, {state.y + offset.y()})")
#                         # state.x += offset.x()
#                         # state.y += offset.y()
#             # Perform paste
#             self.scene.undo_stack.push(PasteCmd(self.scene, save_states))
#
#
if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as temp_dir:
        app = QApplication(sys.argv)
        editor = PipelineEditor(temp_dir=temp_dir)
        sys.exit(app.exec_())
