import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView, 
                            QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem, 
                            QGraphicsLineItem, QMenu, QAction, QInputDialog, QColorDialog,
                            QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                            QSpinBox, QDoubleSpinBox, QComboBox, QPushButton, QCheckBox,
                            QDialogButtonBox, QGroupBox, QMessageBox, QTableWidget, QTableWidgetItem, QWidget,
                            QHBoxLayout)
from PyQt5.QtCore import Qt, QLineF, pyqtSignal, QObject, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QFont
from PyQt5.QtSvg import QSvgWidget
import os
import svgwrite
from node import InvalidInputNodesLength, GridNode, ShapeRepeaterNode, CubicFunNode, PosWarpNode, RelWarpNode, PiecewiseFunNode
import uuid

class ConnectionSignals(QObject):
    """Signals for the connection process"""
    connectionStarted = pyqtSignal(object)  # Emits the source port
    connectionMade = pyqtSignal(object, object)  # Emits source and destination ports

class NodeProperty:
    """Defines a property for a node"""
    def __init__(self, name, prop_type, default_value=None, min_value=None, max_value=None, 
                 options=None, description=""):
        self.name = name
        self.prop_type = prop_type  # "int", "float", "string", "bool", "enum"
        self.default_value = default_value
        self.min_value = min_value
        self.max_value = max_value
        self.options = options  # For enum type
        self.description = description

class NodeType:
    """Defines a type of node with specific inputs and outputs"""
    def __init__(self, name, input_count=1, output_count=1, color=QColor(200, 230, 250), properties=None, node_class=None):
        self.name = name
        self.input_count = input_count
        self.output_count = output_count
        self.color = color
        self.properties = properties or []
        self.node_class = node_class


class NodeItem(QGraphicsRectItem):
    """Represents a node/box in the pipeline"""
    
    def __init__(self, x, y, width, height, node_type):
        super().__init__(0, 0, width, height)
        self.node_id = uuid.uuid4()
        self.setPos(x, y)
        self.setZValue(1)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        self.setBrush(QBrush(node_type.color))
        self.setPen(QPen(Qt.black, 2))
        
        self.title = node_type.name
        self.node_type = node_type
        self.input_ports = []
        self.output_ports = []
        self.property_values = {}
        
        # Initialize property values with defaults
        for prop in self.node_type.properties:
            self.property_values[prop.name] = prop.default_value
        
        self.create_ports()

    def get_input_nodes(self):
        input_nodes = []
        for input_port in self.input_ports:
            if len(input_port.edges) > 0:
                edge = input_port.edges[0] # TODO: assume only 0 or 1 edge
                src_port = edge.source_port
                input_nodes.append(src_port.parent)
            else:
                input_nodes.append(None)
        return input_nodes

    def get_node(self):
        input_nodes = self.get_input_nodes()
        if len(input_nodes) == 0:
            return self.node_type.node_class(self.node_id, [], self.property_values)
        extracted_nodes = []
        for node in input_nodes:
            if node is None:
                extracted_nodes.append(None)
            else:
                extracted_nodes.append(node.get_node())
        return self.node_type.node_class(self.node_id, extracted_nodes, self.property_values)
        
    def create_ports(self):
        # Create input ports (left side)
        for i in range(self.node_type.input_count):
            y_offset = (i + 1) * self.rect().height() / (self.node_type.input_count + 1)
            input_port = PortItem(self, -10, y_offset, is_input=True)
            self.input_ports.append(input_port)
        
        # Create output ports (right side)
        for i in range(self.node_type.output_count):
            y_offset = (i + 1) * self.rect().height() / (self.node_type.output_count + 1)
            output_port = PortItem(self, self.rect().width() + 10, y_offset, is_input=False)
            self.output_ports.append(output_port)
        
    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        
        # Draw node title
        painter.setFont(QFont("Arial", 10))
        painter.drawText(self.rect(), Qt.AlignCenter, self.title)
        
        # Draw port labels if there are multiple
        painter.setFont(QFont("Arial", 8))
        
        # Input port labels
        if self.node_type.input_count > 1:
            for i, port in enumerate(self.input_ports):
                label_pos = port.pos() + QPointF(5, 0)  # Position just right of the port
                painter.drawText(int(label_pos.x()), int(label_pos.y() + 4), f"In {i+1}")
        
        # Output port labels
        if self.node_type.output_count > 1:
            for i, port in enumerate(self.output_ports):
                label_pos = port.pos() + QPointF(-25, 0)  # Position just left of the port
                painter.drawText(int(label_pos.x()), int(label_pos.y() + 4), f"Out {i+1}")
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # Update connected edges when node moves
            for port in self.input_ports + self.output_ports:
                for edge in port.edges:
                    edge.update_position()
                    
        return super().itemChange(change, value)


class PortItem(QGraphicsEllipseItem):
    """Represents connection points on nodes"""
    
    def __init__(self, parent, x, y, is_input=True):
        size = 12  # Slightly larger port for easier clicking
        super().__init__(-size/2, -size/2, size, size, parent)
        self.parent = parent
        self.setPos(x, y)
        self.setZValue(1)
        self.is_input = is_input
        self.edges = []
        
        # Make port interactive
        self.setAcceptHoverEvents(True)
        
        if is_input:
            self.setBrush(QBrush(QColor(100, 100, 100)))
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setBrush(QBrush(QColor(50, 150, 50)))
            self.setCursor(Qt.CrossCursor)  # Shows + cursor when hovering output ports
        
        self.setPen(QPen(Qt.black, 1))
        
    def add_edge(self, edge):
        self.edges.append(edge)
    
    def remove_edge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)
    
    def get_center_scene_pos(self):
        return self.mapToScene(self.rect().center())
    
    def hoverEnterEvent(self, event):
        # Highlight port on hover
        self.setPen(QPen(Qt.red, 2))
        if not self.is_input:
            # Change cursor for output ports to indicate dragging availability
            self.setCursor(Qt.CrossCursor)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.setPen(QPen(Qt.black, 1))
        super().hoverLeaveEvent(event)
    

class EdgeItem(QGraphicsLineItem):
    """Represents connections between nodes"""
    
    def __init__(self, source_port, dest_port):
        super().__init__()
        self.setZValue(0)

        self.source_port = source_port
        self.dest_port = dest_port
        
        self.source_port.add_edge(self)
        self.dest_port.add_edge(self)
        
        # Thicker line with rounded caps for better appearance
        self.setPen(QPen(Qt.black, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        
        self.update_position()
    
    def update_position(self):
        if self.source_port and self.dest_port:
            source_pos = self.source_port.get_center_scene_pos()
            dest_pos = self.dest_port.get_center_scene_pos()
            self.setLine(QLineF(source_pos, dest_pos))


class NodePropertiesDialog(QDialog):
    """Dialog for editing node properties"""
    
    def __init__(self, node_item, parent=None):
        super().__init__(parent)
        self.node_item = node_item
        self.setWindowTitle(f"Properties: {node_item.title}")
        self.setMinimumWidth(400)
        
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Create form layout for properties
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        self.property_widgets = {}
        
        # Add general properties (title)
        self.title_edit = QLineEdit(self.node_item.title)
        form_layout.addRow("Node Name:", self.title_edit)
        
        # Add custom properties based on node type
        if node_item.node_type.properties:
            props_group = QGroupBox("Node Properties")
            props_layout = QFormLayout()
            props_group.setLayout(props_layout)
            
            for prop in node_item.node_type.properties:
                widget = self.create_property_widget(prop, node_item.property_values.get(prop.name, prop.default_value))
                props_layout.addRow(f"{prop.name}:", widget)
                self.property_widgets[prop.name] = widget
                
                # Add tooltip if description is available
                if prop.description:
                    widget.setToolTip(prop.description)
            
            main_layout.addWidget(props_group)
        
        # Create buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)
    
    def create_property_widget(self, prop, current_value):
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
            
        elif prop.prop_type == "enum" and prop.options:
            widget = QComboBox()
            widget.addItems(prop.options)
            if current_value is not None:
                index = prop.options.index(current_value) if current_value in prop.options else 0
                widget.setCurrentIndex(index)

        elif prop.prop_type == "table":
            # Create a table widget
            widget = QTableWidget()
            
            # Set up the basic table structure
            widget.setColumnCount(2)
            widget.setHorizontalHeaderLabels(["X", "Y"])
            
            # Populate with current data
            points = current_value or prop.default_value or []
            widget.setRowCount(len(points))
            
            for row, (x, y) in enumerate(points):
                widget.setItem(row, 0, QTableWidgetItem(str(x)))
                widget.setItem(row, 1, QTableWidgetItem(str(y)))
            
            # Add buttons to add/remove rows
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(0, 0, 0, 0)
            
            add_button = QPushButton("+")
            remove_button = QPushButton("-")
            
            # Add row function
            def add_row():
                row = widget.rowCount()
                widget.setRowCount(row + 1)
                widget.setItem(row, 0, QTableWidgetItem("0.0"))
                widget.setItem(row, 1, QTableWidgetItem("0.0"))
            
            # Remove row function
            def remove_row():
                row = widget.rowCount()
                if row > 0:
                    widget.setRowCount(row - 1)
            
            add_button.clicked.connect(add_row)
            remove_button.clicked.connect(remove_row)
            
            button_layout.addWidget(add_button)
            button_layout.addWidget(remove_button)
            
            # Create a container for the table and buttons
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.addWidget(widget)
            layout.addWidget(button_widget)
            
            # Function to get the current value from the table
            def get_table_value():
                points = []
                for row in range(widget.rowCount()):
                    try:
                        x = float(widget.item(row, 0).text())
                        y = float(widget.item(row, 1).text())
                        points.append((x, y))
                    except (ValueError, AttributeError):
                        # Handle empty or invalid cells
                        pass
                return points
            
            # Store the getter function with the widget
            widget.get_value = get_table_value
            
            widget = container

        else:  # Default to string type
            widget = QLineEdit(str(current_value) if current_value is not None else "")
            
        return widget
            
    def accept(self):
        """Apply properties and close dialog"""
        # Update node title
        self.node_item.title = self.title_edit.text()
        
        # Update custom properties
        for prop_name, widget in self.property_widgets.items():
            if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                value = widget.value()
            elif isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, QComboBox):
                value = widget.currentText()
            elif isinstance(widget, QWidget) and hasattr(widget.layout(), 'itemAt') and widget.layout().count() > 0:
                # This is our table container widget
                table_widget = widget.layout().itemAt(0).widget()
                if isinstance(table_widget, QTableWidget):
                    # Use the custom get_value method we attached to the QTableWidget
                    value = table_widget.get_value()
                else:
                    value = None
            else:  # QLineEdit
                value = widget.text()
                
            self.node_item.property_values[prop_name] = value
        
        # Update the node's appearance
        self.node_item.update()
        
        super().accept()


class PipelineScene(QGraphicsScene):
    """Scene that contains all pipeline elements"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 2000, 2000)
        
        # Connection related variables
        self.connection_signals = ConnectionSignals()
        self.active_connection = None
        self.temp_line = None
        self.source_port = None
        self.dest_port = None
        
        # Node types
        self.node_types = self.create_node_types()
        
        # Connect signals
        self.connection_signals.connectionStarted.connect(self.start_connection)
        self.connection_signals.connectionMade.connect(self.finish_connection)
    
    def create_node_types(self):
        #3.2206*(i**3) - 5.4091*(i**2) + 3.1979*i,
        """Create predefined node types with properties"""
        # Data Source properties
        grid_props = [
            NodeProperty("num_v_lines", "int", default_value=5, 
                        description="Number of squares in width of grid"),
            NodeProperty("num_h_lines", "int", default_value=5, 
                        description="Number of squares in height of grid")
        ]

        cubic_fun_props = [
            NodeProperty("a_coeff", "float", default_value=3.22, 
                        description=""),
            NodeProperty("b_coeff", "float", default_value=-5.41, 
                        description=""),
            NodeProperty("c_coeff", "float", default_value=3.20, 
                        description=""),
            NodeProperty("d_coeff", "float", default_value=0, 
                        description="")
        ]

        piecewise_fun_props = [
            NodeProperty("points", "table", default_value=[(0, 0), (0.5, 0.5), (1, 1)], 
                        description="")
        ]
        
        # Transform properties
        # shape_repeater_props = [
        #     NodeProperty("Operation", "enum", default_value="Map", 
        #                 options=["Map", "Filter", "GroupBy", "Aggregate"], 
        #                 description="Transformation operation type"),
        #     NodeProperty("Formula", "string", default_value="value * 2",
        #                 description="Formula or expression to apply"),
        #     NodeProperty("Column", "string", default_value="",
        #                 description="Target column name")
        # ]

        shape_repeater_props = [
            NodeProperty("shape", "string", default_value="triangle", 
                        description="")
        ]
        
        # Filter properties
        surface_warp_props = [
            NodeProperty("Condition", "string", default_value="value > 0",
                        description="Filter condition expression"),
            NodeProperty("Keep Nulls", "bool", default_value=False,
                        description="Keep null values when filtering")
        ]
        
        # Merger properties
        canvas_props = [
            NodeProperty("Join Type", "enum", default_value="Inner", 
                        options=["Inner", "Left", "Right", "Outer"], 
                        description="Type of join operation"),
            NodeProperty("Join Keys", "string", default_value="id,name",
                        description="Comma-separated list of join key fields")
        ]

        return [
            NodeType("Grid", input_count=2, output_count=1, color=QColor(220, 230, 250), properties=grid_props, node_class=GridNode),
            NodeType("Cubic Function", input_count=0, output_count=1, color=QColor(220, 230, 250), properties=cubic_fun_props, node_class=CubicFunNode),
            NodeType("Piecewise Linear Function", input_count=0, output_count=1, color=QColor(220, 230, 250), properties=piecewise_fun_props, node_class=PiecewiseFunNode),
            NodeType("Position Warp", input_count=1, output_count=1, color=QColor(220, 230, 250), properties=[], node_class=PosWarpNode),
            NodeType("Relative Warp", input_count=1, output_count=1, color=QColor(220, 230, 250), properties=[], node_class=RelWarpNode),
            NodeType("Shape Repeater", input_count=1, output_count=1, color=QColor(220, 250, 220), properties=shape_repeater_props, node_class=ShapeRepeaterNode),
            NodeType("Surface Warp", input_count=1, output_count=1, color=QColor(250, 220, 220), properties=surface_warp_props),
            NodeType("Canvas", input_count=1, output_count=0, color=QColor(240, 220, 240), properties=canvas_props)
        ]
    
    def add_node_from_type(self, node_type, pos):
        """Add a new node of the given type at the specified position"""
        new_node = NodeItem(pos.x(), pos.y(), 150, 80, node_type)
        self.addItem(new_node)
        return new_node
    
    def add_custom_node(self, pos):
        """Add a custom node with user-defined inputs and outputs"""
        node_name, ok = QInputDialog.getText(None, "Custom Node", "Enter node name:")
        if not ok or not node_name:
            return
        
        input_count, ok = QInputDialog.getInt(None, "Custom Node", "Number of input ports:", 1, 0, 10, 1)
        if not ok:
            return
        
        output_count, ok = QInputDialog.getInt(None, "Custom Node", "Number of output ports:", 1, 0, 10, 1)
        if not ok:
            return
        
        color = QColorDialog.getColor(QColor(200, 230, 250), None, "Select Node Color")
        if not color.isValid():
            color = QColor(200, 230, 250)
        
        # Define custom properties
        custom_props = [
            NodeProperty("Description", "string", default_value="Custom node"),
            NodeProperty("Process Time", "float", default_value=1.0, min_value=0.1, max_value=100.0),
            NodeProperty("Enabled", "bool", default_value=True)
        ]
        
        custom_type = NodeType(node_name, input_count, output_count, color, properties=custom_props)
        return self.add_node_from_type(custom_type, pos)
    
    def edit_node_properties(self, node):
        """Open a dialog to edit the node's properties"""
        dialog = NodePropertiesDialog(node)
        if dialog.exec_() == QDialog.Accepted:
            node.update()
        
    def start_connection(self, source_port):
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
    
    def finish_connection(self, source_port, dest_port):
        """Create a permanent connection between source and destination ports"""
        if source_port and dest_port and source_port != dest_port:
            # Don't connect if they're on the same node
            if source_port.parentItem() != dest_port.parentItem():
                # Check if connection already exists
                connection_exists = False
                for edge in source_port.edges:
                    if hasattr(edge, 'dest_port') and edge.dest_port == dest_port:
                        connection_exists = True
                        break
                
                # Check if target port already has a connection
                target_has_connection = len(dest_port.edges) > 0
                
                if not connection_exists and not target_has_connection:
                    edge = EdgeItem(source_port, dest_port)
                    self.addItem(edge)
        
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
            
            if isinstance(item, PortItem) and not item.is_input:
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
            if isinstance(item, PortItem) and item.is_input:
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
            if isinstance(item, PortItem) and item.is_input:
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

    def visualize_node(self, node):
        """Display a visualization of the node's output with fixed size"""
        if node.node_type.node_class is not None:
            width = 500
            height = 500

            try:
                extracted_node = node.get_node()
            except InvalidInputNodesLength as e:
                # Show message if no visualizer is available
                QMessageBox.information(None, "Visualization", 
                                    f"No visualization available: {e}")
                return
                
            svg_path = extracted_node.visualise(height, width/height)
            if svg_path is None:
                # Show message if no visualizer is available
                QMessageBox.information(None, "Visualization", 
                                    f"No visualization available for node type: {node.node_type.name}")
                return
            
            # Create a dialog to display the SVG
            dialog = QDialog()
            dialog.setWindowTitle(f"Visualization: {node.title}")
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            
            # Use QSvgWidget with fixed size
            svg_widget = QSvgWidget(svg_path)
            width = 500
            height = 500
            svg_widget.setFixedSize(width, height)
            
            # Create layout and set fixed size for dialog
            layout = QVBoxLayout()
            layout.setContentsMargins(10, 10, 10, 10)
            layout.addWidget(svg_widget, 0, Qt.AlignCenter)
            dialog.setLayout(layout)
            
            # Fix the dialog size to match the SVG size plus margins
            dialog.setFixedSize(width, height)
            
            # Clean up the temporary file when the dialog is closed
            dialog.finished.connect(lambda: os.remove(svg_path))
            
            dialog.exec_()
        else:
            # Show message if no visualizer is available
            QMessageBox.information(None, "Visualization", 
                                f"No visualization available for node type: {node.node_type.name}")

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
            
            rename_action = QAction("Rename Node", menu)
            rename_action.triggered.connect(lambda: self.rename_node(clicked_item))
            
            delete_action = QAction("Delete Node", menu)
            delete_action.triggered.connect(lambda: self.delete_node(clicked_item))
            
            # Add visualize action
            visualize_action = QAction("Visualize", menu)
            visualize_action.triggered.connect(lambda: self.visualize_node(clicked_item))
            
            menu.addAction(properties_action)
            menu.addAction(rename_action)
            menu.addAction(delete_action)
            menu.addAction(visualize_action)  # Add the new action
            menu.exec_(event.screenPos())
        elif event.scenePos().x() >= 0 and event.scenePos().y() >= 0:
            # Context menu for empty space - Node type selection
            menu = QMenu()
            add_node_menu = QMenu("Add Node", menu)
            menu.addMenu(add_node_menu)
            
            # Add actions for each node type
            for node_type in self.node_types:
                if node_type.name == "Custom Node":
                    # Special handling for custom node
                    action = QAction(node_type.name, add_node_menu)
                    action.triggered.connect(lambda checked=False, pos=event.scenePos(): self.add_custom_node(pos))
                else:
                    action = QAction(node_type.name, add_node_menu)
                    action.triggered.connect(lambda checked=False, nt=node_type, pos=event.scenePos(): 
                                           self.add_node_from_type(nt, pos))
                add_node_menu.addAction(action)
            
            menu.exec_(event.screenPos())
    
    def nodes(self):
        """Return all nodes in the scene"""
        return [item for item in self.items() if isinstance(item, NodeItem)]
    
    def rename_node(self, node):
        """Rename the given node"""
        new_name, ok = QInputDialog.getText(None, "Rename Node", "Enter new name:", text=node.title)
        if ok and new_name:
            node.title = new_name
            node.update()
    
    def delete_edge(self, edge):
        """Delete the given edge"""
        edge.source_port.remove_edge(edge)
        edge.dest_port.remove_edge(edge)
        self.removeItem(edge)
    
    def delete_node(self, node):
        """Delete the given node and all its connections"""
        # Remove all connected edges first
        for port in node.input_ports + node.output_ports:
            for edge in list(port.edges):  # Use a copy to avoid issues while removing
                self.delete_edge(edge)
        
        self.removeItem(node)


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
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Editor")
        self.setGeometry(100, 100, 1000, 800)
        
        # Create the scene and view
        self.scene = PipelineScene()
        self.view = PipelineView(self.scene)
        self.setCentralWidget(self.view)
        
        # Add some example nodes
        self.add_example_nodes()
        
        # Create a status bar with instructions
        self.statusBar().showMessage("Right-click for node menu | Drag from output port (green) to input port (gray) to create connections")
        
        self.show()
    
    def add_example_nodes(self):
        """Add some example nodes to the scene"""
        grid = self.scene.node_types[0]
        shape_repeater = self.scene.node_types[1]
        surface_warp = self.scene.node_types[2]
        canvas = self.scene.node_types[3]

        node1 = self.scene.add_node_from_type(grid, QLineF(100, 100, 0, 0).p1())
        node2 = self.scene.add_node_from_type(shape_repeater, QLineF(400, 100, 0, 0).p1())
        node3 = self.scene.add_node_from_type(surface_warp, QLineF(400, 250, 0, 0).p1())
        node4 = self.scene.add_node_from_type(canvas, QLineF(700, 175, 0, 0).p1())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = PipelineEditor()
    sys.exit(app.exec_())